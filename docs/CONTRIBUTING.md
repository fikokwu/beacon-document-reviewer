# Contributing

## Workflow

1. Pick an issue from the current sprint. Assign yourself.
2. Branch from `main`: `feat/B-03-mp023-rules`, `fix/...`, `docs/...`
3. Commit small and often. Use a clear subject line, for example `Add MP-F-023 header rules`.
4. Open a PR that links the issue (`Closes #12`). Fill in: what changed, how it was tested, which docs were updated.
5. CI must be green (ruff + `pytest -m "not live"`). One review from the other teammate, then squash-merge.

`main` is always deployable.

## Local setup

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements-dev.txt
cp .env.example .env
ruff check .
pytest -m "not live"      # fast, no API key
pytest -m live            # needs GEMINI_API_KEY
```

## Conventions (summary; full spec in [CLAUDE.md](../CLAUDE.md))

- **Rules are pure functions**: `check(extraction) -> list[Issue]`. Every rule gets tests with hand-written JSON.
- **Never hard-code** anything from the sample files (row lists, coordinates, expected values).
- **Rule IDs are stable.** If you add or rename one, update [RULES.md](RULES.md) and the tests.
- **Issue messages** are written for a QA reviewer: plain English that names the section, row and field. The product owner reviews them.
- Prompts live in `app/prompts/*.md`, not inline strings.
- Never commit secrets. `.env` is git-ignored.

## Docs to touch per change

| You changed… | Update… |
|---|---|
| A rule | RULES.md, tests, CHANGELOG |
| Architecture or stack | ARCHITECTURE.md, and an ADR in DECISIONS.md if it's a real choice |
| User-visible UI | USER_GUIDE.md |
| Anything | CHANGELOG.md |
