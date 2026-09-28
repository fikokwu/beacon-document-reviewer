"""FastAPI entrypoint: API routes and the built frontend."""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from app import pipeline
from app.gemini_client import GeminiError
from app.pdf_utils import MAX_BYTES, PdfError
from app.schemas.common import Issue, ReviewResult

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="RegenMed Internal Document Reviewer", version="0.3.0")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/review", response_model=ReviewResult)
def review(file: UploadFile) -> ReviewResult:
    """Review one uploaded PDF. Sync on purpose: FastAPI runs it in a worker thread."""
    name = (file.filename or "").lower()
    if file.content_type not in ("application/pdf", "application/x-pdf") \
            and not name.endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")
    data = file.file.read(MAX_BYTES + 1)  # uploaded PDFs are never stored
    try:
        return pipeline.review_pdf(data)
    except PdfError as exc:
        raise HTTPException(400, str(exc)) from exc
    except GeminiError as exc:
        log.warning("AI failure: %s", exc)
        raise HTTPException(503, str(exc)) from exc


@app.post("/api/locate")
def locate(file: UploadFile, issues: str = Form(...), rotations: str = Form("[]")) -> dict:
    """Second, optional step: bounding boxes for issues, for highlighting on the page."""
    try:
        parsed = [Issue.model_validate(i) for i in json.loads(issues)]
        rots = [int(r) for r in json.loads(rotations)]
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, "Invalid issues list.") from exc
    data = file.file.read(MAX_BYTES + 1)
    try:
        return {"boxes": pipeline.locate_issues(data, parsed, rots)}
    except PdfError as exc:
        raise HTTPException(400, str(exc)) from exc
    except GeminiError as exc:
        log.warning("Locate failure: %s", exc)
        raise HTTPException(503, str(exc)) from exc


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
