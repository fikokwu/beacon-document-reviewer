from app.rules.mp_f_018 import check
from app.schemas.mp_f_018 import DiscardExtraction, DiscardForm, DiscardRow
from tests.factories import blank, f, illegible, na, so


def form(page: int = 1, **overrides) -> DiscardForm:
    """A complete, passing discard form modelled on sample page 2 (unprocessed, dashes)."""
    base = DiscardForm(
        page=page, donor_number=f("22043"), discard_authorized=so("KS", "09-03-24"),
        reason_for_discard=f("1 will not be processed"),
        status_unprocessed=True, status_in_processing=False,
        status_unreleased_packaged=False, status_released_packaged=False,
        rows=[
            DiscardRow(row_number=1, graft_id=f("-"), tissue_description=f("1 Right Femur"),
                       x_confirmed=f("X")),
            DiscardRow(row_number=2, graft_id=f("-"), tissue_description=f("1 2x Gracilis"),
                       x_confirmed=f("X")),
        ],
        tissue_discarded_by=f("NM"), confirmed_by=f("KS"), discarded_date=f("09-03-24"),
        released_freezerpro_updated_by=na(), released_date=na(),
        donor_chart_updated_by=f("MNC"), donor_chart_date=f("09-04-24"),
    )
    return base.model_copy(update=overrides, deep=True)


def ids(issues):
    return sorted((i.rule_id, i.page, i.field) for i in issues)


def test_complete_forms_pass_and_each_page_is_checked():
    ext = DiscardExtraction(forms=[form(1), form(2), form(3)])
    assert check(ext) == []


def test_top_fields_blank():
    ext = DiscardExtraction(forms=[form(2, donor_number=blank(), reason_for_discard=blank())])
    assert ids(check(ext)) == [("DISC-HDR-BLANK", 2, "Donor #"),
                               ("DISC-HDR-BLANK", 2, "Reason for Discard")]


def test_authorized_needs_initials_and_date():
    issues = check(DiscardExtraction(forms=[form(discard_authorized=so("KS", None))]))
    assert ids(issues) == [("DISC-AUTH-BYDATE", 1, "Discard Authorized By/Date")]
    assert "no date" in issues[0].message
    issues = check(DiscardExtraction(forms=[form(discard_authorized=so(None, None))]))
    assert ids(issues) == [("DISC-HDR-BLANK", 1, "Discard Authorized By/Date")]


def test_signature_counts_as_initials():
    ext = DiscardExtraction(forms=[form(discard_authorized=so("E. Widdfield", "02/10/23"))])
    assert check(ext) == []


def test_no_status_checked():
    issues = check(DiscardExtraction(forms=[form(status_unprocessed=False)]))
    assert ids(issues) == [("DISC-STATUS", 1, "Tissue Status")]


def test_multiple_statuses_checked():
    issues = check(DiscardExtraction(forms=[form(status_in_processing=True)]))
    assert [i.rule_id for i in issues] == ["DISC-STATUS"]
    assert "More than one" in issues[0].message


def test_graft_ids_listed_require_packaged_status():
    rows = [DiscardRow(row_number=1, graft_id=f("FD-24-011"), tissue_description=f("Femur"),
                       x_confirmed=f("X"))]
    issues = check(DiscardExtraction(forms=[form(rows=rows)]))  # unprocessed checked
    assert [i.rule_id for i in issues] == ["DISC-STATUS-GRAFT"]
    assert "FD-24-011" in issues[0].message
    ok = form(rows=rows, status_unprocessed=False, status_released_packaged=True)
    assert check(DiscardExtraction(forms=[ok])) == []


def test_na_graft_ids_require_unprocessed_or_in_processing():
    rows = [DiscardRow(row_number=1, graft_id=na(), tissue_description=f("R&L Patellar"),
                       x_confirmed=f("X"))]
    bad = form(rows=rows, status_unprocessed=False, status_unreleased_packaged=True)
    issues = check(DiscardExtraction(forms=[bad]))
    assert [i.rule_id for i in issues] == ["DISC-STATUS-GRAFT"]
    good = form(rows=rows, status_unprocessed=False, status_in_processing=True)
    assert check(DiscardExtraction(forms=[good])) == []


def test_dash_graft_ids_count_as_na():
    bad = form(status_unprocessed=False, status_released_packaged=True)  # rows use "-"
    assert [i.rule_id for i in check(DiscardExtraction(forms=[bad]))] == ["DISC-STATUS-GRAFT"]


def test_missing_x_box():
    f1 = form()
    f1.rows[1].x_confirmed = blank()
    issues = check(DiscardExtraction(forms=[f1]))
    assert [(i.rule_id, i.row) for i in issues] == [("DISC-ROW-X", "Row 2 (1 2x Gracilis)")]


def test_bottom_blank_but_na_is_fine():
    issues = check(DiscardExtraction(forms=[form(3, confirmed_by=blank(), donor_chart_date=blank())]))
    assert ids(issues) == [("DISC-BOTTOM-BLANK", 3, "Confirmed By"),
                           ("DISC-BOTTOM-BLANK", 3, "Donor Chart – Date")]


def test_illegible_is_warning():
    issues = check(DiscardExtraction(forms=[form(confirmed_by=illegible())]))
    assert [(i.rule_id, i.severity) for i in issues] == [("DISC-BOTTOM-BLANK", "warning")]


def test_errors_on_one_page_only_affect_that_page():
    issues = check(DiscardExtraction(forms=[form(1), form(2, tissue_discarded_by=blank()),
                                            form(3)]))
    assert ids(issues) == [("DISC-BOTTOM-BLANK", 2, "Tissue Discarded By")]


def test_no_forms_read():
    assert [i.rule_id for i in check(DiscardExtraction())] == ["DISC-NO-FORM"]
