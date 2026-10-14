import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Model evaluation metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        trained_at TEXT NOT NULL,
        epochs INTEGER,
        batch_size INTEGER,
        lookback INTEGER,
        horizon INTEGER,
        train_loss REAL,
        val_loss REAL,
        test_mae REAL,
        test_rmse REAL,
        test_r2 REAL,
        test_mape REAL,
        baseline_mae REAL,
        baseline_rmse REAL,
        baseline_r2 REAL,
        baseline_mape REAL,
        loss_history TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)

    # Forecast runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        lookback INTEGER,
        horizon INTEGER,
        frequency TEXT,
        summary_stats TEXT,
        predictions_json TEXT
    );
    """)

    # Hyperparameter Optimization Trials table (Optuna / Experiment Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tuning_trials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        study_id TEXT NOT NULL,
        trial_number INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        lookback INTEGER,
        lstm_units INTEGER,
        dropout REAL,
        learning_rate REAL,
        batch_size INTEGER,
        val_loss REAL,
        is_best INTEGER DEFAULT 0
    );
    """)

    conn.commit()
    conn.close()

# Always ensure database schema is initialized on import
init_db()

def save_tuning_trial(
    study_id: str,
    trial_number: int,
    dataset_name: str,
    model_type: str,
    lookback: int,
    lstm_units: int,
    dropout: float,
    learning_rate: float,
    batch_size: int,
    val_loss: float,
    is_best: int = 0
):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO tuning_trials (
        study_id, trial_number, created_at, dataset_name, model_type,
        lookback, lstm_units, dropout, learning_rate, batch_size, val_loss, is_best
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        study_id, trial_number, now, dataset_name, model_type,
        lookback, lstm_units, dropout, learning_rate, batch_size, val_loss, is_best
    ))
    conn.commit()
    conn.close()

def get_tuning_trials(study_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if study_id:
        cursor.execute("SELECT * FROM tuning_trials WHERE study_id = ? ORDER BY trial_number ASC", (study_id,))
    else:
        cursor.execute("SELECT * FROM tuning_trials ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_model_metrics(
    model_name: str,
    model_type: str,
    dataset_name: str,
    epochs: int,
    batch_size: int,
    lookback: int,
    horizon: int,
    train_loss: float,
    val_loss: float,
    test_mae: float,
    test_rmse: float,
    test_r2: float,
    test_mape: float,
    baseline_mae: float,
    baseline_rmse: float,
    baseline_r2: float,
    baseline_mape: float,
    loss_history: List[Dict[str, float]]
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Mark earlier models of same type as inactive
    cursor.execute("UPDATE model_metrics SET is_active = 0 WHERE model_type = ?", (model_type,))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO model_metrics (
        model_name, model_type, dataset_name, trained_at, epochs, batch_size,
        lookback, horizon, train_loss, val_loss, test_mae, test_rmse, test_r2, test_mape,
        baseline_mae, baseline_rmse, baseline_r2, baseline_mape, loss_history, is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        model_name, model_type, dataset_name, now, epochs, batch_size,
        lookback, horizon, train_loss, val_loss, test_mae, test_rmse, test_r2, test_mape,
        baseline_mae, baseline_rmse, baseline_r2, baseline_mape, json.dumps(loss_history)
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_latest_metrics(model_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if model_type:
        cursor.execute("SELECT * FROM model_metrics WHERE model_type = ? ORDER BY id DESC LIMIT 1", (model_type,))
    else:
        cursor.execute("SELECT * FROM model_metrics WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("loss_history"):
        try:
            d["loss_history"] = json.loads(d["loss_history"])
        except Exception:
            d["loss_history"] = []
    return d

def get_all_model_metrics() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_metrics ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("loss_history"):
            try:
                d["loss_history"] = json.loads(d["loss_history"])
            except Exception:
                d["loss_history"] = []
        result.append(d)
    return result

def save_forecast(
    dataset_name: str,
    model_type: str,
    lookback: int,
    horizon: int,
    frequency: str,
    summary_stats: Dict[str, Any],
    predictions: List[Dict[str, Any]]
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO forecast_history (
        created_at, dataset_name, model_type, lookback, horizon, frequency, summary_stats, predictions_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now, dataset_name, model_type, lookback, horizon, frequency,
        json.dumps(summary_stats), json.dumps(predictions)
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_forecast_history(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, dataset_name, model_type, lookback, horizon, frequency, summary_stats FROM forecast_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("summary_stats"):
            try:
                d["summary_stats"] = json.loads(d["summary_stats"])
            except Exception:
                pass
        result.append(d)
    return result

def get_forecast_by_id(forecast_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forecast_history WHERE id = ?", (forecast_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("summary_stats"):
        try:
            d["summary_stats"] = json.loads(d["summary_stats"])
        except Exception:
            pass
    if d.get("predictions_json"):
        try:
            d["predictions"] = json.loads(d["predictions_json"])
        except Exception:
            d["predictions"] = []
    return d
