from app.rules.qs_f_049 import check
from app.schemas.qs_f_049 import QS049Extraction, QS049Item
from tests.factories import blank, f, illegible, na, so


def make() -> QS049Extraction:
    """A passing QS-F-049 modelled on the sample (dash/dot dates, item 9 N/A)."""
    items = [QS049Item(number=n, technical=so("NM", "11-27-24"), quality=so("LC", "12.05.24"))
             for n in range(1, 11)]
    items[8] = QS049Item(number=9, technical=so(na(), None), quality=so(na(), None))
    return QS049Extraction(ddin=f("24015"), cross_reference=f("567542"), items=items,
                           inc_number=f("CT-60, 263"),
                           inc_status=f("Closed", struck_through=True))


def item(ext, n) -> QS049Item:
    return next(i for i in ext.items if i.number == n)


def test_sample_like_form_passes_with_lenient_separators():
    assert check(make(), strict_separator=False) == []


def test_strict_separators_flag_dashes():
    issues = check(make(), strict_separator=True)
    assert issues and {i.rule_id for i in issues} == {"QS049-DATE-FORMAT"}


def test_quality_missing_date():
    ext = make()
    item(ext, 7).quality = so("LC", None)
    issues = check(ext, strict_separator=False)
    assert [(i.rule_id, i.row, i.field) for i in issues] == [
        ("QS049-REVIEW-BLANK", "Item 7", "Quality")]
    assert "initials but no date" in issues[0].message


def test_technical_fully_blank():
    ext = make()
    item(ext, 2).technical = so(None, None)
    issues = check(ext, strict_separator=False)
    assert [(i.row, i.field) for i in issues] == [("Item 2", "Technical")]
    assert "no initials and no date" in issues[0].message


def test_missing_item_is_flagged():
    ext = make()
    ext.items = [i for i in ext.items if i.number != 4]
    issues = check(ext, strict_separator=False)
    assert [(i.rule_id, i.row) for i in issues] == [("QS049-REVIEW-BLANK", "Item 4")]


def test_marked_na_cell_passes():
    ext = make()
    item(ext, 3).quality = so(None, None, marked_na=True)
    assert check(ext, strict_separator=False) == []


def test_bad_date_formats():
    ext = make()
    item(ext, 1).technical = so("NM", "11/27/2024")
    item(ext, 5).quality = so("LC", "27/11/24")
    item(ext, 6).quality = so("LC", "02/30/24")
    issues = check(ext, strict_separator=False)
    assert sorted((i.rule_id, i.row, i.field) for i in issues) == [
        ("QS049-DATE-FORMAT", "Item 1", "Technical"),
        ("QS049-DATE-FORMAT", "Item 5", "Quality"),
        ("QS049-DATE-FORMAT", "Item 6", "Quality"),
    ]


def test_inc_without_status():
    ext = make()
    ext.inc_status = blank()
    issues = check(ext, strict_separator=False)
    assert [(i.rule_id, i.row, i.field) for i in issues] == [
        ("QS049-INC-STATUS", "Item 10", "Status")]
    assert "CT-60, 263" in issues[0].message


def test_no_inc_means_status_not_required():
    ext = make()
    ext.inc_number = blank()
    ext.inc_status = blank()
    assert check(ext, strict_separator=False) == []
    ext.inc_number = na()
    assert check(ext, strict_separator=False) == []


def test_illegible_date_needs_confirmation_only():
    ext = make()
    item(ext, 1).technical = so("NM", illegible())
    issues = check(ext, strict_separator=False)
    assert [(i.rule_id, i.severity) for i in issues] == [("QS049-REVIEW-BLANK", "warning")]
