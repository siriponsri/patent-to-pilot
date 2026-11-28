# How to score Track A

LOE-Bench Track A tests whether a fixed-size review queue captures drugs that receive their first final original US ANDA approval. Track A forecasts use the same 27 November 2026 cohort throughout. The endpoint is an FDA action. The independent registration records the frozen predictions and methods. [OSF registration and updates](https://doi.org/10.17605/OSF.IO/P2SMD).

## Run the scorer

1. Obtain the **version DOI** of the published Track A release. Download and unpack `track-a-release.zip`. The release metadata must say `"freeze": "frozen"`. Compare the SHA-256 of `freeze-manifest.json` with the digest in OSF update 4. The files in a local rehearsal are marked `pending`.
2. Open a terminal in the unpacked directory. Use CPython 3.12.10 and install the NumPy wheel verified by the supplied lock.

   ```sh
   python -m pip install --only-binary=:all: --require-hashes -r requirements-tracka.lock
   ```

3. With `FREEZE_SHA256` replaced by the value from OSF, run the 12-month readout.

   ```sh
   python -m loe_bench.score_release --release . --horizon 12 --out ../track-a-results --freeze-sha256 FREEZE_SHA256
   ```

   An installed matching scorer also accepts `--release 10.5281/zenodo.VERSION_ID`. The argument must identify one publication version. Use the Zenodo record to obtain a clean copy of the software when replaying years later. [Zenodo record versions](https://help.zenodo.org/docs/deposit/manage-versions/).

4. Save the whole first `SCORED` 12-month directory, including its sources, manifest and bootstrap draws. Publish or transfer that archive before the Actions artifact expires. On or after 27 November 2028, run the same command with `--horizon 24`. Reuse the same output root so the scorer picks the first completed 12-month panel. On a new machine, pass `--prior-12 /path/to/first-12-month-run` and retain the archive. When neither location supplies a 12-month result, the 24-month run computes a late first 12-month readout from its covered snapshot and reports that provenance. Prefer the original 12-month archive when one exists.

## Read the outputs

| Status | Exit | What it means |
| --- | ---: | --- |
| `SCORED` | 0 | The specified horizon has a complete source panel. Consult the per-hypothesis status and reported uncertainty. |
| `PENDING` | 2 | The UTC date precedes maturity or the release is a pending rehearsal. The command made no outcome request. |
| `BLOCKED_SOURCE` | 3 | A required edition, partition, date or identity was missing or inconsistent. The report lists the gaps. Score again when the source supports the full window. |
| `INVALID_RELEASE_OR_RUN` | 1 | Required manifest bytes, a file hash, roster order, arm data, or archived results failed a verification check. Recover the exact released files before retrying. |

Each run writes into a new `12m/run-NNNN` or `24m/run-NNNN` directory. `results.json` and `REPORT.md` give the status and aggregate results. `outcome-source-manifest.json` records each attempted snapshot's source, edition, digest, fetch timestamp and gaps. The snapshot ZIPs and FDA index are retained under `sources/`. A completed run carries `bootstrap-draws.npz` with every new draw, `event-witnesses.json` with app and partition locators, and `run-manifest.json` with the hashes of the top-level results. Preserve the prior 12-month archive when a 24-month readout references it.

Later runs create revisions and keep the first scored result in the same output root. Preserve the first result and cite its digest if a later FDA edition revises approvals. To reproduce against identical FDA bytes, use `--snapshot /path/to/run-NNNN/sources`; the supplied directory must still be next to its original `outcome-source-manifest.json`. Use a local release directory for an entirely offline replay. Each result is conditional on recorded approvals and the FDA edition used.

## Outcome coverage and analysis order

The scorer reads every partition listed in the [openFDA Drugs@FDA bulk export](https://open.fda.gov/apis/drug/drugsfda/download/). The index date, the embedded version, partition offsets and record counts must agree, and the edition must cover the window end. If Drugs@FDA product identity or dating needs corroboration, the scorer tries the [openFDA Orange Book export](https://open.fda.gov/apis/drug/orangebook/download/). Orange Book helps link products. A qualifying event still requires Drugs@FDA `ORIG/AP`. The frozen GSRS and FIX2c crosswalk resolves full active-moiety sets. Already-final baseline application IDs remain pre-window. Tentative actions, supplements, NDAs and approvals after maturity contribute no events. Unresolved qualifying records and conflicts are reported for review. The rule covers FDA-recorded events subject to database publication and correction lags. [Bulk download format and revision guidance](https://open.fda.gov/apis/downloads/).

| Earliest date | Report |
| --- | --- |
| 27 November 2027 | Descriptive 12-month estimates, paired intervals and exploratory arms. H3 is `DESCRIPTIVE_PENDING` until the 24-month sequence. |
| 27 November 2028 | Test H1 (24-month M3 minus B1). Test H2 (24-month M3 minus M1) only after H1 passes. Test H3 (12-month M3 minus B1) only after both pass. Otherwise the unreached steps remain descriptive. |

For each reached step, superiority requires a strictly positive one-sided lower bound at α = 0.025. The report gives the observed contrast, its two-sided 95% interval and whether the estimate reaches +10 percentage points. The queue uses `floor(N/5)` slots. A boundary tie allocates each tied drug the same fraction of the remaining capacity. Each interval uses 2,000 paired whole-drug PCG64 draws with seed 20261127 reset per horizon and linear quantiles. A single undefined draw makes that interval unevaluable. The saved draws retain such draws as NaN.

B3 and the optional arms stay outside H1–H3. Core and prior-method arms report native-score AUC and restricted within-cutoff C-index. The latter counts only pairs with a strictly later observed time than the event. The results give its comparable-pair denominator and a null estimate when no pairs qualify. Accuracy uses the inclusive 0.5 threshold. Accuracy and Brier use the calibrated core probabilities, native survival probabilities for P1/P2, and the hard call for B3. L1 and L1e use native parsed risk for the queue and rank malformed completions below valid predictions. C9 GRPO and SFT use that ranking and a 0.5 Brier probability for malformed outputs. `NOT_RUN` contrasts list missing arms. If the freeze missed the deadline or had post-t0 outcome exposure, the release flags its readout exploratory and reports the hypotheses descriptively. [Prior-method metric specification](https://github.com/siriponsri/patent-to-pilot/blob/5861d077/docs/loe-bench/PRIOR-ARMS-SPEC.md).

## GitHub Actions and continuity

The default branch can run **Score Track A** from Actions → Run workflow. Give it the exact release version DOI and the OSF freeze-manifest SHA-256. For a 24-month dispatch with a retained GitHub artifact, supply the first scored 12-month run ID. Download and preserve the result artifact after every useful run. Actions retains artifacts by workflow run ID. The dates near 1 December 2027 and 1 December 2028 are conveniences. GitHub disables schedules after 60 days without activity in public repositories. Manual dispatch or a local run from the archived release is the reliable path. [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

An advisor, reviewer or other maintainer can score the public release with no account. If a frozen prediction file has redistribution limits, the release records `WITHHELD` and scores the remaining arms. A custodian with lawful access may build a separate controlled release from the same frozen bytes and provide aggregate output, manifest digests and the provenance record for the affected arms.

## Publish the prediction package once

The owner or a consenting depositor can complete this before the handoff. Wait for the audited freeze tag and OSF update 4. In Zenodo choose **New upload**, select Dataset, enter the title **LOE-Bench Track A prediction release**, add Siripon Srihangpiboon and Tuchsanai Ploysuwan as creators, and link the OSF registration and repository. Reserve the draft DOI if it will appear in `CITATION`. [Zenodo upload details](https://help.zenodo.org/docs/deposit/create-new-upload/).

From `loe-bench/`, replace the capitalized arguments with the audited values. The private directory must contain `trackA/`, `raw-20261127/` and `moiety/`. `TAGGED_MANIFEST_PATH` is the repo-relative path at the freeze tag, such as `loe-bench/data/TRACKA_FREEZE_MANIFEST.json`. The original manifest must expose `files_sha256` keyed by the package-relative filenames. If the freeze uses different GPU filenames, specify `--arm-file ARM=relative/path.jsonl` for each changed name. Use `--share-optional ARM` only after reviewing the exact frozen GPU file and rights. Include both C9 arms together.

```sh
python -m loe_bench.build_release --private PRIVATE_LOE_ROOT --out RELEASE_DIR \
  --freeze-tag FREEZE_TAG --freeze-git-path TAGGED_MANIFEST_PATH \
  --freeze-manifest PRIVATE_FREEZE_MANIFEST --osf-manifest-sha256 FREEZE_SHA256 \
  --osf-timestamp UPDATE_4_APPROVED_UTC --zenodo-doi VERSION_DOI \
  --archive path/to/track-a-release.zip
```

Check `RIGHTS.csv`, the package hashes, and the result of running the packaged scorer on a clean machine before maturity. Upload only `track-a-release.zip`, set public visibility, choose the project Apache-2.0 license and disclose the CC0 source fields in the description, then publish. In an unauthenticated session, verify that the exact version DOI resolves and that the archive and frozen manifest digests match. Set `TRACKA_RELEASE_DOI` and `TRACKA_FREEZE_SHA256` in GitHub Actions variables. Set `TRACKA_SCORER_REF` to the full Git commit used to build the kit so Actions can keep using those scorer bytes. Send the version DOI and this guide to the advisor or custodian. For revised public bits, make a new version and retain the old record.
