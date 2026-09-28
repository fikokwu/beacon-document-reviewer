"""MP-F-023 — MS Processing Instructions / Tissue Open Checklist."""

from pydantic import BaseModel, Field

from app.schemas.common import Correction, FieldValue, SignOff


class MP023Header(BaseModel):
    donor_number: FieldValue = Field(default_factory=FieldValue)
    verified_by: FieldValue = Field(default_factory=FieldValue)
    cross_reference: FieldValue = Field(default_factory=FieldValue)
    donor_sex: FieldValue = Field(default_factory=FieldValue)
    donor_age: FieldValue = Field(default_factory=FieldValue)
    date_of_recovery: FieldValue = Field(default_factory=FieldValue)
    instruction_verification: FieldValue = Field(
        default_factory=FieldValue, description="Initials of each team member."
    )
    date_of_processing: FieldValue = Field(default_factory=FieldValue)
    clean_room_log_review: SignOff = Field(default_factory=SignOff)
    tissue_checked_in: SignOff = Field(default_factory=SignOff)


class MP023Row(BaseModel):
    name: str = Field(description="Tissue name as printed/written in the first column.")
    shaded: bool = Field(False, description="True for grey/shaded spacer rows.")
    row_voided: bool = False
    produced: FieldValue = Field(default_factory=FieldValue)
    packaged: FieldValue = Field(default_factory=FieldValue)
    page: int = 1


class MP023Extraction(BaseModel):
    form_version: str | None = None
    header: MP023Header = Field(default_factory=MP023Header)
    ops_manager_review: SignOff = Field(default_factory=SignOff)
    processing_rows: list[MP023Row] = []
    corrections: list[Correction] = Field(default_factory=list, description=(
        "Every crossed-out value or struck-through row on the page(s), with any initials/date "
        "written beside it."))
