# Architecture

The authoritative detailed spec is [CLAUDE.md](../CLAUDE.md). This doc is the overview and is kept current as components land.

## Flow

```
PDF upload ──► validate (1 file, PDF, ≤20 MB, ≤10 pages)
          ──► render pages → PNG @200 DPI, normalize rotation        (pdf_utils.py)
          ──► classify: Gemini, all pages, low-res → form_code       (prompts/classify.md)
                 └─ not a supported form → UNKNOWN, stop
          ──► extract: Gemini, form-specific prompt + Pydantic schema, temperature 0
          ──► validate: pure-Python rules for that form → [Issue]    (rules/<form>.py)
          ──► ReviewResult JSON ──► React UI
```

`rules/registry.py` maps `form_type → (schema, prompt, rules)`. Adding a form means adding one schema, one prompt and one rules module, then registering them.

## Components

| Module | Responsibility | Status |
|---|---|---|
| `app/main.py` | FastAPI: `POST /api/review` (400 bad file, 503 AI failure), `GET /api/health`, serves `frontend/dist` | ✅ Sprint 3 |
| `app/pipeline.py` | Orchestrates the flow above, form resolution (code → title fallback), timing | ✅ Sprint 2 |
| `app/pdf_utils.py` | Upload validation, grayscale PNG rendering, clockwise rotation | ✅ Sprint 2 |
| `app/gemini_client.py` | `generate_json(images, prompt, schema)`: all-required JSON schema, retry once, timeout | ✅ Sprint 2 |
| `app/schemas/` | Pydantic models: `common.py` + one per form | ✅ Sprint 1 |
| `app/rules/` | Helpers + one rule module per form + registry + `build_result` | ✅ Sprint 1 |
| `app/prompts/` | `classify.md`, `extract_common.md` (shared conventions) + one per form | ✅ Sprint 2 |
| `frontend/` | React + Vite + TS + Tailwind v4: upload → progress → report (badge, PASS/FAIL, grouped issues, needs confirmation, notes, JSON download) | ✅ Sprint 3 |

## AI calls

| Call | Input | Output schema | Notes |
|---|---|---|---|
| Classify | All pages @100 DPI + `classify.md` | `Classification` (code, title, confidence, per-page rotation) | Resolved by `pipeline.resolve_form` |
| Extract | Pages @200 DPI, rotated upright + `extract_common.md` + form prompt; dense forms split into parallel parts | Form's extraction model, with **each cell a plain string** on the wire | Temperature 0, JSON mode, required fields (ADR-008, ADR-014) |

Try any PDF from the command line: `python -m scripts.review_pdf <file.pdf>`.

## Result assembly

Each rule module returns a flat `list[Issue]`. `registry.build_result()` puts `warning` issues (illegible or low-confidence reads) into `needs_confirmation`. `passed` is true when there are no `error` issues. `info` issues (voided rows) are shown but never fail a form.

## Key design choices

See [DECISIONS.md](DECISIONS.md). In short: the AI only reads (ADR-001); one Cloud Run container (ADR-002).

## API

| Method | Path | Response |
|---|---|---|
| `POST` | `/api/review` | multipart `file` (one PDF) → `ReviewResult` JSON. `400` + `detail` for a bad upload; `503` + `detail` if the AI fails or times out |
| `GET` | `/api/health` | `{"ok": true}` |
| `GET` | `/*` | the built React app |

## Deployment

One Docker image (multi-stage: Node builds `frontend/dist`, then Python 3.12-slim runs Uvicorn and serves it) on Cloud Run in `northamerica-northeast2`. The key comes from Secret Manager. See [DEPLOY.md](DEPLOY.md).

## Configuration

| Env var | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini API key (Secret Manager in prod) |
| `GEMINI_MODEL` | Model name. Never hard-coded. |
| `GEMINI_TIMEOUT_S` | Per-call timeout (default 60) |
| `GEMINI_THINKING_LEVEL` | Optional `low`/`high` for faster or more careful reads |
| `STRICT_DATE_SEPARATOR` | `true` = only `/` accepted in QS-F-049 dates |

## Testing strategy

- **Unit (rules):** hand-written extraction JSON → expected issues. No network. Runs in CI.
- **Live (end-to-end):** fixture PDFs → Gemini → compared to `tests/fixtures/expected/*.json`. Marked `@pytest.mark.live`, skipped without a key.
- **Fixtures:** filled samples, blank templates, synthetic variants (cells whited out by `tests/make_variants.py`).
