# Bounded vector hashing — 10 November 2026

Engineering repair only; SACR remains untested. No corpus, labels, model, GPU or remote job accessed.

## Change and compatibility

`vector_digest` now hashes the existing JSON shape/newline header followed by C-order little-endian float32 bytes in chunks of at most 262144 elements (1 MiB). Buffered NumPy iteration also bounds conversion for noncontiguous and differently typed inputs. The canonical digest format is unchanged; no normalization is introduced.

Fourteen regression cases compare the former implementation for contiguous, Fortran, transposed, negative-stride, big-endian, float64, integer, special float, empty and scalar arrays. Instrumented hashing verifies bounded updates and total byte counts on larger layouts. All 333 SACR and MTM-bound-runner tests passed in 9.53 seconds; Ruff passed both changed Python files.

## Local authored memory observation

Input: `np.ones((16384,1024), dtype=np.float32)`, allocated before tracing, 67108864 bytes. Sequential calls measured with Python `tracemalloc` and `time.perf_counter`; no process-RSS or deployment claim.

| Implementation | Peak traced bytes | Wall seconds |
| --- | ---: | ---: |
| Former concatenated hashing | 134217911 | 0.11171040000044741 |
| Streamed hashing | 1049578 | 0.0837576000194531 |

Both digests: `9e3b1aaae0eb0abe8d112d1e5408ddbe05a03743c4377db26191010f669623c2`.

The first observation command failed before measurement because the standalone Python invocation lacked the `src` import path. Adding that path resolved the command setup; no research attempt or generated output was involved. Timing is a single local observation, not a speed benchmark.

## Remaining gates

`BoundCPUIndex` still copies its entire matrix. This repair removes hash-byte copies only; full-index memory, live caps and actual runtime acceptance remain open. R1 isolation/A03/native and baseline parity are NOT_RUN, curator/environment unanswered. Generation/fidelity failures remain unresolved; proposed generated-family rejection is NOT_ADOPTED. R3/R4 absent, R5 not authorized, R6 incomplete. No model/grammar retry was made.

Next: bound generation termination receipts before view-failure policy integration; inspect independent index-copy resource constraints; obtain curator/R1 and actual anchor provenance before research runs.
