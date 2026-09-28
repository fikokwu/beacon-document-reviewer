from app.rules.registry import FORMS, build_result
from app.schemas.common import Issue


def issue(severity: str) -> Issue:
    return Issue(rule_id="X", severity=severity, page=1, section="S", message="m")


def test_registry_has_all_four_forms():
    assert set(FORMS) == {"MP-F-023", "QS-F-049", "MP-F-021", "MP-F-018"}


def test_build_result_splits_warnings_and_sets_passed():
    r = build_result("MP-F-021", [issue("info"), issue("warning")])
    assert r.passed and len(r.issues) == 1 and len(r.needs_confirmation) == 1
    r = build_result("MP-F-021", [issue("error")])
    assert not r.passed


def test_all_good_message():
    r = build_result("MP-F-023", [])
    assert r.passed
    assert r.message == "Passed all checks. No missing or inconsistent entries were found."


def test_passed_with_notes_and_confirmations_message():
    r = build_result("MP-F-021", [issue("info"), issue("warning"), issue("warning")])
    assert r.message == "Passed all checks. See 1 note and 2 entries to confirm by eye below."


def test_failed_message_counts_issues_and_sections():
    r = build_result("MP-F-021", [issue("error"), issue("error")])
    assert r.message == "2 issues to fix before review in S."
    other = issue("error").model_copy(update={"section": "T"})
    r = build_result("MP-F-021", [issue("error"), other, issue("info")])
    assert r.message == "2 issues to fix before review across 2 sections. Also 1 note."


def test_multi_form_results_split_by_page():
    page2 = issue("error").model_copy(update={"page": 2})
    r = build_result("MP-F-018", [page2], form_labels=[(1, "Form 1"), (2, "Form 2"), (3, "Form 3")])
    assert [(f.label, f.passed, len(f.issues)) for f in r.forms] == [
        ("Form 1", True, 0), ("Form 2", False, 1), ("Form 3", True, 0)]
    assert r.message == "This PDF contains 3 separate forms: 2 passed, 1 needs fixing."
    assert r.forms[0].message.startswith("Passed all checks")


def test_multi_form_all_passed_message():
    r = build_result("MP-F-018", [], form_labels=[(1, "A"), (2, "B")])
    assert r.message == "This PDF contains 2 separate forms. All passed. No missing or inconsistent entries were found."


def test_single_form_has_no_form_list():
    assert build_result("MP-F-018", [], form_labels=[(1, "A")]).forms == []
