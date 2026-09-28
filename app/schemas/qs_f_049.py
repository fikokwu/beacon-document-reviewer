"""QS-F-049 — Technical/Quality Review and Disposition Statement."""

from pydantic import BaseModel, Field

from app.schemas.common import Correction, FieldValue, SignOff


class QS049Item(BaseModel):
    number: int = Field(description="Review element number, 1-10.")
    technical: SignOff = Field(default_factory=SignOff)
    quality: SignOff = Field(default_factory=SignOff)


class QS049Extraction(BaseModel):
    form_version: str | None = None
    ddin: FieldValue = Field(default_factory=FieldValue)
    cross_reference: FieldValue = Field(default_factory=FieldValue)
    items: list[QS049Item] = []
    inc_number: FieldValue = Field(default_factory=FieldValue, description="Item 10 INC #.")
    inc_status: FieldValue = Field(default_factory=FieldValue, description="Item 10 Status.")
    corrections: list[Correction] = Field(default_factory=list, description=(
        "Every crossed-out value or struck-through row on the page(s), with any initials/date "
        "written beside it."))
