# HealthTech G3 integration handoff

Run: `luna-g3-20261028-28dfb1d`  
Date: 2026-10-28  
Candidate: `28dfb1dcaf0f4794d74ba80c2fea09b0108f3f86`  
Status: `BACKEND_COMPLETE_UI_PENDING`

## Delivered

- Added the Luna-owned integration path `docs/healthtech/integration/luna-g3-20261028-28dfb1d/`.
- Recorded the actual Python contract surface, proposed frontend adapter seam, capability delta, tracked fixture hashes, source hashes, and evidence paths in [`adapter-contract.json`](integration/luna-g3-20261028-28dfb1d/adapter-contract.json).
- Recorded the human handoff in [`integration README`](integration/luna-g3-20261028-28dfb1d/README.md).

## Verified backend boundary

The current backend supports closed dossier validation, bounded synchronous offline runs, exact source inspection, exclusive local version creation, expected-parent conflict detection, selected-version JSON/English/Thai export, and separate `user_edits`. The two targeted repair tests are named in the machine-readable handoff, and the current full offline suite is recorded at 281 tests with zero failures/errors/skips.

The handoff does not claim a browser-local store, HTTP job service, collaboration, live provider, PDF/DOCX export, or UI completion. The Claude branch remains paused and untouched. The three public walkthroughs remain facts-only with empty patent pools; they do not establish device–patent coverage.

## Next action

When UX ownership resumes, Claude should recheck the current base and implement the local adapter on its own branch. Review the adapter against the recorded result shapes and capability states before any integration. Keep Bridge rights/cohort/split resolution and final scientific claims separate from this backend handoff.
