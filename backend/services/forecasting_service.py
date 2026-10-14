import numpy as np
import pandas as pd
from datetime import timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import DATASETS_DIR, MODELS_DIR, DEFAULT_DATASET
from data.loader import load_dataset
from data.preprocessor import EnergyPreprocessor
from models.lstm_model import load_model
from models.baseline import PersistenceBaseline
from services.training_service import cached_artifacts
from services.db_service import save_forecast, get_forecast_history, get_forecast_by_id

def run_forecast(
    dataset_name: str = DEFAULT_DATASET,
    horizon: int = 24,
    lookback: int = 24,
    model_type: str = "LSTM"
) -> Dict[str, Any]:
    """
    Generates future energy consumption forecasts using the trained temporal deep learning model.
    """
    # 1. Retrieve model and preprocessor (from cache or load from disk)
    model = cached_artifacts.get("model")
    preprocessor: Optional[EnergyPreprocessor] = cached_artifacts.get("preprocessor")

    # If not cached, attempt to load most recent saved model
    if model is None or preprocessor is None:
        saved_models = sorted(list(MODELS_DIR.glob(f"*.keras")), key=lambda p: p.stat().st_mtime, reverse=True)
        saved_preps = sorted(list(MODELS_DIR.glob(f"*_prep.joblib")), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not saved_models or not saved_preps:
            raise RuntimeError("No trained model found. Please train a model first on the Model Training page.")
            
        model = load_model(saved_models[0])
        preprocessor = EnergyPreprocessor.load(saved_preps[0])
        cached_artifacts["model"] = model
        cached_artifacts["preprocessor"] = preprocessor

    # 2. Load dataset
    dataset_path = DATASETS_DIR / dataset_name
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset '{dataset_name}' not found.")
        
    df, ts_col, target_col, _ = load_dataset(dataset_path)

    # 3. Prepare inference window from latest observations
    inference_input = preprocessor.prepare_inference_input(df)

    # 4. Generate deep learning predictions
    scaled_pred = model.predict(inference_input, verbose=0) # shape (1, horizon)
    unscaled_pred = preprocessor.inverse_transform_targets(scaled_pred).flatten()

    # 5. Generate persistence baseline prediction for comparison
    baseline = PersistenceBaseline(horizon=len(unscaled_pred))
    scaled_base = baseline.predict(inference_input)
    unscaled_base = preprocessor.inverse_transform_targets(scaled_base).flatten()

    # 6. Generate future timestamps
    last_timestamp = pd.to_datetime(df[ts_col].iloc[-1])
    # Detect step frequency
    if len(df) > 1:
        step_diff = pd.to_datetime(df[ts_col].iloc[-1]) - pd.to_datetime(df[ts_col].iloc[-2])
    else:
        step_diff = timedelta(hours=1)

    future_records = []
    for step in range(len(unscaled_pred)):
        step_time = last_timestamp + (step + 1) * step_diff
        pred_val = float(round(max(0.0, unscaled_pred[step]), 2))
        base_val = float(round(max(0.0, unscaled_base[step]), 2))
        future_records.append({
            "step": step + 1,
            "timestamp": step_time.strftime("%Y-%m-%d %H:%M:%S"),
            "predicted": pred_val,
            "baseline": base_val,
            "unit": "Wh" if "wh" in target_col.lower() else "kW"
        })

    # Historical context: last lookback actual points for smooth plotting
    context_df = df.iloc[-lookback:]
    historical_context = []
    for _, row in context_df.iterrows():
        historical_context.append({
            "timestamp": str(row[ts_col]),
            "actual": float(round(row[target_col], 2))
        })

    # Summary Statistics
    pred_values = [r["predicted"] for r in future_records]
    peak_pred = max(pred_values)
    peak_step_idx = pred_values.index(peak_pred)
    peak_time = future_records[peak_step_idx]["timestamp"]
    mean_pred = float(np.mean(pred_values))
    total_pred = float(np.sum(pred_values))
    
    # Comparison with recent history
    recent_actual_mean = float(context_df[target_col].mean())
    pct_diff = round(((mean_pred - recent_actual_mean) / (recent_actual_mean + 1e-5)) * 100.0, 2)

    summary_stats = {
        "mean_forecast": round(mean_pred, 2),
        "peak_forecast": round(peak_pred, 2),
        "peak_time": peak_time,
        "total_forecast": round(total_pred, 2),
        "recent_historical_mean": round(recent_actual_mean, 2),
        "percentage_change": pct_diff,
        "target_column": target_col,
        "unit": "Wh" if "wh" in target_col.lower() else "kW"
    }

    # Save to SQLite
    record_id = save_forecast(
        dataset_name=dataset_name,
        model_type=model_type,
        lookback=lookback,
        horizon=len(future_records),
        frequency="Hourly" if step_diff.total_seconds() == 3600 else f"{int(step_diff.total_seconds()//60)}m",
        summary_stats=summary_stats,
        predictions=future_records
    )

    return {
        "forecast_id": record_id,
        "dataset_name": dataset_name,
        "model_type": model_type,
        "lookback": lookback,
        "horizon": len(future_records),
        "summary": summary_stats,
        "predictions": future_records,
        "historical_context": historical_context
    }

def export_forecast_csv(forecast_id: int) -> str:
    """Exports forecast results to CSV format."""
    data = get_forecast_by_id(forecast_id)
    if not data:
        raise ValueError(f"Forecast ID {forecast_id} not found.")
        
    predictions = data.get("predictions", [])
    if not predictions:
        raise ValueError("No prediction records found for this forecast ID.")
        
    df_export = pd.DataFrame(predictions)
    return df_export.to_csv(index=False)
