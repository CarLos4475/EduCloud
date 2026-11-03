from datetime import UTC, date, datetime, time
from typing import Any, Literal

from pydantic import Field, create_model, field_validator

from campus.domain.contracts import ContractModel


class ProfileInput(ContractModel):
    display_name: str = Field(min_length=1, max_length=100)
    career: str = Field(default="", max_length=120)
    timezone: str = "America/Mexico_City"
    tutorial_step: int = Field(default=0, ge=0, le=5)


class ProfileUpdate(ProfileInput):
    expected_revision: int = Field(ge=0)


class PeriodInput(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None


class SubjectInput(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    period_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    illustration_id: str = Field(default="grid", max_length=80)
    accent_id: Literal["gold", "navy", "sand"] = "gold"
    archived: bool = False


class TopicInput(ContractModel):
    subject_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    title: str = Field(min_length=1, max_length=150)
    order: int = Field(default=0, ge=0)
    prerequisite_ids: list[str] = Field(default_factory=list, max_length=50)


class AgendaInput(ContractModel):
    title: str = Field(min_length=1, max_length=160)
    subject_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    kind: Literal["task", "exam", "study", "other"] = "task"
    due_date: date | None = None
    due_at: datetime | None = None
    status: Literal["pending", "done"] = "pending"
    notes: str = Field(default="", max_length=2000)

    @field_validator("due_at")
    @classmethod
    def aware(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Incluye la zona horaria.")
        return value.astimezone(UTC) if value is not None else None


class ScheduleInput(ContractModel):
    subject_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    weekday: int = Field(ge=0, le=6)
    local_start: time
    local_end: time
    timezone: str = "America/Mexico_City"
    notes: str = Field(default="", max_length=300)
    excluded_dates: list[date] = Field(default_factory=list, max_length=60)


MODELS: dict[str, type[ContractModel]] = {
    "periods": PeriodInput,
    "subjects": SubjectInput,
    "topics": TopicInput,
    "agenda": AgendaInput,
    "schedule": ScheduleInput,
}


def update_schema(model: type[ContractModel]) -> type[ContractModel]:
    fields: dict[str, Any] = {"expected_revision": (int, Field(ge=1))}
    fields.update(
        {
            name: (
                (field.annotation or Any) | None,
                Field(default=None, alias=field.alias),
            )
            for name, field in model.model_fields.items()
        }
    )
    return create_model("Update" + model.__name__, __base__=ContractModel, **fields)


UPDATE_MODELS = {name: update_schema(model) for name, model in MODELS.items()}

READ_MODELS = {
    name: create_model(
        model.__name__.replace("Input", "Record"),
        __base__=model,
        id=(str, ...),
        revision=(int, ...),
        created_at=(datetime, ...),
        updated_at=(datetime, ...),
    )
    for name, model in MODELS.items()
}
