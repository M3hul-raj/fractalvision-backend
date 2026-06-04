"""Box-counting algorithm for fractal dimension estimation."""

import numpy as np


def box_count(
    binary: np.ndarray,
    width: int,
    height: int,
    box_size: int,
) -> int:
    """Count occupied boxes at a single box size."""
    pad_h = (box_size - height % box_size) % box_size
    pad_w = (box_size - width % box_size) % box_size
    if pad_h > 0 or pad_w > 0:
        binary = np.pad(binary, ((0, pad_h), (0, pad_w)), mode='constant', constant_values=0)
    
    h, w = binary.shape
    blocks = binary.reshape(h // box_size, box_size, w // box_size, box_size)
    return int(np.count_nonzero(blocks.sum(axis=(1, 3))))


def box_count_with_offsets(
    binary: np.ndarray,
    width: int,
    height: int,
    box_size: int,
    offsets: list[float],
) -> dict:
    """Run box counting with multiple grid-origin offsets. Returns stats dict."""
    counts = []
    for ox in offsets:
        for oy in offsets:
            start_y = int(box_size * oy)
            start_x = int(box_size * ox)
            shifted = binary[start_y:, start_x:]
            c = box_count(shifted, shifted.shape[1], shifted.shape[0], box_size)
            counts.append(c)
    
    return {
        "mean": float(np.mean(counts)),
        "min": int(np.min(counts)),
        "max": int(np.max(counts)),
        "std": float(np.std(counts)),
    }


def run_box_counting(
    binary: np.ndarray,
    width: int,
    height: int,
    box_sizes: list[int],
    offsets: list[float] | None = None,
) -> dict:
    """Run the full box-counting pipeline across all box sizes. Returns {box_sizes, box_counts}."""
    box_counts = []
    for bs in box_sizes:
        if offsets and len(offsets) > 0:
            stats = box_count_with_offsets(binary, width, height, bs, offsets)
            box_counts.append(stats["min"])
        else:
            box_counts.append(box_count(binary, width, height, bs))
            
    return {
        "box_sizes": box_sizes,
        "box_counts": box_counts
    }


def auto_select_box_sizes(width: int, height: int) -> list[int]:
    """Auto-select valid box sizes (powers of 2) based on image dimensions."""
    min_dim = min(width, height)
    max_box = min_dim // 4
    sizes = []
    bs = 4
    while bs <= max_box:
        sizes.append(bs)
        bs *= 2
    return sizes
