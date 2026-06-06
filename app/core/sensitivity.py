"""Sensitivity and robustness tests — threshold variation analysis."""

import numpy as np

from app.core.image_processing import manual_threshold
from app.core.box_counting import run_box_counting
from app.core.regression import linear_regression, compute_log_values


def run_threshold_sensitivity(
    grayscale_image: np.ndarray,
    computed_threshold: int | None,
    base_box_sizes: list[int],
) -> dict | None:
    """Test how D changes across threshold variations around the computed threshold.
    
    If computed_threshold is None (adaptive/boundary/texture mode), returns None.
    
    Otherwise tests threshold ±15 and returns stability metrics.
    """
    if computed_threshold is None:
        return None
    
    height, width = grayscale_image.shape[:2]
    
    # Build 3 test values: [threshold-15, threshold, threshold+15], clamped to [1, 254]
    test_thresholds = [
        max(1, min(254, computed_threshold - 15)),
        max(1, min(254, computed_threshold)),
        max(1, min(254, computed_threshold + 15)),
    ]
    
    dimensions: list[float | None] = []
    
    for tv in test_thresholds:
        try:
            binary, _ = manual_threshold(grayscale_image, tv)
            bc_result = run_box_counting(binary, width, height, base_box_sizes)
            counts = bc_result["box_counts"]
            x, y = compute_log_values(base_box_sizes, counts)
            reg_result = linear_regression(x, y)
            dimensions.append(float(reg_result["slope"]))
        except (ValueError, Exception):
            dimensions.append(None)
    
    # Compute std_deviation over non-None D values
    valid_dims = [d for d in dimensions if d is not None]
    
    if len(valid_dims) < 2:
        std_deviation = None
        is_stable = False
    else:
        std_deviation = float(np.std(valid_dims))
        is_stable = std_deviation < 0.05
    
    return {
        "thresholds_tested": test_thresholds,
        "dimensions": dimensions,
        "std_deviation": std_deviation,
        "is_stable": is_stable,
    }
