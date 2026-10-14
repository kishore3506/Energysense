import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
import sys

# Ensure backend directory is in path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.loader import load_dataset, auto_detect_columns, get_dataset_summary
from data.preprocessor import EnergyPreprocessor
from models.lstm_model import build_lstm_model
from models.gru_model import build_gru_model
from models.baseline import PersistenceBaseline
from models.evaluator import calculate_metrics
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def create_synthetic_energy_df(rows: int = 120):
    dates = pd.date_range("2024-01-01 00:00:00", periods=rows, freq="h")
    values = 50.0 + 20.0 * np.sin(np.arange(rows) * 2 * np.pi / 24) + np.random.normal(0, 1.0, rows)
    return pd.DataFrame({
        "timestamp": dates.strftime("%Y-%m-%d %H:%M:%S"),
        "energy_consumption": np.maximum(5.0, values),
        "temperature": 15.0 + 5.0 * np.cos(np.arange(rows) * 2 * np.pi / 24)
    })

def test_data_loader_and_autodetect():
    df = create_synthetic_energy_df(80)
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
        df.to_csv(tmp.name, index=False)
        tmp_path = Path(tmp.name)

    try:
        loaded_df, ts_col, target_col, warnings = load_dataset(tmp_path)
        assert ts_col == "timestamp"
        assert target_col == "energy_consumption"
        assert len(loaded_df) == 80
        assert pd.api.types.is_datetime64_any_dtype(loaded_df[ts_col])
        
        summary = get_dataset_summary(loaded_df, ts_col, target_col)
        assert summary["total_rows"] == 80
        assert "mean" in summary["metrics"]
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def test_chronological_split_no_leakage():
    df = create_synthetic_energy_df(100)
    preprocessor = EnergyPreprocessor(lookback=12, horizon=6)
    
    train_df, val_df, test_df = preprocessor.chronological_split(df, train_ratio=0.7, val_ratio=0.15)
    
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15
    
    # Chronological integrity check: timestamps must strictly follow order
    assert pd.to_datetime(train_df['timestamp'].iloc[-1]) < pd.to_datetime(val_df['timestamp'].iloc[0])
    assert pd.to_datetime(val_df['timestamp'].iloc[-1]) < pd.to_datetime(test_df['timestamp'].iloc[0])

def test_sequence_generation_shapes():
    lookback = 10
    horizon = 5
    num_features = 4
    total_steps = 50
    
    features = np.random.randn(total_steps, num_features).astype(np.float32)
    targets = np.random.randn(total_steps, 1).astype(np.float32)
    features[:, 0] = targets[:, 0] # Column 0 represents the target
    
    prep = EnergyPreprocessor(lookback=lookback, horizon=horizon)
    X, y = prep.create_sequences(features, targets)
    
    expected_samples = total_steps - lookback - horizon + 1
    assert X.shape == (expected_samples, lookback, num_features)
    assert y.shape == (expected_samples, horizon)
    
    # Ensure y targets match the exact subsequent time steps (no future or past shift mismatch)
    np.testing.assert_array_almost_equal(X[0, -1, 0], targets[lookback - 1, 0])
    np.testing.assert_array_almost_equal(y[0, 0], targets[lookback, 0])
    np.testing.assert_array_almost_equal(y[0, -1], targets[lookback + horizon - 1, 0])

def test_model_prediction_shapes():
    lookback = 12
    horizon = 6
    num_features = 8
    batch_size = 4
    
    lstm_model = build_lstm_model(lookback=lookback, num_features=num_features, horizon=horizon)
    gru_model = build_gru_model(lookback=lookback, num_features=num_features, horizon=horizon)
    
    dummy_input = np.random.randn(batch_size, lookback, num_features).astype(np.float32)
    
    lstm_preds = lstm_model.predict(dummy_input, verbose=0)
    gru_preds = gru_model.predict(dummy_input, verbose=0)
    
    assert lstm_preds.shape == (batch_size, horizon)
    assert gru_preds.shape == (batch_size, horizon)

def test_baseline_persistence_prediction():
    lookback = 12
    horizon = 6
    num_features = 3
    batch_size = 5
    
    dummy_input = np.random.randn(batch_size, lookback, num_features).astype(np.float32)
    baseline = PersistenceBaseline(horizon=horizon)
    
    preds = baseline.predict(dummy_input)
    assert preds.shape == (batch_size, horizon)
    
    # Target is column index 0; every step in the forecast horizon should equal the last observed step
    for b in range(batch_size):
        expected_val = dummy_input[b, -1, 0]
        np.testing.assert_array_almost_equal(preds[b], np.repeat(expected_val, horizon))

def test_metric_calculations():
    y_true = np.array([[10.0, 20.0], [30.0, 40.0]])
    y_pred = np.array([[11.0, 19.0], [32.0, 38.0]]) # Errors are 1.0, 1.0, 2.0, 2.0
    
    metrics = calculate_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert "mape" in metrics
    
    # MAE = (1 + 1 + 2 + 2) / 4 = 1.5
    assert metrics["mae"] == 1.5
    assert metrics["rmse"] > 1.5
    assert metrics["r2"] > 0.9

def test_api_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "EnergySense" in data["service"]

def test_preprocessor_fit_transform_and_inverse():
    df = create_synthetic_energy_df(200)
    prep = EnergyPreprocessor(lookback=12, horizon=6)
    prep_res = prep.fit_transform_train(df, "timestamp", "energy_consumption")
    
    assert prep.is_fitted
    assert len(prep_res["feature_names"]) >= 2
    assert prep_res["X_train"].shape[1] == 12
    assert prep_res["y_train"].shape[1] == 6
    
    # Test inverse transform
    dummy_scaled = np.array([[0.5, 0.8]])
    unscaled = prep.inverse_transform_targets(dummy_scaled)
    assert unscaled.shape == (1, 2)
    assert np.all(unscaled > 0)

def test_insights_generation():
    from services.insights_service import generate_energy_insights
    insights = generate_energy_insights(dataset_name="uci_appliances_hourly.csv")
    
    assert "statistics" in insights
    assert "peak_hours" in insights
    assert "hourly_breakdown" in insights
    assert "daily_breakdown" in insights
    assert "recommendations" in insights
    assert len(insights["recommendations"]) > 0

def test_api_dataset_summary_and_preview():
    res_summary = client.get("/api/dataset/summary?dataset_name=uci_appliances_hourly.csv")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_rows"] > 1000
    assert "metrics" in summary
    
    res_preview = client.get("/api/dataset/preview?dataset_name=uci_appliances_hourly.csv&limit=10")
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert len(preview["rows"]) == 10

def test_pca_dimensionality_reduction():
    res = client.get("/api/dataset/pca?dataset_name=uci_appliances_hourly.csv")
    assert res.status_code == 200
    data = res.json()
    assert "scree_data" in data
    assert "feature_loadings" in data
    assert len(data["scree_data"]) > 0
    assert data["scree_data"][0]["explained_variance"] > 0

def test_bilstm_architecture():
    from models.bilstm_model import build_bilstm_model
    bilstm = build_bilstm_model(lookback=12, num_features=8, horizon=6)
    dummy_x = np.random.randn(2, 12, 8).astype(np.float32)
    preds = bilstm.predict(dummy_x, verbose=0)
    assert preds.shape == (2, 6)

def test_comparative_benchmark_and_error_analysis():
    res_bench = client.get("/api/model/benchmark?dataset_name=uci_appliances_hourly.csv")
    assert res_bench.status_code == 200
    bench = res_bench.json()
    assert "benchmark_table" in bench
    assert "paper_citation" in bench
    assert len(bench["benchmark_table"]) >= 4

    res_err = client.get("/api/model/error-analysis?dataset_name=uci_appliances_hourly.csv")
    assert res_err.status_code == 200
    err_data = res_err.json()
    assert "statistical_moments" in err_data
    assert "diurnal_error_profile" in err_data

