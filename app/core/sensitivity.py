"""Sensitivity and robustness tests — threshold, rotation, grid-origin."""

import numpy as np

from app.models.responses import SensitivityResult


def threshold_sensitivity(
    grayscale: np.ndarray,
    base_threshold: int,
    offsets: list[int] | None = None,
) -> SensitivityResult:
    """Test how D changes across threshold variations around the base threshold."""
    # TODO: Phase 5
    pass


def rotation_sensitivity(
    binary: np.ndarray,
    angles: list[int] | None = None,
) -> SensitivityResult:
    """Test how D changes when the image is rotated."""
    # TODO: Phase 5
    pass


def grid_origin_sensitivity(
    binary: np.ndarray,
    box_sizes: list[int],
    offsets: list[float] | None = None,
) -> SensitivityResult:
    """Test how D changes with different grid origin placements."""
    # TODO: Phase 5
    pass
