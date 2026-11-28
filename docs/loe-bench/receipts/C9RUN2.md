# C9RUN2 execution receipt

**BLOCKED on 28 November 2026.** GPU admission code and CPU fixtures passed. Development outcome linkage and the registered calendar still gate the production pair. SFT, GRPO and Track A predictions are `NOT_RUN`. Incremental spend is USD 0. This receipt is the executor handoff and memory entry. [C9RUN](C9RUN.md) · [C′ gate PASS](GATE.md) · [C9 protocol](../C9-PROTOCOL.md) · [OSF update 2](../OSF-UPDATE-2-SHEET.md)

## Main-planner approvals

> 1. GPU allowance: the first author approved ONE NVIDIA L4 24 GB, Secure cloud, US-MO-2, quoted USD 0.69/h, all-in cap about USD 4.5 (registered cap USD 8) on 28 Nov 2026. Patch loe-bench/c9 so the GPU check accepts {"NVIDIA A10", "NVIDIA L4"}, requires the SAME GPU name for both arms and for prediction, and records the detected name in manifests. Record "A10 -> L4 hardware substitution (no A10 in US data centers; same 24 GB; equal for both arms)" as a dated deviation. No other code or frozen value changes.
> 2. Development projection: the main planner APPROVES building the C9 training projection now. Build it from the pinned S0 snapshot with the guarded development reader, using exactly the C9 roster rule (annual January 1 cutoffs 1995-2014; dated original NDA and TYPE 1 eligibility; no prior final ANDA; 24-month windows that close on or before 2016-01-01; complete coverage; unresolved linkage and incomplete windows jointly omitted). Filter outcome records to approval dates <= 2016-01-01 BEFORE decoding; never read any later outcome. Write it to C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/c9_dev_projection.json, record its SHA-256, row count and class counts in the receipt, and commit a small manifest under loe-bench/data/ (path, sha256, counts, code commit). This projection is the "approved development-only projection" the spec requires.

**Deviation approved 28 November 2026.** A10 -> L4 hardware substitution (no A10 in US data centers; same 24 GB; equal for both arms). This records the approval and the planner's placement finding. A fresh placement quote is due at pod admission.

## Verified preparation

- `loe/C9RUN2` was cut from fetched `origin/research/loe-bench` at `62359411`. The previous C9RUN receipt was carried over from `5b770f09`. The frozen C9 spec, prompt contract, optimizer, seed and schedules retain their published pins.
- The staged checkpoint manifest was rehashed at `0a9deecdd2deb028c8555a236241f6fe4bc9d9fe9ee64be4493daa397527459e`, matching C9RUN's verified manifest.
- The production guard matches the exact device name against `NVIDIA A10` and `NVIDIA L4`. The shared training manifest makes both arms match the detected hardware and package runtime. Prediction compares its runtime with the shared manifest and the adapter's arm manifest before reading the Track A roster. Arm and prediction manifests carry the detected GPU. The RunPod launcher checks the detected name against the approved placement. [Training](../../../loe-bench/c9/train.py) · [Prediction](../../../loe-bench/c9/predict.py) · [Execution instructions](../../../loe-bench/c9/README.md)
- `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` ran in the existing C9 Python 3.12 CPU runtime. **233 passed**, exit 0. Existing Purple Book file-handle warnings appeared. Mocked GPU tests cover A10 and L4 acceptance, other GPU rejection, cross-arm mismatch rejection and prediction mismatch rejection. The fixture suite checks the 32 × 8 roster schedule and 64 updates per arm.
- Root `python -m pytest` reported **2,760 passed**, **50 skipped**, **1 xfailed** and **8 failed**, exit 1. All failures are the standing SACR r2/r3 `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` variants accepted in `AGENTS.md`.

## Development admission

The generic T1v3 development entrypoint rejected the existing registration lock. The read-only intake then used the same bounded path as C3, checking the C9 spec and S0 manifest pins and requiring the test authorization variable to be absent. The lock and protected partitions were untouched. `c3_dev_run._inputs` verified the pinned FDA raw file hashes and used `project_development_anda`, `project_orange` and the NDA guard. It retained final original approvals only through 2016-01-01 before decoding outcome records. The guarded replay returned 2,445 NDA entities and 11,753 original final ANDA applications, of which 11,375 linked to an NDA entity. The C3 receipt independently records the same 11,753 admissions and 14 applications with no admissible group. [C3 audit](C3.md#development-result) · [Bounded reader](../../../loe-bench/scripts/c3_dev_run.py)

The application-level linkage check found 14 ANDAs with no dated admissible group. Three have a composition candidate in the guarded Orange Book index and 11 have neither an admitted composition nor a cutoff-compatible Orange Book composition for the same application. The 11 dates span 1972-10-25 through 2007-09-19. A second lookup filtered Orange Book products individually before decoding across the three admitted ANDA partitions and checked undated Drugs@FDA ingredient and annotation fields. It recovered zero additional candidates for the 11. The check also found seven undated composition assignments across the whole admitted ANDA stream. An unassigned final approval that predates the first 1995 cutoff could affect prior-ANDA eligibility even when its date precedes a row's outcome window. The pinned intake has yet to establish which drug histories can rule out these missing links. The S0 observation date establishes calendar follow-up and the raw hashes establish snapshot identity. Row-level coverage also requires resolving or bounding the earlier unassigned approvals.

The approved path `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/c9_dev_projection.json` has no certified export or SHA-256. Projection counts, source-to-row coverage, and production roster, keys, messages and token hashes are `NOT_RUN`. Resolve or bound the unresolved applications against allowed dated identity evidence before admitting either class. Then freeze the private projection and its small Git manifest and run the existing CPU roster builder with the independently recorded SHA-256.

## Training and billing

OSF update 2 opens the approved training period in December 2026 or January 2027 after C′ PASS and before the core Track A freeze. The live clock was 2026-11-28 UTC during this card, before the launcher opens at 2026-12-01 00:00 Bangkok. Re-quote the approved placement when admission is possible and stop if the exact placement is unavailable. Use the live quote for the USD 4.50 all-in envelope and preserve the registered per-arm limits of 2.5 GPU-hours and USD 3.50. [Audited OSF copy sheet](../OSF-UPDATE-2-SHEET.md) · [OSF response](https://api.osf.io/v2/schema_responses/6b0a61a4341762fcbae66946/)

| Evidence | Status |
| --- | --- |
| Live quote, placement, volume suitability and pod ID | `NOT_RUN` |
| GPU fit, throughput and detection on hosted runtime | `NOT_RUN` |
| SFT and GRPO updates, wall time, losses and adapter hashes | `NOT_RUN`, 0 updates in each arm |
| Track A predictions and outcome evaluation | `NOT_RUN` |
| Start/stop, billing and deletion | No pod created. Deletion inapplicable. USD 0 incremental spend |

After data and calendar admission, run SFT then GRPO through the training-only commands, retaining the paired directory and logs under the C9 private workspace. Verify retrieval hashes and pod deletion before handback. Pass the verified runtime and adapter pair to the freeze card for prediction.
