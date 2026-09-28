# Beacon Document Reviewer

A web app that checks a scanned, hand-filled RegenMed processing form **before** a person reviews it.

Upload one PDF. The app:

1. **Works out which form it is.** Nobody tells it in advance.
2. **Checks the form against that form's rules**, for example blank fields, missing initials or dates, or dates in the wrong format.
3. **Shows a clear result.** You get either "Passed all checks" or a list of issues. Each issue names the page, section, row and field.

Supported forms: **MP-F-023** (Tissue Open Checklist), **QS-F-049** (Technical/Quality Review & Disposition) and **MP-F-021** (Processing & Packaging Lot Log).

**▶ Live app: https://regenmed-reviewer-211763216976.northamerica-northeast2.run.app**

> Built for the RegenMed hackathon challenge. 🥈 **Runner-up, RegenMed challenge.** No real donor data is used.
>
> **This public repo doesn't include RegenMed's sample forms**, the challenge write-ups, or the fixture PDFs built from them. The rule tests run without them; tests that need a sample PDF are skipped. To run the live scorecard, add your own PDFs to `tests/fixtures/samples/` with matching `tests/fixtures/expected/*.json` files.

## How it works (one paragraph)

The AI model (Google Gemini) **reads** the form and copies each field into a structured record. It never decides pass or fail. Plain Python rules then **judge** that record, and every rule has a unit test. The results are repeatable, each flag can be explained, and the rules can be tested without calling the AI. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start (developers)

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements-dev.txt
cp .env.example .env            # add GEMINI_API_KEY and GEMINI_MODEL
uvicorn app.main:app --reload --port 8080
pytest -m "not live"            # fast tests, no API key needed

# frontend (in a second terminal)
cd frontend && npm install && npm run dev     # http://localhost:5173, proxies /api to :8080
cd frontend && npm run build                  # FastAPI then serves the page at http://localhost:8080
```

## Documentation

| Doc | Audience | What's in it |
|---|---|---|
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | Whole team | Phases, sprints, backlog, roles, definition of done |
| [docs/RULES.md](docs/RULES.md) | Everyone, including judges and QA staff | Every check the app runs, in plain English |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | QA reviewers, judges | How to use the app and read the results |
| [docs/BUSINESS_CASE.md](docs/BUSINESS_CASE.md) | Judges, RegenMed | The problem, the value, and how we measure it |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Engineers | Pipeline, schemas, stack, deployment |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Engineers | Live URL, how to redeploy, rotate the key, roll back |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Engineers, product | Design decisions and why we made them (ADR log) |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Engineers | Branches, PRs, testing, coding conventions |
| [CHANGELOG.md](CHANGELOG.md) | Everyone | What changed, sprint by sprint |
| [CLAUDE.md](CLAUDE.md) | Engineers and AI assistant | The full technical spec |
