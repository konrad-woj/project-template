import math

from data_models.ocr_models.textract import (
    TextractBlockModel,
    TextractBoundingBoxModel,
    TextractGeometryModel,
    TextractPointModel,
)


def make_simple_block(block_id: str, x: float, y: float, width: float, height: float) -> TextractBlockModel:
    """Helper to create a simple OCR block dictionary for testing derotation."""
    points = [
        TextractPointModel(x=x, y=y),  # top-left
        TextractPointModel(x=x + width, y=y),  # top-right
        TextractPointModel(x=x + width, y=y + height),  # bottom-right
        TextractPointModel(x=x, y=y + height),  # bottom-left
    ]
    bounding_box = TextractBoundingBoxModel(width=width, height=height, left=x, top=y)
    geometry = TextractGeometryModel(bounding_box=bounding_box, polygon=points)

    return TextractBlockModel(
        id=block_id,
        block_type="WORD",
        text=f"word_{block_id}",
        confidence=99.0,
        geometry=geometry,
        page=1,
        relationships=[],
    )


def rotate_point(point: TextractPointModel, angle: int) -> TextractPointModel:
    """Rotates a point around the page center (0.5, 0.5) by the given angle (degrees, positive is CCW)."""
    center_x, center_y = 0.5, 0.5
    tx, ty = point.x - center_x, point.y - center_y
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    rx = cos_a * tx - sin_a * ty
    ry = sin_a * tx + cos_a * ty
    return TextractPointModel(x=rx + center_x, y=ry + center_y)


def rotate_block_page(block: TextractBlockModel, angle: int) -> TextractBlockModel:
    """Rotates a block around the page center (0.5, 0.5) by the given angle (degrees, positive is CCW)."""
    if angle == 0:
        return block.model_copy(deep=True)

    new_poly = [rotate_point(p, angle) for p in block.geometry.polygon]
    new_block = block.model_copy(deep=True)
    new_block.geometry.polygon = new_poly
    return new_block
