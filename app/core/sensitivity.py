"""Sensitivity and robustness tests — threshold and rotation analysis."""

import cv2
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


def run_rotation_sensitivity(
    binary_image: np.ndarray,
    box_sizes: list[int],
    angles: list[float] | None = None,
) -> dict:
    """Test how D changes when the binary mask is rotated at multiple angles.

    Tests at 0°, 15°, 30°, 45°, 90°.
    Returns stability metrics in the same format as run_threshold_sensitivity.
    """
    if angles is None:
        angles = [0.0, 15.0, 30.0, 45.0, 90.0]

    height, width = binary_image.shape[:2]
    center = (width / 2.0, height / 2.0)
    dimensions: list[float | None] = []

    for angle in angles:
        try:
            if angle == 0.0:
                rotated = binary_image
            else:
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    binary_image, M, (width, height),
                    flags=cv2.INTER_NEAREST,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0,
                )
            bc_result = run_box_counting(rotated, width, height, box_sizes)
            counts = bc_result["box_counts"]
            x, y = compute_log_values(box_sizes, counts)
            reg_result = linear_regression(x, y)
            dimensions.append(float(reg_result["slope"]))
        except (ValueError, Exception):
            dimensions.append(None)

    valid_dims = [d for d in dimensions if d is not None]

    if len(valid_dims) < 2:
        return {
            "angles_tested": angles,
            "dimensions": dimensions,
            "std_deviation": None,
            "is_stable": False,
        }

    std_deviation = float(np.std(valid_dims))
    return {
        "angles_tested": angles,
        "dimensions": dimensions,
        "std_deviation": std_deviation,
        "is_stable": std_deviation < 0.05,
    }
