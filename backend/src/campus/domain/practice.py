"""Practice evidence, progress and passport contracts. Scores are always set by the server."""

from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator

from campus.domain.contracts import ContractModel


class AttemptInput(ContractModel):
    answers: list[int | None] = Field(min_length=1, max_length=15)


class ReviewInput(ContractModel):
    cards: dict[str, Literal["known", "again"]] = Field(max_length=30)

    @field_validator("cards")
    @classmethod
    def keys_are_card_numbers(cls, cards):
        if any(not key.isdigit() or int(key) > 29 for key in cards):
            raise ValueError("Cada tarjeta se identifica con su número.")
        return cards


class StateInput(ContractModel):
    state: dict[str, Any]
    expected_revision: int | None = Field(default=None, ge=1)


class Read(ContractModel):
    model_config = ConfigDict(extra="ignore")


class QuestionResult(Read):
    picked: int | None = None
    correct_index: int
    correct: bool


class AttemptRead(Read):
    id: str
    version_id: str
    score: int
    total: int
    results: list[QuestionResult]
    created_at: str


class ReviewRead(Read):
    version_id: str
    revision: int = 0
    cards: dict[str, str] = Field(default_factory=dict)


class StateRead(Read):
    version_id: str
    revision: int = 0
    state: dict[str, Any] = Field(default_factory=dict)


class Recommendation(Read):
    text: str
    resource_id: str | None = None


class ProgressRead(Read):
    subject_id: str
    materials_ready: int
    resources_ready: int
    quiz_attempts: int
    average_score: int | None = None
    last_score: int | None = None
    cards_known: int
    cards_to_review: int
    recommendations: list[Recommendation]


class StampRead(Read):
    id: str
    title: str
    description: str
    earned: bool
    earned_at: str | None = None


class PassportRead(Read):
    earned: int
    total: int
    stamps: list[StampRead]
