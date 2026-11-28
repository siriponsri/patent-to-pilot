# TRACKA-READOUT7 verification protocol

29 November 2026. Executor branch `loe/TRACKA-READOUT7` starts at `7bc25790c74d6051ac806eb13438b3839dfbb940` on `origin/research/loe-bench`. The unit of verification is a fictional readout with local REST and attestation fixtures. [Round 6 review](../reviews/EXTERNAL-REVIEW-R6.md) · [First-publication gate](TRACKA-READOUT6-PROTOCOL.md).

## R6-A · Report the publication record and the current witness check

The first verified 24-month publication fixes the aggregate bytes, decisions and UTC publication date. Both ordinary replay and recovery report that the aggregate was formal as verified at publication on that date. Reuse the archived 12-month panel for comparison with the published result.

Before either mode returns, run one shared current check using canonical 12-month result discovery for the same repository, version DOI, freeze and release manifest. Compare the discovered result and FDA source-manifest hashes against the published H3 reference. Report `VERIFIED_CONSISTENT` if both match. Report `CURRENT_DISPUTE` for affirmative result-pin disagreement or a verified result that differs from the archived reference. Report `UNRESOLVED_CONTINUITY` if discovery otherwise cannot establish the required evidence. Include the reason and available witness locators and flag either failure for custodian reconciliation. Store this check in the new run and preserve the original published family.

Publish the fictional 24-month aggregate with uncontested 12-month witnesses. Run ordinary replay and recovery with consistent witnesses, then with two trusted 12-month issue pins that disagree. Check both report files, the machine-readable status and the exact archived asset hashes. Exercise missing evidence and verified digest mismatches. The existing prepublication hold, restoration and retry checks must still pass.

## R6-B · Report failed recovery at the source of the failure

Surface the result-discovery reason, detail and available locators in the top-level missing list and `REPORT.md` when result witnesses prevent recovery. When discovery finds no result, distinguish a verified capture with an absent publication from a genuinely missing capture. Exercise the review's verified-capture and disputed-result probe and a missing-capture fixture.

## Verification boundary

Run `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/`, `npm test` from `ops/tracka-cron/` and repository pytest with a fresh short temporary path. Record the interpreter, commands, counts and raw exit codes. The standing pytest exception covers the eight SACR r2/r3 supervisor budget failures. Keep protected TEST, sealed and private artifacts closed. Keep the forecasts, freeze manifest and tag, OSF and Zenodo records and primary scorer computations unchanged. This card uses no paid API or GPU and exercises no production readout or deployment.
