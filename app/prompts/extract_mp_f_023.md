## This form: MP-F-023 — "MS Processing Instructions / Tissue Open Checklist" (1 page)

### `header` (the boxed grid at the very top)
- `donor_number`: "Donor #" (the number is often printed in the box label, e.g. "Donor # 25017").
- `verified_by`: "Verified By:" initials, in the lower half of the Donor # box.
- `cross_reference`: "Cross Reference #".
- `donor_sex`, `donor_age`, `date_of_recovery`: the matching columns.
- `instruction_verification`: "Instruction Verification – each team member to initial". Transcribe all initials as one string.
- `date_of_processing`: "Date of Processing".
- `clean_room_log_review` (SignOff): "Clean Room Log Review By / Date".
- `tissue_checked_in` (SignOff): "Tissue Checked In By / Date".

### `ops_manager_review` (SignOff)
The line in the middle of the page: "Operations Manager Review – Initials / Date (MM/DD/YY): ____". Initials and date are written after the colon.

### `processing_rows`
The large lower table with columns: Processing Instructions | FRZ/FD | Irradiated | # Produced | # Packaged | Comments.
- One entry per row that has a tissue name in the first column, top to bottom (e.g. "Posterior Tibialis", "Femoral Head", "Cancellous 1-10 mm"). Transcribe the name as printed.
- `shaded=true` only for rows that are grey/shaded across the table (omit it otherwise). Rows with no name and no entries (blank separators) are omitted.
- Only `produced` and `packaged` are needed from the other columns (skip FRZ/FD, Irradiated, Comments). They often contain numbers, volumes (e.g. `150cc`) or counts like `5x30cc`. If a value was corrected, use the final value.
- Do NOT include the upper "Tissue / Description / Received L R / Comments" tables, the TGLN labels, or Special Instructions.
