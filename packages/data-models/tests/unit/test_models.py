import pytest
from pydantic import ValidationError

from data_models import BaseSchema


class _Order(BaseSchema):
    order_id: str
    item_count: int


def test_accepts_pascal_case_aliases_and_field_names() -> None:
    from_alias = _Order.model_validate({"OrderId": "A-1", "ItemCount": 2})
    from_name = _Order.model_validate({"order_id": "A-1", "item_count": 2})

    assert from_alias == from_name


def test_serializes_to_pascal_case_by_alias() -> None:
    order = _Order(order_id="A-1", item_count=2)

    assert order.model_dump(by_alias=True) == {"OrderId": "A-1", "ItemCount": 2}


def test_rejects_unknown_casing() -> None:
    with pytest.raises(ValidationError):
        _Order.model_validate({"ORDERID": "A-1", "ITEMCOUNT": 2})
