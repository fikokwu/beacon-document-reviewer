"""Accuracy scorecard: run every fixture through the live pipeline and compare with
tests/fixtures/expected/*.json (backlog B-17). Needs GEMINI_API_KEY.

Usage: python -m scripts.scorecard [name filter ...]   # prints a Markdown table
"""

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.gemini_client import GeminiError
from app.pdf_utils import PdfError
from app.pipeline import review_pdf

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def score(expected_path: Path) -> dict:
    exp = json.loads(expected_path.read_text())
    started = time.monotonic()
    try:
        result = review_pdf((FIXTURES / exp["fixture"]).read_bytes())
    except (GeminiError, PdfError) as exc:  # report, don't crash the scorecard
        return {"name": expected_path.stem, "ok": False, "detail": f"error: {exc}", "secs": 0}
    found = result.issues + result.needs_confirmation
    missing = [
        e for e in exp["expected_issues"]
        if not any(i.rule_id == e["rule_id"] and i.page == e["page"]
                   and (e["field"] is None or i.field == e["field"])
                   and e["row_contains"].lower() in (i.row or "").lower() for i in found)
    ]
    checks = {
        "form type": result.form_type == exp["form_type"],
        "pass/fail": result.passed == exp["passed"],
        "expected issues": not missing,
    }
    return {
        "name": expected_path.stem,
        "ok": all(checks.values()),
        "detail": ", ".join(k for k, v in checks.items() if not v) or "—",
        "form": result.form_type,
        "passed": result.passed,
        "issues": len([i for i in result.issues if i.severity == "error"]),
        "secs": round(time.monotonic() - started),
    }


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    filters = [a.lower() for a in sys.argv[1:]]
    paths = [p for p in sorted((FIXTURES / "expected").glob("*.json"))
             if not filters or any(f in p.stem.lower() for f in filters)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(score, paths))
    print("| Fixture | Form | Result | Errors | Time | Match | Mismatch |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        result = ("PASS" if r.get("passed") else "FAIL") if "passed" in r else "—"
        print(f"| {r['name']} | {r.get('form', '—')} | {result} | {r.get('issues', '—')} | "
              f"{r['secs']} s | {'✅' if r['ok'] else '❌'} | {r['detail']} |")
    print(f"\n**{sum(r['ok'] for r in rows)}/{len(rows)} fixtures match the expected result.**")


if __name__ == "__main__":
    main()
