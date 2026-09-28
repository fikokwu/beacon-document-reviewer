"""Pipeline tests with a fake Gemini client (offline) plus live tests on the samples."""

import json

import pytest

from app.gemini_client import to_gemini_schema
from app.pipeline import locate_issues, resolve_form, review_pdf
from app.schemas.common import Classification, Issue, LocatedBox, LocateResult
from app.schemas.mp_f_021 import LotLogExtraction, LotP1ItemRow, LotP2ItemRow
from tests.conftest import FIXTURES, sample_bytes
from tests.factories import f, na


class FakeClient:
    """Returns canned responses by schema type and records what it was sent."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[tuple[int, type]] = []

    def generate_json(self, images, prompt, schema, model=None):
        self.calls.append((len(images), schema))
        response = self.responses[schema]
        return response.pop(0) if isinstance(response, list) else response


LOT_LOG = "2142-635946 lot log.pdf"


@pytest.mark.parametrize(
    "code, title, expected",
    [
        ("MP-F-023.009", None, ("MP-F-023", "009")),
        ("QS-F-049.010", None, ("QS-F-049", "010")),
        ("MP-F-021.014", None, ("MP-F-021", "014")),
        ("MPF021", None, ("MP-F-021", None)),
        ("mp - f - 023 . 9", None, ("MP-F-023", "9")),
        ("MP-F-018.005", None, ("MP-F-018", "005")),
        ("MP-F-099.001", "Deviation Report", ("UNKNOWN", None)),
        (None, "Tissue Discard Form", ("MP-F-018", None)),
        (None, "MS Processing & Packaging Lot Log", ("MP-F-021", None)),
        (None, "Technical/Quality Review and Disposition Statement", ("QS-F-049", None)),
        (None, "Invoice", ("UNKNOWN", None)),
    ],
)
def test_resolve_form(code, title, expected):
    assert resolve_form(Classification(form_code=code, form_title=title)) == expected


def test_pipeline_extracts_pages_in_parallel_and_merges():
    page1 = LotLogExtraction(donor_number=f("2142-635946"), p1_items=[
        LotP1ItemRow(name="Gown (L)", row_number=2, lot_number=f("11025080244"),
                     exp_date=na(), manufacturer=f("Medline")),
    ])
    page2 = LotLogExtraction(p2_items=[
        LotP2ItemRow(name="Sieve", row_number=16, table="right"),  # page left at default 1
        LotP2ItemRow(name="Drill", row_number=18, load_number=f("3 3"),
                     sterilization_date=f("17 APR 2026")),
    ])
    client = FakeClient({
        Classification: Classification(form_code="MP-F-021.014", confidence=0.97,
                                       page_rotations=[0, 0]),
        LotLogExtraction: [page1, page2, LotLogExtraction()],  # page 1, page 2 left, page 2 right
    })
    result = review_pdf(sample_bytes(LOT_LOG), client=client)

    assert client.calls == [(2, Classification)] + [(1, LotLogExtraction)] * 3
    assert result.form_type == "MP-F-021" and result.form_version == "014"
    assert result.pages == 2 and not result.passed
    assert sorted(i.field for i in result.issues) == ["Load #", "Sterilization Date"]
    assert all(i.page == 2 for i in result.issues)  # page stamped from the per-page call


def test_pipeline_unknown_form_skips_extraction():
    client = FakeClient({Classification: Classification(form_code="XX-F-999", confidence=0.4)})
    result = review_pdf(sample_bytes(LOT_LOG), client=client)
    assert result.form_type == "UNKNOWN" and not result.issues
    assert "supported forms" in result.message
    assert len(client.calls) == 1


def test_locate_returns_boxes_aligned_with_issues():
    issues = [
        Issue(rule_id="A", severity="info", page=2, section="S", message="note"),
        Issue(rule_id="B", severity="error", page=2, section="S", message="blank"),
        Issue(rule_id="C", severity="error", page=1, section="S", message="blank"),
    ]
    # Per page, items are numbered errors-first: page 2 -> 1:B, 2:A ; page 1 -> 1:C
    page2 = LocateResult(boxes=[LocatedBox(index=1, box=[10, 20, 30, 40]),
                                LocatedBox(index=2, box=[50, 60, 70, 2000])])  # bad -> None
    page1 = LocateResult(boxes=[LocatedBox(index=1, box=[1, 2, 3, 4])])

    class PageClient:
        def generate_json(self, images, prompt, schema, model=None):
            return page2 if "rule" not in prompt and "note" in prompt else page1

    boxes = locate_issues(sample_bytes(LOT_LOG), issues, client=PageClient())
    assert boxes == [None, [10, 20, 30, 40], [1, 2, 3, 4]]


def test_gemini_schemas_require_every_field():
    schema = to_gemini_schema(LotLogExtraction)
    text = json.dumps(schema)
    assert "$ref" not in text and '"default"' not in text
    row = schema["properties"]["p1_items"]["items"]
    assert row["properties"]["lot_number"]["type"] == "string"  # compact cell (ADR-014)
    assert set(row["required"]) == {"name", "row_number", "lot_number", "exp_date",
                                    "manufacturer"}


# ---------- live: real Gemini on the samples, compared to the team baseline ----------

EXPECTED = sorted((FIXTURES / "expected").glob("*.json"))


@pytest.mark.live
@pytest.mark.parametrize("path", EXPECTED, ids=lambda p: p.stem)
def test_live_sample_matches_baseline(path):
    expected = json.loads(path.read_text())
    result = review_pdf((FIXTURES / expected["fixture"]).read_bytes())
    print(result.model_dump_json(indent=2))

    assert result.form_type == expected["form_type"]
    assert result.passed == expected["passed"]
    for exp in expected["expected_issues"]:
        assert any(
            i.rule_id == exp["rule_id"] and i.page == exp["page"]
            and (exp["field"] is None or i.field == exp["field"])
            and exp["row_contains"].lower() in (i.row or "").lower()
            for i in result.issues + result.needs_confirmation
        ), f"missing expected issue {exp}"
