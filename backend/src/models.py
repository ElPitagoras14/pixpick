from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for every model that crosses the API boundary (api-conventions
    spec). Fields are declared in the schema's own snake_case -- the same
    convention as the rest of the backend -- and serialize to the
    client-facing camelCase convention; the internal naming never leaks
    out through a response.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
