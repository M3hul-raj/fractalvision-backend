"""Quality scoring system for fractal analysis reliability assessment."""

from app.models.enums import Reliability


def compute_quality_score(
    r_squared: float,
    num_box_sizes: int,
    image_width: int,
    image_height: int,
    foreground_ratio: float,
    threshold_std: float | None = None,
    rotation_std: float | None = None,
    grid_origin_std: float | None = None,
) -> int:
    """Compute a 0–100 quality score based on weighted components."""
    # TODO: Phase 5
    pass


def classify_reliability(quality_score: int) -> Reliability:
    """Classify reliability as High (85–100), Medium (65–84), or Low (<65)."""
    # TODO: Phase 5
    pass
