# CLAUDE.md — RegenMed Internal Document Reviewer

## What we're building
A deployed web app for the RegenMed hackathon challenge. A user uploads **one scanned PDF** of a hand-filled RegenMed processing form. The app:

1. **Detects the form type** (it is never told in advance).
2. **Checks the form** against that type's rules (below).
3. **Reports** the form type plus either a clear list of issues (each pointing to the exact section / row / field / page) or a clear "Passed all checks".

Judges will upload **new, unseen PDFs**. Nothing may be hard-coded to the sample files (no fixed pixel coordinates, no expected values). Local-only demos are not accepted — it must run on a public URL.

Out of scope: validating product codes against RegenMed's reference list, or any check that needs data outside the form itself. No real donor data is involved.

## Core design principle
**Gemini reads, Python judges.**
- Gemini (vision) classifies the form and transcribes fields into a strict JSON schema. It must *not* decide pass/fail.
- Deterministic Python rules decide pass/fail from that JSON. Every rule is unit-tested.
- This keeps results reproducible, explainable to judges, and testable without API calls.

## Stack
- **Python 3.12**, **FastAPI** (API + serves the built frontend), **Uvicorn**
- **Gemini API** via the `google-genai` SDK. API key in `GEMINI_API_KEY`; model name in `GEMINI_MODEL` (never hard-code a model version — use the current Pro model from AI Studio).
- **Pydantic v2** for extraction schemas (passed to Gemini as `response_schema`) and API responses
- **PyMuPDF** (`pymupdf`) to render PDF pages to PNG (200 DPI) and fix rotation
- **OpenCV / NumPy** (optional) — ink-density check to double-check "blank" cells
- **React + Vite + TypeScript + Tailwind** frontend, built to static files and served by FastAPI
- **pytest** for tests
- **Docker → Google Cloud Run** (single container). Secret in **Secret Manager**.

## Repo layout
```
app/
  main.py              # FastAPI app: POST /api/review, GET /api/health, serves frontend
  pipeline.py          # render → classify → extract → validate → report
  pdf_utils.py         # PDF → page images, deskew/rotation, page count
  gemini_client.py     # thin wrapper: generate_json(images, prompt, schema)
  prompts/             # classify.md, extract_mp_f_023.md, extract_qs_f_049.md, extract_mp_f_021.md
  schemas/
    common.py          # FieldValue, Issue, ReviewResult
    mp_f_023.py
    qs_f_049.py
    mp_f_021.py        # Lot Log
  rules/
    helpers.py         # is_blank, is_na, parse_date_mmddyy, has_initials
    mp_f_023.py
    qs_f_049.py
    mp_f_021.py
    registry.py        # form_type -> (schema, prompt, rules)
frontend/              # React/Vite app
tests/
  fixtures/samples/    # the 3 filled sample PDFs from RegenMed
  fixtures/blank/      # blank templates (added by the team)
  fixtures/variants/   # synthetic variants from make_variants.py
  fixtures/expected/   # <fixture>.json with expected form_type + expected rule_ids
  test_rules_*.py      # rule tests on hand-written JSON (no API calls)
  test_pipeline.py     # end-to-end on fixtures (marked @pytest.mark.live, needs API key)
docs/                  # project plan, rules (plain English), architecture, ADRs, sprints, business case
Dockerfile
.env.example
```

**Docs discipline:** every change updates the relevant doc (see `docs/CONTRIBUTING.md`) and `CHANGELOG.md`. New design choices get an ADR in `docs/DECISIONS.md`.

## Pipeline
1. **Validate upload**: exactly one file, `application/pdf`, ≤ 20 MB, ≤ 10 pages.
2. **Render** each page to PNG at 200 DPI. Samples are **image-only scans with no text layer** (Xerox / VersaLink copiers); some pages are scanned rotated — normalize orientation.
3. **Classify** (one Gemini call, all pages, low-res is fine) → `{form_code, form_title, confidence}`.
   - Primary cue: the form code printed **bottom-right** of each page (e.g. `MP-F-023.009`). Ignore the version suffix after the dot.
   - Secondary cue: the title at the top.
   - If not one of the three supported forms → return `form_type: "UNKNOWN"` with a friendly message; do not run rules.
4. **Extract** (one Gemini call with the form-specific prompt + Pydantic schema, full-res pages, `temperature=0`, `response_mime_type="application/json"`).
5. **Validate** with the form's rule module → list of `Issue`.
6. **Respond** with `ReviewResult`.

## Extraction conventions (apply to every form)
Each extracted field is a `FieldValue`:
```python
class FieldValue(BaseModel):
    raw: str | None          # exact transcription, None if empty
    status: Literal["filled", "blank", "na", "illegible"]
    struck_through: bool = False   # value crossed out (GDP correction)
    page: int
    box_2d: list[int] | None = None  # [ymin, xmin, ymax, xmax] 0-1000, for highlighting (stretch)
```
Instruct Gemini to:
- Transcribe exactly what is written; never guess or fill in values.
- Treat `N/A`, `N\A`, `NA`, `n/a` as `status="na"`.
- Treat `0` and `Ø` as **filled** (zero is a valid value, not blank).
- Treat tally marks (`|`, `||`, `\\\`, `||||`) in Qty columns as filled; also return the count.
- For a struck-through value with a replacement, return the replacement as `raw` and set `struck_through=true`.
- A **whole row** struck through (line across the row, usually with initials/date) = voided row → `row_voided=true`.
- Rows with no item name and no entries are **empty rows** → omit them.
- Use `illegible` only when there is clearly ink but it can't be read.

## Form catalog and rules

Issue IDs are stable strings used in tests and the UI.

### MP-F-023 — "MS Processing Instructions / Tissue Open Checklist" (1 page)
**Header (top of form), in order:** Donor #, Verified By, Cross Reference #, Donor Sex, Donor Age, Date of Recovery, Instruction Verification (each team member initials), Date of Processing, Clean Room Log Review By/Date, Tissue Checked In By/Date.

**Middle:** "Operations Manager Review – Initials / Date (MM/DD/YY)".

**Processing Instructions table** columns: Processing Instructions | FRZ/FD | Irradiated | # Produced | # Packaged | Comments. Rows are tissue lines (e.g. Posterior Tibialis, Patellar Ligament, Femoral Head, Tri-Cortical Block, Cancellous 1–10 mm, Tibia Shaft, …) separated by shaded/blank spacer rows. **Read row names from the form — do not hard-code the list.**

Rules:
- `MP023-HDR-BLANK` — No header field from Donor # through Tissue Checked In By/Date may be blank.
- `MP023-HDR-BYDATE` — Every By/Date field (Clean Room Log Review, Tissue Checked In) must have **both** initials **and** a date.
- `MP023-OPS-REVIEW` — Operations Manager Review must have **both** initials **and** a date.
- `MP023-ROW-PRODUCED` / `MP023-ROW-PACKAGED` — For every white (non-shaded) row that has a tissue name, **# Produced AND # Packaged** must both be filled in. `0` counts as filled. Ignore shaded/spacer rows.

Not in scope for rules (extract only if cheap): Received L/R checkmarks, TGLN labels, Special Instructions.

### QS-F-049 — "Technical/Quality Review and Disposition Statement" (1 page)
**Header:** RegenMed DDIN #, Cross-Reference #, Graft ID #s.

**Review Elements** items 1–10, each with a **Technical** and a **Quality** "Reviewed By/Date" cell. Item 10 also has **INC #** and **Status** fields.

**Disposition section:** Technical Review Signature & Date; release option boxes, each with QA Signature & Date.

Rules:
- `QS049-REVIEW-BLANK` — For every item 1–10, both Technical and Quality cells must contain initials **and** a date, **or** say N/A. Report which item, which column, and what's missing (initials, date, or both).
- `QS049-DATE-FORMAT` — Every date in the Reviewed By/Date cells must be **MM/DD/YY** (2-digit month, 2-digit day, 2-digit year, valid calendar date). Flag 4-digit years, DD/MM order where detectable (e.g. day > 12 in the first position), and impossible dates. Separator strictness is a config flag `STRICT_DATE_SEPARATOR` (default `False`: accept `/`, `-`, `.`; samples use `11-27-24` and `12.05.24`). Confirm with organizers.
- `QS049-INC-STATUS` — In item 10, if an INC # is entered, the Status field must also be filled.

### MP-F-021 — "MS Processing & Packaging Lot Log" (2 pages) — a.k.a. **Lot Log**
**Page 1:** header (Processing/Packaging TPM initials, dates, room temps, RH, pressure) — not in rules. Then:
- **Item table**: Item | Lot Number | Exp. Date | Manufacturer (mix of printed and handwritten rows).
- **RegenMed Item table**: RegenMed Item | Lot | Qty Used.

**Page 2:** two side-by-side **Item tables**: Item | Load # | Sterilization Date (Load # may hold two numbers, e.g. `2 3`). Then **Packaging table**: Packaging | Lot | Qty Used.

Rules (only for **listed** rows = rows with an item name that are not voided):
- `LOT-P1-ITEM` — Lot Number, Exp. Date, and Manufacturer must each be filled or say N/A.
- `LOT-P1-REGENMED` — **Lot AND Qty Used** must both be filled.
- `LOT-P2-ITEM` — **Load # AND Sterilization Date** must both be filled. Check both left and right tables.
- `LOT-P2-PACKAGING` — **Lot AND Qty Used** must both be filled.
- `LOT-VOIDED-ROW` (severity `info`) — report struck-through rows so a reviewer can confirm the void was initialed/dated; never an error.

### MP-F-018 — "Tissue Discard Form" (bonus objective; 1 page per form, a PDF may hold several)
**Top:** Donor #, Discard Authorized By/Date, Reason for Discard, Tissue Status checkboxes (Unprocessed / In Processing / Unreleased Packaged / Released Packaged). **Middle:** Graft IDs | Tissue Description | Storage Location | X. **Bottom:** Tissue Discarded By, Confirmed By, Date; Released Packaged Tissue FreezerPro Updated By + Date; Donor Chart Log/FreezerPro Updated By + Date.

Rules (each page checked as its own form):
- `DISC-HDR-BLANK`: Donor #, Discard Authorized By/Date, Reason not blank.
- `DISC-AUTH-BYDATE`: Authorized By/Date has both initials and a date.
- `DISC-STATUS`: exactly one Tissue Status box is checked.
- `DISC-STATUS-GRAFT`: Graft IDs listed → Unreleased/Released Packaged. Graft IDs N/A (or a drawn dash) → Unprocessed/In Processing.
- `DISC-ROW-X`: the X box is marked for every listed tissue.
- `DISC-BOTTOM-BLANK`: no bottom field blank (N/A is fine).

## Output schema
```python
class Issue(BaseModel):
    rule_id: str
    severity: Literal["error", "warning", "info"]
    page: int
    section: str          # e.g. "Operations Manager Review", "Page 2 – Packaging"
    row: str | None       # e.g. "Item 7", "Gracilis", "Sieve"
    field: str | None     # e.g. "Quality", "# Packaged", "Status"
    message: str          # plain English, e.g. "Quality review for item 7 has initials but no date."
    evidence: str | None  # what was read, e.g. 'raw="LC"'
    box_2d: list[int] | None = None

class ReviewResult(BaseModel):
    form_type: Literal["MP-F-023", "QS-F-049", "MP-F-021", "MP-F-018", "UNKNOWN"]
    form_title: str | None
    form_version: str | None      # e.g. "009"
    classification_confidence: float
    passed: bool                  # True only if no "error" issues
    issues: list[Issue]
    needs_confirmation: list[Issue]  # low-confidence reads (illegible / model-vs-ink disagreement)
    pages: int
    processing_ms: int
```
- `illegible` fields → `warning` in `needs_confirmation`, not a hard error.
- If the optional ink-density check disagrees with Gemini's `blank`/`filled`, downgrade to `needs_confirmation`.

## API
- `POST /api/review` — multipart `file` (single PDF) → `ReviewResult`
- `GET /api/health` → `{"ok": true}`
- Everything else → serves `frontend/dist`

## Frontend (keep it simple and clear)
- Drag-and-drop upload for one PDF; show a progress state.
- Big form-type badge (code + title) and a PASS/FAIL banner.
- Issues grouped by section, each showing page, row, field, and message.
- "Needs confirmation" group shown separately.
- Stretch: page thumbnails with issue boxes drawn from `box_2d`; download report as PDF/JSON.

## Testing
- **Rule tests** (`test_rules_*.py`) use hand-written extraction JSON — fast, no API key. Write these first and keep them passing.
- **Fixtures**: `tests/fixtures/` holds the 3 filled samples plus the **blank templates** the team will add. Each fixture has `tests/fixtures/expected/<name>.json` with the expected `form_type` and the set of expected `rule_id`s (plus row/field).
- **Synthetic variants**: generate extra test PDFs by painting white rectangles over specific filled cells in the samples (e.g. remove the Ops Manager initials, blank a QS Quality date, remove an INC Status, blank a Lot Log Qty Used). Store the generator script in `tests/make_variants.py`.
- Live tests (`@pytest.mark.live`) call Gemini; skip them when `GEMINI_API_KEY` is unset.

## Commands
```bash
# backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
pytest -m "not live"          # fast rule tests
pytest -m live                # end-to-end with Gemini

# frontend
cd frontend && npm install && npm run dev      # dev (proxy /api to :8080)
cd frontend && npm run build                   # builds to frontend/dist

# deploy
# full runbook: docs/DEPLOY.md (project gen-lang-client-0784934773)
gcloud run deploy regenmed-reviewer --source . --region northamerica-northeast2 \
  --allow-unauthenticated --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GEMINI_MODEL=gemini-3.1-pro-preview,GEMINI_THINKING_LEVEL=low,GEMINI_TIMEOUT_S=150 \
  --memory 1Gi --cpu 1 --timeout 300 --min-instances 1 --max-instances 3 --cpu-boost
```

## Conventions
- Never commit API keys; use `.env` locally (`.env.example` checked in).
- Keep prompts in `app/prompts/*.md`, not inline strings.
- Rules are pure functions: `def check(extraction: FormModel) -> list[Issue]`.
- Messages are written for a tissue-bank QA reviewer: plain English, name the exact section/row/field.
- Retry Gemini once on invalid JSON / 5xx; time out at 60 s and return a clear error to the UI.
- Don't store uploaded PDFs beyond the request.

## Open questions (confirm with RegenMed organizers)
1. QS-F-049 dates: is `11-27-24` (dashes) acceptable as MM/DD/YY, or only slashes?
2. MP-F-023: what are "shaded" rows exactly on the clean template (confirm from blank copies)?
3. Lot Log: should a voided row need initials + date on the strike-through to pass?
