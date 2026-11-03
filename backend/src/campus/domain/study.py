from typing import Any, Literal

from pydantic import ConfigDict, Field

from campus.domain.contracts import ContractModel, SourceRef

PERSONALITIES = [
    {
        "id": "patient",
        "name": "Paso a paso",
        "description": "Explicaciones pacientes con ejemplos.",
    },
    {
        "id": "socratic",
        "name": "Preguntemos",
        "description": "Preguntas que te ayudan a construir una idea.",
    },
    {
        "id": "direct",
        "name": "Al grano",
        "description": "Respuestas claras y concisas.",
    },
]


class UploadInput(ContractModel):
    name: str = Field(min_length=1, max_length=180)
    media_type: str = Field(max_length=120)
    size: int = Field(gt=0, le=20 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class UploadComplete(ContractModel):
    generation: str = Field(min_length=1, max_length=128)


class TranscriptEdit(ContractModel):
    block_id: str = Field(pattern=r"^block-[1-9][0-9]{0,2}$")
    text: str = Field(min_length=1, max_length=30000)


class TranscriptInput(ContractModel):
    expected_revision: int = Field(ge=1)
    edits: list[TranscriptEdit] = Field(max_length=50)
    topic_ids: list[str] = Field(default_factory=list, max_length=30)


class ConversationInput(ContractModel):
    subject_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    title: str = Field(default="Nueva conversación", min_length=1, max_length=120)
    personality_id: Literal["patient", "socratic", "direct"] = "patient"
    assistance_mode: Literal["explain", "hints", "solution", "practice"] = "explain"
    material_ids: list[str] = Field(default_factory=list, max_length=10)
    source_mode: Literal["selected_material", "general"] = "selected_material"
    preferences: str = Field(default="", max_length=500)


class ConversationUpdate(ConversationInput):
    expected_revision: int = Field(ge=1)


class TurnInput(ContractModel):
    question: str = Field(min_length=1, max_length=2000)
    allow_general_for_turn: bool = False


class AnswerCitation(ContractModel):
    source_id: str = Field(pattern=r"^S[1-8]$")
    quote: str = Field(min_length=1, max_length=1200)


class TutorAnswer(ContractModel):
    answer: str = Field(min_length=1, max_length=12000)
    citations: list[AnswerCitation] = Field(default_factory=list, max_length=8)
    insufficient_sources: bool = False


class StudyRead(ContractModel):
    model_config = ConfigDict(extra="ignore")


class JobRead(StudyRead):
    id: str
    revision: int
    kind: str
    entity_id: str
    status: Literal[
        "queued",
        "running",
        "needs_review",
        "succeeded",
        "failed",
        "cancel_requested",
        "canceled",
    ]
    stage: str
    progress: int
    attempts: int
    result: dict[str, Any] | None = None
    error: str | None = None
    usage_unknown: bool = False
    usage: dict[str, Any] | None = None
    created_at: str


class UploadTicket(StudyRead):
    upload_id: str
    material_id: str
    signed_url: str
    required_headers: dict[str, str]
    expires_at: str


class ObjectReceipt(StudyRead):
    generation: str
    sha256: str
    size: int


class BlockRead(SourceRef):
    model_config = ConfigDict(extra="ignore")
    text: str
    status: str
    warning: str | None = None


class MaterialRead(StudyRead):
    id: str
    revision: int
    name: str
    media_type: str
    subject_id: str
    size: int
    status: str
    sha256: str
    error: str | None = None
    created_at: str
    extraction_version: str | None = None
    job_id: str | None = None
    topic_ids: list[str] = Field(default_factory=list)
    blocks: list[BlockRead] | None = None
    suggested_topic_ids: list[str] = Field(default_factory=list)
    page_count: int = 0
    failed_pages: int = 0
    reviewed_pages: int = 0
    index_version: str | None = None
    index_job_id: str | None = None


class MaterialAccepted(StudyRead):
    material: MaterialRead
    job: JobRead


class ConversationRead(ConversationInput):
    model_config = ConfigDict(extra="ignore")
    id: str
    revision: int
    created_at: str
    active_turn_id: str | None = None


class CitationRead(SourceRef):
    source_id: str


class TurnRead(StudyRead):
    id: str
    revision: int
    created_at: str
    conversation_id: str
    question: str
    text: str
    citations: list[CitationRead]
    needs_consent: bool
    sources_changed: bool
    partial_sources: bool = False
    source_mode: str
    job_id: str
    status: str
    stage: str
    error: str | None = None
    usage_unknown: bool
    sequence: int
    usage: dict[str, Any] | None = None
