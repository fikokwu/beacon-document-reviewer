"""Generate synthetic test PDFs from the samples (backlog B-16).

Each variant applies edits to a sample: white out a filled cell, write a wrong value,
tick an extra box, rotate pages as if scanned sideways, or make a faint low-res scan.
Coordinates are for this *fixture generator only*; the app never uses coordinates.

Run: python -m tests.make_variants
"""

from pathlib import Path

import pymupdf

FIXTURES = Path(__file__).parent / "fixtures"
MP023 = "samples/25017 MP-F-023.PDF"
QS049 = "samples/24015 QS-F-049_12052024134037.PDF"
LOTLOG = "samples/2142-635946 lot log.pdf"
DISCARDS = "samples/22043 Discards.PDF"
DISCARD3 = "samples/22043 Discard - form 3 of 3.pdf"

# Edits use coordinates measured on renders of the *displayed* (upright) page at `dpi`:
#   ("white", page, (x0, y0, x1, y1))       paint over a cell
#   ("text", page, (x, y), "value", size)   write a value (baseline at x, y)
#   ("tick", page, (x0, y0, x1, y1))        draw an X in a box
#   ("rotate", degrees)                     re-lay every page sideways (no /Rotate flag)
#   ("faint",)                              re-scan as a faint, 72-DPI image
VARIANTS: dict[str, tuple[str, int, list[tuple]]] = {
    "22043 Discards - variant blank confirmed-by p1 and X p2": (
        DISCARDS, 110, [("white", 0, (430, 885, 545, 922)), ("white", 1, (873, 298, 893, 328))]),
    "25017 MP-F-023 - variant no ops manager review": (
        MP023, 100, [("white", 0, (412, 476, 600, 516))]),
    "25017 MP-F-023 - variant blank packaged posterior tibialis": (
        MP023, 100, [("white", 0, (492, 538, 578, 559))]),
    "25017 MP-F-023 - variant rotated 90": (MP023, 100, [("rotate", 90)]),
    "25017 MP-F-023 - variant six errors": (MP023, 100, [
        ("white", 0, (285, 124, 332, 152)),   # Donor Age
        ("white", 0, (538, 124, 612, 152)),   # Date of Processing
        ("white", 0, (722, 147, 814, 170)),   # Tissue Checked In date (initials kept)
        ("white", 0, (412, 476, 600, 516)),   # Ops Manager Review
        ("white", 0, (400, 576, 488, 591)),   # Peroneus Longus # Produced
        ("white", 0, (495, 678, 575, 698)),   # Femoral Head # Packaged
    ]),
    "24015 QS-F-049 - variant INC without status": (
        QS049, 100, [("white", 0, (333, 614, 455, 644))]),
    "24015 QS-F-049 - variant item 7 quality no date": (
        QS049, 100, [("white", 0, (738, 489, 846, 508))]),
    "24015 QS-F-049 - variant item 3 four-digit year": (
        QS049, 100, [("white", 0, (650, 330, 726, 352)), ("text", 0, (654, 347), "11/27/2024", 12)]),
    "24015 QS-F-049 - variant rotated 180": (QS049, 100, [("rotate", 180)]),
    "24015 QS-F-049 - variant faint low-res scan": (QS049, 100, [("faint",)]),
    # Good forms, poor image quality (should still PASS)
    "25017 MP-F-023 - quality faint 72dpi": (MP023, 100, [("faint", 72, 2.6, 40, 0)]),
    "24015 QS-F-049 - quality sideways noisy": (
        QS049, 100, [("rotate", 270), ("faint", 90, 1.6, 35, 6000)]),
    "2142-635946 lot log - quality low-res jpeg": (LOTLOG, 100, [("faint", 75, 1.4, 30, 0)]),
    "22043 Discards - quality faint noisy": (DISCARDS, 110, [("faint", 80, 2.0, 40, 4000)]),
    "2142-635946 lot log - variant blank labels qty": (
        LOTLOG, 100, [("white", 0, (588, 912, 640, 933))]),
    "2142-635946 lot log - variant blank manufacturer pulse lavage": (
        LOTLOG, 100, [("white", 0, (600, 624, 800, 641))]),
    "22043 Discard form 3 - variant no tissue status": (
        DISCARD3, 110, [("white", 0, (128, 208, 152, 230))]),
    "22043 Discard form 3 - variant two tissue statuses": (
        DISCARD3, 110, [("tick", 0, (293, 215, 307, 229))]),
}


def _rect(page: pymupdf.Page, box: tuple, k: float) -> pymupdf.Rect:
    """Displayed-page coordinates -> unrotated page space (handles /Rotate flags)."""
    return pymupdf.Rect(*(v * k for v in box)) * page.derotation_matrix


def _relayout(doc: pymupdf.Document, degrees: int) -> pymupdf.Document:
    out = pymupdf.open()
    for page in doc:
        r = page.rect
        size = (r.height, r.width) if degrees in (90, 270) else (r.width, r.height)
        new = out.new_page(width=size[0], height=size[1])
        new.show_pdf_page(new.rect, doc, page.number, rotate=degrees)
    return out


def _faint(doc: pymupdf.Document, dpi: int = 72, gamma: float = 2.2, quality: int = 45,
           noise: int = 0) -> pymupdf.Document:
    """Re-scan as a degraded image: low DPI, lighter ink, JPEG artefacts, speckle noise."""
    import random

    rng = random.Random(7)
    out = pymupdf.open()
    for page in doc:
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        pix.gamma_with(gamma)
        for _ in range(noise):
            pix.set_pixel(rng.randrange(pix.width), rng.randrange(pix.height), (rng.randrange(60),))
        w, h = pix.width * 72 / dpi, pix.height * 72 / dpi
        new = out.new_page(width=w, height=h)
        new.insert_image(new.rect, stream=pix.tobytes("jpeg", jpg_quality=quality))
    return out


def make(name: str, source: str, dpi: int, edits: list[tuple]) -> Path:
    doc = pymupdf.open(FIXTURES / source)
    k = 72 / dpi
    for edit in edits:
        kind = edit[0]
        if kind == "white":
            page = doc[edit[1]]
            page.draw_rect(_rect(page, edit[2], k), color=(1, 1, 1), fill=(1, 1, 1))
        elif kind == "text":
            page = doc[edit[1]]
            point = pymupdf.Point(edit[2][0] * k, edit[2][1] * k) * page.derotation_matrix
            page.insert_text(point, edit[3], fontsize=edit[4] * k, fontname="helv",
                             rotate=page.rotation)
        elif kind == "tick":
            page = doc[edit[1]]
            r = _rect(page, edit[2], k)
            page.draw_line(r.tl, r.br, width=1.2)
            page.draw_line(r.tr, r.bl, width=1.2)
        elif kind == "rotate":
            doc = _relayout(doc, edit[1])
        elif kind == "faint":
            doc = _faint(doc, *edit[1:])
    out = FIXTURES / "variants" / f"{name}.pdf"
    doc.save(out)
    return out


if __name__ == "__main__":
    for variant, (src, dpi, edits) in VARIANTS.items():
        print("wrote", make(variant, src, dpi, edits).name)
