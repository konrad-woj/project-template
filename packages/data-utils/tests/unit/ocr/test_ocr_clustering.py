import pytest

from data_utils.ocr.ocr_clustering import OcrTextClustering

from .conftest import make_simple_block, rotate_block_page


def test_empty_input():
    """Test that empty input returns an empty string."""
    clusterer = OcrTextClustering()
    assert clusterer.process_ocr_results([]) == ""


def test_single_word():
    """Test that a single word is processed correctly."""
    block = make_simple_block("A", 0.1, 0.1, 0.2, 0.05)
    clusterer = OcrTextClustering()
    result = clusterer.process_ocr_results([block.model_dump(by_alias=True)])
    assert result == "word_A"


def test_simple_horizontal_line():
    """Test clustering of a simple horizontal line of words."""
    blocks = [
        make_simple_block("A", 0.1, 0.1, 0.1, 0.05),
        make_simple_block("B", 0.22, 0.1, 0.1, 0.05),
        make_simple_block("C", 0.34, 0.1, 0.1, 0.05),
    ]
    clusterer = OcrTextClustering()
    result = clusterer.process_ocr_results([b.model_dump(by_alias=True) for b in blocks])
    assert result == "word_A word_B word_C"


def test_simple_vertical_column():
    """Test clustering of a simple vertical column of words."""
    blocks = [
        make_simple_block("A", 0.1, 0.1, 0.2, 0.05),
        make_simple_block("B", 0.1, 0.17, 0.2, 0.05),
        make_simple_block("C", 0.1, 0.24, 0.2, 0.05),
    ]
    clusterer = OcrTextClustering()
    result = clusterer.process_ocr_results([b.model_dump(by_alias=True) for b in blocks])
    assert result == "word_A\nword_B\nword_C"


def test_two_separate_clusters():
    """Test that two separate groups of words are clustered independently."""
    blocks = [
        # Cluster 1.
        make_simple_block("A", 0.1, 0.1, 0.1, 0.05),
        make_simple_block("B", 0.22, 0.1, 0.1, 0.05),
        # Cluster 2 (far away).
        make_simple_block("C", 0.7, 0.7, 0.1, 0.05),
        make_simple_block("D", 0.82, 0.7, 0.1, 0.05),
    ]
    clusterer = OcrTextClustering()
    result = clusterer.process_ocr_results([b.model_dump(by_alias=True) for b in blocks])
    assert result == "word_A word_B\n\nword_C word_D"


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_rotated_text_clustering(rotation):
    """Test that clustering works correctly after derotating text."""
    # Two blocks, one above the other. After rotation, they should still be clustered vertically.
    block1 = make_simple_block("A", 0.3, 0.3, 0.2, 0.05)
    block2 = make_simple_block("B", 0.301, 0.36, 0.201, 0.051)  # With OCR noise.
    blocks = [block1, block2]

    rotated_blocks = [rotate_block_page(b, rotation) for b in blocks]

    clusterer = OcrTextClustering(x_gap_multiplier=0.2, y_gap_multiplier=0.8)
    result = clusterer.process_ocr_results([b.model_dump(by_alias=True) for b in rotated_blocks])

    # The expected result is always the same because derotation happens first.
    # The blocks should be identified as a single vertical cluster.
    assert result == "word_A\nword_B"
