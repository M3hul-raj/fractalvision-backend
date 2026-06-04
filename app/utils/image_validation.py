"""Image upload validation — file type, size, resolution checks."""

from fastapi import UploadFile


ALLOWED_FORMATS = {"image/png", "image/jpeg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def validate_image_upload(file: UploadFile, max_size_bytes: int) -> list[str]:
    """Validate an uploaded image file. Returns list of error messages (empty if valid)."""
    # TODO: Phase 1
    pass


def validate_image_dimensions(
    width: int, height: int, min_dim: int = 128, max_dim: int = 2048
) -> list[str]:
    """Validate image dimensions. Returns list of error messages (empty if valid)."""
    # TODO: Phase 1
    pass
