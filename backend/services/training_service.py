import threading
import uuid
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import tensorflow as tf
from tensorflow import keras

from config import MODELS_DIR, DATASETS_DIR, DEFAULT_DATASET
from data.loader import load_dataset
from data.preprocessor import EnergyPreprocessor
from models.lstm_model import build_lstm_model, save_model
from models.gru_model import build_gru_model
from models.baseline import PersistenceBaseline
from models.evaluator import calculate_metrics
from services.db_service import save_model_metrics

# Global in-memory job registry
training_jobs: Dict[str, Dict[str, Any]] = {}
# Active trained preprocessors & models cache
cached_artifacts: Dict[str, Any] = {}

class EpochProgressCallback(keras.callbacks.Callback):
    def __init__(self, job_id: str, total_epochs: int):
        super().__init__()
        self.job_id = job_id
        self.total_epochs = total_epochs

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        train_loss = float(logs.get("loss", 0.0))
        val_loss = float(logs.get("val_loss", 0.0))
        train_mae = float(logs.get("mae", 0.0))
        val_mae = float(logs.get("val_mae", 0.0))
        
        job = training_jobs.get(self.job_id)
        if job:
            job["current_epoch"] = epoch + 1
            job["progress"] = int(((epoch + 1) / self.total_epochs) * 100)
            job["loss_history"].append({
                "epoch": epoch + 1,
                "train_loss": round(train_loss, 6),
                "val_loss": round(val_loss, 6),
                "train_mae": round(train_mae, 4),
                "val_mae": round(val_mae, 4)
            })

def run_training_worker(
    job_id: str,
    dataset_name: str,
    model_type: str,
    lookback: int,
    horizon: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    lstm_units: List[int],
    dropout: float
):
    try:
        training_jobs[job_id]["status"] = "running"
        dataset_path = DATASETS_DIR / dataset_name
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")
            
        # 1. Load Dataset
        df, ts_col, target_col, warnings = load_dataset(dataset_path)
        training_jobs[job_id]["dataset_info"] = {
            "rows": len(df),
            "timestamp_col": ts_col,
            "target_col": target_col,
            "warnings": warnings
        }

        # 2. Preprocess & Chronological Split
        preprocessor = EnergyPreprocessor(lookback=lookback, horizon=horizon)
        prep_data = preprocessor.fit_transform_train(df, ts_col, target_col)
        
        X_train = prep_data["X_train"]
        y_train = prep_data["y_train"]
        X_val = prep_data["X_val"]
        y_val = prep_data["y_val"]
        X_test = prep_data["X_test"]
        y_test = prep_data["y_test"]
        test_df = prep_data["test_df"]
        num_features = prep_data["num_features"]

        # 3. Model Architecture
        if model_type.upper() == "GRU":
            model = build_gru_model(
                lookback=lookback,
                num_features=num_features,
                horizon=horizon,
                units=lstm_units,
                dropout=dropout,
                learning_rate=learning_rate
            )
        elif model_type.upper() in ["BILSTM", "BI-LSTM", "BIDIRECTIONAL"]:
            from models.bilstm_model import build_bilstm_model
            model = build_bilstm_model(
                lookback=lookback,
                num_features=num_features,
                horizon=horizon,
                units=[max(16, u // 2) for u in lstm_units],
                dropout=dropout,
                learning_rate=learning_rate
            )
        else:
            model = build_lstm_model(
                lookback=lookback,
                num_features=num_features,
                horizon=horizon,
                units=lstm_units,
                dropout=dropout,
                learning_rate=learning_rate
            )

        # 4. Callbacks
        progress_cb = EpochProgressCallback(job_id=job_id, total_epochs=epochs)
        early_stop_cb = keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=0
        )

        # 5. Model Fit
        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[progress_cb, early_stop_cb],
            verbose=0
        )

        # 6. Evaluation on Chronological Test Set
        scaled_test_preds = model.predict(X_test, verbose=0)
        # Invert predictions and actuals to physical engineering units
        unscaled_test_preds = preprocessor.inverse_transform_targets(scaled_test_preds)
        unscaled_test_actuals = preprocessor.inverse_transform_targets(y_test)

        test_metrics = calculate_metrics(unscaled_test_actuals, unscaled_test_preds)

        # 7. Baseline Model Evaluation on the EXACT same test set
        baseline = PersistenceBaseline(horizon=horizon)
        scaled_baseline_preds = baseline.predict(X_test)
        unscaled_baseline_preds = preprocessor.inverse_transform_targets(scaled_baseline_preds)
        baseline_metrics = calculate_metrics(unscaled_test_actuals, unscaled_baseline_preds)

        # 8. Save Artifacts
        model_filename = f"{model_type.lower()}_{job_id[:8]}.keras"
        prep_filename = f"{model_type.lower()}_{job_id[:8]}_prep.joblib"
        model_save_path = MODELS_DIR / model_filename
        prep_save_path = MODELS_DIR / prep_filename

        save_model(model, model_save_path)
        preprocessor.save(prep_save_path)

        # Cache active model
        cached_artifacts["model"] = model
        cached_artifacts["preprocessor"] = preprocessor
        cached_artifacts["model_type"] = model_type
        cached_artifacts["model_path"] = str(model_save_path)
        cached_artifacts["prep_path"] = str(prep_save_path)
        cached_artifacts["dataset_name"] = dataset_name
        cached_artifacts["test_metrics"] = test_metrics
        cached_artifacts["baseline_metrics"] = baseline_metrics

        # Prepare Actual vs Predicted chart sample for the dashboard (first 100 test sequence steps)
        chart_samples = []
        sample_limit = min(120, len(unscaled_test_actuals))
        test_timestamps = test_df[ts_col].iloc[lookback : lookback + sample_limit].astype(str).tolist()
        
        for idx in range(sample_limit):
            chart_samples.append({
                "timestamp": test_timestamps[idx] if idx < len(test_timestamps) else f"Step {idx}",
                "actual": float(round(unscaled_test_actuals[idx, 0], 2)),
                "predicted": float(round(unscaled_test_preds[idx, 0], 2)),
                "baseline": float(round(unscaled_baseline_preds[idx, 0], 2)),
                "error": float(round(abs(unscaled_test_actuals[idx, 0] - unscaled_test_preds[idx, 0]), 2))
            })

        cached_artifacts["chart_samples"] = chart_samples

        # 9. Save to Database
        loss_hist = training_jobs[job_id]["loss_history"]
        final_train_loss = loss_hist[-1]["train_loss"] if loss_hist else 0.0
        final_val_loss = loss_hist[-1]["val_loss"] if loss_hist else 0.0

        save_model_metrics(
            model_name=f"{model_type.upper()} Deep Forecaster",
            model_type=model_type.upper(),
            dataset_name=dataset_name,
            epochs=epochs,
            batch_size=batch_size,
            lookback=lookback,
            horizon=horizon,
            train_loss=final_train_loss,
            val_loss=final_val_loss,
            test_mae=test_metrics["mae"],
            test_rmse=test_metrics["rmse"],
            test_r2=test_metrics["r2"],
            test_mape=test_metrics["mape"],
            baseline_mae=baseline_metrics["mae"],
            baseline_rmse=baseline_metrics["rmse"],
            baseline_r2=baseline_metrics["r2"],
            baseline_mape=baseline_metrics["mape"],
            loss_history=loss_hist
        )

        training_jobs[job_id]["status"] = "completed"
        training_jobs[job_id]["progress"] = 100
        training_jobs[job_id]["metrics"] = test_metrics
        training_jobs[job_id]["baseline_metrics"] = baseline_metrics
        training_jobs[job_id]["chart_samples"] = chart_samples
        training_jobs[job_id]["model_path"] = str(model_save_path)

    except Exception as e:
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["error"] = str(e)

def start_training(
    dataset_name: str = DEFAULT_DATASET,
    model_type: str = "LSTM",
    lookback: int = 24,
    horizon: int = 24,
    epochs: int = 20,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    lstm_units: Optional[List[int]] = None,
    dropout: float = 0.2
) -> str:
    job_id = str(uuid.uuid4())
    if lstm_units is None:
        lstm_units = [64, 32]
        
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "current_epoch": 0,
        "total_epochs": epochs,
        "model_type": model_type,
        "dataset_name": dataset_name,
        "loss_history": [],
        "metrics": None,
        "baseline_metrics": None,
        "error": None,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    worker_thread = threading.Thread(
        target=run_training_worker,
        kwargs={
            "job_id": job_id,
            "dataset_name": dataset_name,
            "model_type": model_type,
            "lookback": lookback,
            "horizon": horizon,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "lstm_units": lstm_units,
            "dropout": dropout
        },
        daemon=True
    )
    worker_thread.start()
    return job_id

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return training_jobs.get(job_id)
