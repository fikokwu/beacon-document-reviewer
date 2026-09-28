# Business Case

*Owner: product owner (economics). This is a working draft. Replace the placeholders with confirmed figures from RegenMed before the pitch.*

## The problem

RegenMed processes donated musculoskeletal tissue for Ontario hospitals. Each donor produces a set of hand-filled forms, many of them completed inside a clean room where tablets aren't practical. Two people review every form before tissue is released.

According to RegenMed, **about half of processing forms come back needing a correction**: a missing initial, a blank field, a date in the wrong format. Reviewers spend their time hunting for blanks instead of applying judgment.

## What we change

The reviewer catches the routine misses **before** the two-person review starts. Staff fix those first, so the reviewers get a clean form and spend their time on judgment calls. The two-person review stays in place. This tool supports it and doesn't replace it.

## Value model (to be filled with real numbers)

| Input | Value | Source |
|---|---|---|
| Forms reviewed per month | *TBD* | Ask RegenMed |
| Share needing correction | ~50% | Challenge brief |
| Minutes a reviewer spends finding routine misses per form | *TBD* | Ask / time a sample review |
| Minutes lost per correction round-trip (form goes back, gets fixed, gets re-reviewed) | *TBD* | Ask |
| Loaded hourly cost of reviewer time | *TBD* | Ontario QA salary data |

**Monthly hours saved ≈ forms × (search minutes saved + correction rate × round-trip minutes avoided) ÷ 60**

Beyond time saved:
- **Faster release** of tissue to hospitals (fewer correction loops)
- **Consistency**: every form is checked against the same rules every time
- **Audit readiness**: each flag names a rule and a location, which fits AATB documentation expectations

## How we'll prove it works

- **Accuracy scorecard** on samples, blank templates and synthetic variants: share of true issues caught (recall) and share of flags that were real (precision). Recall matters most for a safety net.
- **Time per form**: target under 60 seconds from upload to result.

## Risks and honest limits

- AI can misread handwriting. We show low-confidence reads as "Needs confirmation" instead of guessing.
- Only three form types for now. New forms need a schema, a prompt and rules, which is days of work, not months.
- Checks are limited to what's on the form (for example, no product-code lookup), per the challenge scope.
