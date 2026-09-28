"""MP-F-018 — Tissue Discard Form. One PDF may hold several forms (one per page)."""

from pydantic import BaseModel, Field

from app.schemas.common import Correction, FieldValue, SignOff


class DiscardRow(BaseModel):
    row_number: int = Field(description="1-based position of the row in the tissue list.")
    graft_id: FieldValue = Field(default_factory=FieldValue, description=(
        'Graft ID as written. N/A as written; "-" if only a line/dash is drawn; "" if empty.'))
    tissue_description: FieldValue = Field(default_factory=FieldValue)
    x_confirmed: FieldValue = Field(default_factory=FieldValue, description=(
        'The small box in the last "X" column: "X" if it has any mark (X, check, slash), '
        '"" if empty.'))


class DiscardForm(BaseModel):
    page: int = Field(1, description="Page number this form is on.")
    donor_number: FieldValue = Field(default_factory=FieldValue)
    discard_authorized: SignOff = Field(default_factory=SignOff)
    reason_for_discard: FieldValue = Field(default_factory=FieldValue)
    status_unprocessed: bool = Field(description="'Unprocessed Tissue' box is checked.")
    status_in_processing: bool = Field(description="'In Processing Tissue' box is checked.")
    status_unreleased_packaged: bool = Field(
        description="'Unreleased Packaged Tissue' box is checked.")
    status_released_packaged: bool = Field(
        description="'Released Packaged Tissue' box is checked.")
    rows: list[DiscardRow] = []
    tissue_discarded_by: FieldValue = Field(default_factory=FieldValue)
    confirmed_by: FieldValue = Field(default_factory=FieldValue)
    discarded_date: FieldValue = Field(default_factory=FieldValue)
    released_freezerpro_updated_by: FieldValue = Field(default_factory=FieldValue)
    released_date: FieldValue = Field(default_factory=FieldValue)
    donor_chart_updated_by: FieldValue = Field(default_factory=FieldValue)
    donor_chart_date: FieldValue = Field(default_factory=FieldValue)


class DiscardExtraction(BaseModel):
    form_version: str | None = None
    forms: list[DiscardForm] = []
    corrections: list[Correction] = Field(default_factory=list, description=(
        "Every crossed-out value or struck-through row on the page(s), with any initials/date "
        "written beside it."))
