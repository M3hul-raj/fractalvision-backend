"""Standard fractal generators — Cantor Set, Koch Curve, Sierpiński Triangle/Carpet."""

import math
import numpy as np
import cv2


# Registry of known standard fractals and their theoretical dimensions.
STANDARD_FRACTALS: list[dict] = [
    {
        "fractal_id": "cantor_set",
        "name": "Cantor Set",
        "theoretical_dimension": 0.6309,
        "max_iterations": 8,
        "description": "Created by repeatedly removing the middle third of line segments",
    },
    {
        "fractal_id": "koch_curve",
        "name": "Koch Curve",
        "theoretical_dimension": 1.2619,
        "max_iterations": 7,
        "description": "Each line segment is replaced by four segments of one-third length",
    },
    {
        "fractal_id": "koch_snowflake",
        "name": "Koch Snowflake",
        "theoretical_dimension": 1.2619,
        "max_iterations": 7,
        "description": "Three Koch curves forming a closed snowflake boundary",
    },
    {
        "fractal_id": "sierpinski_triangle",
        "name": "Sierpiński Triangle",
        "theoretical_dimension": 1.5850,
        "max_iterations": 8,
        "description": "Equilateral triangle subdivided recursively, removing central triangle",
    },
    {
        "fractal_id": "sierpinski_carpet",
        "name": "Sierpiński Carpet",
        "theoretical_dimension": 1.8928,
        "max_iterations": 6,
        "description": "Square subdivided into 9 equal squares, removing center square recursively",
    },
]

# Look-up: fractal_id → max_iterations
_MAX_ITERS: dict[str, int] = {f["fractal_id"]: f["max_iterations"] for f in STANDARD_FRACTALS}


def _clamp_iterations(fractal_id: str, iterations: int) -> int:
    """Clamp iterations to [1, max_iterations] for the given fractal."""
    iterations = max(1, iterations)
    max_iter = _MAX_ITERS.get(fractal_id, 8)
    return min(iterations, max_iter)


# --------------------------------------------------------------------------- #
# Cantor Set
# --------------------------------------------------------------------------- #

def generate_cantor_set(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Cantor Set image at the given iteration depth.

    Draws ONLY the final iteration's segments as a single horizontal
    line at y = size // 2 so box-counting measures the correct dimension.
    """
    iterations = _clamp_iterations("cantor_set", iterations)
    img = np.zeros((image_size, image_size), dtype=np.uint8)

    margin = int(image_size * 0.05)
    draw_w = image_size - 2 * margin
    y_mid = image_size // 2

    # Build final segments iteratively as (x_start_frac, x_end_frac) in [0, 1]
    segments: list[tuple[float, float]] = [(0.0, 1.0)]
    for _ in range(iterations):
        next_segments: list[tuple[float, float]] = []
        for (s, e) in segments:
            third = (e - s) / 3.0
            next_segments.append((s, s + third))
            next_segments.append((s + 2 * third, e))
        segments = next_segments

    # Draw ONLY the final segments as a single horizontal line
    for (s, e) in segments:
        x0 = int(margin + s * draw_w)
        x1 = int(margin + e * draw_w)
        if x1 > x0:
            cv2.line(img, (x0, y_mid), (x1, y_mid), 255, 2)

    return img


# --------------------------------------------------------------------------- #
# Koch Curve helpers
# --------------------------------------------------------------------------- #

def _koch_subdivide(segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Apply one iteration of Koch subdivision to a list of (p1, p2) segments."""
    result: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for (ax, ay), (bx, by) in segments:
        # P1/3 and P2/3
        p1x = ax + (bx - ax) / 3.0
        p1y = ay + (by - ay) / 3.0
        p2x = ax + 2 * (bx - ax) / 3.0
        p2y = ay + 2 * (by - ay) / 3.0
        # Apex of equilateral triangle bump (rotate 60° outward)
        dx = p2x - p1x
        dy = p2y - p1y
        apex_x = p1x + dx * 0.5 - dy * math.sqrt(3) / 2.0
        apex_y = p1y + dy * 0.5 + dx * math.sqrt(3) / 2.0
        result.append(((ax, ay), (p1x, p1y)))
        result.append(((p1x, p1y), (apex_x, apex_y)))
        result.append(((apex_x, apex_y), (p2x, p2y)))
        result.append(((p2x, p2y), (bx, by)))
    return result


def _draw_segments(img: np.ndarray, segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> None:
    """Draw all segments on the image."""
    pts = np.array(
        [[int(round(ax)), int(round(ay)), int(round(bx)), int(round(by))]
         for (ax, ay), (bx, by) in segments],
        dtype=np.int32,
    )
    for row in pts:
        cv2.line(img, (row[0], row[1]), (row[2], row[3]), 255, 1)


# --------------------------------------------------------------------------- #
# Koch Curve
# --------------------------------------------------------------------------- #

def generate_koch_curve(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Koch Curve image at the given iteration depth."""
    iterations = _clamp_iterations("koch_curve", iterations)
    img = np.zeros((image_size, image_size), dtype=np.uint8)

    margin = int(image_size * 0.05)
    draw_w = image_size - 2 * margin
    y_mid = image_size // 2

    # Single horizontal base segment
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = [
        ((float(margin), float(y_mid)), (float(margin + draw_w), float(y_mid)))
    ]

    for _ in range(iterations):
        segments = _koch_subdivide(segments)

    _draw_segments(img, segments)
    return img


# --------------------------------------------------------------------------- #
# Koch Snowflake
# --------------------------------------------------------------------------- #

def generate_koch_snowflake(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Koch Snowflake image at the given iteration depth."""
    iterations = _clamp_iterations("koch_snowflake", iterations)
    img = np.zeros((image_size, image_size), dtype=np.uint8)

    margin = int(image_size * 0.08)
    cx = image_size / 2.0
    cy = image_size / 2.0
    r = (image_size / 2.0) - margin

    # Three vertices of an equilateral triangle (pointing up)
    angles = [math.pi / 2 + i * 2 * math.pi / 3 for i in range(3)]
    verts = [(cx + r * math.cos(a), cy - r * math.sin(a)) for a in angles]

    # Three initial edges
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = [
        (verts[0], verts[1]),
        (verts[1], verts[2]),
        (verts[2], verts[0]),
    ]

    for _ in range(iterations):
        segments = _koch_subdivide(segments)

    _draw_segments(img, segments)
    return img


# --------------------------------------------------------------------------- #
# Sierpiński Triangle
# --------------------------------------------------------------------------- #

def generate_sierpinski_triangle(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Sierpiński Triangle image using recursive fillPoly."""
    iterations = _clamp_iterations("sierpinski_triangle", iterations)
    img = np.zeros((image_size, image_size), dtype=np.uint8)

    margin = int(image_size * 0.05)
    draw_w = image_size - 2 * margin
    draw_h = image_size - 2 * margin

    # Equilateral triangle vertices (top-center, bottom-left, bottom-right)
    top = (image_size // 2, margin)
    bot_left = (margin, margin + draw_h)
    bot_right = (margin + draw_w, margin + draw_h)

    def fill_triangle(pts: list[tuple[int, int]]) -> None:
        arr = np.array([pts], dtype=np.int32)
        cv2.fillPoly(img, arr, 255)

    def erase_triangle(pts: list[tuple[int, int]]) -> None:
        arr = np.array([pts], dtype=np.int32)
        cv2.fillPoly(img, arr, 0)

    def midpoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
        return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)

    # Fill entire outer triangle first
    fill_triangle([top, bot_left, bot_right])

    # Queue-based iteration: list of triangles to remove at each level
    to_remove: list[list[tuple[int, int]]] = [[top, bot_left, bot_right]]

    for _ in range(iterations):
        next_triangles: list[list[tuple[int, int]]] = []
        for tri in to_remove:
            a, b, c = tri
            mab = midpoint(a, b)
            mbc = midpoint(b, c)
            mac = midpoint(a, c)
            # Erase center triangle
            erase_triangle([mab, mbc, mac])
            # The three sub-triangles for next iteration
            next_triangles.append([a, mab, mac])
            next_triangles.append([mab, b, mbc])
            next_triangles.append([mac, mbc, c])
        to_remove = next_triangles

    return img


# --------------------------------------------------------------------------- #
# Sierpiński Carpet
# --------------------------------------------------------------------------- #

def generate_sierpinski_carpet(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Sierpiński Carpet using iterative numpy slicing, centered on canvas."""
    iterations = _clamp_iterations("sierpinski_carpet", iterations)

    # Pick the largest power-of-3 side that fits inside 90% of the canvas
    max_side = int(image_size * 0.90)
    carpet_size = 1
    while carpet_size * 3 <= max_side:
        carpet_size *= 3

    # Build the carpet as a standalone square array
    carpet = np.ones((carpet_size, carpet_size), dtype=np.uint8) * 255

    squares: list[tuple[int, int, int]] = [(0, 0, carpet_size)]
    for _ in range(iterations):
        next_squares: list[tuple[int, int, int]] = []
        for (r, c, s) in squares:
            third = s // 3
            # Erase center sub-square
            carpet[r + third: r + 2 * third, c + third: c + 2 * third] = 0
            # Queue the 8 surrounding sub-squares for the next level
            for dr in range(3):
                for dc in range(3):
                    if dr == 1 and dc == 1:
                        continue
                    next_squares.append((r + dr * third, c + dc * third, third))
        squares = next_squares

    # Center-paste the carpet onto a black canvas
    img = np.zeros((image_size, image_size), dtype=np.uint8)
    y_offset = (image_size - carpet_size) // 2
    x_offset = (image_size - carpet_size) // 2
    img[y_offset: y_offset + carpet_size, x_offset: x_offset + carpet_size] = carpet

    return img


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #

FRACTAL_DISPATCH: dict[str, callable] = {  # type: ignore[type-arg]
    "cantor_set": generate_cantor_set,
    "koch_curve": generate_koch_curve,
    "koch_snowflake": generate_koch_snowflake,
    "sierpinski_triangle": generate_sierpinski_triangle,
    "sierpinski_carpet": generate_sierpinski_carpet,
}


def generate_fractal(fractal_id: str, iterations: int, image_size: int) -> np.ndarray:
    """Dispatch to the correct generator based on fractal_id.

    Raises ValueError for unknown fractal_id.
    """
    fn = FRACTAL_DISPATCH.get(fractal_id)
    if fn is None:
        raise ValueError(f"Unknown fractal_id: {fractal_id!r}")
    return fn(iterations, image_size)
