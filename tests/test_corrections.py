"""GDP-CORRECTION-UNSIGNED: crossed-out entries on any form need initials and a date."""

from app.rules import mp_f_018, mp_f_023, qs_f_049
from app.rules.helpers import correction_issues
from app.schemas.common import Correction
from app.schemas.mp_f_018 import DiscardExtraction
from app.schemas.mp_f_023 import MP023Extraction
from app.schemas.qs_f_049 import QS049Extraction
from tests.factories import blank, f, illegible


def corr(initials="nm", date="01-23-26", location="Cancellous 3-6 mm – # Packaged", page=1):
    def conv(v):
        return blank() if v is None else (f(v) if isinstance(v, str) else v)
    return Correction(page=page, location=location, struck_value=f("15cc"),
                      initials=conv(initials), date=conv(date))


def test_signed_correction_is_fine():
    assert correction_issues([corr()]) == []


def test_correction_missing_initials_or_date_is_error():
    issues = correction_issues([corr(date=None), corr(initials=None, location="Item 10 – Status")])
    assert [(i.rule_id, i.severity, i.row) for i in issues] == [
        ("GDP-CORRECTION-UNSIGNED", "error", "Cancellous 3-6 mm – # Packaged"),
        ("GDP-CORRECTION-UNSIGNED", "error", "Item 10 – Status")]
    assert "has no date" in issues[0].message and "'15cc'" in issues[0].message


def test_illegible_signature_is_warning():
    assert [i.severity for i in correction_issues([corr(initials=illegible())])] == ["warning"]


def test_duplicate_reports_are_merged():
    assert len(correction_issues([corr(date=None), corr(date=None)])) == 1


def test_every_form_checks_corrections():
    bad = [corr(initials=None, date=None)]
    for module, ext in [(mp_f_023, MP023Extraction(corrections=bad)),
                        (qs_f_049, QS049Extraction(corrections=bad)),
                        (mp_f_018, DiscardExtraction(corrections=bad))]:
        assert "GDP-CORRECTION-UNSIGNED" in {i.rule_id for i in module.check(ext)}
