import pytest

from app.rules.helpers import (
    has_initials,
    is_blank,
    is_filled,
    is_na,
    parse_date_mmddyy,
    signoff_missing,
)
from app.schemas.common import FieldValue
from tests.factories import blank, f, illegible, na, so


@pytest.mark.parametrize("raw", ["N/A", "n/a", "NA", "N\\A", " N / A ", "N.A."])
def test_na_variants(raw):
    assert is_na(FieldValue(raw=raw, status="filled"))


def test_zero_and_slashed_zero_are_filled():
    assert is_filled(f("0"))
    assert is_filled(f("Ø"))


def test_tally_marks_are_filled():
    assert is_filled(f("||||", tally_count=4))
    assert is_filled(FieldValue(raw=None, status="filled", tally_count=2))


def test_raw_wins_over_status():
    assert not is_blank(FieldValue(raw="2", status="blank"))
    assert is_blank(FieldValue(raw="  ", status="filled"))


def test_illegible_is_neither_blank_nor_filled():
    assert not is_blank(illegible())
    assert not is_filled(illegible())


def test_has_initials_needs_letters():
    assert has_initials(f("KS"))
    assert not has_initials(f("12-10-25"))
    assert not has_initials(blank())


@pytest.mark.parametrize(
    "raw", ["11/27/24", "11-27-24", "12.05.24", "02/29/24", "11 - 29 - 24", "9-25-24", "1/5/24"])
def test_valid_dates(raw):
    assert parse_date_mmddyy(raw).ok


@pytest.mark.parametrize(
    "raw, fragment",
    [
        ("11/27/2024", "4-digit year"),
        ("2024-11-27", "4-digit year"),
        ("27/11/24", "DD/MM"),
        ("02/30/24", "not a valid calendar date"),
        ("02/29/25", "not a valid calendar date"),
        ("13/13/24", "not a valid calendar date"),
        ("11/27-24", "mixes separators"),
        ("Nov 27", "not a recognizable date"),
        ("11/27/4", "2-digit year"),
    ],
)
def test_invalid_dates(raw, fragment):
    result = parse_date_mmddyy(raw)
    assert not result.ok
    assert fragment in result.problem


def test_strict_separator():
    assert parse_date_mmddyy("11/27/24", strict_separator=True).ok
    assert not parse_date_mmddyy("11-27-24", strict_separator=True).ok


def test_signoff_missing():
    assert signoff_missing(so("KS", "12/10/25")) == []
    assert signoff_missing(so("KS", None)) == ["date"]
    assert signoff_missing(so(None, "12/10/25")) == ["initials"]
    assert signoff_missing(so(None, None)) == ["initials", "date"]


def test_signoff_na_only_when_allowed():
    cell = so(na(), None)
    assert signoff_missing(cell, allow_na=True) == []
    assert signoff_missing(cell, allow_na=False) == ["initials", "date"]
    assert signoff_missing(so(None, None, marked_na=True), allow_na=True) == []


@pytest.mark.parametrize(
    "text, status, raw, tally",
    [
        ("", "blank", None, None),
        (None, "blank", None, None),
        ("   ", "blank", None, None),
        ("N/A", "na", "N/A", None),
        ("n\\a", "na", "n\\a", None),
        ("[illegible]", "illegible", None, None),
        ("0", "filled", "0", None),
        ("|||", "filled", "|||", 3),
        ("| | |", "filled", "| | |", 3),
        ("\\\\", "filled", "\\\\", 2),
        ("15 APR 2026", "filled", "15 APR 2026", None),
    ],
)
def test_compact_cell_parsing(text, status, raw, tally):
    fv = FieldValue.model_validate(text)
    assert (fv.status, fv.raw, fv.tally_count) == (status, raw, tally)


def test_extraction_accepts_compact_json():
    from app.schemas.mp_f_021 import LotLogExtraction
    ext = LotLogExtraction.model_validate_json(
        '{"p2_items": [{"name": "Sieve", "row_number": 16, "table": "right",'
        ' "load_number": "", "sterilization_date": ""}]}')
    assert is_blank(ext.p2_items[0].load_number)
