import math
from pathlib import Path

import pytest
from data_models.geometry_models.object_detection import BoundingBox
from data_models.geometry_models.primitives import Point
from data_utils.cv_and_math_ops import (
    calculate_angle,
    calculate_human_readable_angle,
    compute_ioa,
    compute_iou,
    resize_img_keep_ratio,
)
from PIL import Image


@pytest.mark.parametrize(
    "p1, p2, expected_degrees, expected_human_degrees",
    [
        (Point(0, 0), Point(1, 0), 0, 0),
        (Point(0, 0), Point(1, 1), 45, 315),
        (Point(0, 0), Point(0, 1), 90, 270),
        (Point(0, 0), Point(-1, 1), 135, 225),
        (Point(0, 0), Point(-1, 0), 180, 180),
        (Point(0, 0), Point(-1, -1), -135, 135),
        (Point(0, 0), Point(0, -1), -90, 90),
        (Point(0, 0), Point(1, -1), -45, 45),
        (Point(0, 0), Point(-1, 0.01), 179, 181),
        (Point(0, 0), Point(-1, -0.01), -179, 179),
    ],
)
def test_calculates_orientation_in_degrees(p1: Point, p2: Point, expected_degrees: int, expected_human_degrees: int):
    degrees = calculate_angle(p1, p2)
    human_readable_degrees = calculate_human_readable_angle(p1, p2)
    assert human_readable_degrees == expected_human_degrees
    assert degrees == expected_degrees


@pytest.fixture
def image_narrow():
    img_path = Path(__file__).parent / "data" / "dog_narrow.png"
    img = Image.open(img_path)
    return img


@pytest.fixture
def image_wide():
    img_path = Path(__file__).parent / "data" / "dog_wide.jpg"
    img = Image.open(img_path)
    return img


@pytest.mark.parametrize(
    "new_longer_side, new_size",
    [
        pytest.param(400, (216, 400), id="narrow_downsize_1"),
        pytest.param(200, (108, 200), id="narrow_downsize_2"),
        pytest.param(50, (27, 50), id="narrow_downsize_3"),
    ],
)
def test_downsize_narrow_image_preserve_ratio(
    image_narrow: Image.Image, new_longer_side: int, new_size: tuple[int, int]
):
    resized = resize_img_keep_ratio(image_narrow, new_longer_side)
    assert resized.size == new_size


@pytest.mark.parametrize(
    "new_longer_side, new_size",
    [
        pytest.param(400, (400, 224), id="wide_downsize_1"),
        pytest.param(200, (200, 112), id="wide_downsize_2"),
        pytest.param(50, (50, 28), id="wide_downsize_3"),
    ],
)
def test_downsize_wide_image_preserve_ratio(image_wide: Image.Image, new_longer_side: int, new_size: tuple[int, int]):
    resized = resize_img_keep_ratio(image_wide, new_longer_side)
    assert resized.size == new_size


@pytest.mark.parametrize(
    "bbox_xywh_1, bbox_xywh_2, expected_iou",
    [
        ((0, 0, 1, 1), (0, 0, 1, 1), 1.0),
        ((0, 0, 1, 1), (1, 1, 1, 1), 0.0),
        ((0, 0, 2, 2), (1, 1, 1, 1), 0.25),
        ((0, 0, 2, 2), (1, 1, 2, 2), 0.14),
        ((0, 0, 4, 4), (1, 1, 2, 2), 0.25),
    ],
)
def test_iou(bbox_xywh_1, bbox_xywh_2, expected_iou):
    iou = compute_iou(
        BoundingBox(top=bbox_xywh_1[0], left=bbox_xywh_1[1], width=bbox_xywh_1[2], height=bbox_xywh_1[3]),
        BoundingBox(top=bbox_xywh_2[0], left=bbox_xywh_2[1], width=bbox_xywh_2[2], height=bbox_xywh_2[3]),
    )
    assert math.isclose(iou, expected_iou, abs_tol=0.01)


@pytest.mark.parametrize(
    "bbox_xywh_1, bbox_xywh_2, area_bbox, expected_ioa",
    [
        ((0, 0, 1, 1), (0, 0, 2, 2), "first", 1.0),
        ((0, 0, 1, 1), (0, 0, 2, 2), "second", 0.25),
        ((0, 0, 2, 2), (0, 0, 2, 2), "first", 1.0),
        ((0, 0, 2, 2), (0, 0, 1, 1), "first", 0.25),
    ],
)
def test_ioa(bbox_xywh_1, bbox_xywh_2, area_bbox, expected_ioa):
    ioa = compute_ioa(
        BoundingBox(top=bbox_xywh_1[0], left=bbox_xywh_1[1], width=bbox_xywh_1[2], height=bbox_xywh_1[3]),
        BoundingBox(top=bbox_xywh_2[0], left=bbox_xywh_2[1], width=bbox_xywh_2[2], height=bbox_xywh_2[3]),
        area_bbox,
    )
    assert ioa == expected_ioa


def test_ioa_throws_error_on_wrong_area_bbox_str():
    with pytest.raises(AssertionError) as e:
        compute_ioa(BoundingBox(1, 2, 3, 4), BoundingBox(4, 3, 2, 1), "wrong string")
    assert str(e.value) == "`area_bbox` must be one of: 'first', 'second'"
