# Sprint 0 — Setup & Discovery

**Date:** 2026-09-26
**Goal:** Understand the challenge, set up the repo and our way of working, and make Phase 1 ready to start.

## Done
- Read the challenge write-up and the technical spec (CLAUDE.md)
- Analyzed all three sample forms (analysis not included in the public repo)
- Repo, CI, Python 3.12 environment, minimal API with health check
- Documentation set, both technical and plain-English
- Backlog with priorities and owners → [PROJECT_PLAN.md](../PROJECT_PLAN.md)

## Findings
- The Lot Log sample has a deliberate error: a blank "Sieve" row on page 2 under a voided "Sieve" row.
- The MP-F-023 and QS-F-049 samples look like they pass → we need blank templates and synthetic variants to prove we catch errors.
- Spec ambiguity: "X **or** Y must not be blank" → we enforce both (ADR-003).

## Open questions for organizers (owner: PO)
1. QS-F-049: are `11-27-24` / `12.05.24` acceptable as MM/DD/YY, or only slashes? → **Organizers: any separator, only the order matters** (ADR-004)
2. MP-F-023: which rows count as "shaded"? → **Answered by the blank template:** the table has no grey rows. Spacer rows are blank rows with no tissue name, and we ignore them.
3. Lot Log: must a voided row carry initials and a date on the strike-through to pass? → **Organizers: no, voided rows are not checked** (ADR-012)
4. "# Produced **or** # Packaged" and "Lot **or** Qty Used": is one enough, or are both required? → **Organizers: assume both are required** (ADR-003)

## Retro
- **Went well:** clear spec, and the samples reveal realistic edge cases (rotation, GDP corrections, tallies, zeros).
- **Watch:** no Python 3.12 on the dev machine, now fixed with `uv`. Waiting on the blank templates.

## Next sprint (Sprint 1 — Rule engine)
B-01 to B-07: schemas, helpers, all three rule modules with unit tests, expected-result JSON for the samples, message review.
