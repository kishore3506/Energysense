import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
from typing import List, Optional

def build_lstm_model(
    lookback: int,
    num_features: int,
    horizon: int,
    units: Optional[List[int]] = None,
    dropout: float = 0.2,
    learning_rate: float = 0.001
) -> keras.Model:
    """
    Builds a multi-layer Long Short-Term Memory (LSTM) sequence-to-sequence forecasting model.
    """
    if units is None:
        units = [64, 32]
        
    model = keras.Sequential(name="EnergySense_LSTM")
    
    # Input layer
    model.add(layers.Input(shape=(lookback, num_features)))
    
    # LSTM Layers
    for i, u in enumerate(units):
        is_last = (i == len(units) - 1)
        model.add(layers.LSTM(
            units=u,
            return_sequences=not is_last,
            activation="tanh",
            recurrent_activation="sigmoid",
            name=f"lstm_layer_{i+1}"
        ))
        if dropout > 0:
            model.add(layers.Dropout(rate=dropout, name=f"lstm_dropout_{i+1}"))
            
    # Fully connected projection layers
    model.add(layers.Dense(units=32, activation="relu", name="dense_intermediate"))
    model.add(layers.Dense(units=horizon, activation="linear", name="forecast_output"))
    
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])
    
    return model

def save_model(model: keras.Model, filepath: Path):
    """Saves model in Keras native format."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    model.save(filepath)

def load_model(filepath: Path) -> keras.Model:
    """Loads saved Keras model."""
    if not filepath.exists():
        raise FileNotFoundError(f"Model file not found at: {filepath}")
    return keras.models.load_model(filepath)
