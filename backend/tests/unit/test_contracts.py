import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from campus.domain.contracts import (
    ApiError,
    Page,
    PeriodInput,
    SourcePolicy,
    SourceRef,
    SubjectInput,
)
from pydantic import ValidationError


def test_shared_fixtures_roundtrip_using_public_field_names() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/fixtures/contracts/valid-contracts.json"
    )
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    assert (
        SourceRef.model_validate(fixtures["sourceRef"]).model_dump(by_alias=True)
        == fixtures["sourceRef"]
    )
    assert (
        ApiError.model_validate(fixtures["apiError"]).model_dump(by_alias=True)
        == fixtures["apiError"]
    )


def test_subject_input_rejects_server_owned_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SubjectInput(
            name="Métodos numéricos II",
            illustration_id="grid",
            owner_id="attacker-controlled-owner",
        )


def test_period_input_requires_iso_date_not_ambiguous_date() -> None:
    period = PeriodInput(name="2026-1", start_date="2026-01-19")

    assert period.start_date == date(2026, 1, 19)
    with pytest.raises(ValidationError):
        PeriodInput(name="2026-1", start_date="19/01/2026")


def test_shared_contracts_preserve_field_names_and_utc_timestamp() -> None:
    source = SourceRef(
        material_id="material-1",
        extraction_version="v2",
        block_id="page-3-block-1",
        locator="page:3",
    )
    policy = SourcePolicy(
        mode="selected_material",
        material_ids=["material-1"],
        allow_general_for_turn=False,
    )
    error = ApiError(
        code="validation_error",
        message="La entrada no es válida.",
        request_id="request-1",
    )
    page = Page(items=[source], next_cursor=None)

    assert source.model_dump(by_alias=True) == {
        "materialId": "material-1",
        "extractionVersion": "v2",
        "blockId": "page-3-block-1",
        "locator": "page:3",
        "quote": None,
    }
    assert policy.model_dump(by_alias=True)["allowGeneralForTurn"] is False
    assert error.model_dump(by_alias=True)["requestId"] == "request-1"
    assert page.model_dump(by_alias=True)["nextCursor"] is None


def test_contract_timestamp_requires_timezone() -> None:
    from campus.domain.contracts import ContractEvent

    event = ContractEvent(
        event_id="event-1",
        schema_version=1,
        owner_id="user-1",
        type="subject.created",
        entity_id="subject-1",
        occurred_at=datetime(2026, 11, 2, 12, 30, tzinfo=UTC),
        payload={},
    )

    assert event.occurred_at.tzinfo is not None
    with pytest.raises(ValidationError):
        ContractEvent(
            event_id="event-2",
            schema_version=1,
            owner_id="user-1",
            type="subject.created",
            entity_id="subject-1",
            occurred_at="2026-11-02T12:30:00",
            payload={},
        )
