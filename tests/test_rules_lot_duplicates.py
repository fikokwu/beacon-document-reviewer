"""LOT-DUP-NAME: duplicate item names in the page-1 Item and RegenMed Item tables."""

from app.rules.mp_f_021 import check
from app.schemas.mp_f_021 import LotLogExtraction, LotP1ItemRow, LotRegenMedRow
from tests.factories import f, na


def items(*names_and_lots):
    return [LotP1ItemRow(name=n, row_number=i, lot_number=f(lot) if lot else na(),
                         exp_date=f("2028-01"), manufacturer=f("Medline"))
            for i, (n, lot) in enumerate(names_and_lots, 1)]


def regen(*names):
    return [LotRegenMedRow(name=n, row_number=i, lot=f(f"IR-{i}"), qty_used=f("|"))
            for i, n in enumerate(names, 1)]


def dups(ext):
    return [(i.row, i.message) for i in check(ext) if i.rule_id == "LOT-DUP-NAME"]


def test_distinct_qualifiers_ok():
    ext = LotLogExtraction(p1_items=items(("Gloves (7)", "A"), ("Gloves (7.5)", "B")),
                           p1_regenmed_items=regen("Poly Bags (15)", "Poly Bags (11)"))
    assert dups(ext) == []


def test_plain_row_among_bracketed_is_flagged():
    ext = LotLogExtraction(p1_items=items(("Gloves (7)", "A"), ("Gloves (7.5)", "B"),
                                          ("Gloves", "C")))
    found = dups(ext)
    assert [r for r, _ in found] == ["Gloves (row 3)"]
    assert "no bracketed label" in found[0][1]
    assert "row 1 ('Gloves (7)')" in found[0][1] and "row 2 ('Gloves (7.5)')" in found[0][1]


def test_empty_brackets_flagged():
    ext = LotLogExtraction(p1_regenmed_items=regen("Poly Bags (15)", "Poly Bags ( )"))
    found = dups(ext)
    assert [r for r, _ in found] == ["Poly Bags ( ) (row 2)"]
    assert "empty brackets" in found[0][1]


def test_repeated_qualifier_flags_both():
    ext = LotLogExtraction(p1_items=items(("Gloves (7)", "A"), ("Gloves (7)", "B")))
    found = dups(ext)
    assert [r for r, _ in found] == ["Gloves (7) (row 1)", "Gloves (7) (row 2)"]
    assert all("same bracketed label '(7)'" in m for _, m in found)


def test_different_names_are_not_duplicates():
    ext = LotLogExtraction(p1_items=items(("Gauze", "A"), ("Fascia Gauze", "B")))
    assert dups(ext) == []


def test_case_spacing_and_subscripts_are_ignored():
    ext = LotLogExtraction(p1_items=items(("H₂O 1000 mL (a)", "A"), ("h2o 1000ml", "B")))
    assert [r for r, _ in dups(ext)] == ["h2o 1000ml (row 2)"]


def test_plain_repeats_with_different_lots_are_allowed():
    ext = LotLogExtraction(p1_items=items(("H₂O 1000 mL", "G181204"), ("H2O 1000 mL", "G181228"),
                                          ("H₂O 1000 mL", "G181860")))
    assert dups(ext) == []


def test_plain_repeats_with_same_or_missing_lot_are_flagged():
    ext = LotLogExtraction(p1_items=items(("Bowl", "605"), ("Bowl", "605")))
    assert [r for r, _ in dups(ext)] == ["Bowl (row 1)", "Bowl (row 2)"]
    ext = LotLogExtraction(p1_items=items(("Bowl", "605"), ("Bowl", None)))
    assert len(dups(ext)) == 2


def test_duplicates_are_flags_not_failures():
    ext = LotLogExtraction(p1_items=items(("Gloves (7)", "A"), ("Gloves", "B")))
    issues = check(ext)
    assert not [i for i in issues if i.severity == "error"]
    assert {i.severity for i in issues if i.rule_id == "LOT-DUP-NAME"} == {"warning"}


def test_duplicate_row_with_all_na_columns_is_unused_and_ignored():
    ext = LotLogExtraction(p1_items=[
        LotP1ItemRow(name="Gloves (7)", row_number=3, lot_number=f("A"), exp_date=f("2027"),
                     manufacturer=f("Medline")),
        LotP1ItemRow(name="Gloves (7.5)", row_number=4, lot_number=f("B"), exp_date=f("2028"),
                     manufacturer=f("Medline")),
        LotP1ItemRow(name="Gloves", row_number=5, lot_number=na("N\\A"), exp_date=na("NA"),
                     manufacturer=na("n/a")),
    ])
    assert dups(ext) == []


def test_partly_na_duplicate_is_still_flagged():
    ext = LotLogExtraction(p1_items=[
        LotP1ItemRow(name="Gloves (7)", row_number=3, lot_number=f("A"), exp_date=f("2027"),
                     manufacturer=f("Medline")),
        LotP1ItemRow(name="Gloves", row_number=5, lot_number=na(), exp_date=na(),
                     manufacturer=f("Medline")),
    ])
    assert [r for r, _ in dups(ext)] == ["Gloves (row 5)"]
