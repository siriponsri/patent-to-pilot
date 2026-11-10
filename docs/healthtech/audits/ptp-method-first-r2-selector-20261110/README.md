# Preparatory R2: SACR specification and selector arithmetic
Draft specification records input boundaries, profile/view contract, precise selector math, fidelity sample/rubric, matched factorial controls and unresolved run-freeze items. It follows supplied handoff §§8–10, 12–13, Appendices B/C. No new external literature claim was made.

Selector module implements average-rank normalization, same-passage local component mean/min then passage/block maxima, and fixed-depth union selection. No extractor, encoder, index, labels or retrieval runner is invoked. All semantic statuses remain unknown.

15 synthetic tests passed in 0.45s; changed-file Ruff passed. Hand-computable complementary passages produce 0.25, not the invalid cross-passage conjunction 1.0; true same-passage 0.2 cosines produce 0.6. Tests cover degeneracies, ties, permutations, condition-free and partial-block behavior, invalid matrices/scores and duplicate IDs.

R1 remains incomplete. This is preparatory work, not R2 completion, pilot declaration, expert fidelity validation or positive retrieval evidence. Actual curator/operator/environment question remains pending from prior turn; no response assumed. Next strict profile validation and audit form, draft parity protocol, then actual integrity/experiment work only after operational gates.
