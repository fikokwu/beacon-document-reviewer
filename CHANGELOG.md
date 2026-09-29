# Changelog

## [Unreleased]

### Sprint 10 — Demo files (2026-09-26)
- `demo-files/`: 10 files with issues (2–3 per form) + 6 good-but-poor-quality scans, with expected outcomes
- New variants: Lot Log Pulse Lavage manufacturer blank; faint/noisy/low-res/sideways quality variants for every form
- Live scorecard: **29/29** (7 new files verified)

### Sprint 9 — Robustness + issue highlighting + duplicate names (2026-09-26)
- **Issue highlighting:** page previews with numbered orange boxes on each problem cell. Click an issue to jump to its box. Boxes arrive ~3–6 s after the result via `/api/locate` (ADR-017)
- **Robustness:** 11 new synthetic variants (other error types, rotated 90°/180°, faint low-res scan). **Live scorecard 22/22**
- **LOT-DUP-NAME:** duplicate item names in the Lot Log page-1 tables need distinct bracketed labels (flag). The sample flags the plain "Gloves" row
- Wider two-column results layout on large screens
- 12 new tests (138 offline)
- **Every strike-through must be initialed and dated (all forms):** new `corrections[]` extraction and `GDP-CORRECTION-UNSIGNED` rule; Lot Log `LOT-VOID-UNSIGNED` back (ADR-018)
- Duplicate-name rule ignores unused rows (all columns N/A)
- Automatic fallback to Gemini 3.5 Flash when Pro is rate-limited (25 req/min)
- Scorecard accepts name filters; **22/22 live**; 147 offline tests

### Sprint 8 — Beacon identity (2026-09-26)
- App renamed **Beacon Document Reviewer** (header and browser tab). New lighthouse icon (`frontend/public/beacon.svg`), also used as the favicon
- Upload box (and progress screen) centred vertically on the page, with the tagline directly beneath it
- Removed: "Internal" tag next to the title, "form type is detected automatically" hint, "Beacon" in the footer. The green "Internal tool" bar and the footer tagline stay

### Sprint 7 — Polish, speed, void flag (2026-09-26)
- Orange changed to `#e15f09`. Footer is now **Beacon**, "RegenMed's document reviewer that pre-screens processing forms to prevent errors and keep records accurate." (centred)
- Discard sample also split into 3 single-form PDFs (`tests/fixtures/samples/22043 Discard - form N of 3.pdf`)
- Multi-form PDFs show one card per form with its own PASS/FAIL (ADR-016)
- Faster: Flash model for form detection, pages rendered during detection, unused columns dropped (ADR-016)
- `LOT-VOID-ADJACENT`: an empty row next to a voided row is flagged, not failed. The Lot Log sample now passes, with the Sieve row flagged (ADR-016, issue #30)
- `scripts/scorecard.py` live accuracy scorecard: **11/11 fixtures match** (B-17)
- 126 offline tests

### Sprint 6 — Bonus: Tissue Discard Form MP-F-018 (2026-09-26)
- New form type **MP-F-018 Tissue Discard Form**: detection, schema, prompt, 6 rules; several forms per PDF, each page checked on its own (ADR-015)
- Classify prompt no longer ignores MP-F-018; title fallback "Discard Form"
- Live: sample → PASS in 16 s; synthetic variant → both whited-out errors caught with page and row
- `tests/make_variants.py` synthetic-variant generator (B-16 started)
- 16 new tests (121 offline)

### Sprint 5 — Speed & branding (2026-09-26)
- **About 3× faster on every form:** compact string cells on the wire, and the Lot Log split into 3 parallel calls (ADR-014). QS 14 s, MP-F-023 16 s, Lot Log 25 s. All 6 fixtures still correct.
- Branding: RegenMed orange `#ff5601` and green `#62783f`, Montserrat font (as on regenmed.ca)
- "Internal tool · RegenMed staff use only" bar and "Internal" tag in the header
- Removed: subtitle, "Supports… / not stored" footer text, Download JSON button, time taken and the elapsed-seconds counter
- 12 new tests for compact cell parsing (105 offline tests)

### Sprint 4 — Deploy (2026-09-26)
- Live on Cloud Run: <your-cloud-run-url>
- Multi-stage `Dockerfile` (Node build → Python 3.12-slim, non-root) and `.dockerignore`
- Gemini key in Secret Manager; APIs enabled; build service account granted `roles/run.builder`
- `docs/DEPLOY.md` runbook; ADR-013; OpenCV/NumPy dropped from runtime deps

### Sprint 3 — API + UI (2026-09-26)
- `POST /api/review`: PDF upload → `ReviewResult`; 400 for bad files, 503 for AI failures; frontend served by FastAPI
- React + Vite + TypeScript + Tailwind page: drag-and-drop upload, live progress with elapsed time, detected-form badge, PASS/FAIL/Unsupported banner with summary, issues grouped by page and section, needs-confirmation and notes groups, JSON download, friendly error panel
- Summary wording: "N issues to fix before review in <section>"
- CI builds the frontend too
- 5 API tests (93 offline tests total)

### Sprint 2 — AI extraction (2026-09-26)
- `pdf_utils`: upload validation (type, size, pages, password, damage), grayscale rendering, rotation
- `gemini_client`: JSON-schema output with every field required, retry once on bad JSON/5xx, timeout, clear user-facing errors
- Prompts: classify + shared transcription conventions + one per form
- `pipeline.review_pdf`: classify → resolve form (code, then title fallback) → extract → rules → `ReviewResult`
- `scripts/review_pdf.py` dev CLI
- 20 new offline tests (fake Gemini client) + 3 live tests against the team baseline (skipped without a key)
- ADR-008
- Live runs: organizers' proxy is text-only → own AI Studio key (ADR-009); billing enabled, Gemini 3.1 Pro
- Faster extraction: optional rare fields, no `box_2d` by default, Lot Log pages extracted in parallel (ADR-010); per-call timing logs
- Organizer answers applied: any date separator and single-digit month/day accepted (ADR-004); voided rows not checked, info only (ADR-012, supersedes ADR-011); both columns required (ADR-003)
- Lot Log prompt requires every row; new `LOT-ROW-UNREAD` safety net for rows the AI skips (ADR-012)
- Blank templates added as fixtures, with expected results
- Friendlier "AI service is busy" error on 503s
- Summary line on every result, including "Passed all checks. No missing or inconsistent entries were found."

### Sprint 1 — Rule engine (2026-09-26)
- Extraction schemas for MP-F-023, QS-F-049 and MP-F-021, plus shared `FieldValue`, `SignOff`, `Issue`, `ReviewResult`
- Rule helpers: N/A detection, blank/filled/illegible logic, MM/DD/YY date validator, By/Date sign-off checks
- All 14 rule IDs implemented as pure functions; form registry and `build_result`
- 61 unit tests (no API calls)
- Team baseline expected results for the 3 samples (no official answer key)
- ADR-006 (uncertain reads), ADR-007 (team baseline)

### Sprint 0 — Setup & discovery (2026-09-26)
- Repo structure, `.gitignore`, `.env.example`, `requirements*.txt`, `pyproject.toml`
- Minimal FastAPI app with `GET /api/health` and its test
- GitHub Actions CI: ruff + `pytest -m "not live"`
- Sample PDFs moved to `tests/fixtures/samples/`, challenge write-up to `docs/challenge/`
- Docs: README, project plan and backlog, plain-English rule catalog, architecture, decision log, sample analysis, business case draft, user guide draft, contributing guide
