# RELEASE-KIT · Track A release and restore

**Build PASS.** The frozen release contains 49 files and all ten admitted arms. The 12-month panel has eight arms, and the 24-month panel has ten. Both use the same 651 active-moiety keys in the registered order. The [Zenodo upload sheet](../ZENODO-UPLOAD-SHEET.md) gives the owner the archive and deposit metadata. The archive and audit files are under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/release/`.

| Check | Verified value |
| --- | --- |
| Base | `25ea28097695744be18f1dfa167b4e19eba22d08` on `loe/RELEASE-KIT`. The live lane had advanced to `40bb137f9badf5f306d46974109d38d8e85a863b` at checkout verification. This card stayed on its assigned base. |
| Annotated freeze tag | `loe-track-a-freeze-20261127` peeled to `6712f32cdfb1252d66e192d770deaa867808a375` on origin. |
| Freeze manifest | Private original, Git tag blob and release member are byte-identical. OSF declares SHA-256 `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d`. |
| OSF update 4 | Public schema response `6b0abacc9917f6722859f5ec`, question `72-61`. State `approved`. Submitted at `2026-11-28T11:30:06.792229Z`, represented to seconds in the kit. All ten per-arm digests match the freeze and private files. [OSF response](https://api.osf.io/v2/schema_responses/6b0abacc9917f6722859f5ec/) |
| Release ZIP | `acb533afb45f34f40d2ece2b97bc72b2b08fc3f6919fd73e1eb7064bf6e8049a` (15,983,054 bytes). The freeze archive recorded in OSF is a separate artifact for the original prediction deposit. |
| Release manifest | `879d27d9e60fb141d0e46ec2bc17aad3de61938460e678e7178841a8d2ca6d76`. The upload sheet gives the other key digests. |
| Member inventory | Local `SHA256SUMS` records exact-byte digests of the archive and all 49 members. ZIP CRC, member bytes, declared rights coverage and bound prediction hashes all passed. The ten predictions also match the bytes of the original OSF-pinned prediction archive. |

## Build and integrity

Run from `loe-bench/` with CPython 3.12.10. Read the OSF status and digest independently from the public response before running the builder. The builder compares the private bytes with the raw blob from `git show refs/tags/loe-track-a-freeze-20261127:loe-bench/data/TRACKA_FREEZE_MANIFEST.json` and checks the OSF digest.

```powershell
$root = 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench'
python -B -m loe_bench.build_release --private $root `
  --out "$root/release/kit" --archive "$root/release/track-a-release.zip" `
  --freeze-manifest "$root/tracka-freeze-20261128/r6fi2d2uyhjzfz/freeze/TRACKA_FREEZE_MANIFEST.json" `
  --freeze-tag loe-track-a-freeze-20261127 --osf-timestamp 2026-11-28T11:30:06Z `
  --osf-manifest-sha256 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d `
  --share-optional L1 --share-optional L1e --share-optional C9-SFT --share-optional C9-GRPO
```

The preflight found that the builder expected the rehearsal's `files_sha256` map and grouped columns. The release now reads the actual `loe-track-a-freeze-v1` roster, file and arm pins, and it retains support for the rehearsal and synthetic format. The first real build exited 1 on the L1 roster comparison. L1 and L1e store ingredient display names. The scorer now reconstructs the ordered, three-field L1 identity projection and checks its exact digest against the frozen `L1DEV_inputs.jsonl` pin for both arms. TRACKA-CORE produced these identities in canonical roster order. The subsequent build exited 0 and kept all ten prediction files byte-for-byte. A regression fixture verifies the per-arm format and rejects swapping M3 onto B1's file even when the dictionary hash is recomputed. [TRACKA-CORE](TRACKA-CORE.md) · [Freeze](TRACKA-FREEZE.md) · [Original scorer](SCORER.md).

## Rights and contents

The ZIP member set exactly equals the 49 shareable rows in `RIGHTS.csv`. The 14 exclusion entries have no ZIP members. D-L is the project licence authority. Source terms remain applicable to source material. [Owner decision D-L](../../maintenance/OWNER-DECISIONS-20261122.md) · [Scorer source-rights inventory](SCORER.md#dry-run-and-rights).

| Files | Rights check |
| --- | --- |
| B1, B3, M1, M3, P1-RSF-OPEN and P2-COX-OPEN prediction JSONLs (6) | Each exact OSF-pinned file carries identifiers, dates, numeric predictions and, where present, project flags or queue weights. The open-input training and forecast provenance reference FDA sources. NBER E8 was prior development only. Project outputs are shareable under Apache-2.0. [Registration sources](../PREREGISTRATION.md#datasets-availability-identifiers-and-access-dates) · [Prior arms](PRIORARMS.md) |
| L1, L1e, C9-SFT and C9-GRPO prediction JSONLs (4) | Checked all 3,906 rows and decoded every completion. Each completion has an action, probability and a missing-evidence list matching the parsed row. L1 lists ingredient-specific or generic missing categories, L1e lists feature names, and C9 lists are empty. The files contain forecast output, public ingredient identities, and run metadata. Both model revisions carry Apache-2.0. Model weights, adapters, prompt messages and evidence projections stay outside the archive. [Qwen 7B licence](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/raw/a09a35458c702b33eeacc393d103063234e8bc28/LICENSE) · [Qwen 1.5B licence](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/989aa7980e4cf806f80c7fef2b1adb7bc71aa306/LICENSE) |
| `roster.jsonl`, `identity.json` (2) | The pinned roster carries keys, cutoff and horizons. The regenerated S0 identity adapter carries public FDA application IDs and GSRS name/UNII mappings. These source fields retain CC0 1.0 and the project projection is Apache-2.0. [openFDA](https://open.fda.gov/license/) · [GSRS](https://gsrs.ncats.nih.gov/licensing) |
| `loe_bench/*.py` (25) | Allowlisted repository scorer and runtime modules. Apache-2.0 with code verification via `scorer-version.json`. |
| `requirements-tracka.lock` (1) | Project dependency pin and public wheel hashes under Apache-2.0. Restore downloads NumPy separately under its own wheel terms. |
| `LICENSE`, `NOTICE` (2) | Repository Apache-2.0 text and copyright/source notices. |
| `README.md`, `SOURCE-RECIPES.md`, `CITATION`, `example-output.json` (4) | Project scoring guide, source acquisition locators, citation and pending example under Apache-2.0. |
| `freeze-manifest.json`, `release.json`, `scorer-version.json`, `arm-dictionary.json`, `RIGHTS.csv` (5) | Frozen provenance and project-authored metadata under Apache-2.0. |
| Restricted and private inputs | NBER archive access is by recipe under publisher terms. Other omitted files include raw inputs, combined intermediate predictions, prompts, fitted models and private projections. The scoring kit uses the exact per-arm forecast files without those inputs. [NBER source terms](https://www.nber.org/terms-and-conditions) |

## Clean restore

**PASS on Windows, 28 November 2026 UTC.** The restored CLI loaded from a fresh ZIP extraction outside the repository, in a new CPython 3.12.10 virtual environment with the packaged lock and NumPy 2.5.4. PyPI supplied `numpy-2.5.4-cp312-cp312-win_amd64.whl`, SHA-256 `a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a`. During scoring, a Python audit hook denied repository and private-artifact reads, subprocesses and socket operations. A repository read probe and a DNS probe both failed as expected. The real-release checks used the machine's calendar. The synthetic checks alone used a fixed UTC date and a local synthetic FDA snapshot.

```powershell
python -m venv <fresh-venv>
<fresh-venv>/Scripts/python.exe -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --require-hashes -r requirements-tracka.lock
<fresh-venv>/Scripts/python.exe -B -m loe_bench.score_release --release . --horizon 12 --out <temp>/pending --freeze-sha256 <OSF-pin>
<fresh-venv>/Scripts/python.exe -B -m loe_bench.score_release --release <temp>/synthetic --horizon 12 --out <temp>/known --freeze-sha256 <fixture-pin> --snapshot <temp>/synthetic-capture/sources
```

Repeat each with `--horizon 24`. The synthetic 24-month run reused the first scored 12-month directory in the same output root. The negative cases used an all-zero external pin and a throwaway ZIP extraction with one space appended to `M3_predictions.jsonl`.

| CLI check | 12 months | 24 months |
| --- | --- | --- |
| Real archive with external OSF pin | Exit 2, `PENDING` until 2027-11-27 | Exit 2, `PENDING` until 2028-11-27 |
| Real archive outcome access | Empty source inventory and zero fetches | Empty source inventory and zero fetches |
| Synthetic known answer | Exit 0, `SCORED`. 20 drugs, 10 events and four slots. With a three-way tie, M3 recall was 1/3 and B1 recall was 0. B3 recall was 0.20, AUC 0.5 and C-index 0.5 over 99 pairs. H3 was descriptive. | Exit 0, `SCORED`. 12 events. H1, H2 and H3 passed the synthetic sequence and the H3 input hash matched the archived 12-month result. |
| Wrong external pin | Exit 1, external pin mismatch | Exit 1, external pin mismatch |
| Altered M3 prediction bytes | Exit 1, prediction SHA-256 mismatch | Exit 1, prediction SHA-256 mismatch |

Neither negative case wrote a scoring directory. The real release emitted only pre-maturity results. The retained scripts and result files are in `release/restore-audit/`. The log is `release/restore-transcript.log`, SHA-256 `551382206fea02e251cb04f95775b30ea0f0cffa962fc928577420f2e52fe752`. The final scorer source also passed all nine `python -m unittest loe_bench.tests.test_score_release -v` checks.

## Repository checks

- From the root, `python -m pytest -o addopts= -q --tb=short --basetemp <fresh-short-path>` in the S4 validation venv with its QA overlay ran the configured `tests/` suite. It returned 2,807 passed, 10 skipped, one xfailed and the eight standing SACR r2/r3 budget failures. Raw exit 1. No additional repository-suite failure appeared.
- The LOE-Bench scorer tests run separately. `python -m pytest -o addopts= -q loe-bench/loe_bench/tests/test_score_release.py` returned nine passed and exit 0 under CPython 3.12.10 with NumPy 2.5.4. An earlier targeted attempt under S4's NumPy 2.5.5 hit the scorer's dependency check on three fixtures. The correct locked runtime passed all nine. Duplicate root-suite attempts started while checking the runtime were interrupted after confirming that the root suite and LOE-Bench tests have separate collection paths.

## Remaining ownership and continuity

- **Zenodo publication and DOI verification — NOT_RUN.** The owner signs in and publishes after main planner review. Use the [upload sheet](../ZENODO-UPLOAD-SHEET.md). Keep the exact version DOI for scoring.
- **Custodian after January 2027 — OPEN.** Name a consenting custodian or record that none accepted. Retain the release version DOI, OSF pin, scoring guide and first completed readout.
- **GitHub Action — release integration pending.** The workflow file is present on origin's default branch at `036a445e51165b68e039308898e16e4610dc4fe8`. That revision still expects the rehearsal manifest. Integrate the reviewed scorer, then set `TRACKA_RELEASE_DOI`, `TRACKA_FREEZE_SHA256` and `TRACKA_SCORER_REF`. Local scoring works with the archived release. [Continuity plan](../ENDGAME-PLAN.md#ending-track-a-without-the-owner) · [Workflow guide](../HOW-TO-SCORE-TRACK-A.md#github-actions-and-continuity).

The planner owns the lane handoff and memory. For integration, record the final build and restore evidence here, retain the freeze unchanged, and carry forward DOI verification, the custodian decision and workflow integration. Real readouts remain **NOT_RUN**. No protected C′ TEST data, paid services or post-snapshot outcome downloads were used.
