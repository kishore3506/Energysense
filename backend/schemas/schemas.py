from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TrainModelRequest(BaseModel):
    dataset_name: str = Field(default="uci_appliances_hourly.csv", description="Name of dataset file")
    model_type: str = Field(default="LSTM", description="Model architecture: LSTM, GRU, or BiLSTM")
    lookback: int = Field(default=24, ge=6, le=168, description="Historical lookback window in hours")
    horizon: int = Field(default=24, ge=1, le=72, description="Forecast horizon in hours")
    epochs: int = Field(default=20, ge=1, le=100, description="Number of training epochs")
    batch_size: int = Field(default=32, ge=8, le=256, description="Mini-batch size")
    learning_rate: float = Field(default=0.001, gt=0, le=0.1, description="Adam optimizer learning rate")
    lstm_units: List[int] = Field(default=[64, 32], description="Units for recurrent layers")
    dropout: float = Field(default=0.2, ge=0.0, le=0.8, description="Dropout rate")

class TuneModelRequest(BaseModel):
    dataset_name: str = Field(default="uci_appliances_hourly.csv", description="Name of dataset file")
    model_type: str = Field(default="LSTM", description="Model architecture to optimize (LSTM/GRU)")
    n_trials: int = Field(default=5, ge=2, le=25, description="Number of Optuna optimization trials")
    epochs_per_trial: int = Field(default=4, ge=2, le=15, description="Epochs per optimization trial")

class ForecastRequest(BaseModel):
    dataset_name: str = Field(default="uci_appliances_hourly.csv", description="Name of dataset file")
    horizon: int = Field(default=24, ge=1, le=72, description="Forecast horizon")
    lookback: int = Field(default=24, ge=6, le=168, description="Lookback window")
    model_type: str = Field(default="LSTM", description="Model to use")

class DatasetSelectRequest(BaseModel):
    dataset_name: str
