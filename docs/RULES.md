# What the Reviewer Checks — Plain-English Rule Catalog

This page lists every check the app runs, written for QA reviewers, judges and non-engineers. Each rule has a stable **ID**. That ID appears in the app's results and in our tests.

**Severity**
- **Error**: the form fails. A person must fix it.
- **Warning / Needs confirmation**: the app couldn't read the field with confidence, so a person should look.
- **Info**: worth a glance, but not a failure.

**Terms used below**
- **Blank**: nothing written in the box.
- **N/A**: the box says N/A (also accepted: `NA`, `N\A`, `n/a`).
- **Zero counts as filled.** `0` or `Ø` is a real answer, not a blank.
- **Tally marks** (`|`, `||`, `||||`) count as a filled quantity.
- **Voided row**: a whole row crossed out with a line, usually initialed and dated.

---

## MP-F-023 — MS Processing Instructions / Tissue Open Checklist (1 page)

| ID | What we check | Example message |
|---|---|---|
| `MP023-HDR-BLANK` | Every box at the top of the form, from **Donor #** through **Tissue Checked In By/Date**, is filled in. | "Header field 'Donor Age' is blank." |
| `MP023-HDR-BYDATE` | Every **By/Date** box (Clean Room Log Review, Tissue Checked In) has **both** initials **and** a date. | "Tissue Checked In By/Date has initials but no date." |
| `MP023-OPS-REVIEW` | **Operations Manager Review** (middle of the form) has **both** initials **and** a date. | "Operations Manager Review is missing initials." |
| `MP023-ROW-PRODUCED` | In the Processing Instructions table, every white (non-shaded) row with a tissue name has **# Produced** filled in. | "Row 'Gracilis': # Produced is blank." |
| `MP023-ROW-PACKAGED` | Same, for **# Packaged**. | "Row 'Femoral Head': # Packaged is blank." |

Shaded spacer rows are ignored.

## QS-F-049 — Technical/Quality Review and Disposition Statement (1 page)

| ID | What we check | Example message |
|---|---|---|
| `QS049-REVIEW-BLANK` | For review items **1–10**, both the **Technical** and **Quality** "Reviewed By/Date" boxes have initials **and** a date, **or** say N/A. | "Item 7, Quality: initials present but no date." |
| `QS049-DATE-FORMAT` | Every date in those boxes is in **month / day / year** order with a 2-digit year, and is a real calendar date. | "Item 3, Technical: '2024-11-27' uses a 4-digit year; expected MM/DD/YY." |
| `QS049-INC-STATUS` | In item 10, if an **INC #** is written, the **Status** box is also filled. | "Item 10: INC # 'CT-60,263' entered but Status is blank." |

Date details (confirmed by organizers: **any separator is fine, only the order matters**): we accept `/`, `-` or `.` and single-digit months or days (`9-25-24`). We flag 4-digit years, day-before-month order where we can tell (for example `27/11/24`), and impossible dates (for example `02/30/24`). See [DECISIONS.md](DECISIONS.md) ADR-004.

## MP-F-021 — MS Processing & Packaging Lot Log (2 pages)

These checks apply only to **listed rows**: rows with an item name that have not been voided. Printed item names count as listed, so a printed row left completely empty is flagged.

| ID | Page / Section | What we check |
|---|---|---|
| `LOT-P1-ITEM` | Page 1, Item table | **Lot Number**, **Exp. Date** and **Manufacturer** are each filled in or say N/A. |
| `LOT-P1-REGENMED` | Page 1, RegenMed Item table | **Lot** and **Qty Used** are filled in. |
| `LOT-P2-ITEM` | Page 2, both Item tables (left and right) | **Load #** and **Sterilization Date** are filled in. |
| `LOT-P2-PACKAGING` | Page 2, Packaging table | **Lot** and **Qty Used** are filled in. |
| `LOT-VOID-UNSIGNED` | Any table | A crossed-out (voided) row **must carry initials and a date** on the strike-through. Missing either → error. Its other cells aren't checked. |
| `LOT-VOIDED-ROW` *(info)* | Any table | A properly initialed and dated void, e.g. "voided by LS on 01-23-26". |
| `LOT-DUP-NAME` *(needs confirmation)* | Page 1 Item table and RegenMed Item table | If the **same item name** appears more than once, each row needs a **different bracketed label**, e.g. `Gloves (7)` / `Gloves (7.5)`. Flags: a row with **no brackets**, **empty brackets** `( )`, or a **repeated label**. The message lists the rows it clashes with. Only exact base names are compared ("Gauze" ≠ "Fascia Gauze"), ignoring case, spacing and H₂O/H2O. **Not flagged:** plain repeats with all-different lot numbers, and rows whose other columns are all N/A (item not used). |
| `LOT-VOID-ADJACENT` *(needs confirmation)* | Any table | A row that is **completely empty** and sits **right next to a crossed-out row** may be covered by the same strike-through line. It's flagged for a person to check instead of failing the form. A partly filled row still fails. |
| `LOT-ROW-UNREAD` *(needs confirmation)* | Any table | Safety net: if the AI's row numbering skips a row, that row is listed so a person can check it. |

## MP-F-018 — Tissue Discard Form (bonus objective)

**One PDF can hold several discard forms (one per page). Each page is checked as its own form. The report shows one card per form, with its own PASS/FAIL.**

| ID | What we check | Example message |
|---|---|---|
| `DISC-HDR-BLANK` | **Donor #**, **Discard Authorized By/Date** and **Reason for Discard** are filled in. | "Reason for Discard is blank." |
| `DISC-AUTH-BYDATE` | **Discard Authorized By/Date** has **both** initials (or a signature) **and** a date. | "Discard Authorized By/Date has initials but no date." |
| `DISC-STATUS` | **Exactly one** Tissue Status box is checked. | "No Tissue Status box is checked." |
| `DISC-STATUS-GRAFT` | If **Graft IDs are listed**, the status must be **Unreleased Packaged** or **Released Packaged Tissue**. If the Graft IDs are **N/A**, it must be **Unprocessed** or **In Processing Tissue**. A drawn line/dash in the Graft ID column counts as N/A. | "Graft IDs are N/A, so Tissue Status must be Unprocessed Tissue or In Processing Tissue, but 'Released Packaged Tissue' is checked." |
| `DISC-ROW-X` | The small **X box** is marked for **every listed tissue**. | "Row 1 (Right Femur): X (confirmed) is blank." |
| `DISC-BOTTOM-BLANK` | **No field at the bottom is blank**: Tissue Discarded By, Confirmed By, Date, both FreezerPro/Log "Updated By" lines and their dates. N/A counts as an entry. | "Confirmed By is blank." |

## How rows are named in results

Lot Log items often repeat (for example eight "Small Round Basin" rows), so Lot Log issues show the row's position in its table, for example **"Sieve (row 16)"**. MP-F-023 rows use the tissue name. QS-F-049 rows use the item number.

## Any form

| Situation | What happens |
|---|---|
| **Anything crossed out or voided** (a corrected value or a struck row), on any form | Must have **initials and a date** beside it → otherwise `GDP-CORRECTION-UNSIGNED` (error). Unreadable initials/date → needs confirmation. |
| The form isn't one of the three supported forms | Result shows **UNKNOWN** with a friendly message. No rules run. |
| Ink in a box that can't be read | Listed under **Needs confirmation**, not as an error. |

## Not checked (out of scope for the challenge)

- Validating product codes against RegenMed's reference list
- Anything that needs information outside the form itself
