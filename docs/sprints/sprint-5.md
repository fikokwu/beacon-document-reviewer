# Sprint 5 Report — Speed & Branding

**Date:** 2026-09-26, 11:58–12:03 EDT
**Goal:** Faster processing on every form, whatever its length, plus the RegenMed look and feel requested by the team.
**Result:** ✅ Goal met. **About 3× faster on every form; all 6 fixtures still correct.**

## Summary (plain English)
The AI was slow because it wrote a lot of extra words for every box on the form. Now it writes just what's in each box, and the app works out the rest. The busiest page (Lot Log page 2) is also split so two parts are read at the same time. Every form now comes back in about 15–25 seconds instead of 30–100. The page also looks like a RegenMed tool: brand orange and green, the Montserrat font from regenmed.ca, and a clear "Internal tool" label.

## Speed (live, Gemini 3.1 Pro)
| Form | Before | After | Still correct? |
|---|---|---|---|
| QS-F-049 sample | 31 s | **14 s** | ✅ PASS |
| MP-F-023 sample | 50 s | **16 s** | ✅ PASS |
| Lot Log sample | 86–97 s | **25 s** | ✅ FAIL on Sieve row 16 |
| QS-F-049 blank | 27 s | **10 s** | ✅ 20 issues |
| MP-F-023 blank | 58 s | **11 s** | ✅ 45 issues |
| Lot Log blank | timed out | **21 s** | ✅ 205 issues (every printed row) |

## Delivered
- Compact string cells on the wire, parsed back by `FieldValue` (ADR-014)
- Dense pages split into parallel calls (`FormSpec.parts`), with a fallback to per-page
- UI: orange `#ff5601` / green `#62783f`, Montserrat, "Internal tool · RegenMed staff use only" bar, "Internal" tag
- UI removals: subtitle, "Supports… / not stored" footer text, Download JSON, time taken, elapsed counter
- New screenshots in `docs/screenshots/`

## Quality
- 105 offline tests pass (12 new, for compact cell parsing). Lint and build are clean.

## Next
Redeploy, then Phase 5/6 options: AI fallback for demo safety, synthetic variants plus a scorecard, issue highlighting on page images, pitch support.
