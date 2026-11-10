# R1 A14 passage-vector binding

Date: 10 November 2026 (Bangkok). Initial base: `f3f3a42b3b78097a0b23f197e2efc695b31da277`.
Status: IMPLEMENTED_FIXTURE_VERIFIED; real CPU inspection PLANNED at this launch checkpoint.

## Attempt 1: invalid launcher; retained

Archive `bfc12bb7cce2af4387fac9d82680a3c4d12a3200` was deployed. Launcher PID 2418646 terminated before Python started: the committed shell script had CRLF bytes, causing Bash `set` and path failures. No status/inspection report was created. `logs/nohup.out` and the archived code remain in the original job directory; no result is inferred. This is a defective infrastructure attempt, not a negative scientific result.

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
