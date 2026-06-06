"""Tests for the quality scoring system."""

from app.core.quality_score import calculate_quality_score


def test_high_reliability():
    """R²=0.9995, 7 scales → expect reliability='High'."""
    result = calculate_quality_score(r_squared=0.9995, num_scales=7)
    assert result["reliability"] == "High"
    assert result["score"] >= 85


def test_low_reliability():
    """R²=0.88, 4 scales → expect reliability='Low'."""
    result = calculate_quality_score(r_squared=0.88, num_scales=4)
    assert result["reliability"] == "Low"
    assert result["score"] < 70
