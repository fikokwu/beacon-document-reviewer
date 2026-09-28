from fastapi.testclient import TestClient

from app import main, pipeline
from app.gemini_client import GeminiError
from app.pdf_utils import PdfError
from app.schemas.common import ReviewResult

client = TestClient(main.app)
PDF = ("form.pdf", b"%PDF-1.4 fake", "application/pdf")


def test_review_returns_result(monkeypatch):
    result = ReviewResult(form_type="MP-F-023", passed=True, pages=1,
                          message="Passed all checks. No missing or inconsistent entries were found.")
    monkeypatch.setattr(pipeline, "review_pdf", lambda data: result)
    resp = client.post("/api/review", files={"file": PDF})
    assert resp.status_code == 200
    assert resp.json()["form_type"] == "MP-F-023" and resp.json()["passed"] is True


def test_rejects_non_pdf():
    resp = client.post("/api/review", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert resp.status_code == 400 and "PDF" in resp.json()["detail"]


def test_missing_file_is_422():
    assert client.post("/api/review").status_code == 422


def test_pdf_error_is_400(monkeypatch):
    def boom(data):
        raise PdfError("The PDF has 12 pages; the limit is 10.")
    monkeypatch.setattr(pipeline, "review_pdf", boom)
    resp = client.post("/api/review", files={"file": PDF})
    assert resp.status_code == 400 and "limit is 10" in resp.json()["detail"]


def test_ai_error_is_503(monkeypatch):
    def boom(data):
        raise GeminiError("The AI service is busy right now. Please try again in a minute.")
    monkeypatch.setattr(pipeline, "review_pdf", boom)
    resp = client.post("/api/review", files={"file": PDF})
    assert resp.status_code == 503 and "busy" in resp.json()["detail"]


def test_locate_endpoint(monkeypatch):
    monkeypatch.setattr(pipeline, "locate_issues", lambda data, issues, rots: [[1, 2, 3, 4]])
    issue = {"rule_id": "X", "severity": "error", "page": 1, "section": "S", "message": "m"}
    import json
    resp = client.post("/api/locate", files={"file": PDF},
                       data={"issues": json.dumps([issue]), "rotations": "[0]"})
    assert resp.status_code == 200 and resp.json() == {"boxes": [[1, 2, 3, 4]]}


def test_locate_rejects_bad_issue_list():
    resp = client.post("/api/locate", files={"file": PDF}, data={"issues": "not json"})
    assert resp.status_code == 400


def test_rate_limit_falls_back_to_second_model(monkeypatch):
    from google.genai import errors

    from app import config
    from app.gemini_client import GeminiClient
    from app.schemas.common import Classification

    calls = []

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "primary":
                raise errors.ClientError(429, {"error": {"message": "quota"}}, None)

            class Resp:
                text = '{"form_code": "MP-F-023.009", "confidence": 1, "page_rotations": [0]}'
                usage_metadata = None
            return Resp()

    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "backup")
    c = GeminiClient(api_key="k", model="primary")
    c._client = type("C", (), {"models": Models()})()
    result = c.generate_json([], "p", Classification)
    assert calls == ["primary", "backup"] and result.form_code == "MP-F-023.009"
