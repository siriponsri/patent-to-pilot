# TRACKA-READOUT10 protocol

29 November 2026. Executor branch `loe/TRACKA-READOUT10` starts at `3d5cba8583f17e28f61cd25ac34376e0f4dbfc1f` on `origin/research/loe-bench`. This protocol is published before implementation. [Round 9 findings](../reviews/EXTERNAL-REVIEW-R9.md#new-findings-table).

## R9-A. Replay attribution

In the unpinned renderer, label the decision table at both replay horizons “current recomputation (not used for inference).” Place the first publication's retained H3 estimate, interval and release link next to the table. At 12 months identify the descriptive first panel that supplies H3 at 24 months, subject to the H1 and H2 gates. At 24 months identify the first published decision family and its H3 result. Explicitly report both point estimates when they differ.

Exercise the ordinary replay path with two synthetic FDA snapshot editions at each horizon. Use the first verified publication as the comparator and pass the revised snapshot explicitly. Assert the replay label, the changed estimate, the retained estimate and interval, the release link, and the SHA-256 match between the final `REPORT.md` and `run-manifest.json`. Check recovery separately through the existing coverage for unchanged published bytes.

## R9-B. Structured result guidance

Update the scoring guide's output table and add a short first-publication 12-month JSON example. Document `family_status` as publication/custody status. Direct consumers to `horizon_months` and the hypothesis entries' `reached` and `decision` for inference. Keep the existing JSON fields and archive-reader contract.

## Acceptance and scope

Run `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/`, including the published source-pin tests, and `npm test` from `ops/tracka-cron/`. Run repository pytest with the Windows test profile used for TRACKA-READOUT9 and record the interpreter, exact commands, counts and raw exit codes. Only the eight documented SACR r2/r3 supervisor budget failures are accepted. Verify a zero diff for all 25 published source-pin paths and check the card diff before committing explicit paths.

Use local synthetic fixtures. Protected TEST data, private artifacts, credentials, paid APIs and GPUs are outside scope. The frozen forecasts, manifest, tag, OSF records and Zenodo deposit are outside the write scope. Record results in the executor receipt and push the card branch for Planner review.
