"""Upload validation utilities — byte-size, magic-byte format, and header dimension checks."""

import asyncio
import struct

import numpy as np
from fastapi import UploadFile

from app.core.image_processing import decode_uploaded_image

_CHUNK_SIZE = 64 * 1024
_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_JPEG_SIG = b"\xff\xd8\xff"
_SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3,
    0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB,
    0xCD, 0xCE, 0xCF,
}


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation with an explicit HTTP status."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


async def read_upload_limited(
    upload: UploadFile,
    max_bytes: int,
    read_timeout_seconds: float,
) -> bytes:
    """Stream-read an uploaded file with size and timeout bounds.

    Reads in 64 KiB chunks so oversized payloads fail fast with HTTP 413
    without buffering unbounded bytes in memory.
    """
    chunks: list[bytes] = []
    total = 0

    async def _read_all() -> bytes:
        nonlocal total
        while True:
            chunk = await upload.read(_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                max_mb = max_bytes / (1024 * 1024)
                raise ImageValidationError(
                    413,
                    f"File size exceeds {max_mb:g} MB limit.",
                )
            chunks.append(chunk)
        return b"".join(chunks)

    try:
        data = await asyncio.wait_for(_read_all(), timeout=read_timeout_seconds)
    except TimeoutError as exc:
        raise ImageValidationError(
            408,
            "Timed out while reading uploaded file.",
        ) from exc

    if not data:
        raise ImageValidationError(400, "Uploaded file is empty.")

    return data


def detect_image_format(data: bytes) -> str:
    """Verify image container from file magic bytes (ignoring extension/MIME headers)."""
    if data.startswith(_PNG_SIG):
        return "png"
    if data.startswith(_JPEG_SIG):
        return "jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    raise ImageValidationError(
        415,
        "Unsupported or unrecognized image content. Accepted formats: JPEG, PNG, WEBP.",
    )


def _parse_png_dimensions(data: bytes) -> tuple[int, int]:
    """Read (width, height) from the PNG IHDR chunk without decompressing IDAT."""
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise ImageValidationError(400, "Corrupt PNG header: missing IHDR chunk.")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _parse_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Scan JPEG markers for SOF0..SOF15 to read (width, height) before decoding."""
    pos = 2
    n = len(data)
    while pos < n:
        while pos < n and data[pos] == 0xFF:
            pos += 1
        if pos >= n:
            break
        marker = data[pos]
        pos += 1

        if marker in (0x00, 0x01) or (0xD0 <= marker <= 0xD7):
            continue
        if marker in (0xD8, 0xD9, 0xDA):
            break

        if pos + 2 > n:
            break
        seg_len = struct.unpack(">H", data[pos : pos + 2])[0]
        if seg_len < 2 or pos + seg_len > n:
            break

        if marker in _SOF_MARKERS:
            if seg_len < 7:
                break
            height, width = struct.unpack(">HH", data[pos + 3 : pos + 7])
            return width, height

        pos += seg_len

    raise ImageValidationError(400, "Corrupt JPEG header: missing Start Of Frame marker.")


def _parse_webp_dimensions(data: bytes) -> tuple[int, int]:
    """Read (width, height) from VP8, VP8L, or VP8X RIFF chunks before decoding."""
    pos = 12
    n = len(data)
    while pos + 8 <= n:
        chunk_id = data[pos : pos + 4]
        chunk_size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        payload = pos + 8

        if chunk_id == b"VP8 " and payload + 10 <= n:
            if data[payload + 3 : payload + 6] != b"\x9d\x01\x2a":
                raise ImageValidationError(400, "Corrupt WEBP VP8 header.")
            raw_w, raw_h = struct.unpack("<HH", data[payload + 6 : payload + 10])
            return raw_w & 0x3FFF, raw_h & 0x3FFF

        if chunk_id == b"VP8L" and payload + 5 <= n:
            if data[payload] != 0x2F:
                raise ImageValidationError(400, "Corrupt WEBP VP8L header.")
            bits = struct.unpack("<I", data[payload + 1 : payload + 5])[0]
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height

        if chunk_id == b"VP8X" and payload + 10 <= n:
            width = int.from_bytes(data[payload + 4 : payload + 7], "little") + 1
            height = int.from_bytes(data[payload + 7 : payload + 10], "little") + 1
            return width, height

        pos = payload + chunk_size + (chunk_size & 1)

    raise ImageValidationError(400, "Corrupt WEBP header: missing dimension chunk.")


def parse_image_dimensions(data: bytes, fmt: str) -> tuple[int, int]:
    """Extract (width, height) from image headers prior to full pixel decoding."""
    if fmt == "png":
        width, height = _parse_png_dimensions(data)
    elif fmt == "jpeg":
        width, height = _parse_jpeg_dimensions(data)
    elif fmt == "webp":
        width, height = _parse_webp_dimensions(data)
    else:
        raise ImageValidationError(415, f"Unsupported image format: {fmt}")

    if width <= 0 or height <= 0:
        raise ImageValidationError(400, "Invalid image dimensions.")
    return width, height


def validate_image_dimensions(
    width: int,
    height: int,
    max_dimension: int,
    max_pixels: int,
) -> None:
    """Enforce axis dimension and total decoded pixel count limits."""
    if width <= 0 or height <= 0:
        raise ImageValidationError(400, "Invalid image dimensions.")
    if width > max_dimension or height > max_dimension:
        raise ImageValidationError(
            413,
            f"Image dimensions {width}x{height} exceed maximum allowed "
            f"dimension of {max_dimension}px.",
        )
    if width * height > max_pixels:
        raise ImageValidationError(
            413,
            f"Decoded pixel count ({width * height:,} pixels) exceeds maximum "
            f"allowed limit of {max_pixels:,} pixels.",
        )


def validate_and_decode_image(
    file_bytes: bytes,
    max_dimension: int,
    max_pixels: int,
) -> np.ndarray:
    """Verify format, header bounds, decode pixels, and re-verify decoded shape."""
    fmt = detect_image_format(file_bytes)
    hdr_w, hdr_h = parse_image_dimensions(file_bytes, fmt)
    validate_image_dimensions(hdr_w, hdr_h, max_dimension, max_pixels)

    try:
        image = decode_uploaded_image(file_bytes)
    except ValueError as exc:
        raise ImageValidationError(400, "Invalid or corrupted image file.") from exc

    dec_h, dec_w = image.shape[:2]
    validate_image_dimensions(dec_w, dec_h, max_dimension, max_pixels)
    return image
