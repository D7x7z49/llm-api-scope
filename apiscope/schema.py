# apiscope/schema.py

from collections.abc import Mapping
from typing import Annotated, Any, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, create_model, model_validator
from pydantic_core import MISSING

# ==============================================================================
# runtime configuration schema
# ==============================================================================


DocumentType = Literal["filesystem", "repo", "openapi", "rfc", "llmstxt"]


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        strict=True,
        validate_assignment=True,
    )


class RuntimeSource(StrictSchemaModel):
    doc_type: DocumentType
    doc_src: str = Field(min_length=1)
    doc_ttl: PositiveInt | None = None


class PublicSetting(StrictSchemaModel):
    doc_ttl: PositiveInt = 7


class LocalSetting(StrictSchemaModel):
    proxy: str | None = None


class RuntimeSetting(StrictSchemaModel):
    public: PublicSetting
    local: LocalSetting


class RuntimeConfig(StrictSchemaModel):
    source: dict[str, RuntimeSource]
    setting: RuntimeSetting


# Derive a shallow partial model and keep nested value models unchanged.
def derive_partial_model(
    name: str,
    base_model: type[BaseModel],
    *,
    field_overrides: Mapping[str, Any] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> type[BaseModel]:
    overrides = {} if field_overrides is None else dict(field_overrides)
    fields: dict[str, Any] = {}

    for field_name, field_info in base_model.model_fields.items():
        field_data = field_info.asdict()
        annotation = overrides.get(field_name, field_data["annotation"])
        fields[field_name] = (
            Annotated[
                annotation,
                *field_data["metadata"],
                Field(**field_data["attributes"]),
            ],
            MISSING,
        )

    if extra_fields is not None:
        fields.update(extra_fields)

    return cast(
        type[BaseModel],
        create_model(
            name,
            __base__=base_model,
            __module__=__name__,
            **fields,
        ),
    )


_SCHEMA_REF_FIELD: tuple[Any, Any] = (
    Annotated[
        str,
        Field(
            min_length=1,
            serialization_alias="$schema",
            validation_alias="$schema",
        ),
    ],
    MISSING,
)


GlobalConfigFile = derive_partial_model(
    "GlobalConfigFile",
    RuntimeConfig,
    extra_fields={"schema_ref": _SCHEMA_REF_FIELD},
)

ProjectConfigFile = derive_partial_model(
    "ProjectConfigFile",
    RuntimeConfig,
    field_overrides={"setting": PublicSetting},
    extra_fields={"schema_ref": _SCHEMA_REF_FIELD},
)


class _LocalConfigFileBase(RuntimeConfig):
    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if "source" in self.model_fields_set and self.source:
            raise ValueError("local configuration cannot define sources")
        return self


LocalConfigFile = derive_partial_model(
    "LocalConfigFile",
    _LocalConfigFileBase,
    field_overrides={"setting": LocalSetting},
    extra_fields={"schema_ref": _SCHEMA_REF_FIELD},
)
