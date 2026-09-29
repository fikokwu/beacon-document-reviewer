# Decision Log (ADRs)

Short records of design decisions: what we chose, why, and what we gave up. Add new ones at the bottom. Don't edit accepted ones. Supersede them with a new entry instead.

Format: **Status** is Proposed, Accepted or Superseded.

---

## ADR-001 — "Gemini reads, Python judges"
**Status:** Accepted (Phase 0)

**Context.** We need to pick up hand-written values from scanned forms, and the judges need to trust and understand every flag.

**Decision.** A vision model (Gemini) classifies the form and transcribes fields into a strict JSON schema. It never decides pass or fail. Deterministic Python rules make every pass/fail decision, and each rule is unit-tested.

**Consequences.** + Reproducible, explainable, testable without API calls, cheap to change rules. − Extraction quality limits accuracy, so we add "needs confirmation" and an optional ink-density cross-check.

## ADR-002 — Single container on Google Cloud Run
**Status:** Accepted (Phase 0)

FastAPI serves both the API and the built React frontend from one Docker image on Cloud Run. The Gemini key lives in Secret Manager. This gives one URL and one deploy, with no CORS and no second service to keep alive during judging.

## ADR-003 — "Or" in the challenge text is enforced as "both must be filled"
**Status:** Accepted and **confirmed by organizers** (2026-09-26): assume both are required

**Context.** The challenge text says *"The column for either # Produced or # Packaged must not be blank"* (MP-F-023) and *"Lot or Qty Used must not be blank"* (Lot Log RegenMed and Packaging tables; "Load # or Sterilization Date" on page 2). Read literally, a row could pass with only one column filled.

**Decision.** We read "X or Y must not be blank" as "**neither** may be blank", so both are required. Each column gets its own issue so the reviewer sees exactly which one is missing.

**Why.** The tool is a pre-review safety net. A half-filled row is almost certainly a miss (you can't have packaged a graft without recording a count). A false flag costs the reviewer a few seconds. A missed blank costs a correction cycle.

**Revisit if** organizers say otherwise. The rule would change in one place (a config flag), and we'd update the tests to match.

## ADR-004 — Date separator strictness is configurable
**Status:** Accepted and **confirmed by organizers** (2026-09-26): any separator is fine, only the order matters. Single-digit month/day are accepted too.

QS-F-049 requires MM/DD/YY. The samples use `11-27-24` and `12.05.24`. `STRICT_DATE_SEPARATOR=false` (the default) accepts `/`, `-` and `.`. Setting it to `true` requires `/`. Format errors we always flag: 4-digit year, DD/MM order where detectable, impossible dates.

## ADR-005 — Python 3.12 managed with `uv`
**Status:** Accepted (Phase 0)

The dev machine had only the system Python 3.9. We use `uv` to pin 3.12 locally (`.python-version`) so the dev and Docker environments match.

## ADR-006 — How rules treat uncertain or inconsistent reads
**Status:** Accepted (Sprint 1)

- **Illegible → "Needs confirmation", never a failure.** When Gemini sees ink it can't read, the rule emits a `warning`. `build_result` moves every warning into `needs_confirmation`, and warnings don't affect PASS/FAIL. A reviewer glances at them. We don't guess.
- **`raw` beats `status`.** If the model says `status="blank"` but transcribed `raw="0"`, we treat the cell as filled. If it says `filled` with an empty `raw`, we treat it as blank. N/A is detected from either the status or the text (`N/A`, `NA`, `N\A`, `N.A.`).
- **By/Date cells:** completely empty → the section's "blank" rule. Half-filled → the "By/Date" rule, with a message saying exactly which half is missing.
- **Missing QS-F-049 item** (the model returned no row for item *n*) → flagged as an error rather than silently passing.

## ADR-007 — Team baseline instead of an answer key
**Status:** Accepted (Sprint 1)

RegenMed didn't provide expected results for the samples. We wrote our own **team baseline** (`tests/fixtures/expected/*.json`) from a careful human read, marked `"source": "Team baseline…"`. It's used to score end-to-end accuracy and must be re-checked by the product owner. It's our reading of the rules, not ground truth.

## ADR-008 — Extraction reliability choices
**Status:** Accepted (Sprint 2)

- **Every schema field is required when sent to Gemini** (`to_gemini_schema`). If the model could skip a field, it would default to "blank" and we'd raise a false flag. `$ref`s are inlined and defaults stripped for compatibility.
- **Orientation comes from the classifier.** The classify call returns a clockwise rotation per page. Extraction images are re-rendered upright. `/Rotate` flags in the PDF (the Lot Log sample uses 270°) are already applied by PyMuPDF. This handles pages physically scanned sideways without extra OCR dependencies.
- **Two-tier form detection.** The bottom-right code is read with a tolerant pattern (`MPF021`, `mp - f - 023`). If it's unreadable, distinctive title phrases are used ("Tissue Open Checklist", "Disposition Statement", "Lot Log"). Anything else → UNKNOWN, and no rules run.
- **Grayscale renders.** The forms are black-and-white scans, so grayscale PNGs are smaller and upload faster with no loss of information.
- **Timeout and thinking are configurable** (`GEMINI_TIMEOUT_S`, default 60 per spec; `GEMINI_THINKING_LEVEL`), so we can tune latency once we measure it with the real model.

## ADR-009 — Use our own Google AI Studio key, not the organizers' proxy
**Status:** Accepted (Sprint 2). Organizer confirmation requested.

**Context.** The organizers provided a Gemini proxy (its documentation isn't included in the public repo). Its `POST /api/generate` accepts `contents` as a **text string only**, with no image parts. We confirmed this against the proxy's OpenAPI spec and with a test call. Our forms are image-only handwritten scans, so a text-only model can't read them. The proxy also has a quota (500 requests for our key), and failed calls count against it.

**Options considered.** (1) Our own AI Studio key: vision works, no code changes. (2) Proxy plus local OCR/computer vision: large effort, weak on handwriting, high risk before the 2 pm MVP. (3) Wait for organizers.

**Decision.** Option 1. `GEMINI_API_KEY` is a personal Google AI Studio key. The proxy key is kept in `.env` as `HACKATHON_API_KEY` and isn't used. The product owner is asking the organizers to confirm this is allowed.

**Consequences.** + Keeps ADR-001 (vision extraction) intact. − Depends on a personal key's free-tier rate limits. If the organizers object, fallback is option 2.

## ADR-010 — Faster extraction: smaller outputs, parallel pages
**Status:** Accepted (Sprint 2)

**Context.** The first live Lot Log run took 146–293 s. Gemini wrote about 30,000 output tokens because every one of ~250 cells repeated every field, and the free tier added queueing.

**Decision.**
- Only `raw` and `status` are required per cell. Rarely used fields (`struck_through`, `tally_count`, `page`, `void_initials`, `void_date`) are optional and default sensibly. `box_2d` isn't requested unless `GEMINI_REQUEST_BOXES=true`.
- Multi-page forms (`per_page=True`, currently the Lot Log) are extracted **one page per call, in parallel**, then merged: lists are concatenated and the first non-empty scalar wins. Page numbers are stamped from the call, not trusted from the model.
- Billing is enabled on the Google project (paid tier): Gemini 3.1 Pro is available, with no free-tier queueing and higher rate limits.

**Trade-off.** Per-page calls can't see the other page. That's fine for the Lot Log, whose tables don't span pages.

**Measured (Gemini 3.1 Pro, paid tier, `thinking_level=low`):** classify 4–6 s, QS-F-049 31 s, MP-F-023 50 s, Lot Log pages 54–132 s (run in parallel). With the default thinking level, some calls stalled for more than 240 s. Defaults are now `GEMINI_THINKING_LEVEL=low` and `GEMINI_TIMEOUT_S=150` per call. The spec's 60 s is too tight for dense handwritten tables.

## ADR-011 — Voided rows must be initialed and dated
**Status:** Superseded by ADR-012 (organizers answered that voided rows are not checked)

A struck-through row needs initials and a date on the strike-through, per good documentation practice. If both are present → `LOT-VOIDED-ROW` (info: who and when). If either is missing → `LOT-VOID-UNSIGNED` (error). If they're unreadable → needs confirmation.

## ADR-012 — Voided rows are not checked; skipped rows are surfaced
**Status:** Partly superseded by ADR-018 (voids must now be initialed and dated). The skipped-row safety net still applies.

- Organizers confirmed that **voided rows are not checked**. `LOT-VOID-UNSIGNED` is removed. Voided rows produce only a `LOT-VOIDED-ROW` info note, which includes who and when if written.
- **The skipped-row problem.** In live testing, Gemini sometimes silently omitted a printed row whose cells were empty. That's exactly the Lot Log sample's deliberate error (right table, "Sieve", row 16). Two fixes:
  1. The Lot Log prompt now requires one entry for **every** body row, including empty ones.
  2. The `LOT-ROW-UNREAD` safety net: any gap in a table's row numbers is listed under "needs confirmation", so a skipped row can never pass silently.

## ADR-013 — Cloud Run deployment settings
**Status:** Accepted (Sprint 4)

- **Project:** `<your-gcp-project>`, the same project as the Gemini key, so billing is in one place.
- **`--timeout 300`:** the two-page Lot Log takes about 100 s end to end. The Cloud Run default (300 s) is kept explicit so nobody lowers it by accident.
- **`--min-instances 1`:** no cold start while judges test. Costs a little per hour. Set it to 0 after the event (DEPLOY.md).
- **`--max-instances 3`:** caps the cost and the Gemini spend if the URL gets hammered.
- **1 GiB memory:** PyMuPDF renders pages at 200 DPI in memory.
- **Lean image:** OpenCV/NumPy removed from `requirements.txt` until the optional ink check (B-19) needs them.
- **Non-root container user**, with the secret never baked into the image.

## ADR-014 — Compact string cells and split dense pages (speed for every form)
**Status:** Accepted (Sprint 5)

**Context.** Timing logs showed latency is almost entirely **output tokens** (decode time), not pages or input size. Each cell was a JSON object (`{"raw": "2", "status": "filled"}`), and the densest page (Lot Log page 2) wrote about 6,000–14,500 tokens.

**Decision.**
1. **Compact wire format.** Gemini returns every cell as a **plain string**: `""` for empty, N/A as written, `"[illegible]"` for unreadable ink, tally marks as characters. `FieldValue` parses the string back (`parse_cell`) into status, raw and tally count, so the rules are unchanged. Correction flags are dropped from the wire, since no rule uses them.
2. **Dense pages are split into parallel calls** (`FormSpec.parts`). The Lot Log runs as 3 simultaneous calls: page 1; page 2 left table; page 2 right table plus packaging. It falls back to one call per page if the page count differs.
3. Boolean flags that are almost always false (`row_voided`, `marked_na`, `shaded`) are optional, so the model omits them.

**Result (live, Gemini 3.1 Pro):** QS-F-049 31 → 14 s, MP-F-023 50 → 16 s, Lot Log 86–97 → 25 s, blanks 10–21 s. All 6 fixtures are still correct.

## ADR-015 — Discard Form (MP-F-018): several forms per PDF, dash = N/A, one status only
**Status:** Accepted (Sprint 6, bonus objective)

- **Several forms in one PDF.** The sample holds 3 discard forms (one per page, same donor). The schema is `DiscardExtraction.forms[]`. Each page is extracted in its own parallel call and checked independently, and every issue carries its page.
- **Dash = N/A.** Staff draw a line in the Graft ID column instead of writing N/A (sample page 2). For the "Graft IDs are N/A → Unprocessed/In Processing" rule, a dash-only cell counts as N/A.
- **"One of the Tissue Status boxes must be checked"** is enforced as **exactly one**. None checked, or several checked, is an error.
- **Detection.** The classify prompt used to tell the model to ignore "MP-F-018" (a reference inside the QS-F-049 body text). It now says to ignore only body-text references; the bottom-right code MP-F-018 identifies the Discard Form. Title fallback: "Discard Form".
- **Signatures count as initials** (sample page 3: "E. Widdfield 02/10/23").

## ADR-016 — Flag (don't fail) empty rows next to a void; faster detection; per-form cards
**Status:** Accepted (Sprint 7)

- **Void-adjacent rows.** The team believes one strike-through on the Lot Log sample covers Sieve rows 15 **and** 16 (issue #30). General rule: a row that is **completely empty** and **directly next to a voided row** → `LOT-VOID-ADJACENT` (needs confirmation), not an error. A partly filled row still fails. The Lot Log sample baseline is now PASS with that flag.
- **Speed.**
  - Form detection uses `GEMINI_CLASSIFY_MODEL` (default `gemini-3.5-flash`). It was 8/8 correct in testing and faster than Pro.
  - Full-resolution pages render **while** detection runs, and are re-rendered only if a page needs rotating.
  - Columns no rule reads were dropped from the schemas: MP-F-023 FRZ/FD, Irradiated and Comments; QS-F-049 Graft IDs and the disposition signatures; Discard Storage Location.
- **Multi-form PDFs.** `FormSpec.form_labels` + `ReviewResult.forms[]`: one `FormResult` per form (label, page, PASS/FAIL, summary, issues). The UI shows one card per form. The overall summary reads "This PDF contains 3 separate forms: 1 passed, 2 need fixing."

## ADR-017 — Robustness variants, issue highlighting, duplicate item names
**Status:** Accepted (Sprint 9)

- **Robustness.** `tests/make_variants.py` now makes 12 variants covering every major rule plus sideways (90°), upside-down (180°) and faint 72-DPI scans. Live scorecard: **22/22**. Each error variant produced exactly its one expected error, with no false alarms.
- **Highlighting is a separate, optional step.** `/api/review` returns upright JPEG page previews and stays fast. The browser then calls `/api/locate` with the same PDF and the issue list, and a Flash model returns a bounding box per issue (one call per page, in parallel, capped at 40 issues). Boxes appear a few seconds after the result. If locating fails, the report is unaffected. We didn't ask for boxes during extraction, because that roughly doubled extraction time (ADR-010).
- **LOT-DUP-NAME** (team requirement): repeated base names in the page-1 Item and RegenMed Item tables need distinct bracketed labels. Names are normalised for case, spacing and subscript digits. Plain repeats with all-different lots are exempt. It's a **flag** (needs confirmation), not a failure, following the team's "flag, don't fail" wording. It's one word to change to `error`.

## ADR-018 — Every strike-through must be initialed and dated; unused duplicates; rate-limit fallback
**Status:** Accepted (team decision, 2026-09-26). Supersedes the "voided rows are not checked" part of ADR-012.

- **All forms:** anything crossed out, whether a corrected value or a voided row, must carry **initials and a date**. Extraction now returns a `corrections[]` list per form (location, struck value, initials, date), and the shared `correction_issues` rule raises `GDP-CORRECTION-UNSIGNED` (error). Lot Log voided rows use `LOT-VOID-UNSIGNED` (error) or `LOT-VOIDED-ROW` (info when signed). Duplicate reports from parallel page-part calls are merged.
- **Duplicate names:** a duplicate row whose other columns are all N/A (any spelling) means the item wasn't used. It's ignored and can't cause clashes.
- **Rate limits:** Gemini 3.1 Pro allows 25 requests/min on this account (hit during scorecard runs). On a 429, the client retries once on `GEMINI_FALLBACK_MODEL` (default `gemini-3.5-flash`, separate quota), so simultaneous judges don't see errors.
- **Live scorecard:** 22/22 after these changes.
