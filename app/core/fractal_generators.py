"""Standard fractal generators — Cantor Set, Koch Curve, Sierpiński Triangle/Carpet."""

import numpy as np


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


def generate_cantor_set(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Cantor Set image at the given iteration depth."""
    # TODO: Phase 7
    pass


def generate_koch_curve(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Koch Curve image at the given iteration depth."""
    # TODO: Phase 7
    pass


def generate_koch_snowflake(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Koch Snowflake image at the given iteration depth."""
    # TODO: Phase 7
    pass


def generate_sierpinski_triangle(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Sierpiński Triangle image at the given iteration depth."""
    # TODO: Phase 7
    pass


def generate_sierpinski_carpet(iterations: int, image_size: int) -> np.ndarray:
    """Generate a Sierpiński Carpet image at the given iteration depth."""
    # TODO: Phase 7
    pass


def generate_fractal(fractal_id: str, iterations: int, image_size: int) -> np.ndarray:
    """Dispatch to the correct generator based on fractal_id."""
    # TODO: Phase 7
    pass
