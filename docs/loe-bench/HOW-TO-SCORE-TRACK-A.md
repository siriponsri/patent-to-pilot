# How to score Track A

LOE-Bench Track A tests whether a fixed-size review queue captures drugs that receive their first final original US ANDA approval. Track A forecasts use the same 27 November 2026 cohort throughout. The endpoint is an FDA action. The independent registration records the frozen predictions and methods. [OSF registration and updates](https://doi.org/10.17605/OSF.IO/P2SMD).

## Run the scorer

1. Use the integrated repository revision containing `loe_bench.tracka_readout`. Run from its `loe-bench/` directory. The readout uses the published [Track A release, version 1.0.0](https://doi.org/10.5281/zenodo.24629100) by exact version DOI or from an unpacked `track-a-release.zip`. Release metadata must say `"freeze": "frozen"`. Compare the SHA-256 of `freeze-manifest.json` with the digest in OSF update 4. The Zenodo kit carries the original scorer for reproducing the release baseline.
2. Use CPython 3.12.10 and install the NumPy wheel verified by the supplied lock.

   ```sh
   python -m pip install --only-binary=:all: --require-hashes -r requirements-tracka.lock
   ```

3. With `FREEZE_SHA256` replaced by the value from OSF, run a standalone 12-month calculation.

   ```sh
   python -m loe_bench.tracka_readout --release 10.5281/zenodo.24629100 --horizon 12 --out ../track-a-results --freeze-sha256 FREEZE_SHA256
   ```

   The registered DOI and freeze pin enable discovery in `siriponsri/patent-to-pilot`. The calculation is `PROVISIONAL` until the first verified publication at this horizon. Later calculations are `REPLAY`. A local unpacked release directory supports standalone provisional scoring. [Zenodo record versions](https://help.zenodo.org/docs/deposit/manage-versions/).

4. On or after 27 November 2028, use the same command with `--horizon 24`. Before the first 24-month publication, the readout checks the first 12-month publication for the H3 input. At either horizon, add `--snapshot /path/to/run/sources` to compute from archived FDA bytes. The resulting family is `PROVISIONAL` or, once the publication exists, `REPLAY`. Use `--recover` with the registered DOI and freeze pin to retrieve an existing publication without an FDA request or fresh comparison.
5. For fully offline provisional scoring, pass a local `--release` directory, `--snapshot /path/to/24-month-run/sources` and optionally `--prior-12 /path/to/first-published-assets --prior-12-sha256 FIRST_RESULT_SHA256`. The prior directory must contain `results.json`, `results.sha256` and `outcome-source-manifest.json`. A local prior archive provides a descriptive H3 estimate. To consult a formal result offline, keep a digest-verified copy of the first publication.

## Read the outputs

| Status | Exit | What it means |
| --- | ---: | --- |
| `SCORED` | 0 | The specified horizon has a complete source panel. The family disposition appears in `family_status`. |
| `RECOVERED` | 0 | `--recover` verified and saved the first publication. The retrieval is a `REPLAY` without a new calculation. |
| `PENDING` | 2 | The UTC date precedes maturity or the release is a pending rehearsal. The command made no outcome request. |
| `BLOCKED_SOURCE` | 3 | A required edition, partition, date or identity was missing or inconsistent. The report lists the gaps. Score again when the source supports the full window. |
| `INVALID_RELEASE_OR_RUN` | 1 | The frozen release, roster, scorer or an operational readout check failed. Recover the released inputs or retry the failed access. H3 vintage dispositions appear inside a `SCORED` result. |

Each run writes into a new `12m/run-NNNN` or `24m/run-NNNN` directory. `results.json` and `REPORT.md` give the status and aggregate results. `outcome-source-manifest.json` records each attempted snapshot's source, edition, digest, fetch timestamp and gaps. The snapshot ZIPs and FDA index are retained under `sources/`. A completed run carries `bootstrap-draws.npz` with every new draw, `event-witnesses.json` with app and partition locators, and `run-manifest.json` with the hashes of the top-level results. Preserve the prior 12-month archive when a 24-month readout references it.

The **first verified publication at each horizon controls the full family** in the registered repository, Zenodo version DOI and OSF freeze scope. The first 12-month publication is descriptive and supplies the H3 input. H3 can be reached formally only in the first 24-month publication. Standalone calculations display `PROVISIONAL` or `REPLAY` decisions for H1–H3. In JSON, `sequence_decision` and `sequence_reached` describe how the fixed sequence evaluated those inputs.

Retrieval stores the exact first assets in `<horizon>m/first-published-<result SHA-256>/`. `REPLAY.md` and `replay_comparison` point to that aggregate and record changed hypothesis values, panel fields and FDA manifest identity. When coverage or recovery-only mode prevents comparison, they record the reason. Verification checks the scoped release notes and every trusted scored issue against the result, checksum and FDA-manifest bytes. Publication time and scoring date are recorded in UTC. [Registration-facing clarification](TRACKA-READOUT-ADDENDUM.md).

If the 12-month release and tag are absent and all surviving trusted issue witnesses agree, H3 uses the covered 24-month snapshot and carries `REVISED_VINTAGE`. `h3_input.discovery` records the scope, queries, times, issue locators and available pins. Conflicting or malformed issue pins give `DISPUTED`. An unresolved publication gives `UNVERIFIED_INPUT`, leaving H3 descriptive and unreached. GitHub access or transport errors stop the run for retry.

## Outcome coverage and analysis order

The scorer reads every partition listed in the [openFDA Drugs@FDA bulk export](https://open.fda.gov/apis/drug/drugsfda/download/). The index date, the embedded version, partition offsets and record counts must agree, and the edition must cover the window end. If Drugs@FDA product identity or dating needs corroboration, the scorer tries the [openFDA Orange Book export](https://open.fda.gov/apis/drug/orangebook/download/). Orange Book helps link products. A qualifying event still requires Drugs@FDA `ORIG/AP`. The frozen GSRS and FIX2c crosswalk resolves full active-moiety sets. Already-final baseline application IDs remain pre-window. Tentative actions, supplements, NDAs and approvals after maturity contribute no events. Unresolved qualifying records and conflicts are reported for review. The rule covers FDA-recorded events subject to database publication and correction lags. [Bulk download format and revision guidance](https://open.fda.gov/apis/downloads/).

| Earliest date | Report |
| --- | --- |
| 27 November 2027 | Descriptive 12-month estimates, paired intervals and exploratory arms. H3 is `DESCRIPTIVE_PENDING` until the 24-month sequence. |
| 27 November 2028 | Test H1 (24-month M3 minus B1). Test H2 (24-month M3 minus M1) only after H1 passes. Test H3 (12-month M3 minus B1) only after both pass. Otherwise the unreached steps remain descriptive. |

For each reached step, superiority requires a strictly positive one-sided lower bound at α = 0.025. The report gives the observed contrast, its two-sided 95% interval and whether the estimate reaches +10 percentage points. The queue uses `floor(N/5)` slots. A boundary tie allocates each tied drug the same fraction of the remaining capacity. Each interval uses 2,000 paired whole-drug PCG64 draws with seed 20261127 reset per horizon and linear quantiles. A single undefined draw makes that interval unevaluable. The saved draws retain such draws as NaN.

B3 and the optional arms stay outside H1–H3. Core and prior-method arms report native-score AUC and restricted within-cutoff C-index. The latter counts only pairs with a strictly later observed time than the event. The results give its comparable-pair denominator and a null estimate when no pairs qualify. Accuracy uses the inclusive 0.5 threshold. Accuracy and Brier use the calibrated core probabilities, native survival probabilities for P1/P2, and the hard call for B3. L1 and L1e use native parsed risk for the queue and rank malformed completions below valid predictions. C9 GRPO and SFT use that ranking and a 0.5 Brier probability for malformed outputs. `NOT_RUN` contrasts list missing arms. If the freeze missed the deadline or had post-t0 outcome exposure, the release flags its readout exploratory and reports the hypotheses descriptively. [Prior-method metric specification](https://github.com/siriponsri/patent-to-pilot/blob/5861d077/docs/loe-bench/PRIOR-ARMS-SPEC.md).

`panels.<horizon>.secondary` records ten-bin ECE, probability-only selective risk, distinct-drug capture and the frozen diagnostic workload, decision loss and clear safety. The module reports `NOT_ESTIMABLE` for the legacy 90% confidence policy because the public release lacks its per-row calls and fitted thresholds. [Measure map and limitations](TRACKA-MEASURE-MAP.md).

## GitHub Actions and continuity

Run **Score Track A** on the registered repository's default branch from Actions → Run workflow. This is the canonical publication path. It checks the configured Zenodo version DOI and OSF freeze pin and fetches live FDA bytes at run time. After verifying absence at the current horizon, the job publishes `results.json`, `results.sha256`, `outcome-source-manifest.json`, `REPORT.md` and `bootstrap-draws.npz` under `track-a-<12 or 24>m-<Zenodo record ID>-<OSF freeze SHA-256>`. The release has no Actions retention timer. The 24-month JSON retains the safety results, including missed clears and upper bounds. For H3 based on the first 12-month publication, its draws remain in that archive. Newly captured FDA bytes remain in the run artifact for 90 days. Preserve those bytes separately for exact offline replay. [GitHub release assets](https://docs.github.com/en/rest/releases/assets).

After owner setup, the [Cloudflare Worker](../../ops/tracka-cron/README.md) dispatches mature horizons daily until the canonical issue records a scored result. Each scored issue records the result, source manifest, draws and report digests, publication time and a link to the archive. The December schedule is a fallback. GitHub disables scheduled workflows after 60 days of inactivity in public repositories. Import the [Bangkok readout calendar](reminders/track-a-readouts.ics) for reminders. [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

### If nobody runs this

The custodian can dispatch the default-branch workflow after maturity. The release records the actual UTC scoring date, unchanged window end and FDA edition. The workflow records a late publication's timing in the issue. Use the standalone command for provisional analysis while publication is pending. If a scored issue or tag survives without the release, recover and verify the original assets against their pins before resuming. [GitHub issues](https://github.com/siriponsri/patent-to-pilot/issues).

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

Check `RIGHTS.csv`, the package hashes, and the result of running the packaged scorer on a clean machine before maturity. Upload only `track-a-release.zip`, set public visibility, choose the project Apache-2.0 license and disclose the CC0 source fields in the description, then publish. In an unauthenticated session, verify that the exact version DOI resolves and that the archive and frozen manifest digests match. Set `TRACKA_RELEASE_DOI` and `TRACKA_FREEZE_SHA256` in GitHub Actions variables. Actions runs the readout from its own Git revision and the archived kit verifies the primary scorer source hashes. Send the version DOI and this guide to the advisor or custodian. For revised public bits, make a new version and retain the old record.
