import pymupdf
import pytest

from app.pdf_utils import MAX_PAGES, PdfError, open_pdf, render_pages
from tests.conftest import sample_bytes


def make_pdf(pages: int = 1, width: int = 200, height: int = 300) -> bytes:
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page(width=width, height=height)
        page.draw_rect(pymupdf.Rect(0, 0, width, 30), color=(0, 0, 0), fill=(0, 0, 0))
    return doc.tobytes()


def png_size(png: bytes) -> tuple[int, int]:
    pix = pymupdf.Pixmap(png)
    return pix.width, pix.height


@pytest.mark.parametrize(
    "name, pages",
    [("25017 MP-F-023.PDF", 1), ("24015 QS-F-049_12052024134037.PDF", 1),
     ("2142-635946 lot log.pdf", 2)],
)
def test_samples_open_and_render_portrait(name, pages):
    doc = open_pdf(sample_bytes(name))
    assert doc.page_count == pages
    for png in render_pages(doc, dpi=50):
        w, h = png_size(png)
        assert h > w  # /Rotate flags (lot log uses 270) are applied → upright portrait


def test_extra_rotation_is_clockwise():
    doc = open_pdf(make_pdf())
    png = render_pages(doc, dpi=72, rotations=[90])[0]
    pix = pymupdf.Pixmap(png)
    assert (pix.width, pix.height) == (300, 200)
    # The black band that was at the top now sits on the right edge.
    right = pix.pixel(pix.width - 2, pix.height // 2)[0]
    left = pix.pixel(1, pix.height // 2)[0]
    assert right < 50 < left


@pytest.mark.parametrize(
    "data, fragment",
    [(b"", "empty"), (b"hello world", "not a PDF"), (b"%PDF-1.4 garbage", "could not be opened")],
)
def test_rejects_bad_files(data, fragment):
    with pytest.raises(PdfError, match=fragment):
        open_pdf(data)


def test_rejects_too_many_pages():
    with pytest.raises(PdfError, match="limit"):
        open_pdf(make_pdf(pages=MAX_PAGES + 1))
