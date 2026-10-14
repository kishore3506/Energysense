import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

def auto_detect_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Automatically detects the timestamp column and target energy consumption column.
    """
    timestamp_col = None
    target_col = None
    
    # 1. Detect Timestamp Column
    time_keywords = ['date', 'time', 'timestamp', 'datetime', 'hour', 'ts']
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in time_keywords):
            # Check if parseable as datetime
            try:
                pd.to_datetime(df[col].dropna().iloc[:10])
                timestamp_col = col
                break
            except Exception:
                continue
                
    if not timestamp_col:
        # Fallback: check all object or string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].dropna().iloc[:10])
                    timestamp_col = col
                    break
                except Exception:
                    pass

    # 2. Detect Target Energy Column
    target_keywords = ['total_energy', 'appliances', 'consumption', 'electricity', 'power', 'kw', 'kwh', 'energy', 'load']
    for kw in target_keywords:
        for col in df.columns:
            if col == timestamp_col:
                continue
            if kw in str(col).lower() and pd.api.types.is_numeric_dtype(df[col]):
                target_col = col
                break
        if target_col:
            break
            
    if not target_col:
        # Fallback to the first numeric column that is not the timestamp
        numeric_cols = [c for c in df.columns if c != timestamp_col and pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            target_col = numeric_cols[0]
            
    return timestamp_col, target_col

def load_dataset(
    filepath: Path,
    timestamp_col: Optional[str] = None,
    target_col: Optional[str] = None
) -> Tuple[pd.DataFrame, str, str, List[str]]:
    """
    Loads and validates a CSV dataset, ensuring timestamps are parsed and chronologically sorted.
    Returns (cleaned_df, timestamp_col, target_col, warnings).
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset file not found at: {filepath}")
        
    df = pd.read_csv(filepath)
    warnings = []
    
    if df.empty:
        raise ValueError("Dataset is empty.")
        
    # Detect columns if not explicitly provided
    detected_ts, detected_target = auto_detect_columns(df)
    
    timestamp_col = timestamp_col or detected_ts
    target_col = target_col or detected_target
    
    if not timestamp_col:
        raise ValueError("Could not find or parse a timestamp column in dataset.")
    if not target_col:
        raise ValueError("Could not find a valid numeric target energy consumption column.")
        
    if timestamp_col not in df.columns:
        raise ValueError(f"Specified timestamp column '{timestamp_col}' does not exist.")
    if target_col not in df.columns:
        raise ValueError(f"Specified target column '{target_col}' does not exist.")

    # Parse timestamp
    try:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    except Exception as e:
        raise ValueError(f"Failed to parse timestamp column '{timestamp_col}': {str(e)}")

    # Sort chronologically and drop duplicate timestamps
    initial_len = len(df)
    df = df.sort_values(timestamp_col).reset_index(drop=True)
    df = df.drop_duplicates(subset=[timestamp_col]).reset_index(drop=True)
    if len(df) < initial_len:
        warnings.append(f"Removed {initial_len - len(df)} duplicate timestamp entries.")

    # Convert target to numeric and handle missing values
    non_numeric_count = pd.to_numeric(df[target_col], errors='coerce').isna().sum() - df[target_col].isna().sum()
    if non_numeric_count > 0:
        warnings.append(f"Found {non_numeric_count} non-numeric values in target column coerced to NaN.")
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    
    # Missing value handling (forward-fill then backward-fill for continuous time-series)
    missing_target = df[target_col].isna().sum()
    if missing_target > 0:
        warnings.append(f"Imputed {missing_target} missing target values using forward/backward fill.")
        df[target_col] = df[target_col].ffill().bfill()
        
    # Drop rows if target is still NaN (e.g. all empty)
    df = df.dropna(subset=[target_col]).reset_index(drop=True)
    
    if len(df) < 50:
        raise ValueError(f"Insufficient historical data: only {len(df)} valid records found. At least 50 required.")
        
    return df, timestamp_col, target_col, warnings

def get_dataset_summary(
    df: pd.DataFrame,
    timestamp_col: str,
    target_col: str
) -> Dict[str, Any]:
    """
    Computes statistical and temporal overview of the dataset.
    """
    series = df[target_col]
    ts_series = df[timestamp_col]
    
    peak_idx = series.idxmax()
    peak_val = float(series.iloc[peak_idx])
    peak_time = str(ts_series.iloc[peak_idx])
    
    # Estimate frequency
    if len(df) > 1:
        time_diffs = ts_series.diff().dropna()
        median_diff_seconds = time_diffs.median().total_seconds()
        if abs(median_diff_seconds - 3600) < 60:
            freq_label = "Hourly (1h)"
        elif abs(median_diff_seconds - 600) < 60:
            freq_label = "10 Minutes (10m)"
        elif abs(median_diff_seconds - 86400) < 300:
            freq_label = "Daily (1d)"
        else:
            freq_label = f"~{int(median_diff_seconds // 60)} minutes"
    else:
        freq_label = "Unknown"

    summary = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "timestamp_column": timestamp_col,
        "target_column": target_col,
        "columns": list(df.columns),
        "start_time": str(ts_series.min()),
        "end_time": str(ts_series.max()),
        "estimated_frequency": freq_label,
        "metrics": {
            "mean": float(round(series.mean(), 2)),
            "std": float(round(series.std(), 2)),
            "min": float(round(series.min(), 2)),
            "max": float(round(series.max(), 2)),
            "median": float(round(series.median(), 2)),
            "p25": float(round(series.quantile(0.25), 2)),
            "p75": float(round(series.quantile(0.75), 2)),
            "peak_value": float(round(peak_val, 2)),
            "peak_timestamp": peak_time
        },
        "missing_values": {col: int(df[col].isna().sum()) for col in df.columns}
    }
    return summary
