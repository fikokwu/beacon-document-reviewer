## This form: MP-F-018 — "Tissue Discard Form"

Each page is a **separate Discard Form**. Return one entry in `forms` for each page you are given. In this call that's normally exactly one, with `page` set to the page number.

### Top of the form
- `donor_number`: "Donor #:".
- `discard_authorized` (SignOff): "Discard Authorized By/Date (MM/DD/YY)". Initials or a signature go in `initials`, the date in `date`. Ignore notes like "(late entry)".
- `reason_for_discard`: the text after "Reason for Discard:" (printed or handwritten).
- Tissue Status checkboxes: set each boolean to **true only if that box is checked** (✓, X or filled): `status_unprocessed` (Unprocessed Tissue), `status_in_processing` (In Processing Tissue), `status_unreleased_packaged` (Unreleased Packaged Tissue), `status_released_packaged` (Released Packaged Tissue). Empty boxes are false.

### Tissue list (middle table: Graft IDs | Tissue Description | Storage Location | X)
- One entry per row that has **any** writing (a graft ID, a tissue description or a mark in the X box), top to bottom. Omit completely empty rows. Skip the Storage Location column.
- `row_number`: position in the table, starting at 1.
- `graft_id`: as written. N/A exactly as written. If only a horizontal line/dash is drawn, write `"-"`.
- `tissue_description`: as written, e.g. `1. R&L Patellar`, `2x Anterior Tibialis`.
- `x_confirmed`: the small box in the last column, `"X"` if it has any mark, `""` if it is empty.

### Bottom of the form
- `tissue_discarded_by`: "Tissue Discarded By".
- `confirmed_by`: "Confirmed By".
- `discarded_date`: the "Date (MM/DD/YY)" on that same line.
- `released_freezerpro_updated_by` and `released_date`: the "Released Packaged Tissue … FreezerPro Updated By" line and its Date.
- `donor_chart_updated_by` and `donor_chart_date`: the "Unprocessed Tissue, In Processing Tissue, Unreleased Packaged Tissue … Log / FreezerPro Updated By" line and its Date.
- Ignore footnotes written below the form.
