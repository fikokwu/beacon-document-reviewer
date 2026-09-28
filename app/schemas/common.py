"""Shared extraction and response models.

Extraction models are also sent to Gemini as the response schema, so keep them
simple: no dicts, no unions other than Optional.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FieldStatus = Literal["filled", "blank", "na", "illegible"]
Severity = Literal["error", "warning", "info"]
FormType = Literal["MP-F-023", "QS-F-049", "MP-F-021", "MP-F-018", "UNKNOWN"]

NA_RE = re.compile(r"^\s*n\s*[/\\.]?\s*a\s*\.?\s*$", re.IGNORECASE)
_TALLY_RE = re.compile(r"^[|\\/](?:\s*[|\\/])*$")
_ILLEGIBLE = {"[illegible]", "illegible", "[?]"}

# What Gemini sees for every cell: a plain string (ADR-014). Parsed by FieldValue below.
CELL_DESCRIPTION = (
    'Exact transcription of the cell. "" if the cell is empty. N/A exactly as written. '
    '"[illegible]" if there is ink you cannot read. For a correction, the final value.'
)


def parse_cell(text: str | None) -> dict[str, Any]:
    """Turn the compact string Gemini returns into FieldValue fields."""
    value = (text or "").strip()
    if not value:
        return {"raw": None, "status": "blank"}
    if value.lower() in _ILLEGIBLE:
        return {"raw": None, "status": "illegible"}
    if NA_RE.match(value):
        return {"raw": value, "status": "na"}
    if _TALLY_RE.match(value):
        return {"raw": value, "status": "filled",
                "tally_count": sum(ch in "|\\/" for ch in value)}
    return {"raw": value, "status": "filled"}


class FieldValue(BaseModel):
    """One handwritten or printed cell, transcribed exactly as seen."""

    raw: str | None = Field(None, description="Exact transcription; null if the cell is empty.")
    status: FieldStatus = Field(
        "blank",
        description="filled | blank | na (N/A, NA, N\\A) | illegible (ink present but unreadable). "
        "0 and Ø are filled.",
    )
    struck_through: bool = Field(
        False, description="True if a value was crossed out and replaced (raw = replacement)."
    )
    tally_count: int | None = Field(None, description="Count if the value is tally marks.")
    page: int = 1
    box_2d: list[int] | None = Field(None, description="[ymin, xmin, ymax, xmax] scaled 0-1000.")

    @model_validator(mode="before")
    @classmethod
    def _from_compact_string(cls, data: Any) -> Any:
        if data is None or isinstance(data, str):
            return parse_cell(data)
        return data


class SignOff(BaseModel):
    """A 'By / Date' cell: initials plus a date, or the whole cell marked N/A."""

    initials: FieldValue = Field(default_factory=FieldValue)
    date: FieldValue = Field(default_factory=FieldValue)
    marked_na: bool = Field(False, description="True if the whole cell says N/A.")
    page: int = 1
    box_2d: list[int] | None = None


class Correction(BaseModel):
    """A crossed-out value or struck-through row anywhere on the form (GDP correction)."""

    page: int = 1
    location: str = Field(description="Where: section, row and field, e.g. 'Item 10 – Status'.")
    struck_value: FieldValue = Field(default_factory=FieldValue,
                                     description="The value that was crossed out, if readable.")
    initials: FieldValue = Field(default_factory=FieldValue,
                                 description="Initials written next to the strike-through.")
    date: FieldValue = Field(default_factory=FieldValue,
                             description="Date written next to the strike-through.")


class Issue(BaseModel):
    rule_id: str
    severity: Severity
    page: int
    section: str
    row: str | None = None
    field: str | None = None
    message: str
    evidence: str | None = None
    box_2d: list[int] | None = None


class FormResult(BaseModel):
    """One form inside a multi-form PDF (e.g. several Discard Forms, one per page)."""

    label: str
    page: int
    passed: bool
    message: str
    issues: list[Issue] = []
    needs_confirmation: list[Issue] = []


class ReviewResult(BaseModel):
    form_type: FormType
    form_title: str | None = None
    form_version: str | None = None
    classification_confidence: float = 0.0
    passed: bool
    issues: list[Issue] = []
    needs_confirmation: list[Issue] = []
    pages: int = 0
    processing_ms: int = 0
    message: str | None = None
    forms: list[FormResult] = []  # filled only when the PDF holds several separate forms
    page_images: list[str] = []  # upright JPEG previews (data URIs) for issue highlighting
    page_rotations: list[int] = []  # clockwise rotation applied per page (sent back to /locate)


class LocatedBox(BaseModel):
    index: int = Field(description="The item number from the list.")
    box: list[int] = Field(description="[ymin, xmin, ymax, xmax] scaled 0-1000.")


class LocateResult(BaseModel):
    boxes: list[LocatedBox] = []


class Classification(BaseModel):
    """Output of the classify call."""

    form_code: str | None = Field(
        None, description="Form code exactly as printed bottom-right, e.g. 'MP-F-023.009'.")
    form_title: str | None = Field(None, description="Title printed at the top of the form.")
    confidence: float = Field(0.0, description="0-1: how sure you are of the form code.")
    page_rotations: list[int] = Field(
        [], description="Per page, in order: degrees clockwise (0, 90, 180, 270) to make it "
        "read upright.")
