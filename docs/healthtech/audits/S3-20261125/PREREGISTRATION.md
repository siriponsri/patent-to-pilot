# S3 controlled DEV preregistration

Frozen on 25 November 2026 at 13:40:22 UTC before policy outcome measurement and before loading reserved DEV for replay. Published S1 entry was `1291a17ffa96bc0c5dc32c3b1dc4cf4d5097b1fc`. The [machine-readable lock](freeze.json) pins the S1 manifest, scorer, runtime, independent validator, runner, fixture, measurement documents and reference environment. Its SHA-256 is `32c176a78159db6d99a9a01c8b3a61ae823cade479ae697d8066a0b82cc9ac64`. The S1 verifier reproduced 20 files without running a method. Development used the wording and passages of the two proposal and two selection families, the canonical schemas, and separately written hand-checkable fixtures. Development labels were inspected for the canonical response format. No optimizer selection, product example, or controlled outcome was used to nominate the policy.

## One nominated contrast

Use `scope` minus `coverage` as the only primary contrast, on Thai reserved DEV. The no-scope-signal ablation is the same `coverage` run. Both arms receive the same supplied ordered seed, six-unit dossier, wording adapter, Unicode normalization, character-trigram Okapi BM25 index, fixed compatibility ranker, exact response extraction and ceilings. The fixed ranker prefers a direct source reference, then more individually matched distinct requirements, then summed full-question BM25. It retains the leading pair on an equal substantive rank. An acquisition checks the same six candidates, adds one new unit, and uses condition BM25 with opaque ID ties. A visible outgoing reference from a condition-matching partial unit can prioritize its licensed target only when selected by the scope controller. This is the scope decision signal carried into the shared candidate operation.

The coverage controller reranks when coverage is complete or after admitting evidence. It stops on stagnant coverage. The scope controller preserves a compatible leading pair, reranks for an eligible compatible pair in the current pool, or searches by the best partial source-stated reference and condition. It uses compatibility to choose both the action and any explicit reference target. A check for the existence of a compatible pair uses already inspected edges and conditions. Full assignment ranking happens only in a metered rerank for both arms. Among eligible partial anchors, match count, full-question BM25 and ascending opaque ID decide. It may use the first uncovered condition when no reference is visible and stops if it has no such search signal. Neither controller adds an inferred reference. On both paths the chosen pair must have a direct reference, cover the request and yield a canonical answer from the target passage. Otherwise it abstains. The parser is a bounded wording adapter for observed grammatical forms. Its supported forms and implications for transfer coverage are part of the frozen code.

Other readouts are the supplied-seed static control, fixed compatibility rerank, and coverage-first fixed rerank. All have the same ceilings. The static control preserves the S1-specified seed instead of spending a rerank action. Optimizer matrix: fixed skill/fixed harness runs once; skill-only, harness-only and joint are NOT_RUN. No proposal edits or scored selection passes are allocated. Fixed-answering-rate diagnostic is NOT_RUN because no threshold was selected prospectively.

## Access, budgets and audit

The policy worker receives a temporary runtime capsule containing the policy file and four allowlisted runtime files projected to a single language. The worker has no evaluator import or evaluator input. The directory is an input boundary and is not an OS sandbox. Case/family IDs are used for joins and corpus selection; opaque unit IDs additionally break ties. The evaluator opens labels and pairs only from its side after a trace capture. The source span, edition, digest, relation basis, inspected universe, monotonically timed candidate operations, selected IDs, final order and returned identity/role are independently checked. The lock and capture sidecars identify code, input order, index inputs and runtime environment. Repeated inspection costs are counted.

Caps per request are four actions including the initial seed, six candidates per action, 24 inspections, eight returned units, 30 seconds and zero model tokens. One serial CPU worker uses standard-library Python. Source loading and index construction have a separate ingest ledger. Wall and CPU clocks are recorded per query. Subprocess wall time includes launch and output handling; total-process CPU beyond metered regions is unmeasured. No paid API, GPU or newly installed dependency is used.

Thirteen independent S3 tests and eight S1 regressions passed. The first ten-check fixture attempt failed the forged-clock test because the mutated value could equal the previous Windows timestamp. The assertion now forces an earlier timestamp and the worker uses the higher-resolution monotonic performance counter. This happened on hand-authored fixtures before the first lock. After v2, the full pipeline validated 50 unscored proposal traces per language. A wrong-path original DEV invocation was denied before runtime loading.

The repository-wide system-Python `python -m pytest --tb=short -q` completed with the eight standing SACR r2/r3 budget errors and no extra failure. That suite started before the audit correction. The 21 targeted checks reran on the final v2 files before publication.

## Prospective audit correction

The Planner/Auditor verified the [withdrawn v1 lock](freeze-v1-withdrawn.json) and caught unmetered assignment sorting in the scope controller's existence check. On the independent Oak fixture v1 called the ranker three times for one recorded rerank, while coverage called it once. V2 replaced the sort with an existence check. Both arms now call the full ranker once for one recorded rerank on that fixture, with unchanged expected decisions. V2 also binds original runs to canonical output paths and requires a shared capture seal before score access. The v1 lock SHA-256 is `b04e9db387ee6111bab23672ef610877c70b5ac93a84ed78d876e2c87cb5fa14`. V1 code and unscored preflight captures are retained under the private experiment root, in `preflight-v1-source/`, `preflight-th/` and `preflight-en/`. No reserved DEV result or dataset change preceded this correction.

## Estimand and report

Score scope-complete success with the S1 scorer, count failed and invalid requested trials as zero, and report coverage, scope, and both-correct, both-failed, improved and worsened counts for every state and family. Weight the three state changes equally. Draw three whole Thai DEV families with replacement in each of 10,000 draws using seed 20261125, preserving paired cases and siblings. Compute the linear-interpolated 2.5th and 97.5th percentiles. Use the same interval computation as a descriptive English transfer diagnostic. Three purposively authored families per language make either interval unstable. Report both-correct invariant pairs with an identical decision and support set, and both-correct changed pairs whose decision or supporting set changes. Audit incompatible used support using the evaluator's permitted sets. Track finite abstention, answer utility, action and candidate costs separately.

No individual examples will be selected for display. The private case audit retains all changed and failed cases under opaque IDs. Optional historical and natural-source rows are handled under the independent [bridge receipt](BRIDGE.md).

## Reproduction

Run in the repository from the preregistration commit or any checkout containing the same locked files. The original execution uses the two canonical private paths, runs Thai before English, and seals both captures before scoring. For an independent audit after the original capture, use `replay-audit` and `score-audit` with a fresh private directory per language. Compare scores, evidence IDs, actions and decisions. Platform-dependent timer readings will vary. The create-only output directories preserve original captures.

```powershell
rtk proxy python scripts/research/s1_packet.py verify
rtk proxy python -m pytest -q tests/test_s3_policy.py tests/test_s1_packet.py
rtk proxy python scripts/research/s3_run.py run dev th ../_private_artifacts/ptp-s3-20261125/th
rtk proxy python scripts/research/s3_run.py run dev en ../_private_artifacts/ptp-s3-20261125/en
rtk proxy python scripts/research/s3_run.py seal-originals
rtk proxy python scripts/research/s3_run.py score dev th ../_private_artifacts/ptp-s3-20261125/th
rtk proxy python scripts/research/s3_run.py score dev en ../_private_artifacts/ptp-s3-20261125/en
```
