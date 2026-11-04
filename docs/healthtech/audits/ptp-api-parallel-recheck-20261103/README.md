# API parallel-path recheck — 2026-11-03

This is a fail-closed recheck for the API branch of the existing
Patent-to-Pilot goal. It does not represent a paid attempt.

The current-head rights-cleared pack was then located at the exact owner-private
source directory recorded by the prior pack receipt. A fresh dry-run using that
pack passed the current route, source-transfer, message, and output-contract
checks for all three cases:

- pack hash: `e033456a1f9fe53a3bf8b2c4d1e6c07e1e6727796620f94f35f1ad505499526e`
- pack file hash: `0b2bef9fcf8c3eff6106a1786885e4407ea4b8c9e628397ab8e52a392204ced9`
- manifest hash: `c298b1027e31a270c7db8956cf36a000c854f5c7374e8bb75241881f84729843`
- cases: `HT-DEV-MITRACLIP`, `HT-DEV-TENDYNE`, `HT-DEV-TRICLIP`
- rights: `ALLOWED_WITH_ATTRIBUTION`
- provider calls and paid cost: `0` and `USD0.00`

The Desktop local artifact store also exposed an older evidence pack whose claimed pack
hash is `d2a91ce2471461b3e5ed5468e15926e7c2359cb21368323a168f9c8fffbb5932`.
The current-head paired contract requires pack hash
`e033456a1f9fe53a3bf8b2c4d1e6c07e1e6727796620f94f35f1ad505499526e`. The API
runner rejected the stale pack during dry-run validation with
`GenerationPayloadError`; it did not write a receipt and did not contact the
provider.

That stale-copy failure is retained as a workspace-availability finding only.
It is not combined with the current-head dry-run receipt and does not weaken
the current-head result above.

The paid branch remains blocked before reservation because the canonical R1
journal/registry and current scoped credit snapshot are still unavailable.
The historical visible debit of `USD0.0001464` remains unchanged.
