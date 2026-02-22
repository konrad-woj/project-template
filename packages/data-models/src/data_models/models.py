from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class BaseSchema(BaseModel):
    model_config = ConfigDict(  # type: ignore[reportCallIssue]
        alias_generator=AliasGenerator(
            serialization_alias=to_pascal,
            validation_alias=to_pascal,
        ),
        validate_by_alias=True,
        validate_by_name=True,
    )
