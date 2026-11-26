# Product lane handoff

**P1–P5 COMPLETE · local engineering demo READY_FOR_REVIEW · `product/ra-pharma`.** Base `2085e4be`. Session ran on Claude Opus 5.5 instead of the requested Sonnet 5.5 medium; the owner and Planner should decide whether that matters for the record. No job is running, no paid service, pod, model or remote machine was used, and cost is zero.

## State

- **Run it:** `Start-PTP.cmd`, tab **แฟ้มทะเบียนยา**; steps in the [walkthrough](../../../examples/ra_pharma/README.md). Scripted: `examples/ra_pharma/walkthrough.py <out> [--render]`.
- **Receipt:** [RECEIPT-P1-P5](RECEIPT-P1-P5.md) has the task table, contract fixture results, deterministic/operator split, verification commands, tool and font record, and limitations.
- **Changed entrypoints:** new modules `workbench/dossier.py`, `letters.py`, `skill_eval.py`; routes under `/api/dossier/` in `server.py`; `static/dossier.js` plus tab markup in `index.html`, hooks in `app.js` and styles in `app.css`; fonts in `workbench/fonts/`. The launcher scripts are unchanged.
- **Demo inputs:** [`sample/ra_pharma/`](../../../src/patent_to_pilot/workbench/sample/ra_pharma/README.md); fictional PDFs built by `examples/ra_pharma/build_fixtures.py`; public excerpts with digests and rights notes in `pack.json`. Source captures are private in `../_private_artifacts/ptp-ra-product-20261126/sources/`.
- **Store:** five new SQLite tables (`dossier_snapshots`, `dossier_blobs`, `dossier_letters`, `dossier_skills`, `dossier_skill_events`) in the existing Workbench store, so `--backup` covers them. Fresh stores start at skill 1.0.0 by design; the walkthrough performs the promotion.
- **QA:** product tests 15 passed. Full gate: 2,809 passed and only the 8 standing SACR budget failures (raw exit 1), environment in the receipt. Deliverables commit `0c77258b`.

## Open decisions and next actions

1. Planner: review and integrate this branch; consider adding `content_sha256` (item hash) and the citation `occurrence` field to the shared evidence contract. Root README link to the walkthrough is Planner-owned.
2. Owner: confirm that the extended rights notes are acceptable (a USPTO description excerpt and table row beyond the S2 claims decision; short ACTD and OPM quotations).
3. Product next: applicant PDF upload, a scanned-letter path, and a second jurisdiction profile with official sources and fixtures.
