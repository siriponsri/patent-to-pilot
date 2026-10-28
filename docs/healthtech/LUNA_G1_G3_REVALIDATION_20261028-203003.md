# HealthTech G1–G3 Current-HEAD Revalidation

Run: `luna-g1-g3-20261028-203003-revalidation`  
Date: 2026-10-28  
Tested code HEAD: `68dbbde83921223d2e4d07352b10bc25a597670d`  
Tested `origin/main`: `68dbbde83921223d2e4d07352b10bc25a597670d`

This is a current-HEAD revalidation receipt. The earlier `LUNA_G1_G3_RECEIPT_20261028-200041.md` remains the historical repair receipt; its results are not rewritten here.

## Status

- HT-G1: `PARTIAL`; the Abbott branch remains a bounded development cohort and Bridge remains `BLOCKED_LOCAL` for rights, per-link provenance, cohort reconciliation, and final split evidence.
- HT-G2: `PARTIAL_DEVELOPMENT_ONLY`; the corrected local baseline package is reused, with no final holdout or generalization claim.
- HT-G3 backend: `BACKEND_COMPLETE_UI_PENDING`; Claude’s UX/UI worktree remains paused and untouched.

## Current revalidation

```text
rtk proxy python -B scripts/healthtech/verify_offline.py results/healthtech/luna-g1-g3-20261028-203003-revalidation/regression --suite all
PASS; 281 tests; 0 failures; 0 errors; 0 skipped; 0 network attempts; 0 credential-file reads; 0 provider calls; paid_cost_usd=0

rtk proxy python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json results/healthtech/luna-g1-g3-20261028-203003-revalidation/synthetic-smoke
ENGINEERING_DRAFT; 2 candidates; provider_calls=0; paid_cost_usd=0

rtk proxy python -B scripts/healthtech/run_api_dry_run.py configs/healthtech/api_dry_run.json
DRY_RUN_NOT_EXECUTED; network_attempts=0; provider_calls=0; paid_cost_usd=0
```

The machine-readable suite receipt is `docs/healthtech/evidence/luna-g1-g3-20261028/revalidation-203003.json` and the full-suite artifact is `results/healthtech/luna-g1-g3-20261028-203003-revalidation/regression/verification.json`.

## Follow-on clean-checkout verification

A second offline-only verification ran from disposable clean worktree `C:/Users/User/AppData/Local/Temp/ptp-ht-clean-a449cca` at commit `a449ccad7f93771a23018e1abccf28f486f466cd`; its tracked status was clean. The initial clean run completed 281 tests with one expected skip because the pinned local tokenizer artifact was unavailable in the clean checkout. The rerun exposed the existing local model snapshot through a junction at `data/raw/healthtech/models` pointing to `C:/Users/User/Desktop/myProject/patent-to-pilot/data/raw/healthtech/models`; no weights were copied or staged.

Rerun artifact: `C:/Users/User/AppData/Local/Temp/ptp-ht-clean-a449cca/results/healthtech/clean-revalidation-a449cca-with-model/verification.json`  
Result: `PASS`; 281 tests; 0 failures; 0 errors; 0 skipped; zero network attempts; zero credential-file reads; zero provider calls; `$0` paid cost. The local model snapshot manifest is `C:/Users/User/Desktop/myProject/patent-to-pilot/data/raw/healthtech/models/manifest.json`, SHA-256 `1ee112fe8d1fe086185ba9bf1fd7d032afe974535fd8e6014752b65f90f6684c`.

The clean verifier hashes raw checkout bytes. The raw hashes for `history.py` and `test_healthtech_repairs.py` differ from the main working copy only because global `core.autocrlf=true` yields LF in the main checkout and CRLF in the clean worktree; `git hash-object` and EOL-normalized SHA-256 match for both files, while `engine.py` matches byte-for-byte. This is a checkout-format difference, not a code or test mutation.

## G3 backend walkthrough

The three existing public dossiers were re-opened from `results/healthtech/public-dossiers-20261027-r3/` without loading evaluator relations or copying raw source pages:

| Case | Sources | Evidence | Candidates | Unresolved | Next requests | History/export/source view |
|---|---:|---:|---:|---:|---:|---|
| K121849 | 1 | 7 | 0 | 3 | 3 | PASS |
| K163345 | 1 | 7 | 0 | 3 | 3 | PASS |
| K190167 | 1 | 7 | 0 | 3 | 3 | PASS |

For each case, the backend created version 1, appended a user note with `expected_parent_version=1`, exported selected version 2 in English and Thai, preserved the note in JSON/Markdown, and viewed the exact `device_name` source field. The output is under `results/healthtech/luna-g1-g3-20261028-203003-revalidation/g3-three-public-cases/`.

These cases are public regulatory fact dossiers with empty patent input pools. They do not establish patent coverage or an exhaustive absence of patents; those gaps remain explicit unresolved items and next information requests.

## Boundaries

No network acquisition, local model inference, provider dispatch, paid call, deployment, credential read, outreach, frontend edit, or Claude worktree mutation occurred during this revalidation. The revalidation confirms backend behavior and current tracked-code health; it does not convert G1/G2/G3 into COMPLETE.

Prior parser replay, corrected baselines, rights/cohort limitations, and R1–R3 repair evidence remain at the paths listed in the machine-readable verification. No clinical, FTO, patent-validity, investment, publication, customer-validation, or production-readiness claim is made.
