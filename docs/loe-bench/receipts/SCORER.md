# SCORER | Track A readout and release kit

The card implements independent CPU scoring from an exact Zenodo version DOI or a local release directory. The starting revision is `5861d077` on `origin/research/loe-bench`, with `09406deb` in its history. The 12-month window ends on 27 November 2027 and the 24-month window on 27 November 2028. The real prospective readouts are **NOT_RUN**. No post-t0 outcome records, protected C′ data, paid APIs or GPU work were used.

## Interface and analysis

- `python -m loe_bench.score_release --release <dir-or-zenodo-version-doi> --horizon {12,24} --out <dir>` verifies the frozen prediction bytes, release and scorer digests, exact roster order and admitted arm columns. Use `--freeze-sha256` to check the manifest against OSF update 4.
- `python -m loe_bench.build_release --out <dir>` takes the private Track A forecasts and S0 inputs. Before the tag, run with `--dry-run`. For publication, the private and tagged manifest bytes and the OSF digest must agree. The public kit carries a recipe for restricted inputs, its scorer and a hash-locked NumPy dependency.
- A covered export requires every Drugs@FDA partition, the declared offsets and record counts, agreeing edition dates, and coverage through maturity. Orange Book may corroborate product identities and dates. Events still require a dated Drugs@FDA final original ANDA action. Retain the capture bytes and their provenance for replay.
- Native-score queues use the shared `ReviewQueue` tie-allocation code used by SCORE and PRIORARMS. The 2,000 paired PCG64 draws resample whole drugs, rebuild queues, retain undefined draws, and use linear quantiles. The 12-month result is descriptive. The 24-month command applies H1, then H2, then H3 to the first available 12-month readout under the registered sequence. It records a late 12-month readout when the first one is unavailable. Later results in the same output root use new run directories.
- The workflow dispatch and December cron run the same CLI. The scheduled path depends on a default-branch integration, release variables and GitHub activity. Manual dispatch or a local run is the durable path. [Third-party scoring and publication guide](../HOW-TO-SCORE-TRACK-A.md).

## Fixture and test evidence

| Check | Evidence |
| --- | --- |
| Known-answer fixture | 20 synthetic drugs, 10 events at 12 months and 12 at 24 months. Four slots. The three-way boundary tie gives M3 10/3 expected queued events and recall 1/3 at 12 months. B1 recall is zero. B3 gives recall 0.20, AUC 0.5 and C-index 0.5 over 99 comparable pairs. |
| Sequence | H3 is `DESCRIPTIVE_PENDING` at 12 months. In the planted 24-month example H1, H2 and H3 pass using the archived 12-month panel. Separate cases verify a zero-bound H2 stop and an unevaluable H1. |
| Integrity | Altered bytes fail the CLI with exit 1. Reordered rows fail even if the affected digests are recomputed. The DOI fixture requires an exact record version. |
| Coverage | Prematurity and a pending freeze avoid outcome fetches. Stale and inconsistent snapshot editions block. A missing original product can be recovered from a dated Orange Book listing, with the approval date still sourced to Drugs@FDA. |
| Revisions and replay | An added FDA approval changes a later 12-month panel while the first result retains its exact hash. Replay from the archived FDA bytes produces the same aggregate panel. The fixtures mock the fetcher. |

| Command | Status |
| --- | --- |
| From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` | **PASS**, 261 tests, 251 passed and 10 skipped, exit 0. Existing Purple Book file warnings appeared. |
| Root `python -m pytest --tb=short -p no:cacheprovider` | **FAIL (standing only)**, 2,760 passed, 50 skipped, 1 xfailed and 8 failures, exit 1. Four cases each in SACR r2 and r3 `test_budget_cannot_use_nonfinite_inflated_or_erased_cost`. |
| Workflow YAML, dispatch and schedule keys, and `bash -n` on shell blocks | **PASS**. GitHub runner execution is **NOT_RUN** pending integration and release. |
| Packaged CLI from the staged directory | **PASS**. Both horizons returned `PENDING` and exit 2 with empty outcome-source lists. |

The initial DOI fixture returned ZIP bytes for the concept-record metadata request. Correcting the mock exercises the intended DOI mismatch. The first workflow parse caught an unquoted colon in the pip argument and passed after using a YAML block scalar. A follow-up dry run exposed a filename check that rejected `__init__.py`. The checker now accepts that Python filename.

## Dry run and rights

The dry run uses the verified private `trackA/` package under the LOE-Bench private root. It stages 651 ordered keys at both horizons, the B1/B3/M1/M3 files, both prior-method files, and the frozen S0 identity projection. Dry-run metadata says `freeze: pending`. The pending manifest references TRACKA-CORE and PRIORARMS hashes for this rehearsal. It does not stand in for the tagged freeze manifest or OSF update 4.

The local `scorer-dry-run-v1/` package contains 17 top-level files and 25 Python source files. Its `release.json` SHA-256 is `d7ebd6dd58d7b576dda38d40bd871c8161336315207291121af59935a296dabc`. The pending freeze-manifest SHA-256 is `b7261e6e0bb3727569edd1cf0ebb0969b5a9a90a5c464afb7373e7cf950acea7`. The rights table SHA-256 is `8a7b7dad05ac6b4f783757313fd6645a918ff4cd928c9d2e2651b2d7394a6d19`. Both packaged readouts are under sibling `scorer-dry-run-check/`.

| Files | Source | License or terms | Shareable after freeze |
| --- | --- | --- | --- |
| `core_predictions_12m.jsonl`, `core_predictions_24m.jsonl` | TRACKA-CORE numeric forecasts | Apache-2.0 project artifacts | Yes |
| `priorarms_predictions_12m.jsonl`, `priorarms_predictions_24m.jsonl` | PRIORARMS numeric forecasts | Apache-2.0 project artifacts | Yes |
| `roster.jsonl`, `identity.json` | S0 openFDA and GSRS names and identifiers, FIX2c | CC0 1.0 source fields and Apache-2.0 project artifacts | Yes |
| `arm-dictionary.json`, `freeze-manifest.json`, `release.json`, `scorer-version.json` | Project release and freeze metadata | Apache-2.0 | Yes |
| `loe_bench/*.py` scoring subset, `requirements-tracka.lock`, `LICENSE` | Repository and official NumPy wheel hashes | Apache-2.0 project files. NumPy BSD-3-Clause wheels are installed separately. | Yes |
| `README.md`, `CITATION`, `RIGHTS.csv`, `SOURCE-RECIPES.md`, `example-output.json` | Project instructions and release metadata | Apache-2.0 | Yes |
| Raw GSRS/S0, prompts, projected evidence, fitted models and NBER-derived bytes | Mixed original sources | See the rights inventory and recipes. NBER site terms restrict redistribution. | Excluded from this kit |
| L1/L1e/C9 prediction files | Future admitted GPU outputs | Exact-file rights review required by the release procedure | Conditionally. The rehearsal has no such prediction bytes. |

`RIGHTS.csv` enumerates each packaged file and the private freeze components. The contributor can reproduce the versioned source references with the [S0 manifest](../../../loe-bench/data/S0_INPUT_MANIFEST.json), [GSRS provenance](FIX2.md#sources), [NBER receipt](E8.md) and [NumPy 2.5.4 wheel list](https://pypi.org/project/numpy/2.5.4/).

## Handoff and memory for the Planner

The release tag and OSF update 4 are publication dependencies. Build the real ZIP from the audited private package once both anchors agree. A depositor signs in to Zenodo, reserves a version DOI if needed, checks the rights table and clean-machine command, and publishes the release archive. Verify the DOI from an unauthenticated session, configure the workflow variables and transfer the version DOI and guide to the advisor or custodian. Use the exact commands and fields in [Publish the prediction package once](../HOW-TO-SCORE-TRACK-A.md#publish-the-prediction-package-once).

The final freeze-manifest naming and GPU admission need reconciliation with TRACKA-FREEZE when its tagged bytes exist. Keep the optional arms `WITHHELD` when they cannot be distributed. A custodian can score identical verified bytes with lawful access and share aggregates and provenance. Future FDA edition availability, actual outcome linkage, execution on the GitHub runner and public DOI restoration are **NOT_RUN**. Integrate the workflow onto the default branch only through the Planner. Record the branch and final verification in the lane handoff and memory at integration.
