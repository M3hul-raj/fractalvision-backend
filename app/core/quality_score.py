"""Quality scoring system for fractal analysis reliability assessment."""


def calculate_quality_score(r_squared: float, num_scales: int) -> dict:
    """Compute a 0-100 quality score based on R² and number of box-counting scales.
    
    Returns {"score": int, "reliability": str}
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
    
    score = int(max(0, min(base, 100)))
    
    if score >= 85:
        reliability = "High"
    elif score >= 70:
        reliability = "Medium"
    else:
        reliability = "Low"
    
    return {"score": score, "reliability": reliability}
