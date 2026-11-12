"""Contracts for generated study resources and their immutable versions."""

from typing import Any, Literal

from pydantic import ConfigDict, Field

from campus.domain.contracts import ContractModel, SourceRef

ResourceKind = Literal["summary", "concepts", "flashcards", "quiz", "interactive"]

KIND_LABELS = {
    "summary": "Resumen",
    "concepts": "Conceptos clave",
    "flashcards": "Tarjetas de estudio",
    "quiz": "Cuestionario",
    "interactive": "Experiencia interactiva",
}


class ResourceInput(ContractModel):
    subject_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    kind: ResourceKind
    title: str = Field(default="", max_length=120)
    instruction: str = Field(default="", max_length=1000)
    material_ids: list[str] = Field(default_factory=list, max_length=10)
    allow_general: bool = False


class ResourceChange(ContractModel):
    instruction: str = Field(min_length=1, max_length=1000)
    allow_general: bool = False


class ResourceUpdate(ContractModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    archived: bool | None = None


class Lenient(ContractModel):
    """Model output is untrusted: ignore unknown keys, keep strict value limits."""

    model_config = ConfigDict(extra="ignore")


class GeneratedCitation(Lenient):
    source_id: str = Field(pattern=r"^S[1-8]$")
    quote: str = Field(min_length=1, max_length=1200)


class Section(Lenient):
    heading: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=4000)


class SummaryContent(Lenient):
    overview: str = Field(min_length=1, max_length=2000)
    sections: list[Section] = Field(min_length=1, max_length=12)
    key_points: list[str] = Field(default_factory=list, max_length=12)


class Concept(Lenient):
    term: str = Field(min_length=1, max_length=120)
    definition: str = Field(min_length=1, max_length=1500)
    example: str | None = Field(default=None, max_length=1500)


class ConceptsContent(Lenient):
    concepts: list[Concept] = Field(min_length=1, max_length=25)


class Card(Lenient):
    front: str = Field(min_length=1, max_length=600)
    back: str = Field(min_length=1, max_length=1200)


class FlashcardsContent(Lenient):
    cards: list[Card] = Field(min_length=1, max_length=30)


class Question(Lenient):
    prompt: str = Field(min_length=1, max_length=800)
    options: list[str] = Field(min_length=2, max_length=5)
    correct_index: int = Field(ge=0, le=4)
    explanation: str = Field(min_length=1, max_length=1200)


class QuizContent(Lenient):
    questions: list[Question] = Field(min_length=1, max_length=15)


class VersionRead(Lenient):
    id: str
    resource_id: str
    number: int
    instruction: str
    status: str
    stage: str
    error: str | None = None
    usage_unknown: bool = False
    job_id: str
    content: dict[str, Any] | None = None
    citations: list[SourceRef] = Field(default_factory=list)
    text_alternative: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    sources_changed: bool = False
    created_at: str


class ResourceRead(Lenient):
    id: str
    revision: int
    subject_id: str
    kind: ResourceKind
    title: str
    material_ids: list[str]
    archived: bool = False
    created_at: str
    version_count: int = 0
    latest_status: str | None = None
    current_version_id: str | None = None
    latest_version_id: str | None = None


class ResourceDetail(ResourceRead):
    versions: list[VersionRead]
