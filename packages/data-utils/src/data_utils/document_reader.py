from pathlib import Path

import structlog
from PIL import Image
from pymupdf import Document

from data_utils.io import (
    document_to_image,
    is_image_pixels_too_large,
)

logger = structlog.get_logger(__name__)


class DocumentReader:
    """Class for reading png and pdf documents and some handy operations (validating size, converting etc.)."""

    def __init__(
        self,
        base_dpi: int = 300,
        max_img_size: int | None = None,
        pixel_threshold: int = 100_000_000,
        raise_on_pixel_threshold: bool = True,
        min_valid_dpi: int = 50,
    ):
        self.base_dpi = base_dpi
        self.max_img_size = max_img_size
        self.pixel_threshold = pixel_threshold
        # This should be true for app, and false for experiments if false it will attempt to downscale the image first.
        self.raise_on_pixel_threshold = raise_on_pixel_threshold
        self.min_valid_dpi = min_valid_dpi

    def is_image_size_ok(self, img: Image.Image) -> bool:
        """Check if image is not too large."""
        if self.max_img_size and (max(img.size) > self.max_img_size):
            logger.info("Image too large (size)", size=img.size, max_size=self.max_img_size)
            return False
        elif self.pixel_threshold and is_image_pixels_too_large(img, pixel_threshold=self.pixel_threshold):
            logger.info("Image too large (pixels)", size=img.size, pixel_threshold=self.pixel_threshold)
            return False

        return True

    def get_image_from_file(self, filepath: Path | str, page_id: int = 0) -> Image.Image:
        """Reads document file and returns resized/validated image."""
        filepath = Path(filepath)

        if filepath.suffix.lower() == ".pdf":
            return self.get_image_from_pdf_path(filepath, page_id)
        elif filepath.suffix.lower() == ".png":
            img = Image.open(filepath)
            return self.get_image_from_document(img)
        else:
            logger.error("Unsupported file type", extension=filepath.suffix.lower(), file=filepath)
            raise NotImplementedError(f"Unsupported file extension: {filepath.suffix.lower()}")

    def get_image_from_pdf_path(self, pdf_path: str | Path, page_id: int) -> Image.Image:
        """Loads PDF page as Image. If too large it will reduce the DPI."""
        pdf = Document(pdf_path)
        return self.get_image_from_document(pdf, page_id)

    def get_image_from_document(self, document: Document | Image.Image, page_id: int = 0) -> Image.Image:
        """Returns a validated, DPI-scaled image from a PDF Document or PIL Image. Reduces DPI if too large."""
        dpi = self.base_dpi
        if self.raise_on_pixel_threshold:
            image = document_to_image(document, page_id=page_id, dpi=dpi, pixel_threshold=self.pixel_threshold)
        else:
            image = document_to_image(document, page_id=page_id, dpi=dpi, pixel_threshold=None)

        while dpi >= self.min_valid_dpi:
            image = resize_image_to_dpi(image, target_dpi=dpi)
            image.format = "PNG"

            if self.is_image_size_ok(image):
                if dpi != self.base_dpi:
                    logger.info("Resized image.", dpi=dpi, size=image.size)
                return image

            # Reduce DPI and try again
            dpi = int(dpi * 0.75)
            logger.info("Page too large, dropping DPI.", dpi=dpi, page_id=page_id)

        raise RuntimeError(f"Failed to extract image for page id={page_id}: minimum DPI reached")


def resize_image_to_dpi(image: Image.Image, target_dpi: int = 300) -> Image.Image:
    """Changes the DPI of a PIL Image.

    Args:
        image: Input PIL Image
        target_dpi: Desired DPI value

    Returns:
        PIL Image with updated DPI
    """
    orig_dpi = image.info.get("dpi")
    if orig_dpi is None:
        logger.info(
            "No DPI metadata found in image, assuming target DPI. Return the same image, no resizing.",
            target_dpi=target_dpi,
        )
        image.info["dpi"] = (target_dpi, target_dpi)
        return image

    orig_dpi = orig_dpi[0]
    scale = target_dpi / orig_dpi
    new_size = (int(image.width * scale), int(image.height * scale))

    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    resized.info["dpi"] = (target_dpi, target_dpi)

    return resized