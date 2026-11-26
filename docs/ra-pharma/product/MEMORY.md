# Product memory

## Dispatch · 26 November 2026

The S4 reader already resolves claims 15 and 18 through different parents and exports their evidence. Reuse that source path for the [dossier walkthrough](BRIEF.md). A patent disclosure cannot fill a missing applicant report. Check the receiving document's sender before selecting an outgoing template. At each task close record the evidence, failures or uncertainty, and the next action here; link the current task state in [HANDOFF](HANDOFF.md).

## P1–P5 closeout · 26 November 2026

- **Decision.** One deterministic dossier build feeds all three specialists and is stored whole, with attached PDF bytes, so old snapshots replay after new attachments or skill promotions. Evidence: [receipt](RECEIPT-P1-P5.md); walkthrough replays all matched.
- **Patent example versus applicant result.** The skill rule, not the UI, must enforce it: version 1.0.0 took the patent's 96% as the applicant's result. Version 1.1.0 accepts only an applicant-authored document naming this product. Keep the rejected candidate and its reason visible; operators need to see why a number was refused.
- **Thai PDF text layers.** Chromium with Sarabun composes stacked marks into glyphs that map to NUL (`ที\x00`). Turning off `liga`, `ccmp` and `clig` keeps each mark; SARA AM still splits into `ํา` and needs repair. A browser drops the space at a line break: rejoin with a space only when a digit or Latin letter meets the break.
- **Repeated words in tables.** A quote such as "Magnesium stearate" occurs twice in the formulation table. Citations must be unique or explicitly bound to the first occurrence; the reference records which.
- **Protected-test interactions.** The G01 oracle guard reads every top-level `static/*` entry as text, so a `static/fonts/` folder fails it. Put binary assets outside `static/` and serve them from an explicit map.
- **UI.** A sticky evidence panel and sticky section nav covered the content they described and blocked clicks. Use a fixed, closable panel (Escape) and a static nav.
- **Launcher checks.** Redirected launcher stdout is block-buffered, and `cmd /c "...cmd" "arg"` strips quotes; start `Start-PTP.cmd` directly and poll `/api/health`.
- **Limitations.** Authored claim statuses, manual ACTD transcription, a small same-lane development family, no Thai patent search, and a session model that differed from the requested one. Next: applicant upload, scanned letters, second jurisdiction.
