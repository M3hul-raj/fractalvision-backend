"""Quality scoring system for fractal analysis reliability assessment."""


def calculate_quality_score(
    r_squared: float,
    num_scales: int,
    foreground_ratio: float = 0.5,
    sensitivity_std_deviation: float | None = None,
) -> dict:
    """Compute a 0-100 quality score based on R² and number of box-counting scales.

    Args:
        r_squared: Coefficient of determination from the OLS regression.
        num_scales: Number of box-counting scales used.
        foreground_ratio: Fraction of binary image pixels that are foreground (0–1).
            Default 0.5 is neutral and does not apply any penalty.
        sensitivity_std_deviation: Standard deviation of D across threshold variants,
            or None when the sensitivity test was not run.

    Returns:
        {"score": int, "reliability": str}
    """
    base = r_squared * 100

    if r_squared >= 0.999:
        base += 5
    if r_squared < 0.95:
        base -= 20
    if r_squared < 0.90:
        base -= 20  # cumulative with above
    if num_scales < 5:
        base -= 10

    # Foreground ratio penalties
    if foreground_ratio < 0.05:
        base -= 15   # too sparse — box counts dominated by noise
    elif foreground_ratio < 0.10:
        base -= 5    # somewhat sparse
    elif foreground_ratio > 0.95:
        base -= 15   # nearly saturated — most boxes always occupied
    elif foreground_ratio > 0.85:
        base -= 5    # somewhat dense

    # Threshold sensitivity penalty (only when test was run)
    if sensitivity_std_deviation is not None:
        if sensitivity_std_deviation > 0.10:
            base -= 20   # very unstable
        elif sensitivity_std_deviation > 0.05:
            base -= 10   # unstable

    score = int(max(0, min(base, 100)))

    if score >= 85:
        reliability = "High"
    elif score >= 70:
        reliability = "Medium"
    else:
        reliability = "Low"

    return {"score": score, "reliability": reliability}
