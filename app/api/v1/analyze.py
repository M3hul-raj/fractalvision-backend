"""Analysis endpoints — single image and batch fractal analysis."""

import time
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, Request, UploadFile

from app.models.responses import AnalyzeResponse, BatchAnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG, WEBP)"),
    analysis_mode: str = Form("full_mask"),
    threshold_method: str = Form("otsu"),
    threshold_value: int = Form(128),
    invert: bool = Form(False),
    denoise: bool = Form(False),
    blur_level: int = Form(0),
    box_sizes: Optional[str] = Form(None),
    grid_offsets: str = Form("0,0.25,0.5,0.75"),
    run_sensitivity: bool = Form(False),
) -> AnalyzeResponse:
    from app.core import image_processing, box_counting, regression
    from app.core.quality_score import calculate_quality_score
    from app.core.sensitivity import run_threshold_sensitivity
    from app.models.responses import AnalysisParameters, AnalysisResultData, SensitivityResult
    from app.models.enums import AnalysisMode, ThresholdMethod
    
    start_time = time.time()
    file_bytes = await file.read()
    
    # 1. Image Processing
    image = image_processing.decode_uploaded_image(file_bytes)
    image = image_processing.resize_if_needed(image, 1024)
    grayscale = image_processing.to_grayscale(image)
    
    thresh_val = None
    if analysis_mode == "boundary":
        binary, thresh_val = image_processing.mode_boundary(grayscale)
    elif analysis_mode == "texture":
        binary, thresh_val = image_processing.mode_texture(grayscale)
    else:
        if threshold_method == "adaptive":
            binary, thresh_val = image_processing.adaptive_threshold(grayscale)
        elif threshold_method == "manual":
            binary, thresh_val = image_processing.manual_threshold(grayscale, threshold_value)
        else:
            thresh_val, binary = image_processing.otsu_threshold(grayscale)
            
    if invert:
        binary = 255 - binary
        
    height, width = binary.shape
    
    # 2. Box Counting
    box_sizes_used = box_counting.auto_select_box_sizes(width, height)
    offsets_list = [float(x.strip()) for x in grid_offsets.split(',')] if grid_offsets else []
    
    bc_result = box_counting.run_box_counting(binary, width, height, box_sizes_used, offsets_list)
    counts = bc_result["box_counts"]
    
    # 3. Regression
    x, y = regression.compute_log_values(box_sizes_used, counts)
    try:
        reg_result = regression.linear_regression(x, y)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    
    foreground_ratio = float(np.count_nonzero(binary) / binary.size)
    binary_b64 = image_processing.encode_image_base64(binary)
    
    # 4. Quality Score
    qs = calculate_quality_score(reg_result["r_squared"], len(box_sizes_used))
    
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
        interpretation="Phase 1 math complete.",
        complexity_class="High",
        warnings=[]
    )
    
    # 5. Sensitivity (conditional)
    sensitivity_data = None
    if run_sensitivity and analysis_mode == AnalysisMode.FULL_MASK.value:
        sens_result = run_threshold_sensitivity(grayscale, thresh_val, box_sizes_used)
        if sens_result is not None:
            sensitivity_data = SensitivityResult(**sens_result)
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    return AnalyzeResponse(
        parameters=params,
        result=result_data,
        sensitivity=sensitivity_data,
        processing_time_ms=processing_time_ms,
        binary_image_b64=binary_b64,
        threshold_method=threshold_method,
        threshold_value=threshold_value,
        analysis_mode=analysis_mode
    )


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def analyze_batch(
    request: Request,
    files: list[UploadFile] = File(..., description="Multiple image files (max 10)"),
    analysis_mode: str = Form("full_mask"),
    threshold_method: str = Form("otsu"),
) -> BatchAnalyzeResponse:
    """Batch-analyze multiple images with the same settings."""
    # TODO: Phase 1
    pass
