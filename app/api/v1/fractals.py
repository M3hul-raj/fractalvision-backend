"""Standard fractal endpoints — list fractal types and generate/analyze them."""

import asyncio
import time
from typing import Annotated

import anyio
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import limiter
from app.config import Settings, get_settings
from app.core.box_counting import auto_select_box_sizes, run_box_counting
from app.core.fractal_generators import (
    FRACTAL_DISPATCH,
    STANDARD_FRACTALS,
    generate_fractal,
)
from app.core.image_processing import encode_image_base64
from app.core.regression import compute_log_values, linear_regression
from app.models.requests import GenerateFractalRequest
from app.models.responses import GenerateFractalResponse, StandardFractalInfo

router = APIRouter()

# Pre-build a lookup from fractal_id → STANDARD_FRACTALS entry
_FRACTAL_META: dict[str, dict] = {f["fractal_id"]: f for f in STANDARD_FRACTALS}


@router.get("/fractals", response_model=list[StandardFractalInfo])
async def list_fractals() -> list[StandardFractalInfo]:
    """List available standard mathematical fractal types."""
    return [StandardFractalInfo(**f) for f in STANDARD_FRACTALS]


def _generate_and_analyze(
    fractal_id: str,
    body: GenerateFractalRequest,
) -> GenerateFractalResponse:
    """CPU-bound fractal generation and box counting executed off the event loop."""
    meta = _FRACTAL_META[fractal_id]
    theoretical_dim: float = meta["theoretical_dimension"]

    start = time.perf_counter()

    img: np.ndarray = generate_fractal(fractal_id, body.iterations, body.image_size)
    h, w = img.shape[:2]

    box_sizes: list[int] = body.box_sizes if body.box_sizes else auto_select_box_sizes(w, h)
    counting_result = run_box_counting(img, w, h, box_sizes)
    counted_sizes: list[int] = counting_result["box_sizes"]
    counted_counts: list[int] = counting_result["box_counts"]

    valid = [(s, c) for s, c in zip(counted_sizes, counted_counts) if c > 0]
    if len(valid) < 2:
        raise ValueError(
            "Not enough valid box-count data points to perform regression. "
            "Try a higher iteration count or a larger image_size."
        )
    valid_sizes, valid_counts = zip(*valid)

    log_x, log_y = compute_log_values(list(valid_sizes), list(valid_counts))
    reg = linear_regression(log_x, log_y)

    computed_dim: float = reg["slope"]
    error_pct: float = abs(computed_dim - theoretical_dim) / theoretical_dim * 100.0
    image_b64: str = encode_image_base64(img)
    processing_ms = int((time.perf_counter() - start) * 1000)

    return GenerateFractalResponse(
        fractal_id=fractal_id,
        name=meta["name"],
        iterations=body.iterations,
        theoretical_dimension=theoretical_dim,
        computed_dimension=round(computed_dim, 6),
        error_percentage=round(error_pct, 4),
        r_squared=round(reg["r_squared"], 6),
        image_base64=image_b64,
        box_sizes=list(valid_sizes),
        box_counts=list(valid_counts),
        log_inverse_sizes=[round(v, 6) for v in log_x.tolist()],
        log_counts=[round(v, 6) for v in log_y.tolist()],
        processing_time_ms=processing_ms,
    )


@router.post("/fractals/{fractal_id}/generate", response_model=GenerateFractalResponse)
@limiter.limit("10/minute")
async def generate_fractal_endpoint(
    request: Request,
    fractal_id: str,
    body: GenerateFractalRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenerateFractalResponse:
    """Generate a standard fractal at the given iteration depth and compute its D."""
    _ = request
    if fractal_id not in FRACTAL_DISPATCH:
        raise HTTPException(status_code=404, detail=f"Unknown fractal: {fractal_id!r}")

    try:
        return await asyncio.wait_for(
            anyio.to_thread.run_sync(_generate_and_analyze, fractal_id, body),
            timeout=settings.ANALYSIS_TIMEOUT_SECONDS,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Fractal generation timed out.",
        ) from exc
