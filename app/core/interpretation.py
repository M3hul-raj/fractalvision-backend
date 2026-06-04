"""Fractal dimension interpretation — D-value bands and complexity classification."""

from app.models.enums import ComplexityClass
from app.models.responses import InterpretationBand


INTERPRETATION_BANDS: list[dict] = [
    {"min": 0.0, "max": 1.0, "label": "Sparse / point-like or line fragments"},
    {"min": 1.0, "max": 1.2, "label": "Smooth line-like structure"},
    {"min": 1.2, "max": 1.5, "label": "Slightly irregular curve"},
    {"min": 1.5, "max": 1.8, "label": "Complex natural pattern"},
    {"min": 1.8, "max": 2.0, "label": "Highly irregular / near space-filling"},
    {"min": 2.0, "max": None, "label": "Invalid for 2D binary box-counting; check preprocessing"},
]


def classify_complexity(fractal_dimension: float) -> ComplexityClass:
    """Classify a fractal dimension value into a complexity class."""
    # TODO: Phase 5
    pass


def interpret_result(
    fractal_dimension: float,
    r_squared: float,
    quality_score: int,
) -> str:
    """Generate a human-readable interpretation of the analysis result."""
    # TODO: Phase 5
    pass


def get_interpretation_bands() -> list[InterpretationBand]:
    """Return the list of interpretation bands as Pydantic models."""
    # TODO: Phase 5
    pass
