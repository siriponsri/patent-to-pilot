# Source/profile-bound component compilation and vector row receipts
research/sacr_components.py validates the canonical profile against exact allowed
source/query/view identity before compiling relation-first, explicit-condition rows.
Raw condition wording is retained; uncertain attachments are counted but excluded
from conjunction. Condition-free blocks remain. Unique row IDs bind block/role/item;
text hashes and complete profile/source identities enter a canonical plan digest.
Source/profile inputs are not mutated. No private generated texts are committed.

Failed/empty profiles emit ANCHOR_FALLBACK with no rows. Existing normalization/
abstraction review flags emit REVIEW_REQUIRED with no rows; these are not silently
treated as faithful or dropped from a future cohort. Unflagged prepared plans still
carry fidelity_review REQUIRED and semantic_status unknown. This is mechanical
preparation, not adoption of the proposed semantic policy or human approval.

Embedding binding requires the expected plan digest, exact ordered row IDs,
a pinned encoder identity-manifest digest and canonical float32 shape/byte hash.
The encoder identity manifest must cover weights/tokenizer/prefix/settings; a model
name alone is insufficient. Unit/finite/dimension checks reject malformed vectors.
Detached read-only arrays feed the existing factorial kernel. No encoding,
normalization, row sorting or output repair occurs here.

Limit: receipt consistency does not prove encoder execution or semantic correctness.
A caller could supply a false receipt; the actual audited encoder/immutable-index
preflight remains required. Component-vector digest is canonical shape + LF +
little-endian float32 bytes, deliberately distinct from the hash of a .npy file.
The compiler/binder does not load a model or authorize benchmark access.

43 targeted tests pass:13 components,19 profile,11 factorial. Coverage includes raw
wording/order, deterministic plans, uncertain/condition-free behavior, failed/flagged
plans, changed text, swapped IDs/vectors, different encoder identities, invalid
norm/nonfinite vectors, detached arrays and compiler-to-factorial integration.
Ruff passed for two new files. No actual text encoding, data/model/GPU run.

Next complete per-query failure/fallback and cost-ledger orchestration, then connect
the actual encoder only behind source/identity/isolation gates. Real R1 curator,
eligibility/parity; viable generation; fidelity observations; R3/R4 and R5 freeze
remain open. No engineering checks establish SACR effectiveness or Goal completion.
