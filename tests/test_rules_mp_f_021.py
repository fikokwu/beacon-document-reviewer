from app.rules.mp_f_021 import check
from app.schemas.mp_f_021 import (
    LotLogExtraction,
    LotP1ItemRow,
    LotP2ItemRow,
    LotPackagingRow,
    LotRegenMedRow,
)
from tests.factories import blank, f, na


def make() -> LotLogExtraction:
    """A passing Lot Log modelled on the sample layout."""
    return LotLogExtraction(
        p1_items=[
            LotP1ItemRow(name="Process Pack", row_number=1, lot_number=f("25LBN680"),
                         exp_date=f("2030-06-30"), manufacturer=f("Medline")),
            LotP1ItemRow(name="Gloves", row_number=2, lot_number=na(), exp_date=na(),
                         manufacturer=na()),
        ],
        p1_regenmed_items=[
            LotRegenMedRow(name="Labels", row_number=1, lot=f("IR-25-009"),
                           qty_used=f("|", tally_count=1)),
        ],
        p2_items=[
            LotP2ItemRow(name="BS Small Tray", row_number=1, table="left", page=2,
                         load_number=f("2 3", page=2), sterilization_date=f("15 APR 2026", 2)),
            LotP2ItemRow(name="Sieve", row_number=15, table="right", page=2, row_voided=True,
                         void_initials=f("LS", 2), void_date=f("01-23-26", 2)),
            LotP2ItemRow(name="Tendon Sizer", row_number=16, table="right", page=2,
                         load_number=f("2 3", page=2), sterilization_date=f("15 APR 2026", 2)),
        ],
        p2_packaging=[
            LotPackagingRow(name="6.5x17 (5)", row_number=4, page=2, lot=f("IR-25-009", 2),
                            qty_used=f("0", 2)),
        ],
    )


def errors(issues):
    return [i for i in issues if i.severity == "error"]


def test_complete_log_passes_with_voided_row_info():
    issues = check(make())
    assert errors(issues) == []
    assert [(i.rule_id, i.severity, i.page) for i in issues] == [
        ("LOT-VOIDED-ROW", "info", 2)]


def test_sample_sieve_error_blank_row_on_page_2_right():
    ext = make()
    ext.p2_items.append(LotP2ItemRow(name="Sieve", row_number=17, table="right", page=2))
    ext.p2_items[1].row_voided = False  # no void next to row 17 -> a real blank row
    ext.p2_items[1].load_number = f("1 3", 2)
    ext.p2_items[1].sterilization_date = f("08 APR 2026", 2)
    errs = errors(check(ext))
    assert sorted((i.rule_id, i.section, i.field) for i in errs) == [
        ("LOT-P2-ITEM", "Page 2 – Item (right table)", "Load #"),
        ("LOT-P2-ITEM", "Page 2 – Item (right table)", "Sterilization Date"),
    ]
    assert all(i.row == "Sieve (row 17)" and i.page == 2 for i in errs)


def test_p1_item_blank_manufacturer():
    ext = make()
    ext.p1_items[0].manufacturer = blank()
    assert [(i.rule_id, i.field) for i in errors(check(ext))] == [
        ("LOT-P1-ITEM", "Manufacturer")]


def test_p1_regenmed_blank_qty_and_lot():
    ext = make()
    ext.p1_regenmed_items[0].qty_used = blank()
    ext.p1_regenmed_items[0].lot = blank()
    assert sorted(i.field for i in errors(check(ext))) == ["Lot", "Qty Used"]


def test_p2_packaging_blank_qty():
    ext = make()
    ext.p2_packaging[0].qty_used = blank(page=2)
    errs = errors(check(ext))
    assert [(i.rule_id, i.field, i.page) for i in errs] == [("LOT-P2-PACKAGING", "Qty Used", 2)]


def test_left_table_checked_too():
    ext = make()
    ext.p2_items[0].sterilization_date = blank(page=2)
    errs = errors(check(ext))
    assert [(i.section, i.field) for i in errs] == [
        ("Page 2 – Item (left table)", "Sterilization Date")]


def test_void_info_says_who_and_when():
    info = next(i for i in check(make()) if i.rule_id == "LOT-VOIDED-ROW")
    assert "by LS on 01-23-26" in info.message


def test_unsigned_void_is_error():
    ext = make()
    ext.p1_items.append(LotP1ItemRow(name="Gown (L)", row_number=3, row_voided=True))
    errs = [i for i in check(ext) if i.row == "Gown (L) (row 3)"]
    assert [(i.rule_id, i.severity) for i in errs] == [("LOT-VOID-UNSIGNED", "error")]
    assert "no initials and no date" in errs[0].message


def test_void_with_initials_but_no_date_is_error():
    ext = make()
    ext.p2_items[1].void_date = blank(page=2)
    assert [i.rule_id for i in errors(check(ext))] == ["LOT-VOID-UNSIGNED"]


def test_skipped_row_number_needs_confirmation():
    ext = make()
    ext.p2_items[2].row_number = 17  # right table now has rows 15 and 17: 16 was skipped
    unread = [i for i in check(ext) if i.rule_id == "LOT-ROW-UNREAD"]
    assert [(i.row, i.severity, i.section) for i in unread] == [
        ("row 16", "warning", "Page 2 – Item (right table)")]


def test_no_gap_no_unread_warning():
    assert not [i for i in check(make()) if i.rule_id == "LOT-ROW-UNREAD"]


def test_rows_without_name_are_ignored():
    ext = make()
    ext.p2_packaging.append(LotPackagingRow(name="  ", row_number=9, page=2))
    assert errors(check(ext)) == []


def test_empty_row_next_to_void_is_flagged_not_failed():
    ext = make()  # right table: row 15 voided
    ext.p2_items[2].row_number = 17  # Tendon Sizer moves down
    ext.p2_items.append(LotP2ItemRow(name="Sieve", row_number=16, table="right", page=2))
    issues = check(ext)
    assert errors(issues) == []
    flagged = [i for i in issues if i.rule_id == "LOT-VOID-ADJACENT"]
    assert [(i.row, i.severity) for i in flagged] == [("Sieve (row 16)", "warning")]


def test_partly_filled_row_next_to_void_still_fails():
    ext = make()
    ext.p2_items[2].row_number = 17
    ext.p2_items.append(LotP2ItemRow(name="Sieve", row_number=16, table="right", page=2,
                                     load_number=f("1 3", 2)))
    assert [(i.rule_id, i.field) for i in errors(check(ext))] == [
        ("LOT-P2-ITEM", "Sterilization Date")]
