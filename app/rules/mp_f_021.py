"""Rules for MP-F-021 — MS Processing & Packaging Lot Log.

Rules apply only to listed rows: rows with an item name that are not voided.
Voided rows' cells are not checked, but the void must be initialed and dated (ADR-018).
"""

import re

from app.rules.helpers import (
    check_field,
    correction_issues,
    evidence,
    has_initials,
    is_blank,
    is_filled,
    is_na,
)
from app.schemas.common import FieldValue, Issue
from app.schemas.mp_f_021 import LotLogExtraction, LotRowBase


def _row_label(row: LotRowBase) -> str:
    return f"{row.name.strip()} (row {row.row_number})"


def _void_issue(row: LotRowBase, section: str, label: str) -> Issue:
    """A voided row must carry initials and a date (GDP); its cells are not checked."""
    ev = f"initials {evidence(row.void_initials)}; date {evidence(row.void_date)}"
    missing = [n for n, ok in (("initials", has_initials(row.void_initials)),
                               ("date", is_filled(row.void_date))) if not ok]
    if missing:
        return Issue(rule_id="LOT-VOID-UNSIGNED", severity="error", page=row.page,
                     section=section, row=label, field="Void initials/date",
                     message=f"Row '{label}' is crossed out (voided) but the void has no "
                     f"{' and no '.join(missing)}. Every void must be initialed and dated.",
                     evidence=ev)
    return Issue(rule_id="LOT-VOIDED-ROW", severity="info", page=row.page, section=section,
                 row=label, message=f"Row '{label}' is crossed out (voided) by "
                 f"{row.void_initials.raw} on {row.void_date.raw}.", evidence=ev)


def _unread_rows(rows: list[LotRowBase], section: str) -> list[Issue]:
    """Safety net: a gap in row numbers means the model skipped a row (often a blank one)."""
    numbers = sorted({r.row_number for r in rows})
    if not numbers:
        return []
    page = rows[0].page
    return [
        Issue(rule_id="LOT-ROW-UNREAD", severity="warning", page=page, section=section,
              row=f"row {n}", message=f"Row {n} in {section} could not be read. Please check "
              "that it is either empty or fully filled in.")
        for n in range(numbers[0], numbers[-1] + 1) if n not in numbers
    ]


def _check_rows(rows: list[LotRowBase], *, section: str, rule_id: str,
                fields: list[tuple[str, str]], allow_na: bool) -> list[Issue]:
    issues: list[Issue] = _unread_rows(rows, section)
    voided_numbers = {r.row_number for r in rows if r.row_voided}
    for row in rows:
        if not row.name.strip():
            continue
        label = _row_label(row)
        if row.row_voided:
            issues.append(_void_issue(row, section, label))
            continue
        cells = [getattr(row, attr) for attr, _ in fields]
        next_to_void = {row.row_number - 1, row.row_number + 1} & voided_numbers
        if next_to_void and all(is_blank(c) for c in cells):
            # One strike-through line often spans two rows; don't fail, ask a person (ADR-016).
            issues.append(Issue(
                rule_id="LOT-VOID-ADJACENT", severity="warning", page=row.page, section=section,
                row=label, field=", ".join(f for _, f in fields),
                message=f"Row '{label}' is completely empty and sits right next to a crossed-out "
                "row. It may be part of the same void. Please check."))
            continue
        for attr, field in fields:
            fv: FieldValue = getattr(row, attr)
            issue = check_field(fv, rule_id=rule_id, section=section, row=label, field=field,
                                allow_na=allow_na, label=f"Row '{label}': {field}")
            if issue:
                issue.page = row.page
                issues.append(issue)
    return issues


_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_BRACKET_RE = re.compile(r"^(?P<before>[^()]*)\((?P<qual>[^()]*)\)(?P<after>.*)$")


def _norm(text: str) -> str:
    """Compare names ignoring case, spacing, and subscript digits (H₂O == H2O)."""
    return re.sub(r"\s+", "", text.translate(_SUBSCRIPTS)).lower()


def _split_name(name: str) -> tuple[str, str | None]:
    """'Gloves (7.5)' -> ('gloves', '7.5'); 'Gloves' -> ('gloves', None); 'Bags ( )' -> ('bags', '')."""
    m = _BRACKET_RE.match(name.strip())
    if not m:
        return _norm(name), None
    return _norm(m["before"] + m["after"]), _norm(m["qual"])


def _duplicate_names(rows: list[LotRowBase], section: str, lot_attr: str,
                     data_attrs: list[str]) -> list[Issue]:
    """LOT-DUP-NAME: repeated item names must be told apart by a bracketed label.
    Rows whose data columns are all N/A (item not used) are ignored."""
    groups: dict[str, list[tuple[LotRowBase, str | None]]] = {}
    for row in rows:
        unused = all(is_na(getattr(row, a)) for a in data_attrs)
        if row.name.strip() and not row.row_voided and not unused:
            base, qual = _split_name(row.name)
            groups.setdefault(base, []).append((row, qual))
    issues: list[Issue] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        if all(q is None for _, q in members):
            lots = [_norm(getattr(r, lot_attr).raw or "") for r, _ in members]
            lots_ok = all(is_filled(getattr(r, lot_attr)) for r, _ in members)
            if lots_ok and len(set(lots)) == len(lots):
                continue  # same item, different lots: allowed (exception)
        for row, qual in members:
            others = [(r, q) for r, q in members if r is not row]
            if qual is None:
                problem, clash = "has no bracketed label to tell it apart", others
            elif qual == "":
                problem, clash = "has empty brackets", others
            elif any(q == qual for _, q in others):
                problem = f"uses the same bracketed label '({qual})' as another row"
                clash = [(r, q) for r, q in others if q == qual]
            else:
                continue
            clash_text = ", ".join(f"row {r.row_number} ('{r.name.strip()}')" for r, _ in clash)
            issues.append(Issue(
                rule_id="LOT-DUP-NAME", severity="warning", page=row.page, section=section,
                row=_row_label(row), field="Item",
                message=f"Row {row.row_number} ('{row.name.strip()}'): this item name appears "
                f"more than once and this row {problem}. Clashes with {clash_text}.",
                evidence=f"name={row.name.strip()!r}"))
    return issues


def check(ext: LotLogExtraction) -> list[Issue]:
    issues = _check_rows(
        ext.p1_items, section="Page 1 – Item", rule_id="LOT-P1-ITEM", allow_na=True,
        fields=[("lot_number", "Lot Number"), ("exp_date", "Exp. Date"),
                ("manufacturer", "Manufacturer")],
    )
    issues += _duplicate_names(ext.p1_items, "Page 1 – Item", "lot_number",
                               ["lot_number", "exp_date", "manufacturer"])
    issues += _check_rows(
        ext.p1_regenmed_items, section="Page 1 – RegenMed Item", rule_id="LOT-P1-REGENMED",
        allow_na=True, fields=[("lot", "Lot"), ("qty_used", "Qty Used")],
    )
    issues += _duplicate_names(ext.p1_regenmed_items, "Page 1 – RegenMed Item", "lot",
                               ["lot", "qty_used"])
    for side in ("left", "right"):
        issues += _check_rows(
            [r for r in ext.p2_items if r.table == side],
            section=f"Page 2 – Item ({side} table)", rule_id="LOT-P2-ITEM", allow_na=True,
            fields=[("load_number", "Load #"), ("sterilization_date", "Sterilization Date")],
        )
    issues += _check_rows(
        ext.p2_packaging, section="Page 2 – Packaging", rule_id="LOT-P2-PACKAGING",
        allow_na=True, fields=[("lot", "Lot"), ("qty_used", "Qty Used")],
    )
    return issues + correction_issues(ext.corrections)
