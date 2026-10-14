import numpy as np

class PersistenceBaseline:
    """
    Standard naive/persistence baseline model for time series forecasting.
    Predicts future values using the last observed time step or seasonal repeat.
    """
    def __init__(self, horizon: int = 24, method: str = "last_value"):
        self.horizon = horizon
        self.method = method

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        X: shape (samples, lookback, num_features)
        Assumes feature index 0 is the target energy consumption.
        Returns: shape (samples, horizon)
        """
        num_samples = X.shape[0]
        lookback = X.shape[1]
        
        # Last observed target value at t=lookback-1
        last_values = X[:, -1, 0] # shape (samples,)
        
        if self.method == "seasonal" and lookback >= self.horizon:
            # Repeat the last matching period
            predictions = X[:, -self.horizon:, 0]
        else:
            # Multi-step constant persistence: future H steps = last value
            predictions = np.repeat(last_values[:, np.newaxis], self.horizon, axis=1)
            
        return predictions
