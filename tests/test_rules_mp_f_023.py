from app.rules.mp_f_023 import check
from app.schemas.mp_f_023 import MP023Extraction, MP023Header, MP023Row
from tests.factories import blank, f, illegible, so


def make(**overrides) -> MP023Extraction:
    """A fully-filled, passing MP-F-023 (modelled on the sample layout)."""
    header = MP023Header(
        donor_number=f("25017"), verified_by=f("KS MW"), cross_reference=f("607512"),
        donor_sex=f("M"), donor_age=f("64"), date_of_recovery=f("04-16-25"),
        instruction_verification=f("KS SL MW"), date_of_processing=f("12-11-25"),
        clean_room_log_review=so("KS", "12-10-25"), tissue_checked_in=so("MW", "12-11-25"),
    )
    rows = [
        MP023Row(name="Posterior Tibialis", produced=f("2"), packaged=f("1")),
        MP023Row(name="Peroneus Longus", produced=f("2"), packaged=f("0")),
        MP023Row(name="", shaded=True),
        MP023Row(name="Femoral Head", produced=f("2"), packaged=f("2")),
    ]
    ext = MP023Extraction(header=header, ops_manager_review=so("AW", "12-10-25"),
                          processing_rows=rows)
    return ext.model_copy(update=overrides)


def test_complete_form_passes():
    assert check(make()) == []


def test_blank_header_field():
    ext = make()
    ext.header.donor_age = blank()
    issues = check(ext)
    assert [(i.rule_id, i.field) for i in issues] == [("MP023-HDR-BLANK", "Donor Age")]
    assert issues[0].severity == "error"


def test_bydate_missing_date():
    ext = make()
    ext.header.tissue_checked_in = so("MW", None)
    issues = check(ext)
    assert [i.rule_id for i in issues] == ["MP023-HDR-BYDATE"]
    assert "initials but no date" in issues[0].message


def test_bydate_completely_blank_is_header_blank():
    ext = make()
    ext.header.clean_room_log_review = so(None, None)
    assert [i.rule_id for i in check(ext)] == ["MP023-HDR-BLANK"]


def test_bydate_date_without_initials():
    ext = make()
    ext.header.clean_room_log_review = so(None, "12-10-25")
    issues = check(ext)
    assert [i.rule_id for i in issues] == ["MP023-HDR-BYDATE"]
    assert "no initials" in issues[0].message


def test_ops_review_blank_and_partial():
    ext = make(ops_manager_review=so(None, None))
    assert [i.rule_id for i in check(ext)] == ["MP023-OPS-REVIEW"]
    ext = make(ops_manager_review=so("AW", None))
    issues = check(ext)
    assert [i.rule_id for i in issues] == ["MP023-OPS-REVIEW"]
    assert "no date" in issues[0].message


def test_row_produced_and_packaged_blank():
    ext = make()
    ext.processing_rows[3].packaged = blank()
    ext.processing_rows[0].produced = blank()
    issues = check(ext)
    assert sorted((i.rule_id, i.row) for i in issues) == [
        ("MP023-ROW-PACKAGED", "Femoral Head"),
        ("MP023-ROW-PRODUCED", "Posterior Tibialis"),
    ]


def test_shaded_and_voided_rows_ignored():
    ext = make()
    ext.processing_rows.append(MP023Row(name="Gracilis", shaded=True))
    ext.processing_rows.append(MP023Row(name="Tibia Shaft", row_voided=True))
    assert check(ext) == []


def test_zero_counts_as_filled():
    ext = make()
    ext.processing_rows[1].produced = f("0")
    ext.processing_rows[1].packaged = f("Ø")
    assert check(ext) == []


def test_illegible_is_warning_not_error():
    ext = make()
    ext.header.donor_age = illegible()
    issues = check(ext)
    assert [(i.rule_id, i.severity) for i in issues] == [("MP023-HDR-BLANK", "warning")]


def test_empty_extraction_flags_everything_in_header():
    issues = check(MP023Extraction())
    assert {i.rule_id for i in issues} == {"MP023-HDR-BLANK", "MP023-OPS-REVIEW"}
    assert len([i for i in issues if i.rule_id == "MP023-HDR-BLANK"]) == 10
