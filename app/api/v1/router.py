"""API v1 router — aggregates all v1 route modules."""

from fastapi import APIRouter

from app.api.v1 import analyze, fractals, health, meta

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(analyze.router, tags=["analysis"])
router.include_router(fractals.router, tags=["fractals"])
router.include_router(meta.router, tags=["meta"])
