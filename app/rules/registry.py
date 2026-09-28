"""form_type -> (title, extraction schema, prompt file, rule function) and result assembly."""

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from app.rules import mp_f_018, mp_f_021, mp_f_023, qs_f_049
from app.schemas.common import FormResult, Issue, ReviewResult
from app.schemas.mp_f_018 import DiscardExtraction
from app.schemas.mp_f_021 import LotLogExtraction
from app.schemas.mp_f_023 import MP023Extraction
from app.schemas.qs_f_049 import QS049Extraction


@dataclass(frozen=True)
class FormSpec:
    code: str
    title: str
    schema: type[BaseModel]
    prompt_file: str
    check: Callable[[BaseModel], list[Issue]]
    per_page: bool = False  # extract each page in its own parallel call, then merge
    # Optional finer split for dense pages: (1-based page, instruction) per parallel call.
    # Used only when the document has exactly `max(page)` pages; else per-page (ADR-014).
    parts: tuple[tuple[int, str], ...] = ()
    # For PDFs that hold several separate forms: extraction -> [(page, label), ...]
    form_labels: Callable[[BaseModel], list[tuple[int, str]]] | None = None


FORMS: dict[str, FormSpec] = {
    # Bonus objective. One PDF may hold several discard forms, one per page.
    "MP-F-018": FormSpec("MP-F-018", "Tissue Discard Form", DiscardExtraction,
                         "extract_mp_f_018.md", mp_f_018.check, per_page=True,
                         form_labels=mp_f_018.form_labels),
    "MP-F-023": FormSpec("MP-F-023", "MS Processing Instructions / Tissue Open Checklist",
                         MP023Extraction, "extract_mp_f_023.md", mp_f_023.check),
    "QS-F-049": FormSpec("QS-F-049", "Technical/Quality Review and Disposition Statement",
                         QS049Extraction, "extract_qs_f_049.md", qs_f_049.check),
    "MP-F-021": FormSpec(
        "MP-F-021", "MS Processing & Packaging Lot Log", LotLogExtraction,
        "extract_mp_f_021.md", mp_f_021.check, per_page=True,
        parts=(
            (1, "Transcribe only the tables on this page (page 1)."),
            (2, ("Transcribe ONLY the LEFT 'Item | Load # | Sterilization Date' table on this "
                 "page (table='left'). Return empty lists for every other table. Only list "
                 "corrections inside that left table.")),
            (2, ("Transcribe ONLY the RIGHT 'Item | Load # | Sterilization Date' table "
                 "(table='right') and the 'Packaging | Lot | Qty Used' table on this page. "
                 "Return empty lists for every other table, including the left table. Only list "
                 "corrections inside those two tables.")),
        ),
    ),
}


def _plural(n: int, word: str, plural: str | None = None) -> str:
    return f"{n} {word if n == 1 else (plural or word + 's')}"


def summary_message(issues: list[Issue], needs_confirmation: list[Issue]) -> str:
    """One plain-English line for the top of the report."""
    errors = [i for i in issues if i.severity == "error"]
    notes = [i for i in issues if i.severity == "info"]
    extras = []
    if notes:
        extras.append(_plural(len(notes), "note"))
    if needs_confirmation:
        extras.append(f"{_plural(len(needs_confirmation), 'entry', 'entries')} to confirm by eye")
    if not errors:
        if not extras:
            return "Passed all checks. No missing or inconsistent entries were found."
        return f"Passed all checks. See {' and '.join(extras)} below."
    sections = list(dict.fromkeys(i.section for i in errors))
    where = f"in {sections[0]}" if len(sections) == 1 else f"across {len(sections)} sections"
    tail = f" Also {' and '.join(extras)}." if extras else ""
    return f"{_plural(len(errors), 'issue')} to fix before review {where}.{tail}"


def build_result(form_type: str, issues: list[Issue],
                 form_labels: list[tuple[int, str]] | None = None, **kwargs) -> ReviewResult:
    """Warnings (low-confidence reads) go to needs_confirmation; pass = no errors.
    With `form_labels`, issues are also split into one FormResult per form (by page)."""
    confirmed = [i for i in issues if i.severity != "warning"]
    needs_confirmation = [i for i in issues if i.severity == "warning"]
    forms = []
    for page, label in form_labels or []:
        f_issues = [i for i in confirmed if i.page == page]
        f_confirm = [i for i in needs_confirmation if i.page == page]
        forms.append(FormResult(
            label=label, page=page, issues=f_issues, needs_confirmation=f_confirm,
            passed=not any(i.severity == "error" for i in f_issues),
            message=summary_message(f_issues, f_confirm)))
    if len(forms) > 1:
        kwargs["message"] = _multi_form_message(forms, confirmed, needs_confirmation)
    else:
        forms = []
    kwargs.setdefault("message", summary_message(confirmed, needs_confirmation))
    return ReviewResult(
        form_type=form_type,
        passed=not any(i.severity == "error" for i in confirmed),
        issues=confirmed,
        needs_confirmation=needs_confirmation,
        forms=forms,
        **kwargs,
    )


def _multi_form_message(forms: list[FormResult], issues: list[Issue],
                        needs_confirmation: list[Issue]) -> str:
    failed = sum(not f.passed for f in forms)
    head = f"This PDF contains {len(forms)} separate forms"
    if not failed:
        return f"{head}. All passed. " + summary_message(issues, needs_confirmation).replace(
            "Passed all checks. ", "")
    return f"{head}: {len(forms) - failed} passed, {failed} need{'s' if failed == 1 else ''} fixing."
