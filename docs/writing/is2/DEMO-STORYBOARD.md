# Workbench: committee demo storyboard (60–90 s; slide 8 of the IS2 deck) — v2, 22 Nov 2026

Purpose: show K2b (what a searcher or R&D engineer gets) as a working evidence workflow. It follows the G08 narrative:
live task → changed source → affected decision. It is **not** evidence of user benefit; that remains NOT_MEASURED.

## Run (local only, no network calls in lexical mode)

- Double-click `Start-PTP.cmd`, then open **http://127.0.0.1:8765/**. The CLI equivalent is
  `.venv\Scripts\python.exe scripts\ptp_run.py --serve`.
- Before the day, run `scripts\ptp_run.py --smoke` (15/15) and `--doctor`.
- Use a fresh data directory (`--data-dir`) so the run starts with no results.
- Owner guide: `artifacts/owner-program/PTP-2026-11-21/G02/OWNER_START.md`.

## Script (60–90 s)

| Time | Screen | Spoken walkthrough (English rendering) | On-screen label |
|---|---|---|---|
| 0–10 s | Open the sample project and show requirements R1–R3. | “We start with three requirements the reader can check.” | Sample data · Lexical mode |
| 10–30 s | Run the comparison, show the matrix and open the Thai citation. | “Each cell leads to the original wording, with the source version and character offsets.” | Live local run |
| 30–55 s | Apply the sample source revision (DEMO-S2 v1 → v2). | “When a source changes, the system rechecks the results that depend on it.” | Changes view |
| 55–75 s | Show A/R2 changing from Meets to Does not meet. Other results are reused; the superseded v1 citation still opens. | “Unrelated results are reused. We can still inspect the earlier evidence.” | Superseded (current: v2) |
| 75–90 s | Optionally show Providers, the Hybrid mode label and a project built from local files. | “Each run records its model and index versions. The lexical workflow also works without a model.” | Your files · Hybrid mode |

**Fallback if the app fails on the day:** use the G01/G02 screenshots in `artifacts/owner-program/PTP-2026-11-21/G01|G02/screenshots/`
or a screen recording of the same build, labelled RECORDED.

**Optional backup demo (legacy):** Solution Scout (`.claude/launch.json` → `scout-backend` + `scout-frontend`,
`http://localhost:5178/scout.html`). It uses patembed-large (CC BY-NC-SA 4.0) and a public HUPD-derived bundle, so it is for
academic use only. Rights and limits: `docs/healthtech/audits/ptp-scout-public-demo-20261106/README.md`.

## Checked before the presentation

- [x] Workbench flow verified in browser QA (G01 21 Nov; G02 22 Nov at 1280/360 px, restart persistence, 0 console errors)
- [ ] Explorer double-click of `Start-PTP.cmd` and default-browser auto-open, observed by the owner
- [ ] One full walk-through recorded as the fallback
- [ ] Rehearsed within 90 s (G08)
