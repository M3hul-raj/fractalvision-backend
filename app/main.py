"""FractalVision Lab — FastAPI application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.deps import limiter
from app.api.v1.router import router as v1_router
from app.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — track start time for health endpoint."""
    app.state.start_time = time.time()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    resolved_settings = settings or get_settings()

    application = FastAPI(
        title="FractalVision Lab API",
        description=(
            "Fractal dimension analysis API — box-counting, regression, "
            "and scientific diagnostics."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # --- Rate Limiter -------------------------------------------------------
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- CORS ---------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

    # --- Routers ------------------------------------------------------------
    application.include_router(v1_router)

    return application


app = create_app()
