from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import IO

import structlog
from PIL import Image, UnidentifiedImageError

logger = structlog.get_logger()


class ImageTooLargeError(Exception):
    """Custom exception for image size errors."""

    pass


def open_image(
    fp: str | bytes | PathLike[str] | PathLike[bytes] | IO[bytes], pixel_threshold: int | None = 100_000_000, **kwargs
) -> Image.Image:
    """Opens an image file and returns it as a PIL Image object.

    Args:
        fp: File path or file-like object to the image.
        pixel_threshold: Maximum number of pixels allowed. If the image size exceeds this threshold, an error is raised.
        **kwargs: Additional keyword arguments to pass to PIL Image.open.

    Returns:
        PIL Image object.

    Raises:
        ImageTooLargeError: If the image size exceeds the pixel threshold.
        UnidentifiedImageError: If the image cannot be identified or opened.
    """
    try:
        if isinstance(fp, bytes):
            fp = BytesIO(fp)
        image = Image.open(fp, **kwargs)
        if pixel_threshold and is_image_pixels_too_large(image, pixel_threshold=pixel_threshold):
            raise ImageTooLargeError(f"Image {fp} exceeds pixel threshold of {pixel_threshold}")
        return image
    except UnidentifiedImageError as e:
        logger.error("Failed to open image", image_path=fp, error=str(e))
        raise e


def document_to_image(
    document,
    page_id: int = 0,
    dpi: int = 300,
    pixel_threshold: int | None = 100_000_000,
    to_rgb: bool = True,
) -> Image.Image:
    """Extracts an image from a document, which can be a PDF or an image file.

    Args:
        document: Document object (pypdfium2.PdfDocument, pymupdf.Document, or PIL Image).
        page_id: Page number to extract if the document is a PDF (0-indexed).
        dpi: Dots per inch; a parameter denoting quality of resulting image.
        pixel_threshold: Maximum number of pixels allowed. If the image size exceeds this threshold, an error is raised.
        to_rgb: If True, converts the image to RGB mode.

    Returns:
        Image object.

    Raises:
        ImageTooLargeError: If the image size exceeds the pixel threshold.
        TypeError: If the document type is unsupported.
    """

    # Try PyMuPDF
    try:
        from data_utils.pdf_pymupdf import Document, pdf_to_images

        if isinstance(document, Document):
            image: Image.Image = pdf_to_images(pdf=document, page_id=page_id, dpi=dpi, pixel_threshold=pixel_threshold)
            if to_rgb:
                image = image_to_rgb(image)
            return image
    except ImportError:
        pass

    # PIL Image
    if isinstance(document, Image.Image):
        image: Image.Image = document
        if pixel_threshold and is_image_pixels_too_large(image, pixel_threshold=pixel_threshold):
            raise ImageTooLargeError(f"Image too large: {image.size}")
        if to_rgb:
            image = image_to_rgb(image)
        return image

    raise TypeError(f"Unsupported page type: {type(document)}.")


def is_image_pixels_too_large(image: Image.Image, pixel_threshold: int) -> bool:
    """Checks if the size (in pixels) of the PIL Image is too large.

    Args:
        image: PIL Image object.
        pixel_threshold: Maximum number of pixels allowed.

    Returns:
        True if the size is too large, False otherwise.
    """

    width_px, height_px = image.size
    total_pixels = round(width_px * height_px)

    if total_pixels > pixel_threshold:
        logger.warning(
            "Image size exceeds threshold.",
            pixel_threshold=pixel_threshold,
            total_pixels=total_pixels,
            image_size=image.size,
        )
        return True

    return False


def image_to_bytes(img: Image.Image) -> bytes:
    """Encodes image as bytes.

    This is equivalent to doing:
    ```
    with open(img_path, "rb") as f:
        encoded_img = f.read()
    ```

    Args:
        img: pillow.Image object

    Returns:
        image as bytes
    """
    buffered = BytesIO()
    img.save(buffered, img.format or "PNG")
    return buffered.getvalue()


def tiff_to_images(
    tiff_path: Path | str, page_id: int | None = None, pixel_threshold: int = 100_000_000
) -> list[Image.Image] | Image.Image:
    """Converts TIFF file to list of Image objects or a single Image if page is specified.

    Args:
        tiff_path: Path to TIFF file.
        page_id: Optional, 0-based page index. If specified returns a single Image for that page.
        pixel_threshold: Maximum number of pixels allowed. If the image size exceeds this threshold, an error is raised.

    Returns:
        List of PIL Image objects or a single image.
    """
    with open_image(tiff_path, pixel_threshold) as img:
        n_frames = getattr(img, "n_frames", 1)

        # Selected page.
        if page_id is not None:
            if page_id > n_frames:
                raise ValueError(f"Page {page_id} does not exist in TIFF with {n_frames} pages")
            img.seek(page_id)
            frame = image_to_rgb(img)
            return frame

        # Single page TIFFs.
        if n_frames == 1:
            img.seek(0)
            frame = image_to_rgb(img)
            return frame

        # Multi-page TIFFs.
        images = []
        for i in range(n_frames):
            img.seek(i)
            frame = image_to_rgb(img)
            images.append(frame)
        return images


def image_to_rgb(image: Image.Image, no_transparency: bool = True, keep_grayscale: bool = False) -> Image.Image:
    """Converts image to RGB mode if not already and handles transparency.

    This is useful as models usually expect RGB images without transparency.

    Args:
        image: PIL Image object to convert.
        no_transparency: If True, converts images with transparency to RGB.
                        If False, preserves transparency (converts to RGBA when needed).
        keep_grayscale: If True, preserves grayscale mode for L and 1-bit images.
                       If False, converts them to RGB.

    Returns:
        PIL Image object in the appropriate mode.
    """
    # Already RGB - return as-is
    if image.mode == "RGB":
        return image

    # RGBA - handle based on transparency preference
    if image.mode == "RGBA":
        return image.convert("RGB") if no_transparency else image

    # Palette with transparency - convert based on preference
    if image.mode == "P" and "transparency" in image.info:
        return image.convert("RGB") if no_transparency else image.convert("RGBA")

    # Palette without transparency - always convert to RGB
    if image.mode == "P":
        return image.convert("RGB")

    # Grayscale and 1-bit images - handle based on keep_grayscale preference
    if image.mode in ("L", "1"):
        return image if keep_grayscale else image.convert("RGB")

    # All other modes - convert to RGB
    return image.convert("RGB")


def is_image_bytes(data: str | bytes | BytesIO) -> bool:
    """Checks if the given bytes look like a common image format (only first 8 bytes are checked)."""
    if isinstance(data, BytesIO):
        pos = data.tell() if hasattr(data, "tell") else 0
        data.seek(0)
        header = data.read(8)
        data.seek(pos)
    elif isinstance(data, str):
        header = data.encode("utf-8")[:8]
    elif isinstance(data, bytes | bytearray):
        header = data[:8]
    else:
        return False

    signatures = [
        (b"\x89PNG", "png"),
        (b"II*\x00", "tiff"),
        (b"MM\x00*", "tiff"),
        (b"\xff\xd8", "jpeg"),
    ]
    for sig, _ in signatures:
        if header.startswith(sig):
            return True
    return False
