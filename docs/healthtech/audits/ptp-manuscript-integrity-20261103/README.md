# Manuscript integrity recheck — 2026-11-03

Status: `PASS_MANUSCRIPT_LINK_AND_CLAIM_BOUNDARY_AUDIT`.

This documentation-only audit rechecks the English manuscript after binding
the current O1 and component-rebind receipts. It verifies local links and the
existing claim boundaries; it does not run a scientific experiment or claim
WPI submission readiness.

## Verification

- Manuscript local links: `18 checked, 0 missing`.
- Computational protocol local links: `0 checked, 0 missing`.
- Manuscript SHA-256: `1149e67baa411f74a0c71c4d77fa9bdf2db4d5fabce8fbae338864da01325441`.
- Manuscript size: `35,259` bytes.
- Claim boundaries retained: realized-budget frontier is descriptive; three
  real-device cases are engineering evidence; business, legal, clinical, and
  user-validation claims remain unsupported.

The manuscript now links the current O1 engineering receipt and the
component-results provenance rebind. WPI-specific author instructions remain
subject to owner recheck because the official route was previously inaccessible
with HTTP 403.

Machine-readable details are in [`verification.json`](verification.json).
