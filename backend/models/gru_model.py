import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
from typing import List, Optional

def build_gru_model(
    lookback: int,
    num_features: int,
    horizon: int,
    units: Optional[List[int]] = None,
    dropout: float = 0.2,
    learning_rate: float = 0.001
) -> keras.Model:
    """
    Builds a Gated Recurrent Unit (GRU) sequence forecasting model for architecture comparison.
    """
    if units is None:
        units = [64, 32]
        
    model = keras.Sequential(name="EnergySense_GRU")
    
    # Input layer
    model.add(layers.Input(shape=(lookback, num_features)))
    
    # GRU Layers
    for i, u in enumerate(units):
        is_last = (i == len(units) - 1)
        model.add(layers.GRU(
            units=u,
            return_sequences=not is_last,
            activation="tanh",
            recurrent_activation="sigmoid",
            name=f"gru_layer_{i+1}"
        ))
        if dropout > 0:
            model.add(layers.Dropout(rate=dropout, name=f"gru_dropout_{i+1}"))
            
    # Dense output layers
    model.add(layers.Dense(units=32, activation="relu", name="dense_intermediate"))
    model.add(layers.Dense(units=horizon, activation="linear", name="forecast_output"))
    
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])
    
    return model
