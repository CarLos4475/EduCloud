import gzip
import json
import math
from collections import OrderedDict

from campus.adapters.extraction import tokens
from campus.services.academic import DomainError


class RetrievalService:
    def __init__(self, materials):
        self.materials = materials
        self.cache = OrderedDict()

    def load_index(self, uid, key, version):
        cache_key = (uid, key, version)
        if cache_key not in self.cache:
            self.materials.get(uid, key)
            record = self.materials.records.get(
                uid, "materialVersions", f"{key}_{version}"
            )
            if not record or not record.get("indexKey"):
                raise DomainError(
                    409,
                    "Estamos preparando de nuevo este material. Inténtalo en un momento.",
                )
            self.cache[cache_key] = (
                self.materials.version(uid, key, version),
                json.loads(
                    gzip.decompress(self.materials.objects.get(record["indexKey"]))
                ),
            )
            while len(self.cache) > 16:
                self.cache.popitem(last=False)
        self.cache.move_to_end(cache_key)
        return self.cache[cache_key]

    def search(self, uid, subject, query, material_ids):
        if not material_ids:
            return []
        blocks = []
        statistics = {}
        for key in material_ids:
            material = self.materials.get(uid, key)
            if material["subjectId"] != subject:
                raise DomainError(404, "El material no pertenece a la materia.")
            if material["status"] not in ("ready", "partial"):
                continue
            version_blocks, index = self.load_index(
                uid, key, material["extractionVersion"]
            )
            for block in version_blocks:
                if block["blockId"] in index:
                    blocks.append(block)
                    statistics[(key, block["blockId"])] = index[block["blockId"]]
        terms = list(dict.fromkeys(tokens(query)))[:64]
        average = sum(value["length"] for value in statistics.values()) / max(
            len(blocks), 1
        )
        idf = {}
        for term in terms:
            frequency = sum(term in value["counts"] for value in statistics.values())
            idf[term] = math.log(
                1 + (len(blocks) - frequency + 0.5) / (frequency + 0.5)
            )
        scored = []
        for block in blocks:
            stats = statistics[(block["materialId"], block["blockId"])]
            score = 0.0
            for term in terms:
                count = stats["counts"].get(term, 0)
                score += (
                    idf[term]
                    * count
                    * 2.5
                    / (count + 1.5 * (0.25 + 0.75 * stats["length"] / max(average, 1)))
                )
            if score > 0:
                scored.append({**block, "score": score})
        found = sorted(scored, key=lambda row: -row["score"])[:8]
        result = []
        budget = 18000
        for block in found:
            matches = [
                block["text"].lower().find(term)
                for term in sorted(terms, key=lambda word: -idf[word])
            ]
            position = next((position for position in matches if position >= 0), 0)
            start = max(0, position - 800)
            text = block["text"][start : start + min(budget, 5000)]
            if not text:
                break
            budget -= len(text)
            result.append(
                {
                    "sourceRef": {
                        name: block[name]
                        for name in (
                            "materialId",
                            "extractionVersion",
                            "blockId",
                            "locator",
                        )
                    },
                    "text": text,
                    "score": block["score"],
                }
            )
        return result

    def overview(self, uid, subject, material_ids, budget=18000, per_block=3000):
        """Opening blocks of each selected material, for resources not tied to a query."""
        result = []
        for key in material_ids:
            material = self.materials.get(uid, key)
            if material["subjectId"] != subject:
                raise DomainError(404, "El material no pertenece a la materia.")
            if material["status"] not in ("ready", "partial"):
                continue
            for block in self.materials.version(
                uid, key, material["extractionVersion"]
            ):
                text = block["text"][: min(per_block, budget)]
                if not text.strip():
                    continue
                budget -= len(text)
                result.append(
                    {
                        "sourceRef": {
                            name: block[name]
                            for name in (
                                "materialId",
                                "extractionVersion",
                                "blockId",
                                "locator",
                            )
                        },
                        "text": text,
                        "score": 0.0,
                    }
                )
                if budget <= 0:
                    return result
        return result

    def citation(self, uid, ref):
        # Historical citations remain resolvable; retrieval always uses current version.
        blocks = self.materials.version(
            uid, ref["materialId"], ref["extractionVersion"]
        )
        for block in blocks:
            if (
                block["blockId"] == ref["blockId"]
                and block["locator"] == ref["locator"]
            ):
                if ref.get("quote") and ref["quote"] not in block["text"]:
                    raise DomainError(
                        422, "La cita no coincide con el texto de esa página."
                    )
                return block
        raise DomainError(404, "No se encontró la página citada.")
