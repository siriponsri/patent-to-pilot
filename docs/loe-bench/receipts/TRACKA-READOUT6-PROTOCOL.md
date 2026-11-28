# TRACKA-READOUT6 publication protocol

29 November 2026. Executor branch `loe/TRACKA-READOUT6` starts at `58f10f15d32f1bc5ec97c81cf9f2daaebc3654c8` on `origin/research/loe-bench`. The unit of verification is a fictional readout or issue fixture. [Round 5 review](../reviews/EXTERNAL-REVIEW-R5.md) · [Capture and custody protocol](TRACKA-READOUT5-PROTOCOL.md).

## R5-A · Require the first 12-month result at promotion

Use the registered repository, version DOI, freeze digest and release manifest digest to discover the first 12-month result through the reader's existing issue, release, capture and attestation checks. Fresh scoring requires this verified result for the formal family. Before staging either a fresh or a restored 24-month result, apply one publication gate that requires successful rediscovery and matches the result SHA-256 and FDA source-manifest SHA-256 against the embedded H3 reference. Apply the same gate again immediately before the release promotion request. Leave an existing draft and its attestation intact. Record the reason and emit `publish=false` when continuity cannot be verified, including disagreement, missing original, an unavailable witness check or a mismatch in either digest.

Use the reviewer's two conflicting trusted issue pins to test fresh scoring, restored draft staging and the final promotion request. Also test a conflict appearing after staging. Remove the conflicting witness in the fixture and verify that a retry promotes the original signed bundle without recomputing or replacing its bytes. Change each of the two staged H3 digests independently and verify that publication is withheld.

## R5-B · Record both verified digests in maintainer issues

Use one documented issue body with the exact scoped `SCORED` marker, a `First result SHA-256` line and an `FDA source manifest SHA-256` line in the Python reader's pin syntax. The Worker requires both well-formed pins for dispatch completion. It logs the scoped incomplete issue and keeps that horizon due in the absence of a complete acknowledgement. The Python reader continues checking issue pins against the attested archive. Check the same example body in both suites and exercise marker-only and malformed pins in the Worker.

## Verification boundary

Run the LOE-Bench unittest suite, Worker npm tests and repository pytest. Record runtimes, commands, counts and exit codes. The standing pytest exception covers only the eight SACR r2/r3 supervisor budget cases. Dispatch `score-track-a.yml` with `synthetic=true` on the executor branch if available and verify that production jobs were skipped. Keep protected TEST, sealed and private artifacts closed. Keep the frozen forecasts and manifest, freeze tag, OSF and Zenodo records, and four primary scorer modules unchanged. This card uses no paid API or GPU.
