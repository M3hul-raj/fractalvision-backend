"""Tests for the threshold sensitivity module."""

import numpy as np

from app.core.sensitivity import run_threshold_sensitivity


def test_threshold_sensitivity_checkerboard():
    """Run threshold sensitivity on a synthetic checkerboard pattern."""
    # Create a 64x64 checkerboard grayscale image
    gray = np.zeros((64, 64), dtype=np.uint8)
    for i in range(64):
        for j in range(64):
            if (i // 8 + j // 8) % 2 == 0:
                gray[i, j] = 200
            else:
                gray[i, j] = 50

    result = run_threshold_sensitivity(
        grayscale_image=gray,
        computed_threshold=128,
        base_box_sizes=[4, 8, 16],
    )

    assert result is not None
    assert "thresholds_tested" in result
    assert "dimensions" in result
    assert "std_deviation" in result
    assert "is_stable" in result
    assert isinstance(result["is_stable"], bool)
    assert len(result["thresholds_tested"]) == 3
    assert len(result["dimensions"]) == 3


def test_threshold_sensitivity_none_for_adaptive():
    """If computed_threshold is None (adaptive mode), should return None."""
    gray = np.zeros((64, 64), dtype=np.uint8)
    result = run_threshold_sensitivity(
        grayscale_image=gray,
        computed_threshold=None,
        base_box_sizes=[4, 8, 16],
    )
    assert result is None
