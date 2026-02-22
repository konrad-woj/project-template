import json
from pathlib import Path

import pytest
from data_models.ocr_models.textract import TextractResultModel

from data_utils.cv_and_math_ops import calculate_angle, calculate_human_readable_angle
from data_utils.ocr.textract import TextractParser

# TODO I remember writing unit tests for TextractParser... Where are they? We need to find them and add them back. -Karol


@pytest.mark.parametrize(
    "filename, expected_angle, expected_human_readable_angle",
    [
        ("0.json", 0, 0),
        ("15.json", -15, 15),
        ("30.json", -30, 30),
        ("45.json", -45, 45),
        ("60.json", -60, 60),
        ("75.json", -75, 75),
        ("90.json", -90, 90),
        ("105.json", -105, 105),
        ("120.json", -120, 120),
        ("135.json", -135, 135),
        ("150.json", -150, 150),
        ("165.json", -165, 165),
        ("180.json", 180, 180),
        ("195.json", 165, 195),
        ("210.json", 150, 210),
        ("225.json", 135, 225),
        ("240.json", 120, 240),
        ("255.json", 105, 255),
        ("270.json", 90, 270),
        ("285.json", 75, 285),
        ("300.json", 60, 300),
        ("315.json", 45, 315),
        ("330.json", 30, 330),
        ("345.json", 15, 345),
    ],
)
def test_computes_orientation_correctly(filename, expected_angle, expected_human_readable_angle):
    root = Path(__file__).parent / "imgs"
    path = root / filename
    parser = TextractParser()

    json_data_blocks = {"Blocks": json.load(path.open())}
    result_model = TextractResultModel(**json_data_blocks)
    parsed_data_blocks, _, _ = parser.parse(result_model)
    parsed_data_block = parsed_data_blocks[0]  # there is only one

    angle = calculate_angle(parsed_data_block.rectangle.p0, parsed_data_block.rectangle.p1)
    angle_hr = calculate_human_readable_angle(parsed_data_block.rectangle.p0, parsed_data_block.rectangle.p1)

    assert abs(angle_hr - expected_human_readable_angle) <= 5
    assert abs(angle - expected_angle) <= 5
