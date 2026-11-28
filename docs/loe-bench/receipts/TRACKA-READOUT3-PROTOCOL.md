# TRACKA-READOUT3 prospective protocol

28 November 2026. This card addresses N1–N3 and the remaining R3 issues before the first outcome maturity on 27 November 2027. The frozen predictions, registration, tag and primary computation stay fixed. The rehearsal uses fictional FDA records and GitHub responses. [External review R2](../reviews/EXTERNAL-REVIEW-R2.md).

## N1 · Authority for the H3 vintage

Formal H3 requires the exact canonical repository, Zenodo version and OSF freeze scope. Use the first verified 12-month publication if available. Local archive options support descriptive replay and carry `UNVERIFIED_INPUT`, including when the caller supplies a correct digest. A missing option, unreadable directory or bad digest also carries `UNVERIFIED_INPUT`. These runs cannot reach H3 or publish a canonical 24-month result.

Canonical discovery records the repository, DOI, freeze and release digests, horizon, UTC query times, queried URLs and results, original identity and disposition. A revised vintage can enter the formal sequence only after the scorer receives a negative disposition directly from canonical discovery. Require successful inspection of the scoped issue history and explicit absence at both the release and tag endpoints. A surviving tag, draft, broken asset, integrity disagreement or uncertain access calls for recovery or retry. Embed the negative record in the resulting aggregate so its exact bytes can be authenticated later by the first 24-month publication's digest. A standalone local receipt has no independent authentication in this card. Offline calculation can use archived FDA bytes with live canonical discovery, and offline inspection can use a previously verified 24-month aggregate.

With the same FDA bytes and frozen forecasts, repeat R2's local-archive, omitted-option and wrong-pin calls while a first publication exists. Require all three to stay descriptive for H3 and verify that canonical discovery retains the first estimate and interval. Cover an unreadable archive, an incorrect canonical scope, a confirmed missing first publication, a surviving tag and integrity and transport failures. Check that a verified first 24-month aggregate survives later runs and FDA revisions.

## N2 · Publication witnesses

Collect all matching trusted issue witnesses and the release notes. Require at least one result pin in a publication record. Compare those pins to `results.sha256` and the exact result bytes. Compare every available source-manifest pin to the result's embedded digest and the exact manifest bytes. Verify supplied GitHub asset digests. A malformed pin or discrepancy gives an explicit invalid disposition and blocks formal H3 use. Recover from release notes when the issue write was interrupted. Exercise a release-only recovery, conflicting result and manifest witnesses, missing publication pins and altered assets.

## N3 · Custody after artifact expiry

Publish the first result JSON, result checksum, FDA source manifest, draws and report for each horizon under its deterministic tag `track-a-<horizon>m-<Zenodo record ID>-<freeze SHA-256>`. Put the result, manifest, draws and report digests in the release notes and scored issue. Verify the published assets before recording the issue. Retries recover the existing verified release and use its original bytes and date. Preserve any existing publication or tag when verification fails. Keep the 90-day artifact for captured FDA inputs and run provenance.

Remove the transient fixture directory and recover the first 24-month JSON, source manifest, draws and report from mocked publication responses. Check exact bytes, the missed-clear counts and upper bounds, and the retained H3 input. Verify that the publication step runs only on the default branch with canonical inputs and that a synthetic dispatch skips both production jobs.

Run the LOE-Bench unit suite, Worker tests and root pytest. Record commands, interpreter, counts, exit codes and the eight standing SACR exceptions if observed. Attempt a synthetic branch dispatch with a read-only fixture job and record its URL or the reason it is unavailable.
