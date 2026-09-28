"""Rules for MP-F-018 — Tissue Discard Form (bonus objective).

A PDF can contain several discard forms (one per page); each is checked on its own.
A graft-ID cell holding only a drawn line/dash is treated like N/A (ADR-015).
"""

import re

from app.rules.helpers import (
    check_field,
    correction_issues,
    describe_missing,
    evidence,
    illegible_signoff_issues,
    is_filled,
    is_na,
    signoff_missing,
)
from app.schemas.common import FieldValue, Issue
from app.schemas.mp_f_018 import DiscardExtraction, DiscardForm

TOP = "Top of form"
TISSUES = "Tissue list"
BOTTOM = "Bottom of form"

_DASH_RE = re.compile(r"^[\s\-–—_~.]+$")
STATUS_LABELS = {
    "status_unprocessed": "Unprocessed Tissue",
    "status_in_processing": "In Processing Tissue",
    "status_unreleased_packaged": "Unreleased Packaged Tissue",
    "status_released_packaged": "Released Packaged Tissue",
}
PACKAGED = {"status_unreleased_packaged", "status_released_packaged"}
NOT_PACKAGED = {"status_unprocessed", "status_in_processing"}
_BOTTOM_FIELDS = [
    ("tissue_discarded_by", "Tissue Discarded By"),
    ("confirmed_by", "Confirmed By"),
    ("discarded_date", "Date (Discarded/Confirmed)"),
    ("released_freezerpro_updated_by", "Released Packaged Tissue – FreezerPro Updated By"),
    ("released_date", "Released Packaged Tissue – Date"),
    ("donor_chart_updated_by", "Donor Chart – Log / FreezerPro Updated By"),
    ("donor_chart_date", "Donor Chart – Date"),
]


def _is_dash(fv: FieldValue) -> bool:
    return bool(fv.raw and _DASH_RE.match(fv.raw))


def _graft_listed(fv: FieldValue) -> bool:
    return is_filled(fv) and not _is_dash(fv)


def _graft_na(fv: FieldValue) -> bool:
    return is_na(fv) or _is_dash(fv)


def _check_form(form: DiscardForm) -> list[Issue]:
    issues: list[Issue] = []
    page = form.page

    def issue(rule_id: str, section: str, message: str, *, row: str | None = None,
              field: str | None = None, ev: str | None = None,
              severity: str = "error") -> Issue:
        return Issue(rule_id=rule_id, severity=severity, page=page, section=section, row=row,
                     field=field, message=message, evidence=ev)

    def add_field(fv: FieldValue, rule_id: str, section: str, label: str,
                  row: str | None = None) -> None:
        found = check_field(fv, rule_id=rule_id, section=section, field=label, row=row,
                            label=f"{row}: {label}" if row else label)
        if found:
            found.page = page
            issues.append(found)

    # Top: Donor #, Reason, Authorized By/Date
    add_field(form.donor_number, "DISC-HDR-BLANK", TOP, "Donor #")
    auth = form.discard_authorized
    issues += [i.model_copy(update={"page": page}) for i in illegible_signoff_issues(
        auth, rule_id="DISC-AUTH-BYDATE", section=TOP, row=None,
        field_prefix="Discard Authorized By/Date")]
    missing = signoff_missing(auth)
    if missing:
        issues.append(issue(
            "DISC-HDR-BLANK" if len(missing) == 2 else "DISC-AUTH-BYDATE", TOP,
            f"Discard Authorized By/Date {describe_missing(missing)}.",
            field="Discard Authorized By/Date",
            ev=f"initials {evidence(auth.initials)}; date {evidence(auth.date)}"))
    add_field(form.reason_for_discard, "DISC-HDR-BLANK", TOP, "Reason for Discard")

    # Tissue Status: exactly one box
    checked = [name for name in STATUS_LABELS if getattr(form, name)]
    if not checked:
        issues.append(issue("DISC-STATUS", TOP, "No Tissue Status box is checked.",
                            field="Tissue Status"))
    elif len(checked) > 1:
        names = ", ".join(STATUS_LABELS[n] for n in checked)
        issues.append(issue("DISC-STATUS", TOP,
                            f"More than one Tissue Status box is checked ({names}).",
                            field="Tissue Status"))

    # Graft IDs vs Tissue Status
    listed_rows = [r for r in form.rows if is_filled(r.tissue_description)
                   or _graft_listed(r.graft_id)]
    listed_ids = [r.graft_id.raw for r in listed_rows if _graft_listed(r.graft_id)]
    all_na = bool(listed_rows) and all(_graft_na(r.graft_id) for r in listed_rows)
    if checked:
        checked_names = ", ".join(STATUS_LABELS[n] for n in checked)
        if listed_ids and not set(checked) <= PACKAGED:
            issues.append(issue(
                "DISC-STATUS-GRAFT", TOP,
                f"Graft IDs are listed (e.g. '{listed_ids[0]}'), so Tissue Status must be "
                f"Unreleased Packaged Tissue or Released Packaged Tissue, but "
                f"'{checked_names}' is checked.", field="Tissue Status",
                ev=f"graft IDs {listed_ids[:3]}"))
        elif all_na and not set(checked) <= NOT_PACKAGED:
            issues.append(issue(
                "DISC-STATUS-GRAFT", TOP,
                f"Graft IDs are N/A, so Tissue Status must be Unprocessed Tissue or In "
                f"Processing Tissue, but '{checked_names}' is checked.", field="Tissue Status"))

    # Tissue list: the X box for every listed tissue
    for r in form.rows:
        if not is_filled(r.tissue_description):
            continue
        label = f"Row {r.row_number} ({r.tissue_description.raw})"
        add_field(r.x_confirmed, "DISC-ROW-X", TISSUES, "X (confirmed)", row=label)

    # Bottom: nothing blank (N/A is an entry, not a blank)
    for attr, label in _BOTTOM_FIELDS:
        add_field(getattr(form, attr), "DISC-BOTTOM-BLANK", BOTTOM, label)

    if not listed_rows:
        issues.append(issue("DISC-NO-TISSUE", TISSUES, "No tissue is listed on this form.",
                            severity="warning"))
    return issues


def check(ext: DiscardExtraction) -> list[Issue]:
    if not ext.forms:
        return [Issue(rule_id="DISC-NO-FORM", severity="error", page=1, section=TOP,
                      message="No discard form content could be read from this document."),
                *correction_issues(ext.corrections)]
    issues: list[Issue] = []
    for form in sorted(ext.forms, key=lambda f: f.page):
        issues += _check_form(form)
    return issues + correction_issues(ext.corrections)



def form_labels(ext: DiscardExtraction) -> list[tuple[int, str]]:
    """One label per discard form, e.g. 'Discard form 2 of 3 · Donor 22043 · Unprocessed Tissue'."""
    forms = sorted(ext.forms, key=lambda f: f.page)
    labels = []
    for n, form in enumerate(forms, 1):
        parts = [f"Discard form {n} of {len(forms)}"]
        if is_filled(form.donor_number):
            parts.append(f"Donor {form.donor_number.raw}")
        checked = [STATUS_LABELS[s] for s in STATUS_LABELS if getattr(form, s)]
        if len(checked) == 1:
            parts.append(checked[0])
        labels.append((form.page, " · ".join(parts)))
    return labels
