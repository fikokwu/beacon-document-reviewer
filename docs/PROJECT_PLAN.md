# Project Plan

## Team and roles

| Person | Role | Owns |
|---|---|---|
| Software engineer | Tech lead | Architecture, backend, AI integration, deployment, code review |
| Economics student | Product owner and QA lead | Requirements and rule interpretation, test cases and expected results, business case, user guide, demo and pitch, questions for organizers |

Both of us review each other's work. The engineer reviews docs for technical accuracy. The product owner reviews every rule and its message for plain-English clarity and faithfulness to the challenge.

## How we'll be judged

Three panel judges review every project; the challenge sponsor (RegenMed) reviews projects in its challenge. There's a winner and a runner-up per challenge. **Someone must be able to open the link and start using it without instructions.** A phone number is required in case the video won't play.

| Criterion | How Beacon addresses it | Evidence |
|---|---|---|
| **Performance: accuracy** | AI only reads; tested Python rules judge; unreadable → "needs confirmation" | Live scorecard 11/11 (`scripts/scorecard.py`) |
| **Performance: speed** | Compact outputs, parallel pages/parts, Flash detection | 7–25 s per form |
| **UI/UX** | One-screen flow, drop a PDF and get PASS/FAIL, issues by page/section/row/field; no instructions needed | Screenshots in `docs/images/` |
| **Interesting features** | Auto form detection (4 types), multi-form PDFs, void handling, *next:* issue highlighting on the page image | Sprints 6–9 |
| **Relevance to RegenMed** | Catches the routine misses that send ~50% of forms back; keeps the two-person review | `docs/BUSINESS_CASE.md` |

## How we work

- **Short sprints** (a half day to a day during the hackathon). Each sprint has a goal, a backlog slice and a short review/retro logged in [docs/sprints/](sprints/).
- **Backlog** lives in the table below and is mirrored as GitHub Issues.
- **Branch → PR → CI green → review → merge to `main`.**
- **Definition of Done** (every item):
  1. Code merged to `main` with CI passing
  2. Tests for new rules and logic
  3. Relevant docs updated (technical and plain-English)
  4. CHANGELOG entry
  5. Deployed build still works (from Phase 4 onward)

## Timeline

**MVP deadline: 2026-09-26, 2:00 pm.** MVP = Phases 1–4 (rules, AI extraction, API + UI, deployed URL). Phases 5–6 run after the MVP if time allows.

## Phases

| Phase | Goal | Key outputs | Status |
|---|---|---|---|
| **0. Setup & discovery** | Understand the challenge, set up the repo and team process | Repo, CI, docs skeleton, sample analysis, backlog | ✅ Done |
| **1. Rule engine** | Deterministic checks for all 3 forms, fully unit-tested, no AI yet | `schemas/`, `rules/`, `test_rules_*.py` | ✅ Done |
| **2. AI extraction** | PDF → images → classify → extract JSON with Gemini | `pdf_utils.py`, `gemini_client.py`, prompts, live tests on samples | ✅ Done (5/5 live forms match baseline) |
| **3. API + UI** | Upload a PDF, get a clear report | `POST /api/review`, React UI | ✅ Done |
| **4. Deploy** | Public URL on Cloud Run | Dockerfile, Secret Manager, deployed URL | ✅ Done (live) |
| **5a. Speed & branding** | ~3× faster, RegenMed look | Compact cells, parallel parts, brand colours/font | ✅ Done |
| **5b. Bonus: Discard Form** | 4th form type MP-F-018 | Schema, prompt, 6 rules, variant generator | ✅ Done |
| **5. Hardening** | Generalize to unseen forms | Blank templates and synthetic variants, accuracy report, edge cases | ⬜ |
| **6. Polish & pitch** | Win the demo | Issue highlighting on page images, report download, pitch deck, demo script | ⬜ |

We deploy early (Phase 4 can start as soon as Phase 3 has a thin slice) so we never end up with a "works on my machine" demo.

## Backlog

Priority: **P0** = required by the challenge, **P1** = strong differentiator, **P2** = nice to have.

| ID | Item | Phase | Pri | Owner |
|---|---|---|---|---|
| B-01 | Common schemas: `FieldValue`, `Issue`, `ReviewResult` | 1 | P0 | Eng |
| B-02 | Rule helpers: `is_blank`, `is_na`, `parse_date_mmddyy`, `has_initials` | 1 | P0 | Eng |
| B-03 | MP-F-023 schema + rules + tests | 1 | P0 | Eng |
| B-04 | QS-F-049 schema + rules + tests (incl. date format) | 1 | P0 | Eng |
| B-05 | MP-F-021 Lot Log schema + rules + tests | 1 | P0 | Eng |
| B-06 | Team baseline for each sample (`tests/fixtures/expected/*.json`). No answer key was provided (ADR-007) | 1 | P0 | PO |
| B-07 | Review every rule message for plain English | 1 | P0 | PO |
| B-08 | PDF rendering + rotation normalization | 2 | P0 | Eng |
| B-09 | Gemini client (JSON schema, retry, timeout) | 2 | P0 | Eng |
| B-10 | Classification prompt + UNKNOWN handling | 2 | P0 | Eng |
| B-11 | Extraction prompts per form | 2 | P0 | Eng |
| B-12 | `POST /api/review` end-to-end pipeline | 3 | P0 | Eng |
| B-13 | React UI: upload, form badge, PASS/FAIL, grouped issues | 3 | P0 | Eng |
| B-14 | Dockerfile + Cloud Run deploy + Secret Manager | 4 | P0 | Eng |
| B-15 | Add blank templates; confirm shaded rows on MP-F-023 | 5 | P0 | PO |
| B-16 | Synthetic variant generator (`tests/make_variants.py`) | 5 | P1 | Eng |
| B-17 | Accuracy scorecard across all fixtures | 5 | P1 | PO + Eng |
| B-18 | "Needs confirmation" group (illegible, ink-check disagreement) | 5 | P1 | Eng |
| B-19 | Ink-density double-check for "blank" cells | 5 | P2 | Eng |
| B-20 | Issue boxes drawn on page thumbnails | 6 | P1 | Eng |
| B-21 | Download report (PDF/JSON) | 6 | P2 | Eng |
| B-22 | Business case, user guide, pitch deck, demo script | 6 | P0 | PO |
| B-23 | Send open questions to organizers and log the answers | 0–5 | P0 | PO |

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| AI misreads handwriting or a blank cell | False flags or missed issues | "Needs confirmation" group, ink-density cross-check, `temperature=0`, strict schema |
| Judges' forms differ from samples (rotation, extra rows, other scanners) | Rules break | Read row names from the page and never hard-code them; test on blank templates and synthetic variants |
| Spec ambiguity ("or" vs "and") | Judges disagree with our result | Documented in DECISIONS.md, configurable, asked organizers |
| Gemini latency, outage or quota | Demo fails | Retry once, 60 s timeout, clear error; keep a recorded demo as a backup |
| API key leak | Security | Secret Manager, `.env` git-ignored |
