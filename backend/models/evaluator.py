import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Any

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes standard regression evaluation metrics between actual and predicted values.
    Flattens arrays to compute overall multi-step forecasting performance.
    """
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()
    
    # 1. MAE
    mae = float(mean_absolute_error(y_true_flat, y_pred_flat))
    
    # 2. RMSE
    mse = mean_squared_error(y_true_flat, y_pred_flat)
    rmse = float(np.sqrt(mse))
    
    # 3. R-squared (Coefficient of Determination)
    r2 = float(r2_score(y_true_flat, y_pred_flat))
    
    # 4. MAPE (Mean Absolute Percentage Error) - safe handling for zero / near-zero actuals
    epsilon = 1e-5
    nonzero_mask = np.abs(y_true_flat) > epsilon
    if np.sum(nonzero_mask) > 0:
        mape_val = np.mean(np.abs((y_true_flat[nonzero_mask] - y_pred_flat[nonzero_mask]) / y_true_flat[nonzero_mask])) * 100.0
        mape = float(mape_val)
    else:
        mape = 0.0

    # 5. Max Absolute Error
    max_err = float(np.max(np.abs(y_true_flat - y_pred_flat)))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mape": round(mape, 2),
        "max_error": round(max_err, 4)
    }

def get_metric_definitions() -> Dict[str, Dict[str, str]]:
    """
    Returns academic/technical definitions and formulas for evaluation metrics.
    """
    return {
        "MAE": {
            "name": "Mean Absolute Error",
            "formula": "(1/n) * sum(|y_true - y_pred|)",
            "unit": "Original units (kWh or Wh)",
            "interpretation": "Measures the average magnitude of forecasting errors in physical energy units without penalizing large deviations disproportionately."
        },
        "RMSE": {
            "name": "Root Mean Squared Error",
            "formula": "sqrt((1/n) * sum((y_true - y_pred)^2))",
            "unit": "Original units (kWh or Wh)",
            "interpretation": "Square root of the mean squared error. Heavily penalizes large forecasting spikes or peak misestimations."
        },
        "R2": {
            "name": "Coefficient of Determination (R²)",
            "formula": "1 - (sum((y_true - y_pred)^2) / sum((y_true - y_mean)^2))",
            "unit": "Dimensionless (-inf to 1.0)",
            "interpretation": "Proportion of variance in energy consumption explained by the deep learning model. 1.0 represents perfect forecasting."
        },
        "MAPE": {
            "name": "Mean Absolute Percentage Error",
            "formula": "(100/n) * sum(|(y_true - y_pred) / y_true|)",
            "unit": "Percentage (%)",
            "interpretation": "Scale-independent relative percentage error, evaluated on non-zero consumption intervals."
        }
    }
