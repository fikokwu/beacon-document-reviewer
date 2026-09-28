# Sprint 7 Report — Polish, Speed, Void Flag

**Date:** 2026-09-26, 12:38–12:43 EDT
**Goal:** Team-requested polish (colour, Beacon footer), a faster pipeline, split Discard files, and a flag instead of a fail for the ambiguous void.
**Result:** ✅ Goal met. **11/11 fixtures match on the live accuracy scorecard.**

## Summary (plain English)
- The page uses the new orange, and the footer now introduces the tool as **Beacon**.
- The Discard sample is split into three separate PDFs (one form each). If someone uploads a PDF with several forms, the report shows one card per form.
- The Lot Log no longer fails because of the empty Sieve row next to a crossed-out row. It's flagged for a person to check instead.
- Everything is a bit faster again, and a new scorecard proves every test file still gives the right answer.

## Live accuracy scorecard (`python -m scripts.scorecard`)
| Fixture | Result | Time | Match |
|---|---|---|---|
| Lot Log sample | PASS (Sieve row 16 flagged) | 25 s | ✅ |
| Discard form 1 / 2 / 3 of 3 (split files) | PASS | 7–10 s | ✅ |
| Discards (3 forms in one PDF) | PASS | 9 s (was 16 s) | ✅ |
| Discards variant (2 cells whited out) | FAIL, 2 errors | 11 s | ✅ |
| QS-F-049 sample / blank | PASS / FAIL 20 | 11 s / 9 s | ✅ |
| MP-F-023 sample / blank | PASS / FAIL 45 | 15 s / 9 s | ✅ |
| Lot Log blank | FAIL 205 | 21 s | ✅ |

**11/11 match.**

## Delivered
- Orange `#e15f09`; centred Beacon footer
- 3 split Discard PDFs + expected results
- Multi-form report cards (`ReviewResult.forms[]`)
- Speed: Flash form detection (8/8 correct), parallel page rendering, unused columns dropped
- `LOT-VOID-ADJACENT` rule (+2 tests); Lot Log baseline updated
- Scorecard script (B-17)

## Quality
126 offline tests pass. Lint and build are clean.

## Next sprint (team-agreed)
**Highlight the problem areas on the page images** (B-20).
