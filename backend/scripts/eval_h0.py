"""Opt-in live evaluation on synthetic material; no private student data."""

import io
import json
from pathlib import Path

from campus.adapters.deepseek import DeepSeekProvider
from campus.adapters.extraction import extract_material, retrieve
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = {
    "calculo": [
        ("derivada", "La derivada de x^2 es 2x."),
        ("integral", "La integral de 2x es x^2 mas una constante C."),
        ("limite", "El limite de x+1 cuando x tiende a 2 es 3."),
        ("pendiente", "La pendiente de y=3x+2 es 3."),
        (
            "continuidad",
            "Una funcion continua no presenta saltos en el punto considerado.",
        ),
    ],
    "algebra": [
        (
            "identidad",
            "La matriz identidad tiene unos en la diagonal y ceros fuera de ella.",
        ),
        ("determinante", "Para una matriz 2x2, el determinante es ad-bc."),
        ("vector", "La suma de vectores se realiza componente a componente."),
        ("transpuesta", "La transpuesta intercambia filas y columnas."),
        (
            "autovalor",
            "Un autovalor lambda satisface Av=lambda v para un vector no nulo.",
        ),
    ],
    "fisica": [
        ("velocidad", "Con velocidad constante, la distancia es velocidad por tiempo."),
        ("fuerza", "La segunda ley de Newton establece F=ma."),
        ("energia", "La energia cinetica es mv^2/2."),
        ("potencia", "La potencia es trabajo dividido entre tiempo."),
        ("densidad", "La densidad es masa dividida entre volumen."),
    ],
    "programacion": [
        ("variable", "Una variable asocia un nombre a un valor."),
        ("bucle", "Un bucle repite instrucciones."),
        ("funcion", "Una funcion agrupa instrucciones y puede devolver un valor."),
        ("lista", "Una lista conserva una secuencia de elementos."),
        ("condicion", "Una condicion permite elegir una rama de ejecucion."),
    ],
}


def main():
    out = ROOT / ".superpowers/sdd/2026-11-02-plataforma-estudio/eval-h0"
    out.mkdir(parents=True, exist_ok=True)
    provider = DeepSeekProvider()
    rows = []
    corpus = []
    for subject, concepts in SUBJECTS.items():
        buffer = io.BytesIO()
        canvas = Canvas(buffer)
        for term, definition in concepts:
            canvas.drawString(50, 760, f"Concepto: {term}")
            canvas.drawString(50, 720, definition)
            canvas.showPage()
        canvas.save()
        (out / f"{subject}.pdf").write_bytes(buffer.getvalue())
        blocks = extract_material(
            buffer.getvalue(),
            "application/pdf",
            "synthetic-owner",
            subject,
            subject + "-material",
        )
        corpus.extend(blocks)
        for n, (term, definition) in enumerate(concepts, 1):
            for split, query in [
                ("development", f"Explica {term}"),
                ("holdout", f"En mis apuntes, que se indica acerca de {term}?"),
            ]:
                results = retrieve(blocks, "synthetic-owner", subject, query)
                rows.append(
                    {
                        "subject": subject,
                        "query": query,
                        "split": split,
                        "expectedLocator": f"page:{n}",
                        "hit": any(b["locator"] == f"page:{n}" for b in results[:8]),
                    }
                )
    image = Image.new("RGB", (1200, 350), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 44)
    draw.text((40, 40), "Apunte de calculo", font=font, fill="black")
    draw.text((40, 130), "f(x) = x^2     f'(x) = 2x", font=font, fill="black")
    picture = io.BytesIO()
    image.save(picture, "PNG")
    (out / "apunte-sintetico.png").write_bytes(picture.getvalue())
    transcript, vision_usage = provider.transcribe_image(picture.getvalue())
    examples = []
    for subject, question in [
        ("calculo", "¿Cuál es la derivada de x^2?"),
        ("algebra", "¿Cómo se calcula el determinante de una matriz 2x2?"),
        ("fisica", "¿Cuál es la energía cinética?"),
        ("programacion", "¿Para qué sirve un bucle?"),
    ]:
        blocks = retrieve(corpus, "synthetic-owner", subject, question)
        answer, usage = provider.answer_from_blocks(question, blocks)
        examples.append(
            {
                "subject": subject,
                "question": question,
                "answer": answer,
                "allowedBlocks": [b["blockId"] for b in blocks],
                "usage": usage,
            }
        )
    report = {
        "model": provider.model,
        "syntheticOnly": True,
        "questions": rows,
        "recallTop8": sum(row["hit"] for row in rows) / len(rows),
        "transcription": transcript.model_dump(by_alias=True),
        "visionUsage": vision_usage,
        "answers": examples,
        "limits": "40 lexical retrieval checks and five live provider calls; not a general academic benchmark. Image transcription always requires review. No cost is inferred from token counts alone.",
    }
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "retrievalCases": len(rows),
                "recallTop8": report["recallTop8"],
                "visionReturnedText": bool(transcript.text),
                "visionNeedsReview": transcript.needs_review,
                "liveAnswers": len(examples),
                "report": str((out / "report.json").relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
