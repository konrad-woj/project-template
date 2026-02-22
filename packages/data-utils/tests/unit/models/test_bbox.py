import pytest
from data_models.geometry_models.object_detection import BoundingBox

from data_utils.cv_and_math_ops import compute_iou


def test_top_left_height_width_provided():
    bbox = BoundingBox(
        top=1,
        left=1,
        height=9,
        width=9,
    )
    assert bbox.right == 10
    assert bbox.bottom == 10


def test_top_left_bottom_right_provided():
    bbox = BoundingBox(top=1, left=1, bottom=5, right=5)
    assert bbox.width == 4
    assert bbox.height == 4


def test_wrong_pair_of_arguments():
    with pytest.raises(ValueError):
        BoundingBox(top=1, left=1, height=5, right=5)


def test_missing_top_left():
    with pytest.raises(TypeError):
        BoundingBox(bottom=5, right=5, height=3, left=7)  # type: ignore[reportCallIssue]


def test_iou_disjoint():
    bbox_1 = BoundingBox(top=1, left=1, bottom=2, right=2)
    bbox_2 = BoundingBox(top=2, left=2, bottom=3, right=3)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 0.0


def test_iou_full_overlap():
    bbox_1 = BoundingBox(top=1, left=1, bottom=2, right=2)
    bbox_2 = BoundingBox(top=1, left=1, bottom=2, right=2)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 1.0


def test_iou_partial_overlap():
    bbox_1 = BoundingBox(top=0, left=0, bottom=2, right=2)
    bbox_2 = BoundingBox(top=1, left=1, bottom=2, right=2)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 0.25

    bbox_1 = BoundingBox(top=0, left=0, bottom=2, right=3)
    bbox_2 = BoundingBox(top=0, left=1, bottom=2, right=4)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 0.5


def test_iou_are_symmetric():
    bbox_1 = BoundingBox(top=0, left=0, bottom=200, right=200)
    bbox_2 = BoundingBox(top=0, left=0, bottom=250, right=250)
    iou_1 = compute_iou(bbox_1, bbox_2)
    iou_2 = compute_iou(bbox_2, bbox_1)
    assert iou_1 == iou_2 == 0.64


def test_iou_negative_coords():
    bbox_1 = BoundingBox(top=-100, left=-100, bottom=100, right=100)
    bbox_2 = BoundingBox(top=-50, left=-50, bottom=50, right=50)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 0.25


def test_iou_zero_area():
    bbox_1 = BoundingBox(top=0, left=0, height=0, width=0)
    bbox_2 = BoundingBox(top=0, left=0, height=0, width=0)
    iou = compute_iou(bbox_1, bbox_2)
    assert iou == 0
