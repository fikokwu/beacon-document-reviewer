You are looking at the scanned pages of ONE document from RegenMed, a tissue bank. The images are in page order. Identify which form it is. Do not evaluate the content.

How to identify the form:
1. **Primary cue: the form code printed at the bottom-right of each page**, e.g. `MP-F-023.009` (code `MP-F-023`, version `009`). Report it in `form_code` exactly as printed, including the version suffix.
2. **Secondary cue: the title printed at the top of the first page.** Report it in `form_title`.
3. Ignore other codes that appear inside the body of the form, for example label codes such as `MP-L-039.001`, or a reference in the body text such as "(initiate MP-F-018)" on the QS-F-049 form. Only the bottom-right code identifies the form.

Forms we know about (for reference only; do not force a match):
- `MP-F-023`: "MS Processing Instructions / Tissue Open Checklist" (1 page)
- `QS-F-049`: "Technical/Quality Review and Disposition Statement" (1 page)
- `MP-F-021`: "MS Processing & Packaging Lot Log" (usually 2 pages)
- `MP-F-018`: "Tissue Discard Form" (1 page per form; a document may contain several discard forms)

If the document is something else, report whatever code and title you actually see (or null) and set `confidence` accordingly. If you cannot read a code at all, set `form_code` to null.

`confidence` (0–1): how sure you are that `form_code` is read correctly.

`page_rotations`: one entry per page, in order. Each entry is the number of degrees to rotate that page **clockwise** so its text reads upright: 0, 90, 180 or 270. Use 0 for a page that is already upright.
