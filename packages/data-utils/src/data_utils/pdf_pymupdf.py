from typing import overload

import pymupdf
import structlog
from PIL import Image
from pymupdf import Document, Page

logger = structlog.get_logger()


def load_pdf_from_disk(pdf_path):
    """Loads pdf from file and returns it as object using PyMuPDF."""
    return Document(pdf_path)


@overload
def pdf_to_images(
    pdf: Document,
    page_id: None = None,
    dpi: int = 200,
    pixel_threshold: int | None = None,
) -> list[Image.Image]: ...


@overload
def pdf_to_images(pdf: Document, page_id: int, dpi: int = 200, pixel_threshold: int | None = None) -> Image.Image: ...


def pdf_to_images(
    pdf: Document, page_id: int | None = None, dpi: int = 200, pixel_threshold: int | None = None
) -> list[Image.Image] | Image.Image:
    if page_id is None:
        images = []
        for page_id in range(len(pdf)):
            images.append(pdf_page_to_image(pdf, page_id, dpi, pixel_threshold))
        return images
    else:
        return pdf_page_to_image(pdf, page_id, dpi, pixel_threshold)


def pdf_bytes_to_images(
    pdf_bytes: str | bytes,
    page_id: int | None = None,
    dpi: int = 200,
    pixel_threshold: int | None = None,
) -> list[Image.Image] | Image.Image:
    pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return pdf_to_images(pdf, page_id, dpi, pixel_threshold)


def pdf_page_to_image(pdf: Document, page_id: int, dpi: int = 200, pixel_threshold: int | None = None) -> Image.Image:
    page = pdf.load_page(page_id)
    if pixel_threshold and pixel_threshold > 0:
        logger.info("Checking page size...", page_id=page_id, pixel_threshold=pixel_threshold)
        if is_page_pixels_too_large(page, pixel_threshold, dpi):
            raise Exception(f"Page {page_id} exceeds pixel threshold of {pixel_threshold}")
    zoom = dpi / 72
    matrix = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)  # type: ignore[reportAttributeAccessIssue]
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def is_page_pixels_too_large(page: Page, pixel_threshold: int, dpi: int) -> bool:
    width_in_points, height_in_points = page.mediabox.width, page.mediabox.height
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
