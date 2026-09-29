# Sprint 4 Report — Deploy

**Date:** 2026-09-26, 11:39–11:44 EDT
**Goal:** A public URL that judges can use: the MVP.
**Result:** ✅ Goal met. **The MVP is live, more than 2 hours before the 2 pm deadline.**

**Live app:** <your-cloud-run-url>

## Summary (plain English)
Anyone with the link can now open the app in a browser, upload a scanned form, and get the report. Nothing to install and no login. It runs on Google Cloud in Toronto, the AI key is stored in Google's secret vault (not in the code), and one copy of the app is always kept running, so judges never wait for it to start up.

## Delivered
| Backlog | Item | Status |
|---|---|---|
| B-14 | Dockerfile, Cloud Run, Secret Manager, public URL | ✅ |
| — | Deployment runbook (`docs/DEPLOY.md`): redeploy, rotate key, switch model, logs, rollback | ✅ |

## Live smoke test (public URL)
| Check | Result |
|---|---|
| `GET /api/health` | ✅ `{"ok": true}` |
| Page loads | ✅ |
| Non-PDF upload | ✅ rejected with a clear 400 message |
| QS-F-049 sample | ✅ PASS in 27 s |
| Lot Log sample (2 pages) | ✅ FAIL: Sieve row 16 Load # and Sterilization Date; row 15 voided note, in 86 s |

## Decisions
- **ADR-013:** same GCP project as the Gemini key; 300 s timeout; min 1 / max 3 instances; 1 GiB; non-root container; lean image.

## Hiccup
- New GCP projects don't give the build service account permission to build from source. Granted `roles/run.builder` (documented in DEPLOY.md).

## MVP status vs. the challenge
| Requirement | Status |
|---|---|
| Accept a single uploaded PDF | ✅ |
| Identify the form type (never told in advance) | ✅ bottom-right code, with a title fallback, and UNKNOWN for other forms |
| Clear list of issues, or "passed all checks", referencing the field or section | ✅ page · section · row · field, plus a summary line |
| Generalize (no hard-coding to the samples) | ✅ row names are read from the page; verified on blank templates |
| Deployed online | ✅ |

## Next — Phase 5/6 (hardening and polish), 11:50–2:00
Suggested priority:
1. **Demo safety:** a Claude or second-Gemini-model fallback if the primary AI errors; UI copy for the long Lot Log wait.
2. **Generalization evidence (B-16/B-17):** synthetic variants (white out cells in the samples) plus an accuracy scorecard for the pitch.
3. **Wow factor (B-20):** highlight each issue on a page thumbnail.
4. **Pitch (B-22, PO):** business case numbers, demo script, slides.
