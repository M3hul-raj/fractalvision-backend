"""Linear regression and statistical analysis for log-log fractal dimension estimation."""

import math
import numpy as np
from scipy import stats


def linear_regression(
    x: np.ndarray, y: np.ndarray
) -> dict:
    """Perform OLS linear regression using scipy.stats.linregress.
    
    Returns {slope, intercept, r_squared, standard_error, confidence_interval,
             fitted_values, residuals}.
    """
    result = stats.linregress(x, y)
    slope = result.slope
    intercept = result.intercept
    r_value = result.rvalue
    stderr = result.stderr  # standard error of the slope
    
    if math.isnan(slope) or math.isinf(slope) or slope < 0.5 or slope > 2.1:
        raise ValueError("Degenerate result: threshold value produces an image with too little variation for reliable box-counting. Try a higher threshold value.")

    r_squared = r_value ** 2
    fitted_values = slope * x + intercept
    residuals = y - fitted_values
    
    ci_low = slope - 1.96 * stderr
    ci_high = slope + 1.96 * stderr
        
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "standard_error": float(stderr),
        "confidence_interval": [float(ci_low), float(ci_high)],
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
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute confidence interval for the slope (fractal dimension).
    
    Uses z=1.96 for 95% confidence (large-sample approximation).
    """
    z = 1.96 if confidence == 0.95 else stats.norm.ppf((1 + confidence) / 2)
    margin = z * standard_error
    return (slope - margin, slope + margin)


def compute_log_values(
    box_sizes: list[int], box_counts: list[int]
) -> tuple[np.ndarray, np.ndarray]:
    """Compute log(1/box_size) and log(box_count) arrays for regression."""
    x = -np.log(box_sizes)
    y = np.log(box_counts)
    return x, y
