"""Versioned, transport-safe contracts shared by current and future modules."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class ContractModel(BaseModel):
    """Forbid over-posting and serialize the public API in camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class ApiError(ContractModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=500)
    request_id: str = Field(min_length=1, max_length=120)
    details: dict[str, Any] | None = None


class Page(ContractModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(default=None, max_length=512)


class SourceRef(ContractModel):
    material_id: str = Field(min_length=1, max_length=128)
    extraction_version: str = Field(min_length=1, max_length=64)
    block_id: str = Field(min_length=1, max_length=128)
    locator: str = Field(min_length=1, max_length=256)
    quote: str | None = Field(default=None, max_length=500)


class SourcePolicy(ContractModel):
    mode: Literal["selected_material", "general"]
    material_ids: list[str] = Field(default_factory=list, max_length=50)
    allow_general_for_turn: bool = False

    @field_validator("material_ids")
    @classmethod
    def material_ids_must_be_nonempty(cls, material_ids: list[str]) -> list[str]:
        if any(not material_id.strip() for material_id in material_ids):
            raise ValueError("material_ids cannot contain empty IDs")
        return material_ids


class Actor(ContractModel):
    uid: str = Field(min_length=1, max_length=128)
    pilot_enabled: bool


class PeriodInput(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def dates_must_use_iso_calendar_format(cls, value: object) -> object:
        if value is not None and not isinstance(value, (str, date)):
            raise ValueError("dates must use YYYY-MM-DD")
        if isinstance(value, datetime) or isinstance(value, str) and len(value) != 10:
            raise ValueError("dates must use YYYY-MM-DD")
        return value


class SubjectInput(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    period_id: str | None = Field(default=None, max_length=128)
    illustration_id: str = Field(min_length=1, max_length=80)
    accent_id: str | None = Field(default=None, max_length=80)


class JobSpec(ContractModel):
    kind: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=128)
    input_version: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any]


class ContractEvent(ContractModel):
    event_id: str = Field(min_length=1, max_length=128)
    schema_version: Literal[1]
    owner_id: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=120)
    entity_id: str = Field(min_length=1, max_length=128)
    occurred_at: datetime
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class InteractivePackageV1(ContractModel):
    schema_version: Literal[1]
    title: str = Field(min_length=1, max_length=160)
    learning_objective: str = Field(min_length=1, max_length=600)
    instructions: str = Field(min_length=1, max_length=3000)
    html: str = Field(max_length=100_000)
    css: str = Field(max_length=100_000)
    javascript: str = Field(max_length=200_000)
    initial_state: dict[str, Any]
    text_alternative: str = Field(min_length=1, max_length=10_000)
    source_refs: list[SourceRef] = Field(default_factory=list)
    requested_capabilities: list[
        Literal["controls", "math", "plot", "canvas2d", "state"]
    ]


PUBLIC_CONTRACTS = (
    ApiError,
    SourceRef,
    SourcePolicy,
    Actor,
    PeriodInput,
    SubjectInput,
    JobSpec,
    ContractEvent,
    InteractivePackageV1,
)
