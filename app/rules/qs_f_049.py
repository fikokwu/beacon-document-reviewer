"""Rules for QS-F-049 — Technical/Quality Review and Disposition Statement."""

from app import config
from app.rules.helpers import (
    check_field,
    correction_issues,
    describe_missing,
    evidence,
    illegible_signoff_issues,
    is_blank,
    is_filled,
    parse_date_mmddyy,
    signoff_missing,
)
from app.schemas.common import Issue, SignOff
from app.schemas.qs_f_049 import QS049Extraction

SECTION = "Technical and Quality Review Elements – Reviewed By/Date"
ITEM_COUNT = 10


def _cell_issues(item_no: int, column: str, so: SignOff, strict: bool) -> list[Issue]:
    row = f"Item {item_no}"
    issues = illegible_signoff_issues(so, rule_id="QS049-REVIEW-BLANK", section=SECTION,
                                      row=row, field_prefix=column)
    missing = signoff_missing(so, allow_na=True)
    if missing:
        issues.append(Issue(
            rule_id="QS049-REVIEW-BLANK", severity="error", page=so.page, section=SECTION,
            row=row, field=column,
            message=f"{column} review for item {item_no} {describe_missing(missing)}. "
            "Enter initials and a date, or N/A.",
            evidence=f"initials {evidence(so.initials)}; date {evidence(so.date)}",
            box_2d=so.box_2d,
        ))
    if is_filled(so.date):
        result = parse_date_mmddyy(so.date.raw, strict_separator=strict)
        if not result.ok:
            issues.append(Issue(
                rule_id="QS049-DATE-FORMAT", severity="error", page=so.date.page,
                section=SECTION, row=row, field=column,
                message=f"{column} date for item {item_no}: {result.problem}.",
                evidence=evidence(so.date), box_2d=so.date.box_2d or so.box_2d,
            ))
    return issues


def check(ext: QS049Extraction, strict_separator: bool | None = None) -> list[Issue]:
    strict = config.STRICT_DATE_SEPARATOR if strict_separator is None else strict_separator
    issues: list[Issue] = []
    by_number = {item.number: item for item in ext.items}

    for n in range(1, ITEM_COUNT + 1):
        item = by_number.get(n)
        if item is None:
            issues.append(Issue(
                rule_id="QS049-REVIEW-BLANK", severity="error", page=1, section=SECTION,
                row=f"Item {n}", field="Technical and Quality",
                message=f"Item {n}: no Technical or Quality review entries were found.",
            ))
            continue
        issues += _cell_issues(n, "Technical", item.technical, strict)
        issues += _cell_issues(n, "Quality", item.quality, strict)

    if is_filled(ext.inc_number):
        status_issue = check_field(ext.inc_status, rule_id="QS049-INC-STATUS", section=SECTION,
                                   row="Item 10", field="Status")
        if status_issue:
            status_issue.message = (
                f"Item 10: INC # '{ext.inc_number.raw}' is entered but Status is "
                f"{'blank' if is_blank(ext.inc_status) else 'unreadable'}."
            )
            issues.append(status_issue)

    return issues + correction_issues(ext.corrections)
