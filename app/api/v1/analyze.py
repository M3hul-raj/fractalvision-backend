"""Analysis endpoints — single image and batch fractal analysis."""

from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.models.responses import AnalyzeResponse, BatchAnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG, WEBP)"),
    analysis_mode: str = Form("full-mask"),
    threshold_method: str = Form("otsu"),
    manual_threshold: Optional[int] = Form(None),
    invert: bool = Form(False),
    denoise: bool = Form(False),
    blur_level: int = Form(0),
    box_sizes: Optional[str] = Form(None),
    grid_offsets: str = Form("0,0.25,0.5,0.75"),
    run_sensitivity: bool = Form(False),
) -> AnalyzeResponse:
    """Analyze an uploaded image for fractal dimension using box-counting."""
    # TODO: Phase 1
    pass


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def analyze_batch(
    request: Request,
    files: list[UploadFile] = File(..., description="Multiple image files (max 10)"),
    analysis_mode: str = Form("full-mask"),
    threshold_method: str = Form("otsu"),
) -> BatchAnalyzeResponse:
    """Batch-analyze multiple images with the same settings."""
    # TODO: Phase 1
    pass
