# TRACKA-READOUT9 protocol

29 November 2026. Address round-eight finding R8-A on `loe/TRACKA-READOUT9` from `origin/research/loe-bench` at `0bebf6ce9f7039073f70e4535b48cde960fed129`. Publish this protocol before editing the implementation. [Review finding](../reviews/EXTERNAL-REVIEW-R8.md#new-findings-table).

## Scope and acceptance

- Edit the unpinned integrated readout renderer and its tests. Change the scoring guide or readout addendum only if either describes the 12-month result as formal. Preserve the 25 installed sources in the published pin map, the frozen forecasts and manifest, the tag, and the OSF and Zenodo records. Use local synthetic fixtures. Keep protected TEST data, private artifacts and credentials outside the run. No paid API or GPU use.
- At 12 months, first publication, ordinary replay and recovery must identify the verified first panel, describe it as descriptive only and retained for later H3 use, and state that H3 can be tested only at the 24-month readout, on or after 27 November 2028, if both H1 and H2 pass. Generated reports for these paths must contain no use of “formal.”
- At 24 months, keep formal wording for the H1 → H2 → H3 family. Replay and recovery must keep the original UTC publication date and the current 12-month witness statement. Preserve the existing witness dispositions and published archive bytes. Compare the final `REPORT.md` digest with the corresponding `run-manifest.json` entry in each path at both horizons.
- Run `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/`, including the source-pin regression against the published metadata fixture. Run `npm test` from `ops/tracka-cron/`. Run `python -m pytest -o addopts= -q --tb=short --basetemp <fresh-short-path>` from the repository root. Only the eight documented SACR r2/r3 supervisor budget failures are accepted. Record interpreter, commands, counts, raw exit codes and any retries.
- Record the branch result in [the executor receipt](TRACKA-READOUT9.md). Check the complete branch diff against the pin map and publish the explicit card paths to origin for Planner review.
