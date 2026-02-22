import io
from pathlib import Path

import pytest
from PIL import Image

from data_utils.io import ImageTooLargeError, image_to_rgb, open_image


@pytest.fixture
def sample_img_path():
    return Path(__file__).parent / "data" / "sample_img.png"


@pytest.fixture
def expected_img(sample_img_path):
    img = Image.open(sample_img_path)
    return img


def test_open_image_loads_image_from_path(sample_img_path, expected_img):
    img_from_path = open_image(Path(sample_img_path))
    img_from_pathstr = open_image(str(sample_img_path))

    assert img_from_path == expected_img
    assert img_from_pathstr == expected_img


def test_open_image_loads_image_from_bytes(sample_img_path, expected_img):
    data = io.BytesIO(open(sample_img_path, "rb").read())

    img_from_bytes = open_image(data)

    assert img_from_bytes == expected_img


def test_open_image_throws_error_on_exceeded_pixel_threshold(sample_img_path):
    with pytest.raises(ImageTooLargeError):
        open_image(sample_img_path, pixel_threshold=1000)


class TestImageToRgb:
    def test_rgb_image_unchanged(self):
        img = Image.new("RGB", (10, 10), color="red")

        result = image_to_rgb(img)

        assert result.mode == "RGB"
        assert result is img  # Should return same object

    def test_palette_with_transparency_to_rgb(self):
        img = Image.new("P", (10, 10))
        img.info["transparency"] = 0

        result = image_to_rgb(img)

        assert result.mode == "RGB"

    def test_palette_with_transparency_no_transparency_flag(self):
        img = Image.new("P", (10, 10))
        img.info["transparency"] = 0

        result = image_to_rgb(img, no_transparency=True)

        assert result.mode == "RGB"

    def test_palette_with_transparency_preserve_transparency(self):
        img = Image.new("P", (10, 10))
        img.info["transparency"] = 0

        result = image_to_rgb(img, no_transparency=False)

        assert result.mode == "RGBA"

    def test_palette_without_transparency_to_rgb(self):
        img = Image.new("P", (10, 10))

        result = image_to_rgb(img)

        assert result.mode == "RGB"

    def test_grayscale_to_rgb(self):
        img = Image.new("L", (10, 10), color=128)

        result = image_to_rgb(img)

        assert result.mode == "RGB"
        assert result.getpixel((0, 0)) == (128, 128, 128)

    def test_grayscale_kept_with_keep_grayscale_true(self):
        img = Image.new("L", (10, 10), color=128)

        result = image_to_rgb(img, keep_grayscale=True)

        assert result.mode == "L"
        assert result is img  # Should return same object

    def test_1bit_to_rgb(self):
        img = Image.new("1", (10, 10), color=1)

        result = image_to_rgb(img)

        assert result.mode == "RGB"

    def test_1bit_kept_with_keep_grayscale_true(self):
        img = Image.new("1", (10, 10), color=1)

        result = image_to_rgb(img, keep_grayscale=True)

        assert result.mode == "1"
        assert result is img  # Should return same object

    def test_rgba_to_rgb_by_default(self):
        img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))

        result = image_to_rgb(img)

        assert result.mode == "RGB"
        assert result is not img

    def test_rgba_preserved_with_no_transparency_false(self):
        img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))

        result = image_to_rgb(img, no_transparency=False)

        assert result.mode == "RGBA"
        assert result is img

    def test_other_modes_to_rgb(self):
        img = Image.new("CMYK", (10, 10), color=(100, 0, 100, 0))

        result = image_to_rgb(img)

        assert result.mode == "RGB"

    def test_preserves_image_data(self):
        img = Image.new("L", (2, 2))
        img.putpixel((0, 0), 0)
        img.putpixel((1, 0), 85)
        img.putpixel((0, 1), 170)
        img.putpixel((1, 1), 255)

        result = image_to_rgb(img)

        assert result.mode == "RGB"
        assert result.size == (2, 2)
        assert result.getpixel((0, 0)) == (0, 0, 0)
        assert result.getpixel((1, 1)) == (255, 255, 255)
