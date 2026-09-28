"""Small, pure helpers shared by every form's rules.

The helpers trust `raw` over `status` when they disagree (e.g. status="blank" but
raw="0"), because a transcription with content is stronger evidence than a label.
"""

import calendar
import re
from dataclasses import dataclass

from app.schemas.common import NA_RE, Correction, FieldValue, Issue, SignOff

_DATE_RE = re.compile(r"^(\d{1,4})\s*([/.\-])\s*(\d{1,2})\s*([/.\-])\s*(\d{1,4})$")


def is_na(fv: FieldValue) -> bool:
    return fv.status == "na" or bool(fv.raw and NA_RE.match(fv.raw))


def is_illegible(fv: FieldValue) -> bool:
    return fv.status == "illegible" and not is_na(fv)


def is_blank(fv: FieldValue) -> bool:
    if is_na(fv) or fv.status == "illegible":
        return False
    return not (fv.raw or "").strip() and fv.tally_count is None


def is_filled(fv: FieldValue) -> bool:
    """Has a readable, non-N/A value. 0 and tally marks count."""
    return not (is_blank(fv) or is_na(fv) or is_illegible(fv))


def has_initials(fv: FieldValue) -> bool:
    return is_filled(fv) and any(ch.isalpha() for ch in fv.raw or "")


def evidence(fv: FieldValue) -> str:
    return f'raw="{fv.raw}"' if fv.raw else f"status={fv.status}"


@dataclass(frozen=True)
class DateCheck:
    ok: bool
    problem: str | None = None


def parse_date_mmddyy(raw: str | None, strict_separator: bool = False) -> DateCheck:
    """Check that `raw` is month/day/year order with a 2-digit year and is a real date.
    Organizers confirmed any separator is fine and only the order matters, so single-digit
    months/days (9-5-24) are accepted."""
    if not raw or not raw.strip():
        return DateCheck(False, "no date")
    text = raw.strip()
    m = _DATE_RE.match(text)
    if not m:
        return DateCheck(False, f"'{text}' is not a recognizable date")
    a, sep1, b, sep2, c = m.groups()

    if len(a) == 4:
        return DateCheck(False, f"'{text}' starts with a 4-digit year; expected MM/DD/YY")
    if len(c) == 4:
        return DateCheck(False, f"'{text}' uses a 4-digit year; expected MM/DD/YY")
    if len(c) != 2:
        return DateCheck(False, f"'{text}' does not have a 2-digit year; expected MM/DD/YY")
    if strict_separator and (sep1 != "/" or sep2 != "/"):
        return DateCheck(False, f"'{text}' must use '/' separators (MM/DD/YY)")
    if sep1 != sep2:
        return DateCheck(False, f"'{text}' mixes separators; expected MM/DD/YY")

    month, day, year = int(a), int(b), 2000 + int(c)
    if month > 12 and day <= 12:
        return DateCheck(False, f"'{text}' looks like DD/MM/YY; expected MM/DD/YY")
    if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(year, month)[1]:
        return DateCheck(False, f"'{text}' is not a valid calendar date")
    return DateCheck(True)


def check_field(
    fv: FieldValue,
    *,
    rule_id: str,
    section: str,
    field: str,
    row: str | None = None,
    allow_na: bool = True,
    label: str | None = None,
) -> Issue | None:
    """Error if blank (or N/A when not allowed); warning if illegible; else None."""
    where = label or (f"{row}: {field}" if row else field)
    if is_illegible(fv):
        return Issue(
            rule_id=rule_id, severity="warning", page=fv.page, section=section, row=row,
            field=field, message=f"{where} has writing that could not be read — please check.",
            evidence=evidence(fv), box_2d=fv.box_2d,
        )
    if is_blank(fv) or (not allow_na and is_na(fv)):
        state = "is blank" if is_blank(fv) else "says N/A but a value is required"
        return Issue(
            rule_id=rule_id, severity="error", page=fv.page, section=section, row=row,
            field=field, message=f"{where} {state}.", evidence=evidence(fv), box_2d=fv.box_2d,
        )
    return None


def signoff_missing(so: SignOff, *, allow_na: bool = False) -> list[str]:
    """Which parts ('initials', 'date') are missing. Illegible parts are not 'missing'."""
    if allow_na and (so.marked_na or (is_na(so.initials) and not is_filled(so.date))):
        return []
    missing = []
    if not (has_initials(so.initials) or is_illegible(so.initials)):
        missing.append("initials")
    if not (is_filled(so.date) or is_illegible(so.date)):
        missing.append("date")
    return missing


def describe_missing(missing: list[str]) -> str:
    if missing == ["initials", "date"]:
        return "is blank (no initials and no date)"
    if missing == ["initials"]:
        return "has a date but no initials"
    return "has initials but no date"


def illegible_signoff_issues(
    so: SignOff, *, rule_id: str, section: str, row: str | None, field_prefix: str
) -> list[Issue]:
    issues = []
    for part_name, part in (("initials", so.initials), ("date", so.date)):
        if is_illegible(part):
            issues.append(Issue(
                rule_id=rule_id, severity="warning", page=part.page, section=section, row=row,
                field=f"{field_prefix} {part_name}",
                message=f"{row + ', ' if row else ''}{field_prefix} {part_name} could not be "
                "read — please check.",
                evidence=evidence(part), box_2d=part.box_2d or so.box_2d,
            ))
    return issues


def correction_issues(corrections: list[Correction]) -> list[Issue]:
    """GDP: every crossed-out value or struck row must carry initials AND a date (ADR-018)."""
    issues: list[Issue] = []
    seen: set[tuple[int, str]] = set()
    for c in corrections:
        key = (c.page, re.sub(r"\s+", " ", c.location.strip().lower()))
        if key in seen:  # parallel page-part calls can report the same correction twice
            continue
        seen.add(key)
        what = f" ('{c.struck_value.raw}')" if is_filled(c.struck_value) else ""
        ev = f"initials {evidence(c.initials)}; date {evidence(c.date)}"
        if is_illegible(c.initials) or is_illegible(c.date):
            issues.append(Issue(
                rule_id="GDP-CORRECTION-UNSIGNED", severity="warning", page=c.page,
                section="Corrections", row=c.location, field="Initials/date",
                message=f"{c.location}: the initials or date on a crossed-out entry{what} could "
                "not be read — please check.", evidence=ev))
            continue
        missing = [n for n, ok in (("initials", has_initials(c.initials)),
                                   ("date", is_filled(c.date))) if not ok]
        if missing:
            issues.append(Issue(
                rule_id="GDP-CORRECTION-UNSIGNED", severity="error", page=c.page,
                section="Corrections", row=c.location, field="Initials/date",
                message=f"{c.location}: a crossed-out entry{what} has no "
                f"{' and no '.join(missing)}. Every correction must be initialed and dated.",
                evidence=ev))
    return issues
