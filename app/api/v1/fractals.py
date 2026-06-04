"""Standard fractal endpoints — list fractal types and generate/analyze them."""

from fastapi import APIRouter

from app.models.requests import GenerateFractalRequest
from app.models.responses import GenerateFractalResponse, StandardFractalInfo

router = APIRouter()


@router.get("/fractals", response_model=list[StandardFractalInfo])
async def list_fractals() -> list[StandardFractalInfo]:
    """List available standard mathematical fractal types."""
    # TODO: Phase 7
    pass


@router.post("/fractals/{fractal_id}/generate", response_model=GenerateFractalResponse)
async def generate_fractal(
    fractal_id: str,
    body: GenerateFractalRequest,
) -> GenerateFractalResponse:
    """Generate a standard fractal at the given iteration depth and compute its box-counting dimension."""
    # TODO: Phase 7
    pass
