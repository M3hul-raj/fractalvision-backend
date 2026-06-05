import numpy as np
import cv2
from app.core.image_processing import (
    to_grayscale, 
    otsu_threshold, 
    resize_if_needed,
    manual_threshold,
    adaptive_threshold,
    mode_boundary,
    mode_texture
)

def test_to_grayscale():
    bgr_img = np.zeros((10, 10, 3), dtype=np.uint8)
    bgr_img[:, :, 0] = 255 # Blue
    gray_img = to_grayscale(bgr_img)
    assert gray_img.shape == (10, 10)
    assert len(gray_img.shape) == 2

def test_manual_threshold():
    gray_img = np.zeros((20, 20), dtype=np.uint8)
    gray_img[5:15, 5:15] = 120
    gray_img[0:5, 0:5] = 200
    binary = manual_threshold(gray_img, 150)
    assert binary[2, 2] == 0
    assert binary[10, 10] == 255

def test_adaptive_threshold():
    gray_img = np.full((20, 20), 128, dtype=np.uint8)
    binary = adaptive_threshold(gray_img)
    assert binary.shape == (20, 20)
    assert binary.dtype == np.uint8

def test_mode_boundary():
    gray_img = np.zeros((30, 30), dtype=np.uint8)
    gray_img[5:25, 5:25] = 255
    edges = mode_boundary(gray_img)
    assert edges.shape == (30, 30)
    assert np.any(edges > 0)

def test_mode_texture():
    gray_img = np.zeros((20, 20), dtype=np.uint8)
    gray_img[5:15, 5:15] = 255
    texture = mode_texture(gray_img)
    assert texture.shape == (20, 20)
    assert len(np.unique(texture)) <= 2

def test_otsu_threshold():
    gray_img = np.zeros((20, 20), dtype=np.uint8)
    gray_img[5:15, 5:15] = 255
    thresh_val, binary = otsu_threshold(gray_img)
    assert 0 <= thresh_val <= 255
    assert binary[0, 0] == 255
    assert binary[10, 10] == 0

def test_resize_if_needed():
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    resized = resize_if_needed(img, 150)
    assert resized.shape[:2] == (100, 150)
    not_resized = resize_if_needed(img, 500)
    assert not_resized.shape == img.shape
