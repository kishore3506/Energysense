import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
DB_PATH = ARTIFACTS_DIR / "energysense.db"

# Ensure runtime directories exist
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Default Model Hyperparameters
DEFAULT_LOOKBACK = 24
DEFAULT_HORIZON = 24
DEFAULT_EPOCHS = 20
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_LSTM_UNITS = [64, 32]
DEFAULT_DROPOUT = 0.2

# Dataset defaults
DEFAULT_DATASET = "uci_appliances_hourly.csv"
