# Method-first R0 reconciliation — 10 November 2026

Status: R0 inventory completed with explicit unknowns; R1 NOT_RUN. Owner: Codex, single active writer. No experiment, model load, paid request, BigQuery query, or protected-label inspection was performed. The previous goal turn made progress by creating the goal and publishing its checkpoint; this package adds current-state evidence.

## Checkout and authority

Inspected base: `b311753` on existing `main`. The five latest commits were `b311753`, `aed40d4`, `c3ff405`, `05a4650`, `4fd4880`. Changes since reference `05a4650` affect only AGENTS.md, CLAUDE.md, HANDOFF.md and HANDOFF_PROMPT.md; no experimental code changed. Initial status contained one pre-existing untracked research handoff, preserved without staging.

The owner's 10 November goal activation and HANDOFF_PROMPT.md govern the new method-first R0–R6 work. Historical GOAL.md, PLAN.md, progress and next-actions entries describe older tracks/holds; they do not authorize spending or supersede this direction. DAPFAM is the external anchor; MTM is the MedTech evaluation; SACR remains an untested candidate. R5 requires explicit owner freeze of at most four methods. Phase 3d and cited-distractor acquisition remain optional, not active work.

## Benchmark and artifact inventory

Paths here use the repository's established private-root and dr-train job-root conventions; no raw payload is included.

| Item | Current evidence | Limit |
|---|---|---|
| MTM frozen protocol | `docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md`, freeze `7d317e7` | Later clauses 12–14 override earlier draft wording |
| MTM input receipt | `medtech-time-machine/inputs/receipt.json` exists locally; `mtm-20261107/inputs/receipt.json` exists remotely | Counts read from receipt, not rebuilt |
| MTM population | Receipt: 899,838 corpus families; 1,985 dev and 1,955 test queries | No protected rows opened |
| MTM split storage | Combined `queries-meta.jsonl`; per-split T/A/brief files, remote P files | No separate safe runtime metadata or isolated test-label manifest identified in inspected inventory |
| MTM corpus hash | Receipt and original T-dev run agree on `4d29bd8136e2a838e9a12e0907e0951dc029ca6f9b22ba7eae1da21bb5c618a6` | Not a fresh 2.1 GB corpus hash check |
| MTM original encoding | Remote `out/receipt-T-dev.json`: 1,553,678 passages, model hash `234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482` | Original receipt does not bind a saved vector hash and passage-order hash |
| MTM reusable matrix | Remote `out/passage-vectors-f32.npy`, 6,363,865,216 bytes | Presence verified; admissible reuse awaits R1 binding |
| MTM reuse receipt | P-dev receipt reports vector hash `8bb35abadf1df98c916eb495997214a225f280fbc2ae4979ca09b9d6ec56330b` | Historical hash, not freshly recomputed |
| DAPFAM local split | `ptp-org-adaptive-20261105/split.json`, 141,779 bytes, opaque SHA256 `dd76c019ee74c8d256e182ecfb329f9235638c1ecf9d2c7b1fa8073c4958e6dc` | Hashed without parsing or printing contents |
| DAPFAM dev exposure | Existing Scout feasibility audit reports 474 dev queries, 349 strict-OUT eligible; project handoff reports 773 protected queries | Native OUT denominator must be verified separately; strict-OUT X-lane result is not native OUT |
| DAPFAM vectors | Remote `org-adaptive-20261105/outputs/dense-single/passage-vectors-f32.npy`, 773,914,752 bytes | Model/corpus/order provenance still to bind |
| Model and Python inventory | Remote PatEmbed-large, Qwen3-8B and bge-reranker-v2-m3 directories exist; established venv executable exists | No weights loaded or rehashed this round |
| Protected outputs | MTM baseline P/T/A test ranking filenames exist remotely | Contents/scores not read. Historical unscored claim retained as PROJECT_REPORTED, not independently proved |

## Evidence ledger and critical repair map

Preserve existing dev findings: baseline P/main/X hit@20/100/200 = 0.180/0.313/0.388; V4 is the only eligible recorded dev method, OOF delta +0.017 [0.010, 0.025]. V1–V3 are INVALID_RUN due to the instruction-prefix defect. Corrected V1b/V2b/V3b, V5/V6 and 3a are negative/null; 3b is NO_GO. These are PROJECT_REPORTED from the methods log and phase audits, not reproduced here.

| Repair | Inspected owning source | Current conclusion / next evidence |
|---|---|---|
| A01 runtime labels | `build_mtm_inputs.py` writes combined targets; `run_mtm_dense_pool.py` loads complete metadata rows | OPEN, confirmed static boundary defect. Formula does not reference targets; this does not prove labels are inaccessible. Strict allowlist and trusted staging required |
| A02 construction roles | Dense runner computes view masks from corpus `sets` | OPEN. Preserve frozen view membership via trusted masks; remove roles from model features |
| A03 exact-mask eligibility | Builder checks publication visibility; runner `keep_mask` also excludes own family and shared CPC | OPEN, incidence UNKNOWN. Audit dev gold only with the exact predicate; do not alter labels/population |
| A14 vector binding | Dense reuse checks shape and records a hash after loading | OPEN. Bind corpus bytes/order, passage construction/ownership and model/preprocessing identities. Existing receipts may help; do not re-encode automatically |
| Protected evaluator gate | `analyze_mtm.py` accepts both dev/test, then parses the combined file before filtering | OPEN. Historical claims that all analysis scripts reject test are too broad. Add fail-closed development entry points before data use |
| DAPFAM native parity | Handoff section 5 pins MTEB `9242b36a1d400fc8c3af573e6a6e0705c0b96e3d` and dataset `780f4011d60297fc6e97a4119b0c516d13afea2d` | Public loader/evaluator inspection and synthetic fixtures remain. IN/OUT qrel filtering must not become X candidate filtering |

Do not run the old analysis scripts against combined metadata for R1. A filtered Python comprehension still parses protected rows. Prepare and test staging on synthetic data, then arrange trusted staging outside the development agent's label access. Do not weaken that boundary by claiming that suppressed output makes protected parsing safe. This dependency does not block schema implementation, fixtures, source review or manifest tooling.

## Resources and observations

Read-only SSH succeeded. At observation, the authorized V100 reported 0 MiB used and `nvidia-smi --query-compute-apps` returned no processes. Existing MTM main, dev2 and dev3a status logs end in `all done`, with analysis exits 0. Other Python processes exist on the shared host; they were not attributed to this project or interrupted. No new job was launched, and availability must be rechecked before any future job.

`local_execution.py` enforces the exact V100 UUID and authorization end `2026-12-31 16:59 UTC`. One project GPU job at a time remains mandatory. No paid API calls. BigQuery requires a dry-run estimate and approval for each new pull, cap 34 GiB. Training, full-corpus re-encoding, protocol amendments, protected scoring and release remain gated.

## Verification and limits

Executed read-only Git status/log/diff, authored source/receipt reads, filesystem name/size inventory, opaque split hashing, and bounded SSH inventory. Protected label content, test rankings and test scores were not opened. No runtime tests were needed for this documentation-only R0 package. Existing results are not newly verified numerical findings.

Two wildcard-based Windows `rg` inventory commands produced path errors; explicit directory listings resolved the required locations. Some broad document outputs were truncated; required source reading must continue in bounded sections before R1 code, especially method sections 8–13. Do not treat those truncated reads as complete. `verification.json` binds inspected source bytes and explicit status limits.

## Next bounded package: R1 boundary implementation

1. Finish required bounded reading, including method sections 8–13 and relevant local instruction files.
2. Implement strict runtime schemas/loaders and synthetic trusted-staging fixtures; reject extra/nested labels, construction tags, duplicate IDs and malformed metadata.
3. Prepare safe dev-only evaluator inputs and a protected staging procedure; execute only when permitted inputs are available. No access-control/global configuration changes.
4. Reuse the actual runtime predicate for the dev eligibility report, with all failure categories and unchanged denominators.
5. Bind existing corpus/vector provenance and add adversarial same-shape/wrong-order fixtures; establish allowed-input baseline parity before method scoring.
6. Inspect the pinned native DAPFAM loader/evaluator and add denominator/text/ranking-universe fixtures. Record remaining owner decisions without blocking independent safe work.
