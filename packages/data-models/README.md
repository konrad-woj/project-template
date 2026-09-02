# data-models

Cross-package Pydantic models and API contracts. Every request/response schema
shared between packages lives here so producers and consumers cannot drift.

## `BaseSchema`

`BaseSchema` (`src/data_models/models.py`) is the base class for all API
contracts in this repo. It accepts and emits `PascalCase` on the wire while
keeping `snake_case` attribute names in Python, and it validates by field name
too, so constructing a model in Python needs no aliases.

```python
from data_models import BaseSchema


class OrderRequest(BaseSchema):
    order_id: str
    item_count: int


OrderRequest.model_validate({"OrderId": "A-1", "ItemCount": 2})
OrderRequest(order_id="A-1", item_count=2).model_dump(by_alias=True)
# {"OrderId": "A-1", "ItemCount": 2}
```

Use `BaseSchema` instead of Pydantic's `BaseModel` for anything that crosses a
package or service boundary; plain `BaseModel` is fine for package-internal
structures.

## Development

```bash
uv sync --all-groups
uv run task test
uv run task precommits
```
