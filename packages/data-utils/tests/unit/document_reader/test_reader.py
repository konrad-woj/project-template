from pathlib import Path

import pytest
from PIL import Image

from data_utils.document_reader import DocumentReader


@pytest.mark.parametrize(
    "base_dpi, max_image_size",
    [
        (200, 3000),  # the sample pdf gives (2200, 1700) with dpi 200
        (200, 2000),
    ],
)
def test_get_image_from_pdf_path(base_dpi, max_image_size):
    reader = DocumentReader(base_dpi=base_dpi, max_img_size=max_image_size)

    filepath = Path(__file__).parent.resolve() / "data" / "sample.pdf"
    extracted_image = reader.get_image_from_pdf_path(filepath, page_id=0)

    assert isinstance(extracted_image, Image.Image)
    assert max(extracted_image.size) <= max_image_size
    # check it's not reduced too much
    assert max(extracted_image.size) > max_image_size / 2
