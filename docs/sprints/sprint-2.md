# Sprint 2 Report — AI Extraction

**Date:** 2026-09-26, 10:23–11:15 EDT
**Goal:** Turn a scanned PDF into the structured record the rules need, using Gemini, and prove it on real forms.
**Result:** ✅ Goal met. **All 5 live-tested forms match the team baseline.**

## Summary (plain English)
The app can now read a real scanned form. It works out which form it is, reads every box, and applies the rules. We tested it on the three filled samples and two of the blank templates, and it gave the answer a careful human reviewer would give on all five. It catches the deliberate error in the Lot Log, correctly passes the two clean forms, and flags every empty field on the blanks.

## Live accuracy (Gemini 3.1 Pro, paid tier, thinking = low)
| Form | Expected (team baseline) | App result | Time |
|---|---|---|---|
| MP-F-023 sample | PASS | ✅ PASS | 50 s |
| QS-F-049 sample | PASS | ✅ PASS | 31 s |
| Lot Log sample | FAIL: Sieve row 16, Load # + Sterilization Date blank; row 15 voided (info) | ✅ Exactly that | 97 s |
| MP-F-023 blank | FAIL: all 10 header fields, Ops review, 17 rows × 2 | ✅ Exactly that (45 issues) | 58 s |
| QS-F-049 blank | FAIL: items 1–10 × 2 columns, no INC-status issue | ✅ Exactly that (20 issues) | 27 s |
| Lot Log blank | FAIL on every printed row | ⏳ Not re-run with the final prompt | — |

## Delivered
| Backlog | Item | Status |
|---|---|---|
| B-08 | PDF validation, rendering, rotation | ✅ |
| B-09 | Gemini client: strict schema, retry, timeout, friendly errors, timing logs | ✅ |
| B-10 | Classification + tolerant code match + title fallback + UNKNOWN | ✅ (5/5 correct live) |
| B-11 | Extraction prompts for all 3 forms | ✅ (5/5 correct live) |
| B-15 | Blank templates added as fixtures, with expected results; the "shaded rows" question answered | ✅ |
| — | Summary message on every result ("Passed all checks…") | ✅ |

## What we learned (and fixed)
1. **The organizers' proxy is text-only**, so it can't read scans. We use our own AI Studio key (ADR-009).
2. **The free tier was unusable:** 20–30 s queueing, "high demand" errors, a 5-requests-a-minute cap and inconsistent reads. Billing is enabled, and Gemini 3.1 Pro is **5× faster** at classification (ADR-010).
3. **Output size drives latency.** Making rare fields optional, dropping bounding boxes by default and reading Lot Log pages in parallel took the Lot Log from 146–293 s to 97 s (ADR-010).
4. **Default thinking sometimes stalled for more than 240 s.** `thinking_level=low` is faster and just as accurate on our forms.
5. **The AI silently skipped the blank "Sieve" row**, which is the very error we need to catch. We fixed the prompt ("every row") and added the `LOT-ROW-UNREAD` safety net (ADR-012).
6. **Organizer answers applied:** any date separator is fine (ADR-004); voided rows are not checked (ADR-012); "or" means both (ADR-003).

## Quality
- 88 offline tests pass. Lint is clean.
- 5 live end-to-end checks match the baseline.

## Risks
| Risk | Plan |
|---|---|
| Lot Log takes ~100 s, which is slow for a demo | Show a progress state in the UI; the demo script explains the wait. Later: a faster model for page 2 |
| Live accuracy is proven on only 5 forms | Synthetic variants (B-16) after the MVP |
| Relies on the Gemini 3.1 Pro *preview* model | The model name is a config value; `gemini-pro-latest` is the fallback |

## Next — Sprint 3: API + UI (target 12:15)
`POST /api/review`, error handling, React upload page: form badge, PASS/FAIL banner with the summary, issues grouped by section, "needs confirmation" group, progress state.
