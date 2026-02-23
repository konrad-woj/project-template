from os import PathLike
from pathlib import Path
from typing import overload

import structlog
from PIL import Image
from pypdfium2 import PdfDocument, PdfPage

from data_utils.io import ImageTooLargeError

logger = structlog.get_logger()


def load_pdf_from_disk(pdf_path: str | Path | PathLike[str]) -> PdfDocument:
    """Loads pdf from file and returns it as object."""
    return PdfDocument(pdf_path)


@overload
def pdf_to_images(
    pdf: PdfDocument, page_id: None = None, dpi: int = 200, pixel_threshold: int | None = None
) -> list[Image.Image]: ...


@overload
def pdf_to_images(
    pdf: PdfDocument, page_id: int, dpi: int = 200, pixel_threshold: int | None = None
) -> Image.Image: ...


def pdf_to_images(
    pdf: PdfDocument, page_id: int | None = None, dpi: int = 200, pixel_threshold: int | None = None
) -> list[Image.Image] | Image.Image:
    if page_id is not None:
        return pdf_page_to_image(pdf, page_id, dpi, pixel_threshold)
    return [pdf_page_to_image(pdf, i, dpi, pixel_threshold) for i in range(len(pdf))]


def pdf_page_to_image(
    pdf: PdfDocument, page_id: int, dpi: int = 200, pixel_threshold: int | None = None
) -> Image.Image:
    page = pdf.get_page(page_id)
    if pixel_threshold and pixel_threshold > 0:
        logger.info("Checking page size...", page_id=page_id, pixel_threshold=pixel_threshold)
        if is_page_pixels_too_large(page, pixel_threshold, dpi):
            raise ImageTooLargeError(f"Page {page_id} exceeds pixel threshold of {pixel_threshold}")
    image = page.render(scale=int(dpi / 72)).to_pil()
    return image


def is_page_pixels_too_large(page: PdfPage, pixel_threshold: int, dpi: int) -> bool:
    width_in_points, height_in_points = page.get_size()
    zoom = dpi / 72
    width_px, height_px = width_in_points * zoom, height_in_points * zoom
    total_pixels = round(width_px * height_px)
    if total_pixels > pixel_threshold:
        logger.warning(
            "Page size exceeds threshold.",
            pixel_threshold=pixel_threshold,
            total_pixels=total_pixels,
            page_size=(width_in_points, height_in_points),
        )
        return True
    return False
