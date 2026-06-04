"""Pydantic response models for FractalVision Lab API."""

from typing import Optional

from pydantic import BaseModel

from app.models.enums import AnalysisMode, Reliability, ThresholdMethod


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #

class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str
    version: str
    uptime_seconds: float


# --------------------------------------------------------------------------- #
# Analysis result components
# --------------------------------------------------------------------------- #

class AnalysisParameters(BaseModel):
    """Parameters that were used for an analysis run."""
    analysis_mode: AnalysisMode
    threshold_method: ThresholdMethod
    computed_threshold: Optional[int] = None
    invert: bool
    denoise: bool
    blur_level: int
    box_sizes_used: list[int]
    image_width: int
    image_height: int


class AnalysisResultData(BaseModel):
    """Core fractal analysis result data."""
    fractal_dimension: float
    r_squared: float
    intercept: float
    standard_error: float
    confidence_interval: tuple[float, float]
    box_sizes: list[int]
    box_counts: list[int]
    log_inverse_sizes: list[float]
    log_counts: list[float]
    fitted_values: list[float]
    residuals: list[float]
    foreground_ratio: float
    quality_score: int
    reliability: Reliability
    interpretation: str
    complexity_class: str
    warnings: list[str]


class SensitivityResult(BaseModel):
    """Result of a single sensitivity test."""
    thresholds_tested: Optional[list[int]] = None
    angles_tested: Optional[list[int]] = None
    offsets_tested: Optional[list[float]] = None
    dimensions: list[float]
    std_deviation: float
    is_stable: bool


class SensitivityReport(BaseModel):
    """Aggregated sensitivity test results."""
    threshold: Optional[SensitivityResult] = None
    rotation: Optional[SensitivityResult] = None
    grid_origin: Optional[SensitivityResult] = None


# --------------------------------------------------------------------------- #
# Single analysis response
# --------------------------------------------------------------------------- #

class AnalyzeResponse(BaseModel):
    """Response for POST /analyze."""
    parameters: AnalysisParameters
    result: AnalysisResultData
    sensitivity: Optional[SensitivityReport] = None
    processing_time_ms: int


# --------------------------------------------------------------------------- #
# Batch analysis response
# --------------------------------------------------------------------------- #

class BatchResultItem(BaseModel):
    """A single item in a batch analysis response."""
    filename: str
    status: str
    result: Optional[AnalysisResultData] = None
    error: Optional[str] = None


class BatchAnalyzeResponse(BaseModel):
    """Response for POST /analyze/batch."""
    total: int
    completed: int
    failed: int
    results: list[BatchResultItem]
    processing_time_ms: int


# --------------------------------------------------------------------------- #
# Standard fractals
# --------------------------------------------------------------------------- #

class StandardFractalInfo(BaseModel):
    """Metadata for a standard mathematical fractal."""
    fractal_id: str
    name: str
    theoretical_dimension: float
    max_iterations: int
    description: str


class GenerateFractalResponse(BaseModel):
    """Response for POST /fractals/{id}/generate."""
    fractal_id: str
    name: str
    iterations: int
    theoretical_dimension: float
    computed_dimension: float
    error_percentage: float
    r_squared: float
    image_base64: str
    box_sizes: list[int]
    box_counts: list[int]
    log_inverse_sizes: list[float]
    log_counts: list[float]
    processing_time_ms: int


# --------------------------------------------------------------------------- #
# Meta / interpretation
# --------------------------------------------------------------------------- #

class InterpretationBand(BaseModel):
    """A single D-value interpretation band."""
    min: float
    max: Optional[float] = None
    label: str


# --------------------------------------------------------------------------- #
# Standard error envelope
# --------------------------------------------------------------------------- #

class ErrorDetail(BaseModel):
    """Detail for a single validation error."""
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    """Standard error response body."""
    code: str
    message: str
    details: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None


class MetaInfo(BaseModel):
    """Metadata attached to every API response."""
    request_id: str
    timestamp: str


class ApiResponse(BaseModel):
    """Standard API response envelope."""
    data: Optional[dict | list] = None
    error: Optional[ErrorBody] = None
    meta: Optional[MetaInfo] = None
