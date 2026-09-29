# Sprint 3 Report — API + UI

**Date:** 2026-09-26, 11:22–11:32 EDT
**Goal:** A user uploads a PDF in a browser and gets a clear report.
**Result:** ✅ Goal met. Tested end to end in a real browser with real forms.

## Summary (plain English)
The app now has a web page. You drag in a scanned form, see a progress message while it's read, and get a report: which form it is, a big PASS or FAIL, a one-line summary, and each problem listed by page, section, row and field. It works on phones too. Errors (wrong file, AI busy) show a friendly message with a "Try again" button.

## Delivered
| Backlog | Item | Status |
|---|---|---|
| B-12 | `POST /api/review`: 400 for a bad upload, 503 for an AI failure; FastAPI serves the built page | ✅ |
| B-13 | React UI: drag-and-drop, progress with elapsed time and step messages, form badge, PASS/FAIL/Unsupported banner with summary, issues grouped by page/section, Needs confirmation and Notes groups, error panel | ✅ |
| B-21 (part) | Download result as JSON | ✅ (PDF report still open) |

## Browser test (headless Chrome, real server, real Gemini)
| Form | Result | Time |
|---|---|---|
| QS-F-049 sample (phone width, 390 px) | ✅ PASS, "Passed all checks…" | 30 s |
| Lot Log sample | ✅ FAIL: Sieve row 16 Load # and Sterilization Date; row 15 voided note | 97 s |

Screenshots: `docs/screenshots/` (upload, progress, PASS on mobile, FAIL Lot Log).

## Quality
- 93 offline tests pass (5 new API tests). Lint is clean. The TypeScript build is clean.
- CI now also builds the frontend.

## Fixes found by looking at the real page
- The note row repeated "Page 2" → fixed.
- The summary nested brackets → now reads "2 issues to fix before review in Page 2 – Item (right table)."

## Risks
| Risk | Plan |
|---|---|
| The Lot Log takes ~100 s | The progress message tells the user; the demo script should upload a 1-page form first |
| No deployment yet | Sprint 4 now |

## Next — Sprint 4: Deploy (target 12:15)
Dockerfile (multi-stage: build the frontend, then Python), Cloud Run in `northamerica-northeast2`, the Gemini key in Secret Manager, public URL smoke test.
**Needed from you:** `gcloud auth login` on this machine, and confirm the GCP project to use (AI Studio project <project-number> has billing).
