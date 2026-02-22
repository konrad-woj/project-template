import math

from data_models.ocr_models.textract import TextractBlockModel

from data_utils.ocr.ocr_derotation import OcrDerotation

from .conftest import make_simple_block, rotate_block_page


def test_derotation_to_canonical_position():
    """
    Test that derotation always produces the same canonical polygon regardless of initial rotation.
    This version generates a canonical block, pre-rotates it around the page center,
    derotates it, and asserts that the result matches the canonical polygon.
    """
    x, y, w, h = 0.2, 0.3, 0.1, 0.05
    canonical_block = make_simple_block("A", x, y, w, h)
    expected_poly = canonical_block.geometry.polygon

    for rotation in [0, 90, 180, 270]:
        rotated_block = rotate_block_page(canonical_block, rotation)
        derotated_dicts = OcrDerotation.detect_and_derotate_blocks([rotated_block.model_dump(by_alias=True)])
        derotated = TextractBlockModel(**derotated_dicts[0])
        derotated_poly = derotated.geometry.polygon
        for dp, ep in zip(derotated_poly, expected_poly, strict=False):
            assert abs(dp.x - ep.x) < 1e-6
            assert abs(dp.y - ep.y) < 1e-6


def test_multiple_blocks_relative_positions_preserved():
    """
    Test that multiple blocks maintain their relative positions after derotation.
    """
    # Arrange two blocks horizontally.
    block1 = make_simple_block("A", 0.2, 0.3, 0.1, 0.05)
    block2 = make_simple_block("B", 0.4, 0.3, 0.1, 0.05)
    blocks = [block1, block2]

    def rotate_blocks_page(blocks_to_rotate: list[TextractBlockModel], angle: int) -> list[TextractBlockModel]:
        return [rotate_block_page(block, angle) for block in blocks_to_rotate]

    for rotation in [0, 90, 180, 270]:
        rotated_blocks = rotate_blocks_page(blocks, rotation)
        derotated_dicts = OcrDerotation.detect_and_derotate_blocks(
            [b.model_dump(by_alias=True) for b in rotated_blocks]
        )
        derotated = [TextractBlockModel(**b) for b in derotated_dicts]
        # After derotation, block2 should still be to the right of block1.
        b1_center = (
            sum(p.x for p in derotated[0].geometry.polygon) / 4,
            sum(p.y for p in derotated[0].geometry.polygon) / 4,
        )
        b2_center = (
            sum(p.x for p in derotated[1].geometry.polygon) / 4,
            sum(p.y for p in derotated[1].geometry.polygon) / 4,
        )
        assert b2_center[0] > b1_center[0]
        assert abs(b2_center[1] - b1_center[1]) < 1e-6


def test_reading_direction_vector_after_derotation():
    """
    Test that after derotation, the reading direction vector (from point 0 to 1) is always left-to-right (horizontal).
    """
    block = make_simple_block("A", 0.2, 0.3, 0.1, 0.05)

    for rotation in [0, 90, 180, 270]:
        rotated_block = rotate_block_page(block, rotation)
        derotated_dicts = OcrDerotation.detect_and_derotate_blocks([rotated_block.model_dump(by_alias=True)])
        derotated = TextractBlockModel(**derotated_dicts[0])
        p0, p1 = derotated.geometry.polygon[0], derotated.geometry.polygon[1]
        dx, dy = p1.x - p0.x, p1.y - p0.y
        angle = math.degrees(math.atan2(dy, dx))
        # Should be close to 0 degrees (horizontal, left-to-right).
        assert abs(angle) < 1e-4


def test_empty_input_returns_empty():
    """
    Test that empty input returns empty list.
    """
    assert OcrDerotation.detect_and_derotate_blocks([]) == []


def test_single_block_no_rotation_needed():
    """
    Test that a block already in canonical orientation is unchanged.
    """
    block = make_simple_block("A", 0.2, 0.3, 0.1, 0.05)
    result_dicts = OcrDerotation.detect_and_derotate_blocks([block.model_dump(by_alias=True)])
    result = TextractBlockModel(**result_dicts[0])
    assert result.geometry.polygon == block.geometry.polygon
