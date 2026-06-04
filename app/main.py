"""FractalVision Lab — FastAPI application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.deps import limiter
from app.api.v1.router import router as v1_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — track start time for health endpoint."""
    app.state.start_time = time.time()
    yield


settings = get_settings()

app = FastAPI(
    title="FractalVision Lab API",
    description="Fractal dimension analysis API — box-counting, regression, and scientific diagnostics.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Rate Limiter -----------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ----------------------------------------------------------------
app.include_router(v1_router)
