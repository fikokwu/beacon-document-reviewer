"""PDF validation and page rendering (PyMuPDF).

Samples are image-only scans with no text layer. Some pages carry a /Rotate flag,
which PyMuPDF applies when rendering; pages physically scanned sideways are fixed
with the per-page rotation the classifier reports (see pipeline.py).
"""

import pymupdf

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 10
EXTRACT_DPI = 200
CLASSIFY_DPI = 100
PREVIEW_DPI = 110
LOCATE_DPI = 150


class PdfError(ValueError):
    """A user-facing problem with the uploaded file."""


def open_pdf(data: bytes) -> pymupdf.Document:
    if not data:
        raise PdfError("The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise PdfError(f"The file is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    if not data.lstrip()[:5] == b"%PDF-":
        raise PdfError("The file is not a PDF.")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several types for corrupt files
        raise PdfError("The PDF could not be opened (it may be damaged).") from exc
    if doc.needs_pass:
        raise PdfError("The PDF is password-protected.")
    if doc.page_count == 0:
        raise PdfError("The PDF has no pages.")
    if doc.page_count > MAX_PAGES:
        raise PdfError(f"The PDF has {doc.page_count} pages; the limit is {MAX_PAGES}.")
    return doc


def render_pages(doc: pymupdf.Document, dpi: int = EXTRACT_DPI,
                 rotations: list[int] | None = None) -> list[bytes]:
    """Render every page to PNG bytes, applying an extra clockwise rotation per page."""
    images = []
    for i, page in enumerate(doc):
        extra = (rotations[i] if rotations and i < len(rotations) else 0) % 360
        matrix = pymupdf.Matrix(dpi / 72, dpi / 72).prerotate(extra)
        images.append(page.get_pixmap(matrix=matrix, colorspace=pymupdf.csGRAY).tobytes("png"))
    return images


def render_previews(doc: pymupdf.Document, rotations: list[int] | None = None) -> list[str]:
    """Small upright JPEG previews as data URIs, for drawing issue boxes in the browser."""
    import base64

    previews = []
    for i, page in enumerate(doc):
        extra = (rotations[i] if rotations and i < len(rotations) else 0) % 360
        matrix = pymupdf.Matrix(PREVIEW_DPI / 72, PREVIEW_DPI / 72).prerotate(extra)
        jpeg = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csGRAY).tobytes(
            "jpeg", jpg_quality=70)
        previews.append("data:image/jpeg;base64," + base64.b64encode(jpeg).decode())
    return previews
