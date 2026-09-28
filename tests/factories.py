"""Tiny builders for hand-written extraction data in rule tests."""

from app.schemas.common import FieldValue, SignOff


def f(raw: str, page: int = 1, **kw) -> FieldValue:
    return FieldValue(raw=raw, status="filled", page=page, **kw)


def blank(page: int = 1) -> FieldValue:
    return FieldValue(raw=None, status="blank", page=page)


def na(raw: str = "N/A", page: int = 1) -> FieldValue:
    return FieldValue(raw=raw, status="na", page=page)


def illegible(page: int = 1) -> FieldValue:
    return FieldValue(raw=None, status="illegible", page=page)


def so(initials: FieldValue | str | None = "KS", date: FieldValue | str | None = "12/10/25",
       marked_na: bool = False, page: int = 1) -> SignOff:
    def conv(v):
        if v is None:
            return blank(page)
        return f(v, page) if isinstance(v, str) else v
    return SignOff(initials=conv(initials), date=conv(date), marked_na=marked_na, page=page)


def rule_ids(issues) -> list[str]:
    return sorted(i.rule_id for i in issues)
