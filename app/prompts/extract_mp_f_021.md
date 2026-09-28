## This form: MP-F-021 — "MS Processing & Packaging Lot Log" (usually 2 pages)

Ignore the PROCESSING / PACKAGING header blocks at the top of page 1 (TPM initials, room temperature, RH, pressure, PI numbers). Transcribe `donor_number` ("Donor #:" at the top right).

For every table:
- `name` = the item name in the first column, exactly as written (printed or handwritten), **including any bracketed size/number**, e.g. `Gloves (7.5)`, `Poly Bags (15)`, `8 x 18 (10)`. Keep empty brackets as `( )` if that's what is written.
- `row_number` = the row's position in that table's body, counting every body row from the top **including empty ones**, starting at 1. A reviewer uses it to find the row.
- **Return one entry for EVERY body row of every table, top to bottom, and never skip a row.** That includes rows whose cells are all empty, and completely empty rows at the bottom (use `name: ""` for rows with no name). A printed item name with empty cells is exactly what reviewers need to see.
- Voided rows (a line struck through the whole row) get `row_voided=true`. If initials and a date are written on or next to the strike-through, put them in `void_initials` and `void_date` (e.g. `LS` and `01-23-26`). Omit both for rows that are not voided.
- `page` = 1 or 2.

### Page 1
- `p1_items`: table "Item | Lot Number | Exp. Date | Manufacturer". Fields: `lot_number`, `exp_date`, `manufacturer`. N/A entries are written as they appear.
- `p1_regenmed_items`: table "RegenMed Item | Lot | Qty Used". Fields: `lot`, `qty_used` (often tally marks).

### Page 2
- `p2_items`: the two side-by-side tables "Item | Load # | Sterilization Date". Use `table="left"` for the left table and `table="right"` for the right table. Number rows separately per table.
  - `load_number`: the Load # column has two sub-columns. Transcribe both numbers separated by a space (e.g. `2 3`). If only one number is present, transcribe just that one.
  - `sterilization_date`: e.g. `15 APR 2026`.
- `p2_packaging`: table "Packaging | Lot | Qty Used". Fields: `lot`, `qty_used` (tally marks as characters; `0` is a value).
