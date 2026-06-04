import numpy as np
import cv2
from app.core.image_processing import to_grayscale, otsu_threshold, resize_if_needed

def test_to_grayscale():
    # Create a dummy BGR image
    bgr_img = np.zeros((10, 10, 3), dtype=np.uint8)
    bgr_img[:, :, 0] = 255 # Blue
    gray_img = to_grayscale(bgr_img)
    assert gray_img.shape == (10, 10)
    assert len(gray_img.shape) == 2

def test_otsu_threshold():
    # Create a simple image with distinct background and foreground
    gray_img = np.zeros((20, 20), dtype=np.uint8)
    gray_img[5:15, 5:15] = 255
    thresh_val, binary = otsu_threshold(gray_img)
    assert 0 <= thresh_val <= 255
    # Since cv2.THRESH_BINARY_INV is used, background (0) becomes 255, foreground (255) becomes 0
    assert binary[0, 0] == 255
    assert binary[10, 10] == 0

def test_resize_if_needed():
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    resized = resize_if_needed(img, 150)
    # The max dimension is 300, scale factor = 150 / 300 = 0.5
    # New size should be 100 x 150
    assert resized.shape[:2] == (100, 150)
    
    # If max dimension is larger than current size, no resize should happen
    not_resized = resize_if_needed(img, 500)
    assert not_resized.shape == img.shape
