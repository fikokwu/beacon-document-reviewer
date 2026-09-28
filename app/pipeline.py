"""render → classify → extract → validate → report."""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path

from pydantic import BaseModel

from app import config
from app.gemini_client import GeminiClient, JsonGenerator
from app.pdf_utils import (
    CLASSIFY_DPI,
    EXTRACT_DPI,
    LOCATE_DPI,
    open_pdf,
    render_pages,
    render_previews,
)
from app.rules.registry import FORMS, FormSpec, build_result
from app.schemas.common import Classification, FieldValue, Issue, LocateResult, ReviewResult

PROMPTS_DIR = Path(__file__).parent / "prompts"

_CODE_RE = re.compile(r"\b(MP|QS)\s*-?\s*F\s*-?\s*(\d{3})(?:\s*\.\s*(\d{1,3}))?", re.IGNORECASE)
# Title fallback when the bottom-right code is unreadable. Distinctive phrases only.
_TITLE_HINTS = [
    ("tissue open checklist", "MP-F-023"),
    ("discard form", "MP-F-018"),
    ("disposition statement", "QS-F-049"),
    ("lot log", "MP-F-021"),
]
UNKNOWN_MESSAGE = (
    "This doesn't look like one of the supported forms (MP-F-023 Tissue Open Checklist, "
    "QS-F-049 Technical/Quality Review, MP-F-021 Lot Log, MP-F-018 Tissue Discard Form), "
    "so no checks were run."
)


@cache
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def resolve_form(cls: Classification) -> tuple[str, str | None]:
    """Map the classifier's reading to a supported form type and version."""
    if cls.form_code:
        m = _CODE_RE.search(cls.form_code)
        if m:
            code = f"{m.group(1).upper()}-F-{m.group(2)}"
            if code in FORMS:
                return code, m.group(3)
            return "UNKNOWN", None
    title = (cls.form_title or "").lower()
    for phrase, code in _TITLE_HINTS:
        if phrase in title:
            return code, None
    return "UNKNOWN", None


def _stamp_page(ext: BaseModel, page: int) -> None:
    """Force the page number on every row (and its cells) from a single-page call."""
    for name in type(ext).model_fields:
        value = getattr(ext, name)
        if not isinstance(value, list):
            continue
        for row in value:
            if hasattr(row, "page"):
                row.page = page
            for cell_name in type(row).model_fields:
                cell = getattr(row, cell_name)
                if isinstance(cell, FieldValue):
                    cell.page = page


def merge_extractions(schema: type[BaseModel], parts: list[BaseModel]) -> BaseModel:
    """Concatenate list fields across per-page results; take the first non-empty scalar."""
    merged = {}
    for name in schema.model_fields:
        values = [getattr(p, name) for p in parts]
        if isinstance(values[0], list):
            merged[name] = [item for v in values for item in v]
        else:
            merged[name] = next((v for v in values if _has_content(v)), values[0])
    return schema(**merged)


def _has_content(value) -> bool:
    if isinstance(value, FieldValue):
        return bool((value.raw or "").strip()) or value.status != "blank"
    return bool(value)


def _extract(client: JsonGenerator, spec: FormSpec, images: list[bytes]) -> BaseModel:
    prompt = load_prompt("extract_common.md") + "\n\n" + load_prompt(spec.prompt_file)
    if not spec.per_page or len(images) == 1:
        return client.generate_json(images, prompt, spec.schema)

    if spec.parts and max(page for page, _ in spec.parts) == len(images):
        jobs = list(spec.parts)
    else:
        per_page_note = ("Transcribe only the tables that appear on this page and return "
                         "empty lists for tables that are on other pages.")
        jobs = [(i + 1, per_page_note) for i in range(len(images))]

    def run(job: tuple[int, str]) -> BaseModel:
        page, instruction = job
        note = f"\n\n## This call\nYou are given ONLY page {page} of {len(images)}. {instruction}"
        part = client.generate_json([images[page - 1]], prompt + note, spec.schema)
        _stamp_page(part, page)
        return part

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        parts = list(pool.map(run, jobs))
    return merge_extractions(spec.schema, parts)


def review_pdf(data: bytes, client: JsonGenerator | None = None) -> ReviewResult:
    """Review one uploaded PDF. Raises PdfError (bad upload) or GeminiError (AI failure)."""
    start = time.monotonic()

    def elapsed_ms() -> int:
        return int((time.monotonic() - start) * 1000)

    doc = open_pdf(data)
    pages = doc.page_count
    client = client or GeminiClient()

    # Render the full-resolution pages while the (fast) classifier runs.
    with ThreadPoolExecutor(max_workers=1) as pool:
        upright = pool.submit(render_pages, doc, EXTRACT_DPI)
        cls = client.generate_json(render_pages(doc, CLASSIFY_DPI), load_prompt("classify.md"),
                                   Classification, model=config.GEMINI_CLASSIFY_MODEL or None)
        images = upright.result()
    form_type, version = resolve_form(cls)
    if form_type == "UNKNOWN":
        return ReviewResult(
            form_type="UNKNOWN", form_title=cls.form_title, classification_confidence=cls.confidence,
            passed=False, pages=pages, processing_ms=elapsed_ms(), message=UNKNOWN_MESSAGE,
        )

    spec = FORMS[form_type]
    if any(r % 360 for r in cls.page_rotations):  # page scanned sideways: re-render upright
        images = render_pages(doc, EXTRACT_DPI, rotations=cls.page_rotations)
    extraction = _extract(client, spec, images)

    return build_result(
        form_type,
        spec.check(extraction),
        form_labels=spec.form_labels(extraction) if spec.form_labels else None,
        form_title=spec.title,
        form_version=version or getattr(extraction, "form_version", None),
        classification_confidence=cls.confidence,
        pages=pages,
        page_images=render_previews(doc, cls.page_rotations),
        page_rotations=[r % 360 for r in cls.page_rotations][:pages],
        processing_ms=elapsed_ms(),
    )


MAX_LOCATE = 40  # beyond this (e.g. a blank template) highlighting adds little


def locate_issues(data: bytes, issues: list[Issue], rotations: list[int] | None = None,
                  client: JsonGenerator | None = None) -> list[list[int] | None]:
    """Find each issue's cell on its page (one fast AI call per page, in parallel).
    Returns boxes aligned with `issues`: [ymin, xmin, ymax, xmax] on 0-1000, or None."""
    doc = open_pdf(data)
    client = client or GeminiClient()
    boxes: list[list[int] | None] = [None] * len(issues)
    wanted = [i for i, issue in enumerate(issues) if 1 <= issue.page <= doc.page_count]
    wanted = sorted(wanted, key=lambda i: {"error": 0, "warning": 1}.get(issues[i].severity, 2))
    by_page: dict[int, list[int]] = {}
    for i in wanted[:MAX_LOCATE]:
        by_page.setdefault(issues[i].page, []).append(i)
    images = render_pages(doc, LOCATE_DPI, rotations=rotations)

    def run(page: int) -> None:
        idx = by_page[page]
        items = "\n".join(
            f"{n}. Section: {issues[i].section}; row: {issues[i].row or '-'}; "
            f"field: {issues[i].field or '-'}. Problem: {issues[i].message}"
            for n, i in enumerate(idx, 1))
        result = client.generate_json([images[page - 1]], load_prompt("locate.md")
                                      + "\n\n## Items\n" + items, LocateResult,
                                      model=config.GEMINI_CLASSIFY_MODEL or None)
        for located in result.boxes:
            ok = len(located.box) == 4 and all(0 <= v <= 1000 for v in located.box)
            if ok and 1 <= located.index <= len(idx):
                boxes[idx[located.index - 1]] = located.box

    if by_page:
        with ThreadPoolExecutor(max_workers=len(by_page)) as pool:
            list(pool.map(run, by_page))
    return boxes
