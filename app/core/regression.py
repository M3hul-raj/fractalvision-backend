"""Linear regression and statistical analysis for log-log fractal dimension estimation."""

import numpy as np


def linear_regression(
    x: np.ndarray, y: np.ndarray
) -> dict:
    """Perform OLS linear regression. Returns {slope, intercept, r_squared, standard_error, fitted_values, residuals}."""
    slope, intercept = np.polyfit(x, y, 1)
    
    import math
    if math.isnan(slope) or math.isinf(slope) or slope < 0.5 or slope > 2.1:
        raise ValueError("Degenerate result: threshold value produces an image with too little variation for reliable box-counting. Try a higher threshold value.")

    fitted_values = slope * x + intercept
    residuals = y - fitted_values
    
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    n = len(x)
    if n > 2:
        mse = ss_res / (n - 2)
        var_x = np.sum((x - np.mean(x))**2)
        standard_error = np.sqrt(mse / var_x) if var_x > 0 else 0.0
    else:
        standard_error = 0.0
        
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "standard_error": float(standard_error),
        "fitted_values": fitted_values.tolist(),
        "residuals": residuals.tolist()
    }


def compute_r_squared(y_actual: np.ndarray, y_predicted: np.ndarray) -> float:
    """Compute the coefficient of determination (R²)."""
    ss_res = np.sum((y_actual - y_predicted)**2)
    ss_tot = np.sum((y_actual - np.mean(y_actual))**2)
    return float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0


def compute_confidence_interval(
    slope: float,
    standard_error: float,
    n: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute confidence interval for the slope (fractal dimension)."""
    # TODO: Phase 5
    pass


def compute_log_values(
    box_sizes: list[int], box_counts: list[int]
) -> tuple[np.ndarray, np.ndarray]:
    """Compute log(1/box_size) and log(box_count) arrays for regression."""
    x = -np.log(box_sizes)
    y = np.log(box_counts)
    return x, y
