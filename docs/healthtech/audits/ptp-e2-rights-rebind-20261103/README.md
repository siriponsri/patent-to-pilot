# Patent-to-Pilot E2 rights-cleared payload rebind

Date: 3 November 2026 (Asia/Bangkok)

This additive checkpoint continues the existing Patent-to-Pilot goal. It
resolves the payload-transfer blocker for the small FDA factual canary without
creating a goal, changing the E2 journal, reading a credential, or dispatching
a provider request.

## Input and projection

The source was the existing private current pack:

- Parent pack hash: `918f615210546b65111cbc683181dc43886ace2267f16c19d62c31175ea6607b`.
- Input file SHA-256: `b132f0409b24262cff09e6a162a7c3d3ec30858bc90a7ba4b9836ce303256f36`.
- Three cases: MitraClip, Tendyne, and TriClip.
- FDA source rights: `ALLOWED_WITH_ATTRIBUTION` for structured `pma_number`,
  `trade_name`, and `applicant` fields under the openFDA terms reference.

The projection removed patent/disclosure sources, generic/GMDN fields, raw
payloads, evaluator labels, and other restricted or unreviewed content. It
retained source IDs, source revisions, source hashes, locators, and exact
message provenance. A `remote_transfer_review` was added per case and bound to
the exact message hash.

## Result

The prepared private pack has:

- Prepared pack hash: `e146ab85db3792c3028e9becb0d71ea645a0cd0cfe426a9233622496e7aef489`.
- Manifest hash: `b9b0d1fea5c8d7c6e34801053034526103fca77d5c6b992fb29a008b64f57d28`.
- `3` cases and `9` evidence rows.
- `source_backed_transfer_review=PASS`.
- Rights decision: `ALLOWED_WITH_ATTRIBUTION`.

The API generation runner dry-run completed with
`DRY_RUN_NOT_EXECUTED`, exit code `0`, and zero provider calls/cost. Its
manifest and per-case payload hashes match the prepared receipt. The
preparation script was replayed with the same captured timestamp; prepared
pack, manifest, exact-message, and payload hashes all matched the first run.

The exact message hashes are the same as the existing private local-canary
contract. This proves input/message equivalence for the canary boundary, not a
new local inference run and not a paid local-versus-API result.

## Paid and research boundaries

The canonical E2 journal remains the authority. No reservation, attempt,
retry, provider call, cost, budget reset, or time-window reset occurred. The
previous current-credit observation still lacks scoped account credit and
remaining key-limit evidence, so paid dispatch remains blocked before
reservation. Route pricing must be refreshed inside the runner's 300-second
admission window after credit evidence exists.

This FDA-only canary is a smoke test of the transfer/generation path. It does
not replace the device-patent study, establish semantic retrieval quality,
prove adaptive superiority, or support external business validation.

The reproducible preparation script is
`docs/healthtech/audits/ptp-resume-e2-current-r2-20261103/prepare_fda_canary_from_current_pack.py`.
Private pack, exact messages, preparation receipts, and dry-run output remain
under `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/` and are not
staged in Git.
