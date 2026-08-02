---
type: Python Package
title: Data Models Package
description: The `data-models` package defines shared Pydantic data models and API contracts for the monorepo.
tags: [data, models, pydantic, api]
---
# Data Models Package

The `data-models` package (`/packages/data-models`) is responsible for defining common data structures and API contracts used across different services within the monorepo. It leverages [Pydantic](https://docs.pydantic.dev/latest/) for data validation and serialization.

## Purpose

This package ensures consistency in data representation throughout the system, particularly for:

*   **API Request/Response Schemas**: Standardizing the format of data exchanged between services.
*   **Data Validation**: Automatically validating incoming and outgoing data against defined schemas.
*   **Type Hinting**: Providing clear and consistent type hints for data structures.

## Public API Surface

The primary public API surface of this package is its Pydantic models, defined in `/packages/data-models/src/data_models/models.py`.

### `BaseSchema`

The `BaseSchema` class serves as a foundational Pydantic model for other schemas. It includes configuration for automatic PascalCase alias generation, ensuring that model fields can be represented in PascalCase when serialized or validated via alias.

**Source**: `/packages/data-models/src/data_models/models.py`

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=to_pascal,
            validation_alias=to_pascal,
        ),
        validate_by_alias=True,
        validate_by_name=True,
    )
```
