"""Health check endpoint — fully implemented in Phase 0."""

import time

from fastapi import APIRouter, Request

from app.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Return application health status and uptime."""
    uptime = time.time() - request.app.state.start_time
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
    )
