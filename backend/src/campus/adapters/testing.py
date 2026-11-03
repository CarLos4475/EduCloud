"""Explicit emulator-only provider for repeatable browser tests; never a fallback."""

import json


class TestStudyProvider:
    __test__ = False

    def transcribe_image(self, content, media_type="image/png"):
        from campus.adapters.deepseek import Transcription

        return Transcription(text="Transcripción de prueba local: V = I R."), {
            "total_tokens": 30
        }

    def tutor_answer(self, messages, on_progress=None):
        context = json.loads(messages[-1]["content"])
        source = context["sources"][0] if context["sources"] else None
        return {
            "answer": f"Proveedor de prueba local. {source['text'][:200] if source else 'Ejemplo de explicación general.'}",
            "citations": [
                {"sourceId": source["sourceId"], "quote": source["text"][:100]}
            ]
            if source
            else [],
            "insufficientSources": False,
        }, {"total_tokens": 30}
