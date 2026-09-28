"""Rules for MP-F-023 — MS Processing Instructions / Tissue Open Checklist."""

from app.rules.helpers import (
    check_field,
    correction_issues,
    describe_missing,
    evidence,
    illegible_signoff_issues,
    signoff_missing,
)
from app.schemas.common import Issue, SignOff
from app.schemas.mp_f_023 import MP023Extraction

HEADER = "Header"
OPS = "Operations Manager Review"
TABLE = "Processing Instructions"

_SIMPLE_HEADER_FIELDS = [
    ("donor_number", "Donor #"),
    ("verified_by", "Verified By"),
    ("cross_reference", "Cross Reference #"),
    ("donor_sex", "Donor Sex"),
    ("donor_age", "Donor Age"),
    ("date_of_recovery", "Date of Recovery"),
    ("instruction_verification", "Instruction Verification"),
    ("date_of_processing", "Date of Processing"),
]
_BYDATE_FIELDS = [
    ("clean_room_log_review", "Clean Room Log Review By/Date"),
    ("tissue_checked_in", "Tissue Checked In By/Date"),
]


def _signoff_issues(so: SignOff, *, section: str, field: str, blank_rule: str,
                    partial_rule: str) -> list[Issue]:
    issues = illegible_signoff_issues(so, rule_id=partial_rule, section=section, row=None,
                                      field_prefix=field)
    missing = signoff_missing(so)
    if missing:
        rule = blank_rule if len(missing) == 2 else partial_rule
        issues.append(Issue(
            rule_id=rule, severity="error", page=so.page, section=section, field=field,
            message=f"{field} {describe_missing(missing)}.",
            evidence=f"initials {evidence(so.initials)}; date {evidence(so.date)}",
            box_2d=so.box_2d,
        ))
    return issues


def check(ext: MP023Extraction) -> list[Issue]:
    issues: list[Issue] = []
    h = ext.header

    for attr, label in _SIMPLE_HEADER_FIELDS:
        issue = check_field(getattr(h, attr), rule_id="MP023-HDR-BLANK", section=HEADER,
                            field=label, label=f"Header field '{label}'")
        if issue:
            issues.append(issue)

    for attr, label in _BYDATE_FIELDS:
        issues += _signoff_issues(getattr(h, attr), section=HEADER, field=label,
                                  blank_rule="MP023-HDR-BLANK", partial_rule="MP023-HDR-BYDATE")

    ops = ext.ops_manager_review
    issues += _signoff_issues(ops, section=OPS, field=OPS, blank_rule="MP023-OPS-REVIEW",
                              partial_rule="MP023-OPS-REVIEW")

    for row in ext.processing_rows:
        if row.shaded or row.row_voided or not row.name.strip():
            continue
        for fv, field, rule in ((row.produced, "# Produced", "MP023-ROW-PRODUCED"),
                                (row.packaged, "# Packaged", "MP023-ROW-PACKAGED")):
            issue = check_field(fv, rule_id=rule, section=TABLE, row=row.name, field=field,
                                label=f"Row '{row.name}': {field}")
            if issue:
                issues.append(issue)

    return issues + correction_issues(ext.corrections)
