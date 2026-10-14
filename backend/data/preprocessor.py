import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from sklearn.preprocessing import MinMaxScaler
import joblib
from pathlib import Path

class EnergyPreprocessor:
    def __init__(self, lookback: int = 24, horizon: int = 24):
        self.lookback = lookback
        self.horizon = horizon
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_names: List[str] = []
        self.target_col: str = ""
        self.timestamp_col: str = ""
        self.is_fitted: bool = False

    def engineer_features(self, df: pd.DataFrame, timestamp_col: str, target_col: str) -> pd.DataFrame:
        """
        Creates temporal and historical features from the time series.
        """
        data = df.copy()
        ts = pd.to_datetime(data[timestamp_col])
        
        # 1. Temporal calendar features
        data['hour'] = ts.dt.hour
        data['dayofweek'] = ts.dt.dayofweek
        data['month'] = ts.dt.month
        data['is_weekend'] = (data['dayofweek'] >= 5).astype(int)
        
        # 2. Cyclical encoding for periodic time components
        data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24.0)
        data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24.0)
        data['day_sin'] = np.sin(2 * np.pi * data['dayofweek'] / 7.0)
        data['day_cos'] = np.cos(2 * np.pi * data['dayofweek'] / 7.0)
        data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12.0)
        data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12.0)
        
        # 3. Domain Thermodynamic and Weather Features (if sensor columns exist)
        col_lower_map = {str(c).lower(): c for c in data.columns}
        t_out_col = col_lower_map.get('t_out') or col_lower_map.get('outdoor_temperature_c')
        t_in_col = col_lower_map.get('t1') or col_lower_map.get('t2')
        dew_col = col_lower_map.get('tdewpoint')
        
        if t_out_col and t_in_col and t_out_col in data.columns and t_in_col in data.columns:
            data['temp_gradient_in_out'] = data[t_out_col] - data[t_in_col]
        if t_out_col and dew_col and t_out_col in data.columns and dew_col in data.columns:
            data['dewpoint_spread'] = data[t_out_col] - data[dew_col]

        # 4. Multi-step Lag features of the target
        data['lag_1'] = data[target_col].shift(1)
        data['lag_2'] = data[target_col].shift(2)
        if len(data) > 24:
            data['lag_24'] = data[target_col].shift(24)
        else:
            data['lag_24'] = data[target_col].shift(1)
            
        # 5. Rolling statistics (avoiding future lookahead by shifting first)
        shifted_target = data[target_col].shift(1)
        data['rolling_mean_6'] = shifted_target.rolling(window=6, min_periods=1).mean()
        data['rolling_std_6'] = shifted_target.rolling(window=6, min_periods=1).std().fillna(0)
        data['rolling_mean_24'] = shifted_target.rolling(window=24, min_periods=1).mean()
        data['rolling_max_24'] = shifted_target.rolling(window=24, min_periods=1).max()
        data['rolling_min_24'] = shifted_target.rolling(window=24, min_periods=1).min()

        # Fill any initial lag NaNs using backward fill
        feature_cols = [c for c in data.columns if c not in [timestamp_col]]
        data[feature_cols] = data[feature_cols].bfill().ffill()
        
        return data

    def select_features(self, df: pd.DataFrame, timestamp_col: str, target_col: str) -> List[str]:
        """
        Selects valid numeric feature columns, keeping the target column first.
        """
        candidate_cols = [c for c in df.columns if c != timestamp_col and pd.api.types.is_numeric_dtype(df[c])]
        # Ensure target_col is at index 0
        if target_col in candidate_cols:
            candidate_cols.remove(target_col)
        selected = [target_col] + candidate_cols
        return selected

    def chronological_split(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits data chronologically without random shuffling to strictly prevent leakage.
        """
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)
        
        return train_df, val_df, test_df

    def create_sequences(
        self,
        features: np.ndarray,
        targets: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Constructs (X, y) sliding window sequences:
        X: (samples, lookback, num_features)
        y: (samples, horizon)
        """
        num_samples = len(features) - self.lookback - self.horizon + 1
        if num_samples <= 0:
            raise ValueError(
                f"Data length ({len(features)}) is too short for lookback ({self.lookback}) + horizon ({self.horizon})."
            )
            
        X = np.zeros((num_samples, self.lookback, features.shape[1]), dtype=np.float32)
        y = np.zeros((num_samples, self.horizon), dtype=np.float32)
        
        for i in range(num_samples):
            X[i] = features[i : i + self.lookback]
            y[i] = targets[i + self.lookback : i + self.lookback + self.horizon, 0]
            
        return X, y

    def fit_transform_train(
        self,
        df: pd.DataFrame,
        timestamp_col: str,
        target_col: str,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ) -> Dict[str, Any]:
        """
        Full preprocessing pipeline:
        1. Feature engineering
        2. Feature selection
        3. Chronological split
        4. Scaler fit strictly on training set ONLY
        5. Sequence generation
        """
        self.timestamp_col = timestamp_col
        self.target_col = target_col
        
        # Feature Engineering
        engineered = self.engineer_features(df, timestamp_col, target_col)
        self.feature_names = self.select_features(engineered, timestamp_col, target_col)
        
        # Chronological Split
        train_df, val_df, test_df = self.chronological_split(engineered, train_ratio, val_ratio)
        
        # Extract numpy arrays
        train_feat_raw = train_df[self.feature_names].values
        val_feat_raw = val_df[self.feature_names].values
        test_feat_raw = test_df[self.feature_names].values
        
        train_target_raw = train_df[[target_col]].values
        val_target_raw = val_df[[target_col]].values
        test_target_raw = test_df[[target_col]].values
        
        # FIT scalers strictly on training data
        self.feature_scaler.fit(train_feat_raw)
        self.target_scaler.fit(train_target_raw)
        self.is_fitted = True
        
        # Transform splits
        train_feat_scaled = self.feature_scaler.transform(train_feat_raw)
        val_feat_scaled = self.feature_scaler.transform(val_feat_raw)
        test_feat_scaled = self.feature_scaler.transform(test_feat_raw)
        
        train_target_scaled = self.target_scaler.transform(train_target_raw)
        val_target_scaled = self.target_scaler.transform(val_target_raw)
        test_target_scaled = self.target_scaler.transform(test_target_raw)
        
        # Create sequences
        X_train, y_train = self.create_sequences(train_feat_scaled, train_target_scaled)
        X_val, y_val = self.create_sequences(val_feat_scaled, val_target_scaled)
        X_test, y_test = self.create_sequences(test_feat_scaled, test_target_scaled)
        
        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "train_df": train_df,
            "val_df": val_df,
            "test_df": test_df,
            "feature_names": self.feature_names,
            "num_features": len(self.feature_names)
        }

    def inverse_transform_targets(self, scaled_targets: np.ndarray) -> np.ndarray:
        """
        Inverts scaled target predictions back to original engineering units (kW or Wh).
        """
        orig_shape = scaled_targets.shape
        flat = scaled_targets.reshape(-1, 1)
        inverted = self.target_scaler.inverse_transform(flat)
        return inverted.reshape(orig_shape)

    def prepare_inference_input(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepares the most recent window of observations for forecasting future steps.
        """
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before running inference.")
            
        engineered = self.engineer_features(df, self.timestamp_col, self.target_col)
        if len(engineered) < self.lookback:
            raise ValueError(f"Need at least {self.lookback} rows for inference, got {len(engineered)}")
            
        recent_window = engineered[self.feature_names].iloc[-self.lookback:].values
        scaled_window = self.feature_scaler.transform(recent_window)
        # Reshape to (1, lookback, num_features)
        return np.expand_dims(scaled_window, axis=0)

    def save(self, filepath: Path):
        """Persists preprocessor state, scalers, and metadata."""
        state = {
            "lookback": self.lookback,
            "horizon": self.horizon,
            "feature_scaler": self.feature_scaler,
            "target_scaler": self.target_scaler,
            "feature_names": self.feature_names,
            "target_col": self.target_col,
            "timestamp_col": self.timestamp_col,
            "is_fitted": self.is_fitted
        }
        joblib.dump(state, filepath)

    @classmethod
    def load(cls, filepath: Path) -> 'EnergyPreprocessor':
        """Restores preprocessor state from file."""
        state = joblib.load(filepath)
        instance = cls(lookback=state["lookback"], horizon=state["horizon"])
        instance.feature_scaler = state["feature_scaler"]
        instance.target_scaler = state["target_scaler"]
        instance.feature_names = state["feature_names"]
        instance.target_col = state["target_col"]
        instance.timestamp_col = state["timestamp_col"]
        instance.is_fitted = state["is_fitted"]
        return instance
