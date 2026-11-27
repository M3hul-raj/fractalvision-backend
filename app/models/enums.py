"""Enum definitions for FractalVision Lab API."""

from enum import StrEnum


class AnalysisMode(StrEnum):
    """Available analysis modes for fractal dimension estimation."""
    FULL_MASK = "full_mask"
    BOUNDARY = "boundary"
    TEXTURE = "texture"


class ThresholdMethod(StrEnum):
    """Available thresholding methods for binary conversion."""
    OTSU = "otsu"
    MANUAL = "manual"
    ADAPTIVE = "adaptive"


class Reliability(StrEnum):
    """Reliability classification for analysis results."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ComplexityClass(StrEnum):
    """Complexity classification derived from fractal dimension."""
    SPARSE = "Sparse"
    SMOOTH_LINE = "Smooth line-like"
    SLIGHTLY_IRREGULAR = "Slightly irregular"
    COMPLEX = "Complex natural pattern"
    HIGHLY_IRREGULAR = "Highly irregular"
    NEAR_SPACE_FILLING = "Near space-filling"
    INVALID = "Invalid"
