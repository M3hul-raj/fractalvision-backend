import numpy as np
from app.core.box_counting import box_count, auto_select_box_sizes, run_box_counting

def test_box_count():
    # 8x8 image, a simple 4x4 square in the middle
    binary = np.zeros((8, 8), dtype=np.uint8)
    binary[2:6, 2:6] = 255
    
    count = box_count(binary, 8, 8, 2)
    assert count == 4
    
    count = box_count(binary, 8, 8, 4)
    assert count == 4
    
    count = box_count(binary, 8, 8, 8)
    assert count == 1

def test_auto_select_box_sizes():
    sizes = auto_select_box_sizes(1024, 1024)
    assert sizes == [4, 8, 16, 32, 64, 128, 256]

def test_run_box_counting():
    binary = np.zeros((8, 8), dtype=np.uint8)
    binary[2:6, 2:6] = 255
    res = run_box_counting(binary, 8, 8, [2, 4, 8])
    assert res["box_sizes"] == [2, 4, 8]
    assert res["box_counts"] == [4, 4, 1]
