"""Unit tests for image magic-byte detection, header parsing, and bomb guards."""

import io
import struct
import zlib

import cv2
import numpy as np
import pytest

from app.utils.image_validation import (
    ImageValidationError,
    detect_image_format,
    parse_image_dimensions,
    validate_and_decode_image,
    validate_image_dimensions,
)
from tests.conftest import make_test_image_bytes


def _make_png_with_ihdr(width: int, height: int) -> bytes:
    """Craft a minimal valid-header PNG claiming arbitrary width/height."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
    return sig + ihdr + iend


def test_detect_format_ignores_extension() -> None:
    """Valid PNG/JPEG/WEBP magic bytes should be detected regardless of filename."""
    assert detect_image_format(make_test_image_bytes(".png", 64, 64)) == "png"
    assert detect_image_format(make_test_image_bytes(".jpg", 64, 64)) == "jpeg"
    assert detect_image_format(make_test_image_bytes(".webp", 64, 64)) == "webp"


@pytest.mark.parametrize(
    "payload",
    [
        b"<html><script>alert(1)</script></html>",
        b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
        b"BM" + b"\x00" * 50,  # BMP
        b"GIF89a" + b"\x00" * 20,  # GIF
        b"PK\x03\x04" + b"\x00" * 20,  # ZIP
    ],
)
def test_detect_format_rejects_non_allowed_bytes(payload: bytes) -> None:
    """Unsupported or non-image payloads must fail with HTTP 415."""
    with pytest.raises(ImageValidationError) as exc_info:
        detect_image_format(payload)
    assert exc_info.value.status_code == 415


@pytest.mark.parametrize("ext,expected_fmt", [(".png", "png"), (".jpg", "jpeg"), (".webp", "webp")])
def test_parse_image_dimensions_headers(ext: str, expected_fmt: str) -> None:
    """Header parser must accurately extract dimensions across PNG, JPEG, and WEBP."""
    data = make_test_image_bytes(ext, width=137, height=91)
    fmt = detect_image_format(data)
    assert fmt == expected_fmt
    w, h = parse_image_dimensions(data, fmt)
    assert (w, h) == (137, 91)


def test_decompression_bomb_rejected_before_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Header pixel bomb must be rejected before cv2.imdecode allocates pixel memory."""
    bomb_png = _make_png_with_ihdr(30000, 30000)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("cv2.imdecode should never be called on a decompression bomb!")

    monkeypatch.setattr(cv2, "imdecode", fail_if_called)

    with pytest.raises(ImageValidationError) as exc_info:
        validate_and_decode_image(
            bomb_png,
            max_dimension=4096,
            max_pixels=16_777_216,
        )
    assert exc_info.value.status_code == 413


def test_pixel_count_limit_blocks_square_under_axis_limit() -> None:
    """An image within axis max_dimension can still exceed max_pixels and must fail."""
    with pytest.raises(ImageValidationError) as exc_info:
        validate_image_dimensions(
            width=2000,
            height=2000,
            max_dimension=4096,
            max_pixels=1_000_000,
        )
    assert exc_info.value.status_code == 413


def test_corrupt_png_payload_returns_400() -> None:
    """Valid PNG header with garbage IDAT payload must raise 400, not 500."""
    corrupt_png = _make_png_with_ihdr(64, 64)[:-12] + b"corrupt-data"
    with pytest.raises(ImageValidationError) as exc_info:
        validate_and_decode_image(corrupt_png, max_dimension=4096, max_pixels=16_777_216)
    assert exc_info.value.status_code == 400


def test_webp_lossy_and_lossless_dimension_parse() -> None:
    """Verify WEBP lossy/lossless encoding produced by OpenCV decodes cleanly."""
    arr = np.zeros((75, 113, 3), dtype=np.uint8)
    arr[10:60, 10:100] = 255
    ok, buf = cv2.imencode(".webp", arr)
    assert ok
    decoded = validate_and_decode_image(buf.tobytes(), max_dimension=1024, max_pixels=1_048_576)
    assert decoded.shape[:2] == (75, 113)
    assert io.BytesIO(buf.tobytes()).getbuffer().nbytes > 0


def test_read_upload_limited_aborts_stream_early() -> None:
    """Oversized streams must abort as soon as max_bytes is exceeded without full buffering."""
    import asyncio

    from app.utils.image_validation import read_upload_limited

    class _FakeStreamUpload:
        def __init__(self, chunk: bytes, num_chunks: int) -> None:
            self.chunk = chunk
            self.remaining = num_chunks
            self.reads = 0

        async def read(self, _size: int = -1) -> bytes:
            if self.remaining <= 0:
                return b""
            self.remaining -= 1
            self.reads += 1
            return self.chunk

    fake = _FakeStreamUpload(b"A" * (64 * 1024), 100)  # 6.4 MB total if drained
    with pytest.raises(ImageValidationError) as exc_info:
        asyncio.run(read_upload_limited(fake, max_bytes=200 * 1024, read_timeout_seconds=2.0))

    assert exc_info.value.status_code == 413
    assert fake.reads == 4  # Stopped at 256 KB (> 200 KB), did not drain all 100 chunks!
