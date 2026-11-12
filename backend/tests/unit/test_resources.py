import pytest
from campus.adapters.testing import TestStudyProvider
from campus.services.academic import DomainError
from campus.services.resources import ResourceService
from campus.services.retrieval import RetrievalService
from test_materials import setup_study, upload_note


def build(tmp_path, provider=None):
    records, subject, jobs, _, materials, uploads = setup_study(tmp_path)
    ticket, upload = upload_note(uploads, subject)
    materials.ingest(jobs.claim("alice", upload["job"]["id"]))
    service = ResourceService(
        records, jobs, RetrievalService(materials), provider or TestStudyProvider()
    )
    return service, jobs, materials, subject, ticket["materialId"]


def request(subject, material, kind="summary", **extra):
    return {
        "subjectId": subject["id"],
        "kind": kind,
        "instruction": "resistencia y corriente",
        "materialIds": [material],
        **extra,
    }


def run_latest(service, jobs, detail):
    job_id = detail["versions"][-1]["jobId"]
    service.run(jobs.claim("alice", job_id))
    return service.detail("alice", detail["id"])


@pytest.mark.parametrize(
    "kind", ["summary", "concepts", "flashcards", "quiz", "interactive"]
)
def test_every_kind_is_generated_with_verified_citations(tmp_path, kind):
    service, jobs, _, subject, material = build(tmp_path)
    detail = service.create("alice", request(subject, material, kind), f"key-{kind}")
    assert detail["versions"][0]["status"] == "queued"
    assert detail["versions"][0]["content"] is None
    detail = run_latest(service, jobs, detail)
    version = detail["versions"][0]
    assert version["status"] == "succeeded" and version["content"]
    assert version["citations"][0]["materialId"] == material
    assert detail["currentVersionId"] == version["id"]
    if kind == "interactive":
        assert version["textAlternative"]
        assert version["content"]["sourceRefs"][0]["materialId"] == material


def test_create_is_idempotent_and_rejects_other_payload(tmp_path):
    service, _, _, subject, material = build(tmp_path)
    first = service.create("alice", request(subject, material), "same")
    again = service.create("alice", request(subject, material), "same")
    assert again["id"] == first["id"] and len(service.list("alice", subject["id"])) == 1
    with pytest.raises(DomainError) as conflict:
        service.create("alice", request(subject, material, "quiz"), "same")
    assert conflict.value.status == 409


def test_changes_create_immutable_versions_and_keep_the_last_valid_one(tmp_path):
    service, jobs, _, subject, material = build(tmp_path)
    detail = run_latest(
        service, jobs, service.create("alice", request(subject, material), "a")
    )
    first = detail["versions"][0]
    with pytest.raises(DomainError) as busy:
        service.change("alice", detail["id"], {"instruction": "más corto"}, "b")
        service.change("alice", detail["id"], {"instruction": "otro"}, "c")
    assert busy.value.status == 409
    detail = service.detail("alice", detail["id"])
    assert len(detail["versions"]) == 2 and detail["latestStatus"] == "queued"
    assert detail["currentVersionId"] == first["id"]
    jobs.cancel("alice", detail["versions"][1]["jobId"])
    detail = service.detail("alice", detail["id"])
    assert detail["versions"][0]["content"] == first["content"]
    assert detail["currentVersionId"] == first["id"]
    assert detail["versions"][1]["status"] == "canceled"


class Invalid:
    model = "invalid"

    def __init__(self, raw):
        self.raw, self.calls = raw, 0

    def structured_answer(self, messages, on_progress=None, max_tokens=0):
        self.calls += 1
        return self.raw, {"total_tokens": 10}


@pytest.mark.parametrize(
    "raw",
    [
        {  # fabricated quote
            "overview": "x",
            "sections": [{"heading": "a", "body": "b"}],
            "citations": [{"sourceId": "S1", "quote": "texto que no existe"}],
        },
        {  # unknown source
            "overview": "x",
            "sections": [{"heading": "a", "body": "b"}],
            "citations": [{"sourceId": "S7", "quote": "V = I R"}],
        },
        {  # malformed package
            "overview": "x",
            "citations": [{"sourceId": "S1", "quote": "V = I R"}],
        },
    ],
)
def test_invalid_output_gets_one_repair_then_fails_without_becoming_current(
    tmp_path, raw
):
    provider = Invalid(raw)
    service, jobs, _, subject, material = build(tmp_path, provider)
    detail = service.create("alice", request(subject, material), "bad")
    with pytest.raises(DomainError):
        service.run(jobs.claim("alice", detail["versions"][0]["jobId"]))
    assert provider.calls == 2  # initial attempt plus one bounded repair
    stored = service.records.list("alice", "resourceVersions")[0]
    assert stored["content"] is None and stored["failedDraft"]


@pytest.mark.parametrize(
    "patch",
    [
        {"javascript": "fetch('https://example.com')"},
        {"javascript": "document.body.innerHTML = 'x'"},
        {"html": "<script>alert(1)</script>"},
        {"html": '<button id="b" onclick="x()">b</button>'},
        {"html": '<p id="p">hola</p><a href="https://example.com">x</a>'},
        {"css": "@import url(https://example.com/a.css);"},
    ],
)
def test_interactive_packages_with_unsafe_code_are_rejected(tmp_path, patch):
    service, _, _, subject, material = build(tmp_path)
    detail = service.create("alice", request(subject, material, "interactive"), "i")
    raw, _ = TestStudyProvider().structured_answer(
        [
            {
                "content": '{"kind":"interactive","sources":[{"sourceId":"S1","text":"V = I R"}]}'
            }
        ]
    )
    context = next(
        j
        for j in service.records.list("alice", "jobs")
        if j["kind"] == "generate_resource"
    )["payload"]["context"]
    with pytest.raises(ValueError):
        service._validate("interactive", {**raw, **patch}, context)
    assert detail["kind"] == "interactive"


def test_sources_are_required_unless_general_knowledge_is_authorised(tmp_path):
    service, _, _, subject, _ = build(tmp_path)
    with pytest.raises(DomainError) as failure:
        service.create(
            "alice",
            {"subjectId": subject["id"], "kind": "summary", "instruction": "Ohm"},
            "none",
        )
    assert failure.value.status == 422
    allowed = service.create(
        "alice",
        {
            "subjectId": subject["id"],
            "kind": "summary",
            "instruction": "Ohm",
            "allowGeneral": True,
        },
        "general",
    )
    assert allowed["versions"][0]["status"] == "queued"


def test_resources_are_private_and_flag_changed_sources(tmp_path):
    service, jobs, materials, subject, material_id = build(tmp_path)
    detail = run_latest(
        service, jobs, service.create("alice", request(subject, material_id), "p")
    )
    with pytest.raises(DomainError):
        service.detail("bob", detail["id"])
    with pytest.raises(DomainError):
        service.update("bob", detail["id"], {"expectedRevision": 1, "title": "Robado"})
    assert detail["versions"][0]["sourcesChanged"] is False
    material = materials.get("alice", material_id)
    materials.revise(
        "alice",
        material_id,
        material["revision"],
        [{"blockId": "block-1", "text": "Ley de Ohm corregida: V = I R."}],
        [],
    )
    assert service.detail("alice", detail["id"])["versions"][0]["sourcesChanged"]


def test_rename_and_archive_require_the_current_revision(tmp_path):
    service, _, _, subject, material = build(tmp_path)
    detail = service.create("alice", request(subject, material), "r")
    renamed = service.update(
        "alice", detail["id"], {"expectedRevision": 1, "title": "Mi resumen"}
    )
    assert renamed["title"] == "Mi resumen"
    with pytest.raises(DomainError) as stale:
        service.update("alice", detail["id"], {"expectedRevision": 1, "archived": True})
    assert stale.value.status == 409
    service.update(
        "alice",
        detail["id"],
        {"expectedRevision": renamed["revision"], "archived": True},
    )
    assert service.list("alice", subject["id"]) == []
    assert len(service.list("alice", subject["id"], archived=True)) == 1


class Flaky:
    model = "flaky"

    def __init__(self, failures, usage):
        self.failures, self.usage, self.calls = failures, usage, 0
        self.good = TestStudyProvider()

    def structured_answer(self, messages, on_progress=None, max_tokens=0):
        from campus.adapters.deepseek import ProviderFailure

        self.calls += 1
        if self.calls <= self.failures:
            raise ProviderFailure("provider_interrupted", self.usage)
        first_user = next(m for m in messages if m["role"] == "user")
        return self.good.structured_answer([first_user], on_progress, max_tokens)


def test_a_cut_off_answer_is_retried_once_only_when_its_cost_is_known(tmp_path):
    provider = Flaky(1, {"total_tokens": 25})
    service, jobs, _, subject, material = build(tmp_path, provider)
    detail = run_latest(
        service, jobs, service.create("alice", request(subject, material), "retry")
    )
    assert provider.calls == 2 and detail["versions"][0]["status"] == "succeeded"
    # Unknown cost: never repeat an external call that may already have been billed.
    unknown = Flaky(1, None)
    service, jobs, _, subject, material = build(tmp_path / "other", unknown)
    created = service.create("alice", request(subject, material), "unknown")
    from campus.adapters.deepseek import ProviderFailure

    with pytest.raises(ProviderFailure):
        service.run(jobs.claim("alice", created["versions"][0]["jobId"]))
    assert unknown.calls == 1
