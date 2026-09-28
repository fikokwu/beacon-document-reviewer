"""MP-F-021 — MS Processing & Packaging Lot Log (2 pages)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Correction, FieldValue


class LotRowBase(BaseModel):
    name: str = Field(description="Item name as printed/written in the first column.")
    row_number: int = Field(description="1-based position of the row within its table.")
    row_voided: bool = Field(False, description="Whole row struck through (voided).")
    void_initials: FieldValue = Field(
        default_factory=FieldValue,
        description="Only if row_voided: initials written on/next to the strike-through line.")
    void_date: FieldValue = Field(
        default_factory=FieldValue,
        description="Only if row_voided: date written on/next to the strike-through line.")
    page: int = 1


class LotP1ItemRow(LotRowBase):
    lot_number: FieldValue = Field(default_factory=FieldValue)
    exp_date: FieldValue = Field(default_factory=FieldValue)
    manufacturer: FieldValue = Field(default_factory=FieldValue)


class LotRegenMedRow(LotRowBase):
    lot: FieldValue = Field(default_factory=FieldValue)
    qty_used: FieldValue = Field(default_factory=FieldValue)


class LotP2ItemRow(LotRowBase):
    table: Literal["left", "right"] = "left"
    load_number: FieldValue = Field(default_factory=FieldValue)
    sterilization_date: FieldValue = Field(default_factory=FieldValue)


class LotPackagingRow(LotRowBase):
    lot: FieldValue = Field(default_factory=FieldValue)
    qty_used: FieldValue = Field(default_factory=FieldValue)


class LotLogExtraction(BaseModel):
    form_version: str | None = None
    donor_number: FieldValue = Field(default_factory=FieldValue)
    p1_items: list[LotP1ItemRow] = []
    p1_regenmed_items: list[LotRegenMedRow] = []
    p2_items: list[LotP2ItemRow] = []
    p2_packaging: list[LotPackagingRow] = []
    corrections: list[Correction] = Field(default_factory=list, description=(
        "Every crossed-out single value (not whole voided table rows, which use row_voided) on the page(s), with any initials/date "
        "written beside it."))
