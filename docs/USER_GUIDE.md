# User Guide: Beacon Document Reviewer

*For QA reviewers and judges.*

## Using the app

1. Open the app's URL (see [DEPLOY.md](DEPLOY.md) to run your own copy).
2. Drag one scanned PDF of a RegenMed form onto the upload area, or click to choose a file.
   - One PDF at a time, up to 20 MB and 10 pages.
3. Wait while the form is read and checked. A progress message shows what's happening. It usually takes 15–30 seconds.

![Upload page](images/upload.png)

## Reading the result




- The app is called **Beacon Document Reviewer** (lighthouse icon). The green bar at the top marks it as an **internal RegenMed tool**.
- **Form badge**: which form the app detected, for example *MP-F-023 · MS Processing Instructions / Tissue Open Checklist*.
- **PASS / FAIL banner** with a one-line summary, for example *"Passed all checks. No missing or inconsistent entries were found."* or *"3 issues to fix before review across 2 sections."*
  - **PASS**: no errors found.
  - **FAIL**: at least one error. Each is listed below the banner.
- **Issues**: grouped by section of the form. Each one shows the **page**, **row**, **field** and a plain-English description, for example *"Item 10: INC # entered but Status is blank."*
- **Needs confirmation**: fields the app couldn't read with confidence. Look at these on the paper form. They don't cause a FAIL on their own.
- **Where on the form**: on the right, the page is shown with a numbered orange box on each problem. The same number appears next to the issue in the list. Click an issue to jump to its box. Boxes appear a few seconds after the result.
- **Several forms in one PDF** (e.g. three Discard Forms): each form gets its own card with PASS/FAIL, and the banner summarises, e.g. "This PDF contains 3 separate forms: 2 passed, 1 needs fixing."
- **Info notes**: for example crossed-out (voided) rows, so you can confirm they were initialed and dated.

- **Check another form**: returns to the upload page.

If something goes wrong (not a PDF, too large, the AI service busy), a red panel explains it, with **Try again** and **Choose another file** buttons.

For the full list of checks, see [RULES.md](RULES.md).

## Good to know

- The app does **not** replace the two-person review. It catches routine misses first.
- Uploaded files are not stored after the check finishes.
- If the form isn't one of the three supported types, the app says so and doesn't run any checks.
