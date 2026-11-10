# Preparatory R2 profile validation and fidelity form
Strict sacr-profile-v0 validator implemented with source hash/query/input-view binding, exact Unicode offsets, schema/duplicate-ID checks, raw source-backed roles/conditions/units, source-order blocks, eight-block/eight-condition caps and explicit versus uncertain condition counts. Changed normalization and context abstraction are flagged for review; every output retains semantic_status unknown and fidelity_review REQUIRED.

34 combined tests passed in 0.57s (19 profile cases and 15 selector cases); Ruff passed. Fixtures include invalid offsets, Boolean offsets, hidden fields/labels, invented raw roles/units, Unicode text, normalized inventions requiring review, uncertain attachments, failed/empty profiles and reordered blocks. No real text, model or retrieval was used.

Blank developer audit form is docs/healthtech/research/SACR_FIDELITY_AUDIT_FORM_20261110_EN.md. Its existence is not a completed audit. Generated-view acceptance, prompt/budgets, actual fidelity observations and pilot integration remain incomplete. Structural PASS is never semantic acceptance.

An initial read-only PowerShell command had nested quoting failure before reading files; corrected Python read and standalone rg succeeded. No mutation resulted from the failed read.

Next implement generated-view validation/prompt contract and draft parity protocol. Curator/environment question remains pending; actual R1 data integrity and all experiments remain gated.
