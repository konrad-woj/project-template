import timeit

import cv2
import numpy as np
import pytest
from PIL import Image

from data_utils import image_preprocessing as ip


@pytest.fixture
def sample_img():
    img = np.zeros((100, 100), dtype=np.uint8)
    cv2.line(img, (10, 50), (90, 50), (255,), 2)
    return img


@pytest.fixture
def color_img(sample_img):
    return cv2.cvtColor(sample_img, cv2.COLOR_GRAY2BGR)


@pytest.fixture
def pil_img(sample_img):
    return Image.fromarray(sample_img)


def test_to_grayscale(color_img, sample_img):
    gray = ip.to_grayscale(color_img)
    assert len(gray.shape) == 2
    assert np.array_equal(gray, sample_img)


def test_denoise(sample_img):
    noisy = sample_img + np.random.randint(0, 10, sample_img.shape, dtype=np.uint8)
    denoised = ip.denoise(noisy)
    assert denoised.shape == sample_img.shape


def test_enhance_contrast(sample_img):
    low_contrast = np.full(sample_img.shape, 120, dtype=np.uint8)
    enhanced = ip.enhance_contrast(low_contrast)
    assert enhanced.shape == sample_img.shape


def test_binarize(sample_img):
    binary = ip.binarize(sample_img)
    assert set(np.unique(binary)).issubset({0, 255})


def test_image_to_array_and_array_to_image(pil_img):
    arr = ip.image_to_array(pil_img)
    img2 = ip.array_to_image(arr)
    assert isinstance(img2, Image.Image)


@pytest.mark.parametrize("dpi", [72, 150, 200, 300, 600])
def test_evaluate_multiple_orientations_dpi(dpi):
    # Simulate an A4 page at the given DPI (width x height in pixels)
    # A4 size: 8.27 x 11.69 inches
    width = int(8.27 * dpi)
    height = int(11.69 * dpi)
    img = np.zeros((height, width), dtype=np.uint8)
    # Draw a horizontal line in the middle
    cv2.line(
        img, (int(width * 0.1), height // 2), (int(width * 0.9), height // 2), (255,), thickness=max(1, dpi // 150)
    )
    # Test for 0 and 90 degree orientations
    best_angle = ip.evaluate_multiple_orientations(img, [0, 90])
    assert best_angle == 0


@pytest.mark.parametrize(
    "angle,orientations,expected_angle",
    [
        (0, (0, 90), 0),
        (90, (0, 90), 90),
        (180, (0, 180), 0),  # 0 and 180 are equivalent.
        (270, (0, 90, 270), 90),  # 90 and 270 are equivalent.
        (90, (0, 90, 180, 270), 90),
        (270, (0, 90, 180, 270), 90),
        (0, (0, 90, 3, -3), 0),
        (5, (0, 90, 5, -5), 5),
        (-3, (0, 90, 3, -3), -3),
        (357, (0, 90, -3, 3), -3),  # 357 and -3 are equivalent.
        (273, (0, 90, 87, 93), 93),  # 93 and 273 are equivalent.
    ],
)
def test_horizontalize(sample_img, angle, orientations, expected_angle):
    if angle != 0:
        M = cv2.getRotationMatrix2D((50, 50), angle, 1)
        rotated = cv2.warpAffine(sample_img, M, (100, 100))
    else:
        rotated = sample_img

    _, detected_angle = ip.horizontalize(rotated, orientations_to_test=orientations)
    assert detected_angle == expected_angle


def test_run_pipeline(color_img, sample_img):
    processed = ip.run_pipeline(color_img, pipeline=("to_grayscale", "denoise", "enhance_contrast"))
    assert processed.shape == sample_img.shape


# Benchmark tests.


@pytest.mark.parametrize("dpi", [72, 150, 200, 300, 600])
def test_evaluate_multiple_orientations_benchmark(dpi):
    width = int(8.27 * dpi)
    height = int(11.69 * dpi)
    img = np.zeros((height, width), dtype=np.uint8)
    cv2.line(
        img, (int(width * 0.1), height // 2), (int(width * 0.9), height // 2), (255,), thickness=max(1, dpi // 150)
    )
    angles = [0, 90, 3, -3, 87, 93]
    # Warm-up
    ip.evaluate_multiple_orientations(img, angles)
    # Benchmark
    t = timeit.timeit(lambda: ip.evaluate_multiple_orientations(img, angles), number=5)
    print(f"DPI: {dpi}, shape: {img.shape}, avg time: {t / 5:.4f}s")


@pytest.mark.parametrize("dpi", [72, 150, 200, 300, 600])
def test_horizontalize_benchmark(dpi):
    width = int(8.27 * dpi)
    height = int(11.69 * dpi)
    img = np.zeros((height, width), dtype=np.uint8)
    cv2.line(
        img, (int(width * 0.1), height // 2), (int(width * 0.9), height // 2), (255,), thickness=max(1, dpi // 150)
    )
    angles = [0, 90, 3, -3, 87, 93]
    # Warm-up
    ip.evaluate_multiple_orientations(img, angles)
    # Benchmark
    t = timeit.timeit(lambda: ip.horizontalize(img, angles), number=5)
    print(f"DPI: {dpi}, shape: {img.shape}, avg time: {t / 5:.4f}s")
