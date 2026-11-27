"""Integration and security tests for FastAPI endpoints, uploads, timeouts, and CORS."""

import asyncio
import struct
import time
import zlib

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import analyze as analyze_module
from app.config import Settings, get_settings
from app.main import create_app
from tests.conftest import make_test_image_bytes


def _craft_png_bomb_bytes(width: int, height: int) -> bytes:
    """Build a small valid-IHDR PNG claiming huge dimensions (~60 bytes)."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
    return sig + ihdr + iend


def test_health_and_fractals_endpoints(client: TestClient) -> None:
    """Health and standard fractal endpoints return expected 200 responses."""
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    fractals = client.get("/api/v1/fractals")
    assert fractals.status_code == 200
    assert len(fractals.json()) == 5

    gen = client.post(
        "/api/v1/fractals/cantor_set/generate",
        json={"iterations": 4, "image_size": 256},
    )
    assert gen.status_code == 200
    assert 0.5 <= gen.json()["computed_dimension"] <= 1.0


def test_analyze_accepts_valid_png_regardless_of_extension(client: TestClient) -> None:
    """Valid PNG bytes with .txt extension and octet-stream MIME must be verified and accepted."""
    png_bytes = make_test_image_bytes(".png", 128, 128)
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("not_an_image.txt", png_bytes, "application/octet-stream")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0.5 <= body["result"]["fractal_dimension"] <= 2.1


@pytest.mark.parametrize("ext,mime", [(".jpg", "image/jpeg"), (".webp", "image/webp")])
def test_analyze_accepts_jpeg_and_webp(client: TestClient, ext: str, mime: str) -> None:
    """Valid JPEG and WEBP uploads decode and analyze cleanly."""
    img_bytes = make_test_image_bytes(ext, 128, 128)
    resp = client.post(
        "/api/v1/analyze",
        files={"file": (f"sample{ext}", img_bytes, mime)},
    )
    assert resp.status_code == 200


def test_analyze_rejects_oversized_file_with_413(test_settings: Settings) -> None:
    """Files larger than MAX_UPLOAD_SIZE_MB are rejected cleanly with HTTP 413."""
    tiny_limit_settings = test_settings.model_copy(update={"MAX_UPLOAD_SIZE_MB": 1})
    app = create_app(tiny_limit_settings)
    app.dependency_overrides[get_settings] = lambda: tiny_limit_settings

    oversized_bytes = b"\x89PNG\r\n\x1a\n" + (b"0" * (1024 * 1024 + 64))
    with TestClient(app) as tc:
        resp = tc.post(
            "/api/v1/analyze",
            files={"file": ("huge.png", oversized_bytes, "image/png")},
        )
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["detail"].lower()


def test_analyze_rejects_empty_file_with_400(client: TestClient) -> None:
    """Empty uploads fail cleanly with HTTP 400."""
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert resp.status_code == 400


def test_analyze_rejects_disguised_non_image_with_415(client: TestClient) -> None:
    """Text/SVG/HTML disguised with .png extension and image/png MIME is rejected with 415."""
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("fake.png", b"<svg><script>alert(1)</script></svg>", "image/png")},
    )
    assert resp.status_code == 415


def test_analyze_rejects_corrupt_image_bytes_with_400(client: TestClient) -> None:
    """Valid PNG header with truncated/corrupt body returns clean 400, never 500."""
    corrupt = _craft_png_bomb_bytes(128, 128)
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("corrupt.png", corrupt, "image/png")},
    )
    assert resp.status_code == 400


def test_analyze_rejects_dimension_limit_with_413(client: TestClient) -> None:
    """Images exceeding MAX_IMAGE_DIMENSION (1024 in test_settings) return 413."""
    too_wide = _craft_png_bomb_bytes(2048, 128)
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("wide.png", too_wide, "image/png")},
    )
    assert resp.status_code == 413
    assert "dimension" in resp.json()["detail"].lower()


def test_analyze_rejects_decompression_bomb_pixels_with_413(test_settings: Settings) -> None:
    """Small PNG claiming huge pixel count (e.g. 900x900 > 500k pixels) fails with 413."""
    bomb_settings = test_settings.model_copy(
        update={"MAX_IMAGE_DIMENSION": 4096, "MAX_IMAGE_PIXELS": 500_000}
    )
    app = create_app(bomb_settings)
    app.dependency_overrides[get_settings] = lambda: bomb_settings

    bomb_bytes = _craft_png_bomb_bytes(900, 900)  # 810,000 pixels > 500,000
    with TestClient(app) as tc:
        resp = tc.post(
            "/api/v1/analyze",
            files={"file": ("bomb.png", bomb_bytes, "image/png")},
        )
    assert resp.status_code == 413
    assert "pixel" in resp.json()["detail"].lower()


def test_analyze_rejects_invalid_form_params_with_422(client: TestClient) -> None:
    """Out-of-bounds or invalid preprocessing parameters return clean 422 errors."""
    png_bytes = make_test_image_bytes(".png", 64, 64)
    bad_blur = client.post(
        "/api/v1/analyze",
        files={"file": ("ok.png", png_bytes, "image/png")},
        data={"blur_level": "999"},
    )
    assert bad_blur.status_code == 422

    bad_mode = client.post(
        "/api/v1/analyze",
        files={"file": ("ok.png", png_bytes, "image/png")},
        data={"analysis_mode": "invalid_mode"},
    )
    assert bad_mode.status_code == 422

    bad_offsets = client.post(
        "/api/v1/analyze",
        files={"file": ("ok.png", png_bytes, "image/png")},
        data={"grid_offsets": "abc,def"},
    )
    assert bad_offsets.status_code == 422


def test_analyze_rejects_too_small_image_with_422(client: TestClient) -> None:
    """Images smaller than 16x16 cannot yield >= 2 box scales and return 422."""
    tiny_png = make_test_image_bytes(".png", 8, 8)
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("tiny.png", tiny_png, "image/png")},
    )
    assert resp.status_code == 422


def test_analyze_compute_timeout_returns_504(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Long-running analysis exceeding ANALYSIS_TIMEOUT_SECONDS returns 504."""
    short_timeout_settings = test_settings.model_copy(update={"ANALYSIS_TIMEOUT_SECONDS": 0.05})
    app = create_app(short_timeout_settings)
    app.dependency_overrides[get_settings] = lambda: short_timeout_settings

    def slow_pipeline(**_kwargs):
        time.sleep(0.25)
        raise AssertionError("Should have timed out before returning")

    monkeypatch.setattr(analyze_module, "_run_analysis_pipeline", slow_pipeline)

    png_bytes = make_test_image_bytes(".png", 64, 64)
    with TestClient(app) as tc:
        resp = tc.post(
            "/api/v1/analyze",
            files={"file": ("ok.png", png_bytes, "image/png")},
        )
    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"].lower()


def test_upload_read_timeout_returns_408(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slow upload stream exceeding UPLOAD_READ_TIMEOUT_SECONDS returns 408."""
    short_read_settings = test_settings.model_copy(update={"UPLOAD_READ_TIMEOUT_SECONDS": 0.05})
    app = create_app(short_read_settings)
    app.dependency_overrides[get_settings] = lambda: short_read_settings

    from starlette.datastructures import UploadFile as StarletteUploadFile

    async def slow_read(_self, _size: int = -1) -> bytes:
        await asyncio.sleep(0.25)
        return b""

    monkeypatch.setattr(StarletteUploadFile, "read", slow_read)

    png_bytes = make_test_image_bytes(".png", 64, 64)
    with TestClient(app) as tc:
        resp = tc.post(
            "/api/v1/analyze",
            files={"file": ("ok.png", png_bytes, "image/png")},
        )
    assert resp.status_code == 408
    assert "timed out" in resp.json()["detail"].lower()


@pytest.mark.parametrize(
    "origin",
    [
        "https://fractalvision-frontend.vercel.app",
        "http://localhost:3000",
    ],
)
def test_cors_allows_configured_frontend_and_localhost(
    client: TestClient,
    origin: str,
) -> None:
    """Allowed production and localhost origins receive Access-Control-Allow-Origin."""
    preflight = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == origin


def test_cors_blocks_untrusted_origin(client: TestClient) -> None:
    """Untrusted third-party origins must NOT receive Access-Control-Allow-Origin."""
    resp = client.get(
        "/api/v1/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_cors_rejects_wildcard_configuration() -> None:
    """Wildcard '*' in ALLOWED_ORIGINS must fail settings validation."""
    with pytest.raises(ValueError, match="Wildcard"):
        Settings(_env_file=None, ALLOWED_ORIGINS="*")


def test_analyze_batch_returns_501(client: TestClient) -> None:
    """Unimplemented batch endpoint returns 501 instead of crashing with 500."""
    png_bytes = make_test_image_bytes(".png", 64, 64)
    resp = client.post(
        "/api/v1/analyze/batch",
        files={"files": ("ok.png", png_bytes, "image/png")},
    )
    assert resp.status_code == 501
