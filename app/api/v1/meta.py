"""Meta endpoints — interpretation bands and reference data."""

from fastapi import APIRouter

from app.models.responses import InterpretationBand

router = APIRouter()


@router.get("/meta/interpretation-bands", response_model=list[InterpretationBand])
async def get_interpretation_bands() -> list[InterpretationBand]:
    """Get the D-value interpretation bands used for complexity classification."""
    # TODO: Phase 5
    pass
