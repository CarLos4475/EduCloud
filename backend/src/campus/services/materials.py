import gzip
import io
import json
from collections import Counter
from uuid import uuid4

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

from campus.adapters.deepseek import ProviderFailure
from campus.adapters.extraction import extract_material, tokens
from campus.services.academic import DomainError
from campus.services.jobs import changed, new_row


class MaterialService:
    # SECURITY-DEBT:
    # What is unsafe: parsing has format/page/byte bounds but no separate OS memory/CPU sandbox.
    # Why temporarily accepted: closed local pilot with synthetic validation; no public upload service deployed.
    # Before production: isolate conversion/parsing with process/container resource limits and deadlines.
    # Where the real fix belongs: worker ingest isolation and H6 container/runtime configuration.
    def __init__(self, records, objects, jobs, provider=None):
        self.records, self.objects, self.jobs, self.provider = (
            records,
            objects,
            jobs,
            provider,
        )

    def get(self, uid, key):
        row = self.records.get(uid, "materials", key)
        if not row or row["status"] in ("deleted", "deleting"):
            raise DomainError(404, "No se encontró el material.")
        return row

    def list(self, uid, subject):
        if not self.records.get(uid, "subjects", subject):
            raise DomainError(404, "No se encontró la materia.")
        return [
            m
            for m in self.records.list(uid, "materials")
            if m["subjectId"] == subject and m["status"] != "deleted"
        ]

    def version(self, uid, key, version=None):
        material = self.get(uid, key)
        row = self.records.get(
            uid, "materialVersions", f"{key}_{version or material['extractionVersion']}"
        )
        if not row:
            raise DomainError(404, "La extracción todavía no está disponible.")
        return json.loads(self.objects.get(row["blocksKey"]))

    def _store_version(self, uid, material_id, version, blocks):
        key = f"private/{uid}/materials/{material_id}/versions/{version}"
        self.objects.put(key, json.dumps(blocks, ensure_ascii=False).encode())
        index = {}
        for block in blocks:
            if block["status"] in ("text", "reviewed") and block["text"]:
                counts = Counter(tokens(block["text"]))
                index[block["blockId"]] = {
                    "counts": dict(counts),
                    "length": sum(counts.values()),
                }
        index_key = f"{key}-index"
        self.objects.put(
            index_key,
            gzip.compress(json.dumps(index).encode(), mtime=0),
            "application/gzip",
        )
        return new_row(
            id=f"{material_id}_{version}",
            materialId=material_id,
            extractionVersion=version,
            blocksKey=key,
            indexKey=index_key,
        )

    def ingest(self, job):
        uid, key, token = job["ownerId"], job["entityId"], job["leaseToken"]
        material = self.get(uid, key)
        data = self.objects.get(material["objectKey"], material["generation"])
        version = job["payload"]["version"]
        media = material["mediaType"]
        usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
        vision_calls = 0

        def transcribe(content):
            nonlocal vision_calls
            if self.provider is None or vision_calls >= 4:
                return ""
            self.jobs.checkpoint(
                uid, job["id"], token, "transcribing", min(90, vision_calls * 20)
            )
            self.jobs.mark_external_started(uid, job["id"], token)
            vision_calls += 1
            with Image.open(io.BytesIO(content)) as image:
                image.thumbnail((2000, 2000))
                output = io.BytesIO()
                image.convert("RGB").save(output, "JPEG", quality=85)
            try:
                draft, observed = self.provider.transcribe_image(
                    output.getvalue(), "image/jpeg"
                )
            except ProviderFailure as failure:
                if failure.usage is not None:
                    for name in usage:
                        usage[name] += int(failure.usage.get(name, 0))
                    failure.usage = usage
                raise
            for name in usage:
                usage[name] += int(observed.get(name, 0))
            self.jobs.observe_usage(uid, job["id"], token, usage)
            return draft.text

        if media == "application/pdf":
            pdf = PdfReader(io.BytesIO(data))
            if pdf.is_encrypted or len(pdf.pages) > 200:
                raise DomainError(422, "PDF protegido o con más de 200 páginas.")
            units = [(f"page:{i + 1}", page) for i, page in enumerate(pdf.pages)]
        else:
            extracted = extract_material(
                data,
                media,
                uid,
                material["subjectId"],
                key,
                transcriber=transcribe if media.startswith("image/") else None,
            )
            units = [(block["locator"], block) for block in extracted]
        blocks = []
        for i, (locator, unit) in enumerate(units, 1):
            self.jobs.checkpoint(
                uid,
                job["id"],
                token,
                f"page:{i}/{len(units)}",
                int(i * 90 / max(1, len(units))),
            )
            block_key = f"private/{uid}/materials/{key}/checkpoints/{version}/{i}"
            try:
                block = json.loads(self.objects.get(block_key))
            except DomainError as missing:
                if missing.status != 404:
                    raise
                try:
                    if media == "application/pdf":
                        writer = PdfWriter()
                        writer.add_page(unit)
                        buffer = io.BytesIO()
                        writer.write(buffer)
                        block = extract_material(
                            buffer.getvalue(),
                            media,
                            uid,
                            material["subjectId"],
                            key,
                            transcriber=transcribe,
                        )[0]
                    else:
                        block = unit
                    if len(block["text"]) > 30000:
                        block = {
                            **block,
                            "text": block["text"][:30000],
                            "status": "needs_review",
                            "warning": "page_text_truncated",
                        }
                except (OSError, ValueError, RuntimeError, PyPdfError):
                    block = {
                        "text": "",
                        "status": "failed",
                        "warning": "page_processing_failed",
                    }
                block = {
                    **block,
                    "blockId": f"block-{i}",
                    "locator": locator,
                    "extractionVersion": version,
                    "ownerId": uid,
                    "subjectId": material["subjectId"],
                    "materialId": key,
                }
                self.objects.put(
                    block_key, json.dumps(block, ensure_ascii=False).encode()
                )
            blocks.append(block)
        version_row = self._store_version(uid, key, version, blocks)
        status = self._status(blocks)
        current = self.get(uid, key)
        published = changed(
            current,
            status=status,
            extractionVersion=version,
            pageCount=len(blocks),
            reviewedPages=sum(b["status"] in ("text", "reviewed") for b in blocks),
            failedPages=sum(b["status"] == "failed" for b in blocks),
            indexVersion=version,
        )
        self.jobs.finish(
            uid,
            job["id"],
            token,
            "needs_review"
            if status == "needs_review"
            else "failed"
            if status == "failed"
            else "succeeded",
            {
                "materialId": key,
                "status": status,
                **({"error": "empty_or_unreadable"} if status == "failed" else {}),
            },
            additions=[
                ("materialVersions", version_row["id"], version_row, None),
                ("materials", key, published, current["revision"]),
            ],
            usage=usage,
        )

    def rebuild_index(self, uid, key, version):
        blocks = self.version(uid, key, version)
        derived = self._store_version(uid, key, version, blocks)
        row = self.records.get(uid, "materialVersions", f"{key}_{version}")
        if row.get("indexKey") != derived["indexKey"]:
            self.records.save(
                uid,
                "materialVersions",
                row["id"],
                changed(row, indexKey=derived["indexKey"]),
                row["revision"],
            )
        return blocks

    @staticmethod
    def _status(blocks):
        if not blocks:
            return "failed"
        if any(b["status"] == "needs_review" for b in blocks):
            return "needs_review"
        if any(b["status"] == "failed" for b in blocks):
            return "partial" if any(b.get("text") for b in blocks) else "failed"
        return "ready"

    def revise(self, uid, key, revision, edits, topic_ids):
        material = self.get(uid, key)
        if material["revision"] != revision:
            raise DomainError(409, "La transcripción cambió. Recarga antes de guardar.")
        if len(topic_ids) != len(set(topic_ids)):
            raise DomainError(422, "No repitas temas.")
        for topic in topic_ids:
            row = self.records.get(uid, "topics", topic)
            if not row or row["subjectId"] != material["subjectId"]:
                raise DomainError(404, "El tema no pertenece a esta materia.")
        blocks = self.version(uid, key)
        ids = {b["blockId"] for b in blocks}
        if any(e["blockId"] not in ids or not e["text"].strip() for e in edits):
            raise DomainError(422, "Selecciona una página válida y confirma su texto.")
        corrections = {e["blockId"]: e["text"] for e in edits}
        version = uuid4().hex
        revised = [
            {
                **b,
                "extractionVersion": version,
                **(
                    {"text": corrections[b["blockId"]], "status": "reviewed"}
                    if b["blockId"] in corrections
                    else {}
                ),
            }
            for b in blocks
        ]
        version_row = self._store_version(uid, key, version, revised)
        updated = changed(
            material,
            extractionVersion=version,
            indexVersion=version,
            status=self._status(revised),
            topicIds=topic_ids,
            reviewedPages=sum(b["status"] in ("text", "reviewed") for b in revised),
        )
        job = self.jobs.create(
            uid,
            "index",
            key,
            {"version": version},
            f"revision-{key}-{revision}",
            additions=lambda index_job: [
                (
                    "materials",
                    key,
                    {
                        **updated,
                        "jobId": index_job["id"],
                        "indexJobId": index_job["id"],
                    },
                    revision,
                ),
                ("materialVersions", version_row["id"], version_row, None),
            ],
        )
        old_job = self.jobs.get(uid, material["jobId"])
        if old_job["status"] == "needs_review":
            self.jobs.cancel(uid, old_job["id"])
        return {**updated, "jobId": job["id"], "indexJobId": job["id"]}

    def suggestions(self, uid, key):
        material = self.get(uid, key)
        words = set(tokens(" ".join(b["text"][:200] for b in self.version(uid, key))))
        topics = [
            t
            for t in self.records.list(uid, "topics")
            if t["subjectId"] == material["subjectId"]
        ]
        return [t["id"] for t in topics if words.intersection(tokens(t["title"]))]
