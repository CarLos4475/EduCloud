import io

import pytest
from campus.adapters.extraction import extract_material, retrieve
from PIL import Image
from pptx import Presentation
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas


def test_pdf_and_pptx_preserve_physical_locators():
    buffer = io.BytesIO()
    canvas = Canvas(buffer)
    canvas.drawString(60, 700, "La derivada de x al cuadrado es 2x.")
    canvas.showPage()
    canvas.drawString(60, 700, "La energia cinetica depende de la masa y velocidad.")
    canvas.save()
    blocks = extract_material(
        buffer.getvalue(), "application/pdf", "a", "calculus", "mat-1"
    )
    assert blocks[0]["locator"] == "page:1"
    assert (
        retrieve(blocks, "a", "calculus", "derivada cuadrado", 1)[0]["locator"]
        == "page:1"
    )
    assert retrieve(blocks, "b", "calculus", "derivada", 8) == []
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "Matrices y vectores"
    output = io.BytesIO()
    presentation.save(output)
    assert (
        extract_material(
            output.getvalue(),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "a",
            "algebra",
            "mat-2",
        )[0]["locator"]
        == "slide:1"
    )


def test_invalid_or_oversized_material_rejected():
    with pytest.raises(ValueError):
        extract_material(b"not a pdf", "application/pdf", "a", "s", "m")
    with pytest.raises(ValueError):
        extract_material(b"x" * (20 * 1024 * 1024 + 1), "text/plain", "a", "s", "m")


def test_scanned_pdf_is_rasterized_for_vision_and_kept_under_review():
    picture = Image.new("RGB", (400, 200), "white")
    buffer = io.BytesIO()
    canvas = Canvas(buffer)
    canvas.drawImage(ImageReader(picture), 20, 500, width=400, height=200)
    canvas.save()
    seen = []

    def transcribe(content):
        seen.append(content.startswith(b"\x89PNG"))
        return "Borrador de transcripción"

    blocks = extract_material(
        buffer.getvalue(), "application/pdf", "a", "s", "m", transcriber=transcribe
    )
    assert seen == [True]
    assert blocks[0]["text"] == "Borrador de transcripción"
    assert blocks[0]["status"] == "needs_review"
