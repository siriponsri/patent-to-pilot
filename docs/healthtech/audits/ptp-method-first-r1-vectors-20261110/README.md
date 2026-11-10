# R1 A14 passage-vector binding

Date: 10 November 2026 (Bangkok). Initial base: `f3f3a42b3b78097a0b23f197e2efc695b31da277`.
Status: REAL_IDENTITY_OBSERVED_HISTORICAL_RECEIPTS_MATCHED; prospective runner integration and ranking parity remain open.

## Actual inspection result

Corrected archive `1df23a5f81cef4b7cc6eb6045e66c0106ac52627`, launcher PID 2427095 / Python PID 2427097, ran from 00:14:21Z to 00:16:20Z on 10 November 2026 (07:14:21–07:16:20 Bangkok), exit 0. The terminal status log and missing child process confirm completion. No job remains from this package.

[vector-identity.json](vector-identity.json) contains the observed binding and explicit provenance limits:

- 899,838 families; 1,553,678 passages; float32 matrix shape 1,553,678 × 1,024, 6,363,865,216 bytes; finite-value check passed.
- Fresh corpus hash `4d29bd8136e2a838e9a12e0907e0951dc029ca6f9b22ba7eae1da21bb5c618a6` and vector hash `8bb35abadf1df98c916eb495997214a225f280fbc2ae4979ca09b9d6ec56330b` match the historical dev receipts.
- Fresh ordered-family and ordered-passage/owner hashes are recorded, along with current model, tokenizer, encoder and preprocessing source hashes.
- The original receipts did not attest original tokenizer files or passage-order hashes. This new observation cannot retroactively supply that attestation. Real ranking parity remains NOT_RUN; no automatic re-encoding is justified by this inspection.

The scoped LF attribute fixed the archive export. The original committed launcher blob had zero CR bytes; the first exported archive had CRLF. Version 2 was explicitly checked in the produced archive and with `bash -n` before launch. Both the failed and successful remote attempt directories remain intact. No shared source/data file was modified.

## Attempt 1: invalid launcher; retained

Archive `bfc12bb7cce2af4387fac9d82680a3c4d12a3200` was deployed. Launcher PID 2418646 terminated before Python started: the exported archive had CRLF bytes (the committed blob itself has LF), causing Bash `set` and path failures. No status/inspection report was created. `logs/nohup.out` and the archived code remain in the original job directory; no result is inferred. This is a defective infrastructure attempt, not a negative scientific result.

Correction: scoped `.gitattributes` enforces LF for this launcher only; no global Git/hook configuration changes. The corrected version uses a distinct `r1-vector-identity-20261110-v2` directory and a new pushed archive. It is a versioned engineering repair with the first attempt preserved, not an overwrite/retry of an experiment. Before launch, verify the archived launcher has no CR bytes and passes Bash syntax checking. All input identities and inspection settings are unchanged.

`research/vector_identity.py` hashes the corpus bytes, ordered family IDs, ordered passage text and ownership (including global/local indices), the actual passage-builder source, encoder source, model weights/configuration/tokenizer files and the entire vector file. It verifies float32 shape and finite values in bounded chunks without loading a model. Hash serialization uses length-prefixed canonical JSON; no patent text is emitted. A trusted expected snapshot comparison rejects all identity changes rather than accepting an equal matrix shape.

`inspect_mtm_vector_identity.py` also checks the original T-dev encoding and P-dev reuse receipts against current corpus/model/vector hashes and counts. A matching chain is historical evidence, not proof of the original tokenizer or original passage order, which were not attested in those receipts. The report retains those gaps and marks re-encoding/ranking parity NOT_RUN. A freshly observed manifest cannot certify its own historical provenance.

## Verification before real inspection

- Targeted pytest across vector identity and MTM boundary/eligibility/pipeline/methods: 56 passed in 4.17 s, exit 0.
- Changed-file Ruff passed, exit 0.
- Adversarial tests reject same-shape corpus reorder, vector reorder, altered text, tokenizer/weights/encoder changes; wrong dtype/shape, NaN and duplicate families. Historical receipt mismatch tests also pass.
- Remote model file inventory confirmed required files exist. GPU process query returned no compute processes; the planned job is CPU-only in any case.
- No label/query/ranking files are inputs. The existing two dev receipts contain hashes/counts, not labels.

## Bounded CPU inspection

Run directory: `mtm-20261107/r1-vector-identity-20261110` under the established dr-train job root. Deploy only `git archive <pushed-sha>` into its new `code` directory. Launch `run_cpu.sh` with `setsid nohup`, one job, no retries. Write PID to `logs/pid`, status to `logs/status.log`, stdout/error to `logs/inspection.log`, and aggregate hashes to `vector-identity.json`.

Monitor the same PID and status log until a terminal exit. An observation timeout does not authorize restart. This is a read-only inspection of existing corpus/vector/model files, with new receipts only. No paid API, BigQuery, GPU generation, training, corpus encoding or test-label access is involved. No output overwrite is permitted.

Next: record the actual result, preserve gaps honestly, then implement native DAPFAM parity and prospective runtime/ranking-parity integration. Trusted staging remains necessary before real dev label-dependent checks.

## Independent source inspection while the CPU job ran

Inspected the [pinned native DAPFAM loader](https://github.com/embeddings-benchmark/mteb/blob/9242b36a1d400fc8c3af573e6a6e0705c0b96e3d/mteb/tasks/retrieval/eng/dapfam_patent_retrieval.py): domain selection filters positive qrels, leaving the corpus unchanged. Queries without positives in a selected partition are omitted from that qrel mapping. Generic evaluator denominator behavior and parity fixtures remain to be checked. No dataset labels were downloaded for this source inspection.
