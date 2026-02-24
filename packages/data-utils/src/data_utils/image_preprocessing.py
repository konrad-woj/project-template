"""Image preprocessing."""

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import structlog
from PIL import Image

logger = structlog.get_logger()


def image_to_array(image: Image.Image | np.ndarray) -> np.ndarray:
    """Converts PIL to OpenCV format if needed."""

    if isinstance(image, Image.Image):
        match image.mode:
            case "1":
                # if it is one bit representation, we convert it to grayscale
                return np.array(image.convert("L"))
            case "L":
                # if it is grayscale, we leave it as is
                return np.array(image)
        # in any other case convert to RGB and then BGR for cv2 processing
        return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)

    return image


def array_to_image(arr: np.ndarray) -> Image.Image:
    """Converts OpenCV array to PIL Image."""

    if len(arr.shape) == 3:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)

    return Image.fromarray(arr)


def to_grayscale(arr: np.ndarray) -> np.ndarray:
    """Converts to grayscale if not already."""

    if len(arr.shape) == 3:
        return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

    return arr


def denoise(arr: np.ndarray) -> np.ndarray:
    """Apply noise reduction while preserving edges."""

    return cv2.fastNlMeansDenoising(arr, None, h=10, templateWindowSize=7, searchWindowSize=21)


def enhance_contrast(arr: np.ndarray) -> np.ndarray:
    """Enhances contrast using CLAHE."""

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(arr)


def sharpen_text(arr: np.ndarray) -> np.ndarray:
    """Sharpens text edges."""

    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(arr, -1, kernel)


def set_threshold(arr: np.ndarray) -> np.ndarray:
    """Converts image array to binary using threshold.

    Use after denoising and contrast enhancement on grayscale images.
    """

    _, arr_bin = cv2.threshold(arr, 128, 255, cv2.THRESH_BINARY)
    return arr_bin


def binarize(arr: np.ndarray) -> np.ndarray:
    """Converts grayscale to binary using adaptive thresholding.

    Use after denoising and contrast enhancement on grayscale images.
    """

    return cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)


def evaluate_multiple_orientations(
    arr: np.ndarray,
    orientations_to_test: list[int],
    halve_size_if_exceeds: int = 1000,
) -> int:
    """Returns the best orientation angle for horizontalization."""
    # Adaptive downscaling
    max_dim = max(arr.shape)
    if max_dim > 2 * halve_size_if_exceeds:
        scale = 0.25
    elif max_dim > halve_size_if_exceeds:
        scale = 0.5
    else:
        scale = 1.0

    if scale < 1.0:
        small_arr = cv2.resize(arr, (0, 0), fx=scale, fy=scale)
    else:
        small_arr = arr

    scores = []
    for angle in orientations_to_test:
        if angle == 0:
            rotated = small_arr
        else:
            rotated = rotate(small_arr, -angle, interpolation=cv2.INTER_LINEAR)
        h_projection = np.sum(rotated, axis=1)
        scores.append(np.var(h_projection))

    best_angle = orientations_to_test[np.argmax(scores)]
    return best_angle


def horizontalize(
    arr: np.ndarray,
    orientations_to_test: Sequence[int] = (0, 90, -1, 1, -2, 2, -3, 3),
) -> tuple[np.ndarray, int]:
    """Detects vertical text orientation and rotates the image array to make it horizontal.

    Args:
        arr: Input image array.
        orientations_to_test: List of angles to test for derotation. Should include 0.

    Returns:
        Tuple of (rotated image array, angle applied to original image).
    """
    angle_mapping = {}
    normalized_angles = []

    # Normalize angles to [0, 360) and map back to original angles.
    for angle in orientations_to_test:
        normalized = angle % 360
        normalized_angles.append(normalized)
        if normalized not in angle_mapping:
            angle_mapping[normalized] = angle

    # Remove opposite angles to avoid redundant checks.
    filtered = []
    angles_set = set(normalized_angles)
    for angle in angles_set:
        counterpart = (angle + 180) % 360
        if counterpart not in angles_set or angle < counterpart:
            filtered.append(angle)

    # Evaluate best angle.
    orientations_to_test = list(filtered)
    best_angle = evaluate_multiple_orientations(arr, orientations_to_test)
    if best_angle == 0:
        return arr, 0

    correction_angle = -best_angle
    original_angle = angle_mapping[best_angle]
    rotated = rotate(arr, correction_angle, interpolation=cv2.INTER_CUBIC)
    return rotated, original_angle


def rotate(arr: np.ndarray, angle: float, border_mode=cv2.BORDER_WRAP, interpolation=cv2.INTER_CUBIC) -> np.ndarray:
    """Rotates image array by the specified angle.

    Args:
        arr: Input image array.
        angle: Rotation angle in degrees.
        border_mode: Border handling mode for areas outside the original image.
        interpolation: Interpolation mode for areas outside the original image.

    Returns:
        Rotated image array.
    """
    height, width = arr.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    abs_cos = abs(np.cos(np.radians(angle)))
    abs_sin = abs(np.sin(np.radians(angle)))

    new_width = int(height * abs_sin + width * abs_cos)
    new_height = int(height * abs_cos + width * abs_sin)

    rotation_matrix[0, 2] += (new_width / 2) - center[0]
    rotation_matrix[1, 2] += (new_height / 2) - center[1]

    return cv2.warpAffine(
        arr, M=rotation_matrix, dsize=(new_width, new_height), flags=interpolation, borderMode=border_mode
    )


def resize_array_to_dpi(arr: np.ndarray, target_dpi: int = 300, source_dpi: int = 72) -> np.ndarray:
    """Changes the DPI of an image array.

    Args:
        arr: Input image array
        target_dpi: Desired DPI value
        source_dpi: Source DPI value

    Returns:
        Image array with updated DPI
    """
    height, width = arr.shape[:2]
    scale = target_dpi / source_dpi
    new_size = (int(width * scale), int(height * scale))
    return cv2.resize(arr, new_size, interpolation=cv2.INTER_CUBIC)


def save_image(arr: np.ndarray, save_dir: str = "debug_dir") -> np.ndarray:
    """Saves the image to a file. Can be used as pipeline step for debugging.

    Args:
        arr: Image array
        save_dir: Subdirectory to save to

    Returns:
        Unchanged image array
    """
    now = datetime.now()
    dt = now.strftime("%Y_%m_%d")
    ts = now.strftime("%H%M%S")

    root_dir = Path(__file__).parent
    _save_dir = root_dir / save_dir / dt
    _save_dir.mkdir(parents=True, exist_ok=True)
    save_path = _save_dir / f"{ts}.png"

    cv2.imwrite(str(save_path), arr)

    return arr


# Registry of named preprocessing steps for use in run_pipeline.
_PIPELINE_REGISTRY: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "to_grayscale": to_grayscale,
    "denoise": denoise,
    "enhance_contrast": enhance_contrast,
    "sharpen_text": sharpen_text,
    "set_threshold": set_threshold,
    "binarize": binarize,
    "save_image": save_image,
}


def run_pipeline(arr: np.ndarray, pipeline: Sequence[str] = ("to_grayscale", "denoise")) -> np.ndarray:
    """Preprocesses an image for OCR using named pipeline steps.

    Args:
        arr: Input image in cv2 format.
        pipeline: Ordered step names to apply. Each name must be a key in _PIPELINE_REGISTRY.

    Returns:
        Processed image array.
    """
    if not pipeline:
        return arr

    arr = arr.copy()
    for step in pipeline:
        step_fn = _PIPELINE_REGISTRY.get(step)
        if step_fn is None:
            logger.warning(
                "Unknown preprocessing step — skipping.",
                step=step,
                available=list(_PIPELINE_REGISTRY),
            )
            continue
        arr = step_fn(arr)

    return arr
