"""Explicit emulator-only provider for repeatable browser tests; never a fallback."""

import json


class TestStudyProvider:
    __test__ = False

    def transcribe_image(self, content, media_type="image/png"):
        from campus.adapters.deepseek import Transcription

        return Transcription(text="Transcripción de prueba local: V = I R."), {
            "total_tokens": 30
        }

    def structured_answer(self, messages, on_progress=None, max_tokens=6000):
        context = json.loads(messages[-1]["content"])
        source = context["sources"][0] if context["sources"] else None
        quote = source["text"][:80] if source else ""
        citations = [{"sourceId": source["sourceId"], "quote": quote}] if source else []
        kind = context["kind"]
        note = "Proveedor de prueba local. "
        if kind == "summary":
            body = {
                "overview": note + "Resumen de ejemplo.",
                "sections": [
                    {"heading": "Idea principal", "body": quote or "Ejemplo."}
                ],
                "keyPoints": ["Punto uno", "Punto dos"],
            }
        elif kind == "concepts":
            body = {"concepts": [{"term": "Ley de Ohm", "definition": "$V = IR$"}]}
        elif kind == "flashcards":
            body = {
                "cards": [{"front": "¿Qué dice la ley de Ohm?", "back": "$V = IR$"}]
            }
        elif kind == "quiz":
            body = {
                "questions": [
                    {
                        "prompt": "Si R = 2 y I = 3, ¿cuánto vale V?",
                        "options": ["1", "5", "6", "9"],
                        "correctIndex": 2,
                        "explanation": "V = I R = 6.",
                    }
                ]
            }
        else:
            body = {
                "schemaVersion": 1,
                "title": "Explorador de la ley de Ohm",
                "learningObjective": "Ver cómo cambia el voltaje con la resistencia.",
                "instructions": "Mueve la resistencia.",
                "html": '<label for="r">Resistencia</label><input id="r" type="range" min="1" max="10" value="5"><p id="v"></p><div id="chart"></div>',
                "css": "",
                "javascript": "function draw(r){ui.patch('v',{text:'V = '+(2*r)+' V'});ui.plot('chart',{points:[[0,0],[1,r],[2,2*r]],label:'V frente a I'});}var saved=state.read();var r0=saved.r||5;ui.patch('r',{value:r0});ui.on('r','input',function(x){state.write({r:Number(x)});draw(Number(x));});draw(r0);",
                "initialState": {"r": 5},
                "textAlternative": "Una gráfica lineal de V frente a I; su pendiente es R.",
                "requestedCapabilities": ["controls", "plot", "state"],
            }
        return {**body, "citations": citations}, {"total_tokens": 40}

    def tutor_answer(self, messages, on_progress=None, max_tokens=3000):
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
