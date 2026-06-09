"""Fractal dimension interpretation — D-value bands and complexity classification."""

from dataclasses import dataclass


# ── D-value band table ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _Band:
    """One interpretation band: [d_min, d_max) with its class label and base text."""
    d_min: float
    d_max: float | None   # None means "≥ d_min"
    label: str
    base_text: str


_BANDS: tuple[_Band, ...] = (
    _Band(
        d_min=0.0,
        d_max=1.1,
        label="Simple / Linear",
        base_text=(
            "Near-linear structure with minimal branching or surface roughness. "
            "Characteristic of simple edges or smooth boundaries."
        ),
    ),
    _Band(
        d_min=1.1,
        d_max=1.4,
        label="Low Complexity",
        base_text=(
            "Sparse fractal structure with limited self-similarity. "
            "Typical of basic branching patterns or moderately rough coastlines."
        ),
    ),
    _Band(
        d_min=1.4,
        d_max=1.6,
        label="Moderate Complexity",
        base_text=(
            "Moderate space-filling pattern. "
            "Characteristic of complex networks, river systems, or jagged natural borders."
        ),
    ),
    _Band(
        d_min=1.6,
        d_max=1.8,
        label="High Complexity",
        base_text=(
            "Dense space-filling pattern with high self-similarity. "
            "Typical of intricate natural formations like detailed leaf venation "
            "or highly textured surfaces."
        ),
    ),
    _Band(
        d_min=1.8,
        d_max=None,
        label="Very High Complexity",
        base_text=(
            "Highly space-filling structure, approaching full 2D coverage. "
            "Characteristic of extremely dense porous materials or hyper-complex textures."
        ),
    ),
)

_LOW_R2_WARNING = (
    "Note: The low R\u00b2 score indicates that the structure may not be perfectly "
    "self-similar across all scales, and the fractal dimension should be treated "
    "as an approximation."
)

_R2_GOOD_THRESHOLD = 0.95


def _match_band(d_value: float) -> _Band:
    """Return the interpretation band that contains *d_value*."""
    for band in _BANDS:
        if band.d_max is None or d_value < band.d_max:
            if d_value >= band.d_min:
                return band
    # Fallback: return the last band for any out-of-range value
    return _BANDS[-1]


# ── Public API ────────────────────────────────────────────────────────────────

def get_fractal_interpretation(d_value: float, r_squared: float) -> dict[str, str]:
    """
    Return a dict with ``complexity_class`` and ``interpretation`` strings
    derived from the computed fractal dimension and goodness-of-fit score.

    Args:
        d_value:    Computed fractal dimension (slope of log-log regression).
        r_squared:  R² of the regression fit (0–1).

    Returns:
        {
            "complexity_class": str,   # e.g. "High Complexity"
            "interpretation":   str,   # Human-readable paragraph
        }
    """
    band = _match_band(d_value)
    text = band.base_text

    if r_squared < _R2_GOOD_THRESHOLD:
        text = f"{text} {_LOW_R2_WARNING}"

    return {
        "complexity_class": band.label,
        "interpretation": text,
    }


# ── Legacy stubs — kept for backward-compat; delegate to get_fractal_interpretation ──

def classify_complexity(fractal_dimension: float) -> str:
    """Classify a fractal dimension value into a complexity class string."""
    return _match_band(fractal_dimension).label


def interpret_result(
    fractal_dimension: float,
    r_squared: float,
    quality_score: int,  # noqa: ARG001 — reserved for future quality-adjusted text
) -> str:
    """Generate a human-readable interpretation of the analysis result."""
    return get_fractal_interpretation(fractal_dimension, r_squared)["interpretation"]
