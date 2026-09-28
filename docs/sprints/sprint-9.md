# Sprint 9 Report — Robustness + Issue Highlighting + Duplicate Names

**Date:** 2026-09-26, 13:19–13:32 EDT (deadline extended to 2:30 pm)
**Goal:** Prove accuracy on unseen-style files, add the most visible feature (highlighting), and add the team's duplicate-name rule.
**Result:** ✅ Goal met. **Live scorecard 22/22.**

## Summary (plain English)
- **Robustness:** we made 11 new test copies of the forms with different kinds of mistakes, plus sideways, upside-down and faint scans. The app got every one right, catching exactly the planted mistake with no false alarms.
- **Highlighting:** after the result appears, the page is shown on the right with a numbered orange box on each problem. Click an issue and the page jumps to it.
- **Duplicate names:** on the Lot Log, if an item such as "Gloves" appears more than once, each row needs its own bracketed label ("Gloves (7)", "Gloves (7.5)"). The sample's plain "Gloves" row is now flagged for checking.

## Live accuracy scorecard (22 files)
| Group | Files | Match |
|---|---|---|
| Original samples | 3 (+3 split Discard pages) | ✅ 6/6 |
| Blank templates | 3 | ✅ 3/3 |
| Error variants: Ops review, # Packaged, INC Status, missing date, 4-digit year, Qty Used, no status, two statuses, Discard 2-error | 9 | ✅ 9/9 (exactly one error each, except the 2-error Discard) |
| Scan variants: rotated 90°, rotated 180°, faint 72 DPI | 3 | ✅ 3/3 (PASS) |
| Combined Discard PDF | 1 | ✅ |
| **Total** | **22** | **✅ 22/22** |

Times: 6–28 s per file.

## Highlighting (browser test)
| File | Result shown | Boxes shown | Box placement |
|---|---|---|---|
| MP-F-023, Ops review blank | 11 s | +3 s | ✅ on the blank after the label |
| Discards, 2 errors (pages 1 and 2) | 12.5 s | +6 s | ✅ "Confirmed By" (p1) and Right Femur's X box (p2) |

## Duplicate names (`LOT-DUP-NAME`)
Implemented exactly per the team spec (no brackets / empty brackets / repeated label; exact base names; case, spacing and H₂O normalised; different-lot exception). 9 unit tests. Live Lot Log sample: flags **row 5 "Gloves"** (clashes with rows 3 and 4). The H₂O rows are not flagged because their lots differ.

## Late additions (13:40–14:00, team requests)
- **Every strike-through must be initialed and dated, on all forms** (`GDP-CORRECTION-UNSIGNED`, `LOT-VOID-UNSIGNED`). The samples' real corrections are signed, so they still pass.
- **Duplicate names:** rows whose other columns are all N/A are unused and not flagged. The sample's plain "Gloves" row is no longer flagged.
- **Rate-limit fallback:** Pro allows 25 requests/min; on a 429 we retry on Flash automatically.
- Scorecard re-run: **22/22**.

## Quality
147 offline tests pass. Lint and build are clean.
