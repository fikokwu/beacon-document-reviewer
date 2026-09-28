# Sprint 6 Report — Bonus Objective: Tissue Discard Form (MP-F-018)

**Date:** 2026-09-26, 12:17–12:21 EDT
**Goal:** Detect and validate the fourth form type, the Discard Form, the same way as the original three.
**Result:** ✅ Goal met. Correct on the sample and on a synthetic variant with errors.

## Summary (plain English)
The app now recognises the Tissue Discard Form and applies its six rules. The sample PDF actually contains three separate discard forms, one per page, so the app checks each page as its own form and says which page each problem is on. The sample passes. When we deliberately blanked out a signature on page 1 and an X box on page 2, the app caught both and pointed to the exact page and row.

## Rules (from the bonus write-up)
| ID | Check |
|---|---|
| `DISC-HDR-BLANK` | Donor #, Discard Authorized By/Date, Reason for Discard not blank |
| `DISC-AUTH-BYDATE` | Authorized By/Date has initials and a date |
| `DISC-STATUS` | Exactly one Tissue Status box checked |
| `DISC-STATUS-GRAFT` | Graft IDs listed → Unreleased/Released Packaged; N/A (or a dash) → Unprocessed/In Processing |
| `DISC-ROW-X` | X box marked for every listed tissue |
| `DISC-BOTTOM-BLANK` | No bottom field blank (N/A is fine) |

## Live results (Gemini 3.1 Pro)
| File | Expected | Result | Time |
|---|---|---|---|
| `22043 Discards.PDF` (3 forms) | PASS | ✅ PASS, detected as MP-F-018.005 | 16 s |
| Variant: p1 Confirmed By + p2 row 1 X whited out | FAIL ×2 | ✅ "Confirmed By is blank" (page 1); "Row 1 (1 Right Femur): X (confirmed) is blank" (page 2) | 13 s |

## Decisions
- **ADR-015:** several forms per PDF; a dash counts as N/A; "one of" means exactly one; classify prompt fixed (it used to tell the model to ignore MP-F-018).

## Quality
- 121 offline tests pass (16 new). Lint and build are clean.

## Still open
- Issue #30: is Lot Log Sieve row 16 voided?
- Deploy this sprint to the live URL (next step).
