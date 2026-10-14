import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
from typing import List, Optional

def build_bilstm_model(
    lookback: int,
    num_features: int,
    horizon: int,
    units: Optional[List[int]] = None,
    dropout: float = 0.2,
    learning_rate: float = 0.001
) -> keras.Model:
    """
    Builds a Stacked Bidirectional Long Short-Term Memory (Bi-LSTM) sequence forecasting model.
    Captures both forward and backward temporal dynamics in the lookback context.
    """
    if units is None:
        units = [32, 16] # 32 units forward + 32 backward = 64 total per step
        
    model = keras.Sequential(name="EnergySense_BiLSTM")
    model.add(layers.Input(shape=(lookback, num_features)))
    
    for i, u in enumerate(units):
        is_last = (i == len(units) - 1)
        model.add(layers.Bidirectional(
            layers.LSTM(
                units=u,
                return_sequences=not is_last,
                activation="tanh",
                recurrent_activation="sigmoid"
            ),
            name=f"bilstm_layer_{i+1}"
        ))
        if dropout > 0:
            model.add(layers.Dropout(rate=dropout, name=f"bilstm_dropout_{i+1}"))
            
    model.add(layers.Dense(units=32, activation="relu", name="dense_intermediate"))
    model.add(layers.Dense(units=horizon, activation="linear", name="forecast_output"))
    
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])
    
    return model
