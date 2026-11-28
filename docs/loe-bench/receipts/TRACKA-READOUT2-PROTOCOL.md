# TRACKA-READOUT2 prospective protocol

28 November 2026. Executor card for [external review R3 and R4](../reviews/EXTERNAL-REVIEW-R1.md#findings-table). Track A outcomes are pending until at least 27 November 2027. The prediction release, forecast files, freeze manifest and tag, OSF records, primary estimator, bootstrap and fixed-sequence gate are held fixed.

## R3 · First-publication identity and recovery

The first published 12-month result controls H3. Identify it by the SHA-256 of the exact JSON and the SHA-256 of its FDA source manifest, which lists each source edition, fetch timestamp and byte digest. Record the scoring date and first GitHub publication time. Publish the first canonical scored result as assets under a deterministic GitHub release tag scoped to the Zenodo version and freeze digest. Include the aggregate JSON, SHA-256, source manifest, report and bootstrap draws. Publish before writing the scored issue marker. Runs reuse the published assets on retry and never replace the first publication. A 24-month runner discovers the archive from the same scope, verifies the result and manifest digests and verifies the release, maturity, horizon and scorer identity before using the archived panel. Actions retention remains a convenience for full run artifacts.

If the original is absent or fails verification, compute the earlier window from the covered 24-month FDA snapshot and label H3 `REVISED_VINTAGE`. Give the original date where documented, otherwise record it as unknown alongside the scheduled 12-month maturity. Give the revised snapshot edition and scoring date. Preserve any prior publication. Treat a remote access or transport failure as an operational failure for retry. Keep the registered numerical computation and gate and identify any revised-vintage H3 decision explicitly.

Add a readout entry point over the existing digest-pinned release reader and statistical code. Scope the newer entry point to publication, vintage selection and secondary analysis so the published Zenodo kit and pinned primary scorer modules remain reproducible.

## R4 · Secondary outputs

Map the preregistration and U1–U4 by track, arm, horizon, output and frozen source. For B1, M1 and M3 at both maturities, report ten-bin ECE from calibrated probabilities, probability-only AURC80 and E-AURC, and frozen diagnostic action counts, rates, workload, event referrals, missed clears, decision loss and the existing whole-drug clear-safety interval and 3% criterion. Reuse the registered metric functions and conventions. Report distinct event-drug capture from the queue where it adds a named output. Examine the legacy confidence policy separately from the diagnostic policy. Report `NOT_ESTIMABLE` with a dated reason for measures whose necessary prediction-time fields are absent from the public freeze. Keep B3, prior-method and LLM semantics from the filed text and report additional comparisons descriptively. Publish the mapping and the H3 rule in the scoring guide and a dated repository implementation note for registration review.

## Acceptance before handoff

- Exercise archive discovery, verified identity, missing and invalid archive, and a two-vintage FDA fixture on separate output roots. Check that revised FDA history changes the fallback H3 estimate and leaves the verified first result and primary computations intact.
- Verify known answers for calibration bins, selective risk, flag/referral/clear workload, decision loss, and safety including zero clears. Verify any omitted field receives its documented disposition.
- Test the workflow using a synthetic dispatch if GitHub accepts it. Keep synthetic execution confined to local fixtures with no Zenodo or FDA outcome request and no canonical publication. Record the run URL or the reason it was `NOT_RUN`.
- Run the repo suite and affected scorer and Worker fixtures. Record interpreter, commands, counts, exits and failures. Verify the protocol and final commit on the remote card branch. Planner integration and live deployment follow review.
