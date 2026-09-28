# Sprint 1 Report — Rule Engine

**Date:** 2026-09-26, 10:15–10:45 EDT
**Goal:** Deterministic, unit-tested checks for all three forms, with no AI involved yet.
**Result:** ✅ Goal met.

## Summary (plain English)
We built the "judge" half of the app. Given a structured record of what's written on a form, it now decides exactly which fields are missing or wrong and writes a clear message for each. It covers all 14 checks from the challenge. We tested it with 61 automated tests, all passing, without calling the AI. Next sprint builds the "reader" half: the AI turns a scanned PDF into that structured record.

## Delivered
| Backlog | Item | Status |
|---|---|---|
| B-01 | Shared data models (`FieldValue`, `SignOff`, `Issue`, `ReviewResult`) | ✅ |
| B-02 | Helpers: N/A detection, blank/filled/illegible, MM/DD/YY validator, sign-off checks | ✅ |
| B-03 | MP-F-023 schema + 5 rules + 11 tests | ✅ |
| B-04 | QS-F-049 schema + 3 rules + 10 tests | ✅ |
| B-05 | Lot Log schema + 5 rules + 8 tests | ✅ |
| B-06 | Team baseline for the 3 samples (no official answer key) | ✅ draft, PO to confirm |
| B-07 | Plain-English review of messages | ⏳ PO |

## Quality
- **Tests:** 61 passed (helpers 30, MP-F-023 11, QS-F-049 10, Lot Log 8, registry 2), in 0.2 s, no network
- **Lint:** ruff clean
- **Covered edge cases:** `0`/`Ø` count as filled, tally marks, all N/A spellings, voided rows, shaded rows, half-filled By/Date cells, 4-digit years, DD/MM order, impossible dates (Feb 30, Feb 29 in a non-leap year), mixed separators, missing QS items, illegible → needs confirmation

## Decisions made
- **ADR-006:** unreadable ink goes to "needs confirmation" and never fails a form. The transcribed text wins over the model's status label. A missing QS item is flagged.
- **ADR-007:** no answer key was provided, so we use a team baseline from a human read.

## Risks and open items
- The date rule requires 2-digit month and day (per spec), so `9-25-24` is flagged. That could look strict to judges. It's easy to relax if the organizers say so.
- The four organizer questions are still open (sprint-0.md).

## Next — Sprint 2: AI extraction (target done by ~12:00)
PDF rendering and rotation, Gemini client, classify and extract prompts, first live run on the 3 samples compared to the baseline.
**Needed from the team now:** a Gemini API key (from AI Studio), the current Pro model name, and a GCP project with billing, for the Cloud Run deploy in Sprint 4.
