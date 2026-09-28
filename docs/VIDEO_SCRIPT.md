# Walkthrough Video Script (≤ 2:00)

**Narration:** about 270 words, which is roughly 1:55 at a calm pace. Every number said out loud is backed by the repo.

## Before recording (5 min)
- **Browser:** Chrome, one tab, zoom 110%, bookmarks bar hidden. Open https://regenmed-reviewer-211763216976.northamerica-northeast2.run.app
- **Finder:** open `demo-files/` beside the browser, so you can drag files in.
- **Recorder:** QuickTime → File → New Screen Recording (or ⌘⇧5), full screen, with microphone.
- **Warm-up:** upload one file before you start recording, so the first real upload is quick.
- **Uploads:** one at a time, a few seconds apart.

## Shot list and narration

| Time | On screen | Say |
|---|---|---|
| **0:00–0:15** | Beacon home page | "At RegenMed, about half of all hand-filled processing forms come back needing a correction, like a missing initial, a blank field, or a wrong date format. Beacon catches those routine misses **before** the two-person review, so reviewers spend their time on judgment, not hunting for blanks." |
| **0:15–0:35** | Drag in **`demo_film/1-pass.pdf`**. Show the progress screen, then PASS. | "No login and no setup: just drop in a scanned PDF. Beacon works out the form type by itself. This is a completed MS Processing Instructions checklist, and every required field is there, so it gets a clear pass." |
| **0:35–1:05** | *Check another form* → drag **`demo_film/2-few-errors.pdf`**. Click each issue; the page jumps to the orange box. | "This file holds **three Discard Forms**. Beacon checks each one separately: form 1 is missing *Confirmed By*, form 2 has an unticked X box for the Right Femur, and form 3 passes. Every issue names the page, section, row and field, and it's **highlighted on the scan**. Click it and you go straight there." |
| **1:05–1:35** | *Check another form* → drag **`demo_film/3-many-errors.pdf`**. Scroll the issue list and point at the boxes. | "And here's a checklist with lots of problems: two blank header fields, a Tissue Checked In with initials but no date, a missing Operations Manager review, and two blank table counts. Six issues across three sections, grouped so the reviewer can fix them in one pass. Beacon also enforces good documentation practice: anything crossed out must be initialed and dated." |
| **1:35–1:55** | Stay on the result, or show `docs/screenshots/` | "Under the hood, the AI only **reads** the form, and tested rules **decide** pass or fail, so results are consistent and explainable. It covers all four form types, including the bonus Discard Form. It got **30 out of 30** test files right, including blanks, planted errors and bad scans, in about ten to twenty-five seconds per form." |
| **1:55–2:00** | Home page with the lighthouse logo | "Beacon: pre-screening RegenMed's forms so every record is right the first time." |

## Editing tips
- **Waits:** keep one wait at real speed (the pass, about 12 s) to show real performance. On others you can trim or speed up the wait, and caption it "(sped up)" to stay honest.
- **Length:** stay under 2:00, cutting pauses rather than content.
- **Export:** 1080p MP4 (QuickTime → File → Export As → 1080p).

## Backup (if something fails live while recording)
Just re-record that segment. The screenshots in `docs/screenshots/` (`highlight-discard.png`, `fail-lot-log.png`, `discard-multi-form.png`) can be used as stills.
