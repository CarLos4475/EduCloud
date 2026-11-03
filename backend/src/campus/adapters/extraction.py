"""Bounded local extraction and lexical retrieval for the H0 spike."""

import io
import math
import re
import unicodedata
import zipfile
from collections import Counter

from PIL import Image
from pptx import Presentation
from pypdf import PdfReader


def extract_material(
    content: bytes,
    media_type: str,
    owner: str,
    subject: str,
    material: str,
    transcriber=None,
):
    if len(content) > 20 * 1024 * 1024:
        raise ValueError("El documento excede 20 MiB.")
    pages: list[tuple[str, str, str]] = []
    if media_type == "application/pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("El contenido no es un PDF.")
        pdf = PdfReader(io.BytesIO(content))
        if pdf.is_encrypted or len(pdf.pages) > 200:
            raise ValueError("PDF protegido o con más de 200 páginas.")
        pages = [
            (f"page:{n}", page.extract_text() or "", "text")
            for n, page in enumerate(pdf.pages, 1)
        ]
        if transcriber and any(not text.strip() for _, text, _ in pages):
            import pypdfium2 as pdfium

            with pdfium.PdfDocument(content) as rendered:
                drafts = []
                for n, (locator, text, status) in enumerate(pages):
                    if not text.strip():
                        page = rendered.get_page(n)
                        try:
                            width, height = page.get_size()
                            if min(width, height) <= 0:
                                raise ValueError("Página sin dimensiones válidas.")
                            bitmap = page.render(
                                scale=min(1.5, 2000 / max(width, height))
                            )
                            image = bitmap.to_pil()
                            output = io.BytesIO()
                            image.save(output, "PNG")
                            text = transcriber(output.getvalue())
                            image.close()
                            bitmap.close()
                            status = "needs_review"
                        finally:
                            page.close()
                    drafts.append((locator, text, status))
                pages = drafts
    elif media_type.endswith("presentationml.presentation"):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if sum(entry.file_size for entry in archive.infolist()) > 100 * 1024 * 1024:
                raise ValueError("La presentación expandida es demasiado grande.")
        presentation = Presentation(io.BytesIO(content))
        if len(presentation.slides) > 200:
            raise ValueError("La presentación supera 200 diapositivas.")
        pages = [
            (
                f"slide:{n}",
                "\n".join(shape.text for shape in slide.shapes if shape.has_text_frame)
                + (
                    "\n" + slide.notes_slide.notes_text_frame.text
                    if slide.has_notes_slide
                    else ""
                ),
                "needs_review"
                if any(
                    shape.shape_type == 13 or shape.has_chart for shape in slide.shapes
                )
                else "text",
            )
            for n, slide in enumerate(presentation.slides, 1)
        ]
    elif media_type in ("text/plain", "text/markdown"):
        pages = [("section:1", content.decode("utf-8"), "text")]
    elif media_type in ("image/png", "image/jpeg", "image/webp"):
        if len(content) > 10 * 1024 * 1024:
            raise ValueError("La imagen excede 10 MiB.")
        with Image.open(io.BytesIO(content)) as image:
            if (
                image.format not in {"PNG", "JPEG", "WEBP"}
                or image.width * image.height > 30_000_000
            ):
                raise ValueError("Imagen no admitida o demasiado grande.")
            image.verify()
        pages = [
            ("image:1", transcriber(content) if transcriber else "", "needs_review")
        ]
    else:
        raise ValueError("Formato no admitido.")
    return [
        {
            "ownerId": owner,
            "subjectId": subject,
            "materialId": material,
            "extractionVersion": "v1",
            "blockId": f"block-{n}",
            "locator": locator,
            "text": text,
            "status": status if text else "needs_review",
        }
        for n, (locator, text, status) in enumerate(pages, 1)
    ]


def tokens(text):
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )
    return re.findall(r"[a-z0-9]+", text)


def retrieve(blocks, owner, subject, query, top_k=8, material_ids=None):
    scoped = [
        b
        for b in blocks
        if b["ownerId"] == owner
        and b["subjectId"] == subject
        and (material_ids is None or b["materialId"] in material_ids)
        and b.get("text")
    ]
    documents = [Counter(tokens(block["text"])) for block in scoped]
    average = sum(sum(doc.values()) for doc in documents) / max(len(documents), 1)
    scores = []
    for block, doc in zip(scoped, documents):
        score = 0.0
        for term in tokens(query):
            frequency = sum(term in other for other in documents)
            inverse = math.log(
                1 + (len(documents) - frequency + 0.5) / (frequency + 0.5)
            )
            count = doc[term]
            score += (
                inverse
                * count
                * 2.5
                / (count + 1.5 * (0.25 + 0.75 * sum(doc.values()) / max(average, 1)))
            )
        if score > 0:
            scores.append({**block, "score": score})
    return sorted(scores, key=lambda item: -item["score"])[: min(top_k, 50)]
