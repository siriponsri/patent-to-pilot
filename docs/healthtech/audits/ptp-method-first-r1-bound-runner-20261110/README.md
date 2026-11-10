# R1 prospective dev baseline entry point

## Implemented
The new run_mtm_dev_bound.py entry point pins metadata/query manifests, original A14 identity, projection receipt and historical runner source. It validates dev query population, explicit missing-query ledger, strict projected corpus and full vector/model identity before dynamically importing the historical runner or allocating output. It then invokes the unchanged runner for main/U and main/X, with the existing passage vectors and a P-dev, T-dev or A-dev name. It exposes no test split or corpus re-encoding option.

The historical main view short-circuits the sets lookup, so the strict projected corpus has no construction-role field. Historical MaxP and torch.topk behavior, including possible cutoff tie selection limitations, remain unchanged for comparison. This is not a newly improved tie policy.

Query text is preserved verbatim; no prefix stripping, rewriting or tuning occurs. Its manifest has exact fields format, split, view, sha256, queries, missing_ids. Format is ptp-mtm-query-text-v1, split dev, view P/T/A. Payload queries.jsonl has exactly id/text rows. Available IDs and explicit missing IDs must partition the complete metadata cohort. Missing rankings must later score zero under that fixed cohort; the wrapper reports counts but does not score.

## Verification
61 targeted tests passed in 4.61 seconds; Ruff passed. Twelve new cases test query payload/schema/population/digest rejection, protected-manifest rejection before payload read, corrupt-vector rejection before historical runner import, and synthetic success/failure orchestration. These use a stand-in historical main: no actual model, GPU or ranking computation was run. The preflight itself runs on synthetic model/vector files.

The wrapper preserves preflight and outcome/failure receipts in an exclusive new output directory. Exceptions and interruptions are re-raised without embedding their text in receipts. Failed output cannot be overwritten or silently resumed. Invocation restores process arguments.

## Remaining operational gate
Inputs must be immutable and physically isolated by the curator; hashes alone are not isolation. The original-identity argument accepts the bare identity object extracted from the committed A14 report, not its surrounding provenance fields. Pin that extracted file independently. Receipt digests must come from curator-reviewed staging, never be generated and immediately accepted by the experimental runtime.

Actual corpus projection, dev query bundle preparation, mixed metadata separation, dev A03 counts and numerical baseline parity are NOT_RUN. The prospective wrapper is implemented but actual main-view parity is unproven; sensitivity views remain outside this entry point. A curator preparation command and complete operational procedure are the next package. A protocol entry must precede any real baseline parity job; no new method experiment is authorized by this code.
