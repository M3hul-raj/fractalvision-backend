"""Analysis endpoints — single image and batch fractal analysis."""

import asyncio
import time
from typing import Annotated

import anyio
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.deps import limiter
from app.config import Settings, get_settings
from app.core import box_counting, image_processing, regression
from app.core.image_processing import apply_denoise, apply_gaussian_blur
from app.core.interpretation import get_fractal_interpretation
from app.core.quality_score import calculate_quality_score
from app.core.sensitivity import (
    run_rotation_sensitivity as run_rotation_sensitivity_fn,
)
from app.core.sensitivity import (
    run_threshold_sensitivity,
)
from app.models.enums import AnalysisMode, ThresholdMethod
from app.models.responses import (
    AnalysisParameters,
    AnalysisResultData,
    AnalyzeResponse,
    BatchAnalyzeResponse,
    RotationSensitivityResult,
    SensitivityResult,
)
from app.utils.image_validation import (
    ImageValidationError,
    read_upload_limited,
    validate_and_decode_image,
)

router = APIRouter()

_VALID_MODES = {m.value for m in AnalysisMode}
_VALID_METHODS = {m.value for m in ThresholdMethod}
_MAX_ANALYSIS_DIMENSION = 1024


def _parse_grid_offsets(grid_offsets: str) -> list[float]:
    """Parse and validate comma-separated grid offsets in [0, 1)."""
    if not grid_offsets or not grid_offsets.strip():
        return []
    parts = [part.strip() for part in grid_offsets.split(",") if part.strip()]
    if len(parts) > 8:
        raise HTTPException(
            status_code=422,
            detail="grid_offsets supports at most 8 offsets.",
        )
    offsets: list[float] = []
    for part in parts:
        try:
            val = float(part)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid grid_offset value {part!r}: must be a number.",
            ) from exc
        if not (0.0 <= val < 1.0):
            raise HTTPException(
                status_code=422,
                detail=f"grid_offset {val} must be in [0, 1).",
            )
        offsets.append(val)
    return offsets


def _validate_analysis_params(
    analysis_mode: str,
    threshold_method: str,
    threshold_value: int,
    blur_level: int,
    adaptive_block_size: int,
    adaptive_c: int,
    grid_offsets: str,
) -> list[float]:
    """Validate form parameters before running image processing."""
    if analysis_mode not in _VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid analysis_mode {analysis_mode!r}. Expected: {sorted(_VALID_MODES)}.",
        )
    if threshold_method not in _VALID_METHODS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid threshold_method {threshold_method!r}. "
                f"Expected: {sorted(_VALID_METHODS)}."
            ),
        )
    if not (0 <= threshold_value <= 255):
        raise HTTPException(
            status_code=422,
            detail="threshold_value must be between 0 and 255.",
        )
    if not (0 <= blur_level <= 5):
        raise HTTPException(
            status_code=422,
            detail="blur_level must be between 0 and 5.",
        )
    if not (3 <= adaptive_block_size <= 101):
        raise HTTPException(
            status_code=422,
            detail="adaptive_block_size must be between 3 and 101.",
        )
    if not (-50 <= adaptive_c <= 50):
        raise HTTPException(
            status_code=422,
            detail="adaptive_c must be between -50 and 50.",
        )
    return _parse_grid_offsets(grid_offsets)


def _run_analysis_pipeline(
    *,
    file_bytes: bytes,
    max_dimension: int,
    max_pixels: int,
    analysis_mode: str,
    threshold_method: str,
    threshold_value: int,
    invert: bool,
    denoise: bool,
    blur_level: int,
    offsets_list: list[float],
    run_sensitivity: bool,
    run_rotation_sensitivity: bool,
    adaptive_block_size: int,
    adaptive_c: int,
    start_time: float,
) -> AnalyzeResponse:
    """Synchronous CPU-bound analysis pipeline executed in a worker thread."""
    image = validate_and_decode_image(
        file_bytes,
        max_dimension=max_dimension,
        max_pixels=max_pixels,
    )
    image = image_processing.resize_if_needed(image, _MAX_ANALYSIS_DIMENSION)
    grayscale = image_processing.to_grayscale(image)

    if blur_level > 0:
        grayscale = apply_gaussian_blur(grayscale, blur_level)
    if denoise:
        grayscale = apply_denoise(grayscale)

    thresh_val = None
    if analysis_mode == AnalysisMode.BOUNDARY.value:
        binary, thresh_val = image_processing.mode_boundary(grayscale)
    elif analysis_mode == AnalysisMode.TEXTURE.value:
        binary, thresh_val = image_processing.mode_texture(grayscale)
    elif threshold_method == ThresholdMethod.ADAPTIVE.value:
        binary, thresh_val = image_processing.adaptive_threshold(
            grayscale,
            block_size=adaptive_block_size,
            c=adaptive_c,
        )
    elif threshold_method == ThresholdMethod.MANUAL.value:
        binary, thresh_val = image_processing.manual_threshold(grayscale, threshold_value)
    else:
        thresh_val, binary = image_processing.otsu_threshold(grayscale)

    if invert:
        binary = 255 - binary

    height, width = binary.shape

    box_sizes_used = box_counting.auto_select_box_sizes(width, height)
    if len(box_sizes_used) < 2:
        raise ImageValidationError(
            422,
            "Image dimensions are too small for multi-scale box counting (minimum 16x16 px).",
        )

    bc_result = box_counting.run_box_counting(binary, width, height, box_sizes_used, offsets_list)
    counts = bc_result["box_counts"]
    if any(c <= 0 for c in counts):
        raise ImageValidationError(
            422,
            "Degenerate result: no foreground pixels detected at one or more scales.",
        )

    x, y = regression.compute_log_values(box_sizes_used, counts)
    try:
        reg_result = regression.linear_regression(x, y)
    except ValueError as exc:
        raise ImageValidationError(422, str(exc)) from exc

    foreground_ratio = float(np.count_nonzero(binary) / binary.size)
    binary_b64 = image_processing.encode_image_base64(binary)

    params = AnalysisParameters(
        analysis_mode=analysis_mode,
        threshold_method=threshold_method,
        computed_threshold=thresh_val,
        invert=invert,
        denoise=denoise,
        blur_level=blur_level,
        box_sizes_used=box_sizes_used,
        image_width=width,
        image_height=height,
    )

    interp = get_fractal_interpretation(
        d_value=reg_result["slope"],
        r_squared=reg_result["r_squared"],
    )

    sensitivity_data = None
    if run_sensitivity and analysis_mode == AnalysisMode.FULL_MASK.value:
        sens_result = run_threshold_sensitivity(grayscale, thresh_val, box_sizes_used)
        if sens_result is not None:
            sensitivity_data = SensitivityResult(**sens_result)

    rotation_sensitivity_data = None
    if run_rotation_sensitivity:
        rot_result = run_rotation_sensitivity_fn(binary, box_sizes_used)
        rotation_sensitivity_data = RotationSensitivityResult(**rot_result)

    qs = calculate_quality_score(
        reg_result["r_squared"],
        len(box_sizes_used),
        foreground_ratio=foreground_ratio,
        sensitivity_std_deviation=(
            sensitivity_data.std_deviation if sensitivity_data is not None else None
        ),
        rotation_std_deviation=(
            rotation_sensitivity_data.std_deviation
            if rotation_sensitivity_data is not None
            else None
        ),
    )

    result_data = AnalysisResultData(
        fractal_dimension=reg_result["slope"],
        r_squared=reg_result["r_squared"],
        intercept=reg_result["intercept"],
        standard_error=reg_result["standard_error"],
        confidence_interval=reg_result["confidence_interval"],
        box_sizes=box_sizes_used,
        box_counts=counts,
        log_inverse_sizes=x.tolist(),
        log_counts=y.tolist(),
        fitted_values=reg_result["fitted_values"],
        residuals=reg_result["residuals"],
        foreground_ratio=foreground_ratio,
        quality_score=qs["score"],
        reliability=qs["reliability"],
        interpretation=interp["interpretation"],
        complexity_class=interp["complexity_class"],
        warnings=[],
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    return AnalyzeResponse(
        parameters=params,
        result=result_data,
        sensitivity=sensitivity_data,
        rotation_sensitivity=rotation_sensitivity_data,
        processing_time_ms=processing_time_ms,
        binary_image_b64=binary_b64,
        threshold_method=threshold_method,
        threshold_value=threshold_value,
        analysis_mode=analysis_mode,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG, WEBP)"),
    analysis_mode: str = Form("full_mask"),
    threshold_method: str = Form("otsu"),
    threshold_value: int = Form(128),
    invert: bool = Form(False),
    denoise: bool = Form(False),
    blur_level: int = Form(0),
    box_sizes: str | None = Form(None),
    grid_offsets: str = Form("0,0.25,0.5,0.75"),
    run_sensitivity: bool = Form(False),
    run_rotation_sensitivity: bool = Form(False),
    adaptive_block_size: int = Form(11),
    adaptive_c: int = Form(2),
) -> AnalyzeResponse:
    """Analyze an uploaded image and return its fractal dimension and diagnostics."""
    _ = box_sizes  # Reserved for future custom scale overrides
    start_time = time.time()

    offsets_list = _validate_analysis_params(
        analysis_mode=analysis_mode,
        threshold_method=threshold_method,
        threshold_value=threshold_value,
        blur_level=blur_level,
        adaptive_block_size=adaptive_block_size,
        adaptive_c=adaptive_c,
        grid_offsets=grid_offsets,
    )

    try:
        file_bytes = await read_upload_limited(
            file,
            max_bytes=settings.max_upload_bytes,
            read_timeout_seconds=settings.UPLOAD_READ_TIMEOUT_SECONDS,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    def _execute() -> AnalyzeResponse:
        return _run_analysis_pipeline(
            file_bytes=file_bytes,
            max_dimension=settings.MAX_IMAGE_DIMENSION,
            max_pixels=settings.MAX_IMAGE_PIXELS,
            analysis_mode=analysis_mode,
            threshold_method=threshold_method,
            threshold_value=threshold_value,
            invert=invert,
            denoise=denoise,
            blur_level=blur_level,
            offsets_list=offsets_list,
            run_sensitivity=run_sensitivity,
            run_rotation_sensitivity=run_rotation_sensitivity,
            adaptive_block_size=adaptive_block_size,
            adaptive_c=adaptive_c,
            start_time=start_time,
        )

    try:
        return await asyncio.wait_for(
            anyio.to_thread.run_sync(_execute),
            timeout=settings.ANALYSIS_TIMEOUT_SECONDS,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Image analysis timed out. Try a smaller image or disable extra sensitivity passes.",
        ) from exc


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def analyze_batch(
    request: Request,
    files: list[UploadFile] = File(..., description="Multiple image files (max 10)"),
    analysis_mode: str = Form("full_mask"),
    threshold_method: str = Form("otsu"),
) -> BatchAnalyzeResponse:
    """Batch-analyze multiple images with the same settings."""
    _ = (request, files, analysis_mode, threshold_method)
    raise HTTPException(status_code=501, detail="Batch analysis is not implemented.")
