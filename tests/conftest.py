"""Shared test fixtures and configuration."""

from collections.abc import Iterator

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.deps import limiter
from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Iterator[None]:
    """Reset slowapi in-memory counters between tests so tests stay isolated."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def test_settings() -> Settings:
    """Deterministic settings independent of any local .env file."""
    return Settings(
        _env_file=None,
        ALLOWED_ORIGINS="https://fractalvision-frontend.vercel.app,http://localhost:3000",
        MAX_UPLOAD_SIZE_MB=2,
        MAX_IMAGE_DIMENSION=1024,
        MAX_IMAGE_PIXELS=1_048_576,
        UPLOAD_READ_TIMEOUT_SECONDS=2.0,
        ANALYSIS_TIMEOUT_SECONDS=5.0,
    )


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    """FastAPI TestClient configured with isolated test_settings."""
    app = create_app(test_settings)
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_test_image_bytes(
    fmt: str = ".png",
    width: int = 128,
    height: int = 128,
) -> bytes:
    """Create a synthetic binary-friendly pattern encoded in the requested format."""
    img = np.full((height, width, 3), 255, dtype=np.uint8)
    for y in range(0, height, 8):
        for x in range(0, width, 8):
            if ((x // 8) ^ (y // 8)) & 1:
                img[y : y + 4, x : x + 4] = 0
    ok, buf = cv2.imencode(fmt, img)
    assert ok, f"Failed to encode test image as {fmt}"
    return buf.tobytes()
