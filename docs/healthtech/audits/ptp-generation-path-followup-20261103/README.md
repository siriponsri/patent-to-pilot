# Generation-path contract follow-up — 2026-11-03

This is an additive checkpoint for the original Patent-to-Pilot O1-O4 goal.
It does not open a new goal, scientific batch, API budget, GPU window, ledger,
or 24-hour authorization window.

## Scope and inputs

- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Tested source HEAD: `89bc03409f5b9dae35c6c4f50b68ea11c2f8951b`
- Audit/checkpoint commit: recorded after verification; source files were unchanged by the receipt commit.
- Pepo review: `C:/Users/User/Documents/Codex/2026-11-02/task/ptp-parallel-readiness-review-20261102/READINESS_REVIEW_TH.md`
- Pepo evidence index: `C:/Users/User/Documents/Codex/2026-11-02/task/ptp-parallel-readiness-review-20261102/evidence-index.json`
- Parent readiness receipt: `docs/healthtech/audits/ptp-parallel-readiness-followup-20261103/verification.json`

The candidate was clean before the check. No relevant local experiment process
was active. The existing SSH process was already classified by the parent
preflight as a Codex remote app-server proxy, not a scientific or paid run; it
was not relaunched or modified.

## Review findings applied

The reviewed baseline runner already contains the requested prospective repair:

- an attempt is appended before action execution;
- action failures preserve measured wall and CPU elapsed time;
- fields that cannot be measured are marked `PARTIAL_UNKNOWN`;
- method-level failures preserve completed and failed attempts;
- no synthetic zero-cost attempt is appended;
- historical receipts are not rewritten and retrospective cost is not inferred.

The B2/B3/offline-B4 evidence remains a descriptive realized
quality-resource frontier. Frozen inputs and per-call depths are shared, but
realized query/rerank units differ: B1 `3/123`, B2 `9/369`, B3 `5/205`, and
offline B4 `5/205`, with eight B4 controller steps as a separate unit. This
does not establish equal-total-budget superiority or adaptive benefit.

## Current-head offline verification

The following package was run without network, provider, API, GPU, dataset, or
ledger activity:

```text
python -B -m pytest -ra -q \
  tests/test_healthtech_real_baselines.py \
  tests/test_healthtech_generation_payload.py \
  tests/test_o3_generation_repair.py \
  tests/test_o3_adversarial_repair.py \
  tests/test_healthtech_api_generation.py \
  tests/test_healthtech_qwen_evidence_pack.py \
  tests/test_healthtech_ledger_registry.py \
  --junitxml=docs/healthtech/audits/ptp-generation-path-followup-20261103/offline-targeted-tests.xml
```

Result: **75 passed, 0 failed, 0 errors, 0 skipped** in 2.891 seconds.

The suite covers failure accounting, rights-cleared paired payloads, duplicate
and provenance rejection, exact Qwen3-32B route/model binding, conservative
reservation bounds, credit freshness, unknown billing, canonical ledger
binding, local evidence-pack schema checks, and mock-only API runner behavior.

Raw outputs are retained in:

- `offline-targeted-tests.log`
- `offline-targeted-tests.xml`

Relevant source and regression-test hashes are recorded in
`verification.json`.

## Status at this checkpoint

- Engineering: `COMPLETE_FOR_FAILURE_ACCOUNTING_AND_GENERATION_CONTRACTS`
- Scientific evidence: `PARTIAL`; semantic gold, equalized final budgets,
  powered inference, and exact-head real-case assets remain incomplete.
- Business validation: `PARTIAL_OPERATIONAL_POTENTIAL_ONLY`; no external user,
  demand, WTP, revenue, or ROI evidence was created.
- Manuscript readiness: `PARTIAL_OWNER_REVIEW_REQUIRED`; the budget and claim
  boundaries remain descriptive and the WPI author-guide recheck is still for
  owner review.

No paid call, GPU job, dataset download, ledger mutation, budget reset, or new
experiment was started. Live O3 remains gated on the existing canonical R1
history, current credit, route/pricing, rights-cleared payload, and dispatch
allocation evidence.

## Resume action

Keep this goal active. Continue only with independent offline work or owner
review. A future paid or remote batch must reuse the existing canonical ledger
and cumulative authorization, freeze the total-budget controls before reading
results, and preserve all failures and unknown billing states.
