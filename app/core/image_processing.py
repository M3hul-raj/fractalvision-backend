"""Image processing utilities — grayscale, thresholding, morphology, edge detection."""

import base64
import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR color image to grayscale using cv2."""
    if len(image.shape) == 2:
        return image
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def otsu_threshold(grayscale: np.ndarray) -> tuple[int, np.ndarray]:
    """Apply Otsu's thresholding. Returns (threshold_value, binary_image)."""
    thresh_val, binary = cv2.threshold(
        grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return int(thresh_val), binary


def manual_threshold(
    grayscale: np.ndarray, threshold: int, invert: bool = False
) -> np.ndarray:
    """Apply manual thresholding to a grayscale image."""
    _, binary = cv2.threshold(grayscale, threshold, 255, cv2.THRESH_BINARY_INV)
    return binary


def adaptive_threshold(
    grayscale: np.ndarray, block_size: int = 11, c: int = 2
) -> np.ndarray:
    """Apply adaptive thresholding for images with uneven lighting."""
    return cv2.adaptiveThreshold(
        grayscale, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, c
    )

def mode_boundary(grayscale: np.ndarray) -> np.ndarray:
    """Apply Otsu first, then cv2.Canny to extract boundary/edges."""
    _, binary = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return cv2.Canny(binary, 50, 150)

def mode_texture(grayscale: np.ndarray) -> np.ndarray:
    """Compute morphological gradient, then threshold with Otsu."""
    kernel = np.ones((3,3), np.uint8)
    gradient = cv2.morphologyEx(grayscale, cv2.MORPH_GRADIENT, kernel)
    _, binary = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def apply_blur(image: np.ndarray, kernel_size: int) -> np.ndarray:
    """Apply Gaussian blur to an image."""
    # TODO: Phase 3
    pass


def denoise_image(image: np.ndarray) -> np.ndarray:
    """Apply non-local means denoising."""
    # TODO: Phase 3
    pass


def extract_boundary(binary: np.ndarray) -> np.ndarray:
    """Extract boundary pixels: boundary = binary - eroded(binary)."""
    # TODO: Phase 3
    pass


def skeletonize(binary: np.ndarray) -> np.ndarray:
    """Extract skeleton/venation structure from binary image."""
    # TODO: Phase 3
    pass


def detect_edges(grayscale: np.ndarray) -> np.ndarray:
    """Apply Canny edge detection."""
    # TODO: Phase 3
    pass


def decode_uploaded_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes into a cv2 BGR numpy array."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image file")
    return image


def resize_if_needed(image: np.ndarray, max_dimension: int) -> np.ndarray:
    """Resize image if either dimension exceeds max_dimension."""
    h, w = image.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / float(max(h, w))
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image


def encode_image_base64(image: np.ndarray) -> str:
    """Encode a numpy image array to a base64 PNG string."""
    success, buffer = cv2.imencode('.png', image)
    if not success:
        return ""
    return base64.b64encode(buffer).decode("utf-8")
