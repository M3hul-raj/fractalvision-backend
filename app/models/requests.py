"""Pydantic request models for FractalVision Lab API."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AnalysisMode, ThresholdMethod


class AnalyzeRequestParams(BaseModel):
    """Parameters for single image analysis (parsed from multipart form fields)."""
    analysis_mode: AnalysisMode = AnalysisMode.FULL_MASK
    threshold_method: ThresholdMethod = ThresholdMethod.OTSU
    manual_threshold: Optional[int] = Field(None, ge=0, le=255)
    invert: bool = False
    denoise: bool = False
    blur_level: int = Field(default=0, ge=0)
    box_sizes: Optional[str] = Field(
        default=None,
        description="Comma-separated powers of 2, e.g. '4,8,16,32,64,128,256'",
    )
    grid_offsets: str = Field(
        default="0,0.25,0.5,0.75",
        description="Comma-separated grid origin offsets as fractions of box size",
    )
    run_sensitivity: bool = False


class GenerateFractalRequest(BaseModel):
    """Request body for standard fractal generation and analysis."""
    iterations: int = Field(default=5, ge=1, le=12)
    image_size: int = Field(default=1024, ge=128, le=4096)
    box_sizes: Optional[list[int]] = Field(
        default=None,
        description="Custom box sizes (powers of 2). Auto-selected if not provided.",
    )
