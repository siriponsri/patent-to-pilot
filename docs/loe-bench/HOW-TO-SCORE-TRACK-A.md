# How to score Track A

LOE-Bench Track A tests whether a fixed-size review queue captures drugs that receive their first final original US ANDA approval. Track A forecasts use the same 27 November 2026 cohort throughout. The endpoint is an FDA action. The independent registration records the frozen predictions and methods. [OSF registration and updates](https://doi.org/10.17605/OSF.IO/P2SMD).

## Run the scorer

1. Download and unpack `track-a-release.zip` from the published [Track A release, version 1.0.0](https://doi.org/10.5281/zenodo.24629100). The release metadata must say `"freeze": "frozen"`. Compare the SHA-256 of `freeze-manifest.json` with the digest in OSF update 4. The files in a local rehearsal are marked `pending`.
2. Open a terminal in the unpacked directory. Use CPython 3.12.10 and install the NumPy wheel verified by the supplied lock.

   ```sh
   python -m pip install --only-binary=:all: --require-hashes -r requirements-tracka.lock
   ```

3. With `FREEZE_SHA256` replaced by the value from OSF, run the 12-month readout.

   ```sh
   python -m loe_bench.score_release --release . --horizon 12 --out ../track-a-results --freeze-sha256 FREEZE_SHA256
   ```

   An installed matching scorer also accepts `--release 10.5281/zenodo.24629100`. The argument must identify one publication version. Use the Zenodo record to obtain a clean copy of the software when replaying years later. [Zenodo record versions](https://help.zenodo.org/docs/deposit/manage-versions/).

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

The default branch can run **Score Track A** from Actions → Run workflow. The workflow uses the repository's pinned Zenodo version DOI and OSF freeze-manifest SHA-256 by default. For a 24-month dispatch with a retained GitHub artifact, supply the first scored 12-month run ID. For an older archive saved elsewhere, use the CLI with `--prior-12`. Preserve the full first scored artifacts before GitHub deletes them after up to 90 days. [GitHub artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-retention-period-for-artifacts-and-logs-in-your-repository).

After owner setup, the [Cloudflare Worker](../../ops/tracka-cron/README.md) dispatches mature horizons daily until the canonical issue records a scored result. The issue includes the report, timing and Actions run link. The existing December schedule is a fallback. GitHub disables scheduled workflows after 60 days of inactivity in public repositories. Import the [Bangkok readout calendar](reminders/track-a-readouts.ics) for reminders. [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

### If nobody runs this

Anyone can download the public release and use the scoring command above. Use version DOI `10.5281/zenodo.24629100` and the freeze-manifest SHA-256 in OSF update 4. A readout run after the maturity date in UTC is late and remains valid. Record the actual UTC scoring date, the unchanged window end, the FDA edition, both release identifiers and the result table with the archive link. Keep the first scored output for each horizon. A later FDA edition may change the result while the endpoint window stays fixed.

Post the report and archive link in the existing **Track A 12-month readout** or **Track A 24-month readout** GitHub issue, or open an issue with that title when none exists. An OSF registration comment is also suitable where comments are enabled. For an independently scored result, a repository maintainer can verify the report and add `<!-- tracka:HORIZON:SCORED:FREEZE_SHA256:VERSION_ID -->` as a line in a maintainer-authored issue body of that title, replacing the three placeholders. This records the result for the Worker and stops daily dispatches for that horizon. [GitHub issues](https://github.com/siriponsri/patent-to-pilot/issues) · [OSF registration](https://doi.org/10.17605/OSF.IO/P2SMD).

If a frozen prediction file has redistribution limits, the public release records `WITHHELD` and scores the remaining arms. A custodian with lawful access may build a separate controlled release from the same frozen bytes and provide aggregate output, manifest digests and the provenance record for the affected arms.

## Publish the prediction package once

The owner or a consenting depositor can complete this before the handoff. Wait for the audited freeze tag and OSF update 4. In Zenodo choose **New upload**, select Dataset, enter the title **LOE-Bench Track A prediction release**, add Siripon Srihangpiboon and Tuchsanai Ploysuwan as creators, and link the OSF registration and repository. Reserve the draft DOI if it will appear in `CITATION`. [Zenodo upload details](https://help.zenodo.org/docs/deposit/create-new-upload/).

From `loe-bench/`, replace the capitalized arguments with the audited values. The private directory must contain `trackA/`, `raw-20261127/` and `moiety/`. The Track A freeze manifest pins the roster and the admitted per-arm files. `TAGGED_MANIFEST_PATH` is the repo-relative path at the freeze tag, `loe-bench/data/TRACKA_FREEZE_MANIFEST.json`. Pass `--share-optional ARM` for each GPU file cleared for redistribution. Include both C9 arms together. Omit `--zenodo-doi` if you have yet to reserve a DOI for this archive.

```sh
python -m loe_bench.build_release --private PRIVATE_LOE_ROOT --out RELEASE_DIR \
  --freeze-tag FREEZE_TAG --freeze-git-path TAGGED_MANIFEST_PATH \
  --freeze-manifest PRIVATE_FREEZE_MANIFEST --osf-manifest-sha256 FREEZE_SHA256 \
  --osf-timestamp UPDATE_4_APPROVED_UTC --zenodo-doi VERSION_DOI \
  --archive path/to/track-a-release.zip
```

Check `RIGHTS.csv`, the package hashes, and the result of running the packaged scorer on a clean machine before maturity. Upload only `track-a-release.zip`, set public visibility, choose the project Apache-2.0 license and disclose the CC0 source fields in the description, then publish. In an unauthenticated session, verify that the exact version DOI resolves and that the archive and frozen manifest digests match. Set `TRACKA_RELEASE_DOI` and `TRACKA_FREEZE_SHA256` in GitHub Actions variables. Set `TRACKA_SCORER_REF` to the full Git commit used to build the kit so Actions can keep using those scorer bytes. Send the version DOI and this guide to the advisor or custodian. For revised public bits, make a new version and retain the old record.
