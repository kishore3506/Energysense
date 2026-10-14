import optuna
import threading
import uuid
import time
from typing import Dict, Any, Optional, List
import tensorflow as tf
from tensorflow import keras

from config import DATASETS_DIR, DEFAULT_DATASET
from data.loader import load_dataset
from data.preprocessor import EnergyPreprocessor
from models.lstm_model import build_lstm_model
from models.gru_model import build_gru_model
from services.db_service import save_tuning_trial, get_tuning_trials

# Optuna logging verbosity
optuna.logging.set_verbosity(optuna.logging.WARNING)

tuning_jobs: Dict[str, Dict[str, Any]] = {}

def run_tuning_worker(
    job_id: str,
    dataset_name: str,
    model_type: str,
    n_trials: int,
    epochs_per_trial: int = 5
):
    try:
        tuning_jobs[job_id]["status"] = "running"
        dataset_path = DATASETS_DIR / dataset_name
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")
            
        df, ts_col, target_col, _ = load_dataset(dataset_path)
        
        study = optuna.create_study(direction="minimize", study_name=job_id)
        best_loss = float("inf")
        
        for trial_idx in range(n_trials):
            trial = study.ask()
            
            # Suggest Hyperparameters
            lookback = trial.suggest_categorical("lookback", [12, 24, 36])
            lstm_units = trial.suggest_categorical("lstm_units", [32, 64])
            dropout = trial.suggest_float("dropout", 0.1, 0.3, step=0.1)
            learning_rate = trial.suggest_categorical("learning_rate", [0.001, 0.003])
            batch_size = trial.suggest_categorical("batch_size", [32, 64])
            
            # Prepare Preprocessor
            prep = EnergyPreprocessor(lookback=lookback, horizon=12)
            prep_data = prep.fit_transform_train(df, ts_col, target_col)
            
            X_train = prep_data["X_train"]
            y_train = prep_data["y_train"]
            X_val = prep_data["X_val"]
            y_val = prep_data["y_val"]
            num_features = prep_data["num_features"]
            
            # Build model
            if model_type.upper() == "GRU":
                model = build_gru_model(
                    lookback=lookback,
                    num_features=num_features,
                    horizon=12,
                    units=[lstm_units, max(16, lstm_units // 2)],
                    dropout=dropout,
                    learning_rate=learning_rate
                )
            else:
                model = build_lstm_model(
                    lookback=lookback,
                    num_features=num_features,
                    horizon=12,
                    units=[lstm_units, max(16, lstm_units // 2)],
                    dropout=dropout,
                    learning_rate=learning_rate
                )
                
            # Quick training for hyperparameter ranking
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs_per_trial,
                batch_size=batch_size,
                verbose=0
            )
            
            val_loss = float(min(history.history["val_loss"]))
            study.tell(trial, val_loss)
            
            is_best = 1 if val_loss < best_loss else 0
            if is_best:
                best_loss = val_loss
                
            # Log to SQLite
            save_tuning_trial(
                study_id=job_id,
                trial_number=trial_idx + 1,
                dataset_name=dataset_name,
                model_type=model_type,
                lookback=lookback,
                lstm_units=lstm_units,
                dropout=round(dropout, 2),
                learning_rate=learning_rate,
                batch_size=batch_size,
                val_loss=round(val_loss, 5),
                is_best=is_best
            )
            
            # Update job state
            trial_summary = {
                "trial_number": trial_idx + 1,
                "lookback": lookback,
                "lstm_units": lstm_units,
                "dropout": round(dropout, 2),
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "val_loss": round(val_loss, 5),
                "is_best": bool(is_best)
            }
            tuning_jobs[job_id]["trials"].append(trial_summary)
            tuning_jobs[job_id]["progress"] = int(((trial_idx + 1) / n_trials) * 100)
            
        tuning_jobs[job_id]["status"] = "completed"
        tuning_jobs[job_id]["progress"] = 100
        tuning_jobs[job_id]["best_params"] = study.best_params
        tuning_jobs[job_id]["best_val_loss"] = round(study.best_value, 5)
        
    except Exception as e:
        tuning_jobs[job_id]["status"] = "failed"
        tuning_jobs[job_id]["error"] = str(e)

def start_hyperparameter_tuning(
    dataset_name: str = DEFAULT_DATASET,
    model_type: str = "LSTM",
    n_trials: int = 5,
    epochs_per_trial: int = 4
) -> str:
    """Spawns asynchronous Optuna study optimization in background thread."""
    job_id = f"tune_{str(uuid.uuid4())[:8]}"
    
    tuning_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "model_type": model_type,
        "dataset_name": dataset_name,
        "total_trials": n_trials,
        "trials": [],
        "best_params": None,
        "best_val_loss": None,
        "error": None,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    thread = threading.Thread(
        target=run_tuning_worker,
        kwargs={
            "job_id": job_id,
            "dataset_name": dataset_name,
            "model_type": model_type,
            "n_trials": n_trials,
            "epochs_per_trial": epochs_per_trial
        },
        daemon=True
    )
    thread.start()
    return job_id

def get_tuning_status(job_id: str) -> Optional[Dict[str, Any]]:
    return tuning_jobs.get(job_id)
