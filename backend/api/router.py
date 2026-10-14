import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Response
from fastapi.responses import PlainTextResponse

from config import DATASETS_DIR, DEFAULT_DATASET
from schemas.schemas import TrainModelRequest, ForecastRequest, TuneModelRequest
from data.loader import load_dataset, get_dataset_summary, auto_detect_columns
from models.evaluator import get_metric_definitions
from services.training_service import (
    start_training, get_job_status, cached_artifacts
)
from services.forecasting_service import run_forecast, export_forecast_csv
from services.insights_service import generate_energy_insights
from services.db_service import (
    get_latest_metrics, get_all_model_metrics, get_forecast_history, get_forecast_by_id
)

router = APIRouter(prefix="/api")
current_active_dataset = DEFAULT_DATASET

@router.get("/health")
def health_check():
    """Returns backend and environment health status."""
    return {
        "status": "healthy",
        "service": "EnergySense Backend API",
        "version": "1.0.0",
        "active_dataset": current_active_dataset,
        "is_model_trained": cached_artifacts.get("model") is not None
    }

@router.get("/dataset/list")
def list_datasets():
    """Lists all available CSV datasets in the datasets directory."""
    files = []
    for p in DATASETS_DIR.glob("*.csv"):
        files.append({
            "name": p.name,
            "size_kb": round(p.stat().st_size / 1024, 1),
            "is_active": p.name == current_active_dataset
        })
    return {"datasets": files, "active": current_active_dataset}

@router.post("/dataset/select")
def select_dataset(dataset_name: str = Query(..., description="Dataset filename to select")):
    """Sets the active dataset for analysis and training."""
    global current_active_dataset
    path = DATASETS_DIR / dataset_name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found.")
    current_active_dataset = dataset_name
    return {"message": f"Active dataset set to '{dataset_name}'", "active_dataset": current_active_dataset}

@router.get("/dataset/summary")
def dataset_summary(dataset_name: Optional[str] = Query(None)):
    """Computes and returns structural & statistical summary of the selected dataset."""
    name = dataset_name or current_active_dataset
    path = DATASETS_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")
    try:
        df, ts_col, target_col, warnings = load_dataset(path)
        summary = get_dataset_summary(df, ts_col, target_col)
        summary["dataset_name"] = name
        summary["warnings"] = warnings
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dataset/preview")
def dataset_preview(
    dataset_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=5, le=500)
):
    """Returns safe preview records and column descriptors for frontend inspection."""
    name = dataset_name or current_active_dataset
    path = DATASETS_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")
    try:
        df, ts_col, target_col, warnings = load_dataset(path)
        preview_df = df.head(limit).copy()
        
        # Convert timestamp to string for JSON serialization
        preview_df[ts_col] = preview_df[ts_col].astype(str)
        
        records = preview_df.to_dict(orient="records")
        return {
            "dataset_name": name,
            "timestamp_column": ts_col,
            "target_column": target_col,
            "columns": list(df.columns),
            "total_rows": len(df),
            "preview_limit": limit,
            "rows": records,
            "warnings": warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dataset/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Validates and saves an uploaded CSV dataset."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    save_path = DATASETS_DIR / file.filename
    try:
        # Save file to datasets folder
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Validate uploaded CSV
        df, ts_col, target_col, warnings = load_dataset(save_path)
        global current_active_dataset
        current_active_dataset = file.filename
        
        return {
            "message": f"File '{file.filename}' uploaded and validated successfully.",
            "filename": file.filename,
            "total_rows": len(df),
            "detected_timestamp": ts_col,
            "detected_target": target_col,
            "warnings": warnings
        }
    except Exception as e:
        if save_path.exists():
            save_path.unlink() # Cleanup invalid file
        raise HTTPException(status_code=400, detail=f"Dataset validation failed: {str(e)}")

@router.post("/model/train")
def train_model(request: TrainModelRequest):
    """Starts asynchronous model training in a background thread."""
    dataset_name = request.dataset_name or current_active_dataset
    path = DATASETS_DIR / dataset_name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found.")
        
    try:
        job_id = start_training(
            dataset_name=dataset_name,
            model_type=request.model_type,
            lookback=request.lookback,
            horizon=request.horizon,
            epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            lstm_units=request.lstm_units,
            dropout=request.dropout
        )
        return {
            "message": f"{request.model_type} training started in background.",
            "job_id": job_id,
            "dataset_name": dataset_name,
            "epochs": request.epochs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

@router.get("/model/status/{job_id}")
def check_training_status(job_id: str):
    """Checks the real-time status and epoch progress of a training job."""
    status_info = get_job_status(job_id)
    if not status_info:
        raise HTTPException(status_code=404, detail=f"Training job '{job_id}' not found.")
    return status_info

@router.get("/model/metrics")
def get_metrics(model_type: Optional[str] = Query(None)):
    """Returns actual evaluation metrics, baseline comparison, and metric definitions."""
    latest_db_metrics = get_latest_metrics(model_type=model_type)
    all_history = get_all_model_metrics()
    definitions = get_metric_definitions()
    
    # Check if we have active in-memory artifacts
    active_test_metrics = cached_artifacts.get("test_metrics")
    active_baseline_metrics = cached_artifacts.get("baseline_metrics")
    active_chart_samples = cached_artifacts.get("chart_samples", [])
    active_model_type = cached_artifacts.get("model_type", "LSTM")

    return {
        "active_model_type": active_model_type,
        "latest_metrics": latest_db_metrics,
        "active_test_metrics": active_test_metrics,
        "active_baseline_metrics": active_baseline_metrics,
        "chart_samples": active_chart_samples,
        "definitions": definitions,
        "history": all_history
    }

@router.post("/forecast")
def generate_forecast(request: ForecastRequest):
    """Generates future energy consumption forecasts using the trained deep learning model."""
    dataset_name = request.dataset_name or current_active_dataset
    try:
        result = run_forecast(
            dataset_name=dataset_name,
            horizon=request.horizon,
            lookback=request.lookback,
            model_type=request.model_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/forecast/history")
def forecast_history(limit: int = Query(20, ge=1, le=100)):
    """Retrieves saved forecast records from the SQLite database."""
    history = get_forecast_history(limit=limit)
    return {"history": history}

@router.get("/forecast/export")
def export_forecast(forecast_id: Optional[int] = Query(None)):
    """Exports forecast results as downloadable CSV data."""
    if forecast_id is None:
        history = get_forecast_history(limit=1)
        if not history:
            raise HTTPException(status_code=404, detail="No forecasts available to export.")
        forecast_id = history[0]["id"]
        
    try:
        csv_content = export_forecast_csv(forecast_id)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=energysense_forecast_{forecast_id}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/insights")
def energy_insights(dataset_name: Optional[str] = Query(None)):
    """Returns data-derived energy usage patterns, peak loads, and actionable recommendations."""
    name = dataset_name or current_active_dataset
    try:
        insights = generate_energy_insights(dataset_name=name)
        return insights
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dataset/pca")
def dataset_pca(dataset_name: Optional[str] = Query(None)):
    """Computes Principal Component Analysis (PCA), scree plot, and feature loadings."""
    from data.dimensionality import compute_pca_analysis
    name = dataset_name or current_active_dataset
    try:
        result = compute_pca_analysis(dataset_name=name)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/model/tune")
def tune_model(request: TuneModelRequest):
    """Starts automated hyperparameter tuning via Optuna across recurrent architectures."""
    from services.tuning_service import start_hyperparameter_tuning
    dataset_name = request.dataset_name or current_active_dataset
    try:
        job_id = start_hyperparameter_tuning(
            dataset_name=dataset_name,
            model_type=request.model_type,
            n_trials=request.n_trials,
            epochs_per_trial=request.epochs_per_trial
        )
        return {
            "message": f"Optuna study started with {request.n_trials} trials.",
            "job_id": job_id,
            "dataset_name": dataset_name,
            "model_type": request.model_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/tune/status/{job_id}")
def check_tune_status(job_id: str):
    """Retrieves status and trial history for an Optuna hyperparameter study."""
    from services.tuning_service import get_tuning_status
    status = get_tuning_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Tuning job '{job_id}' not found.")
    return status

@router.get("/model/benchmark")
def model_benchmark(dataset_name: Optional[str] = Query(None)):
    """Executes comparative benchmarking against SOTA literature and baseline models."""
    from services.benchmarking_service import run_comparative_benchmark
    name = dataset_name or current_active_dataset
    try:
        return run_comparative_benchmark(dataset_name=name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/model/error-analysis")
def model_error_analysis(dataset_name: Optional[str] = Query(None)):
    """Performs rigorous statistical residual and error analysis (diurnal profile, bias, heteroscedasticity)."""
    from services.benchmarking_service import compute_rigorous_error_analysis
    name = dataset_name or current_active_dataset
    try:
        return compute_rigorous_error_analysis(dataset_name=name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
