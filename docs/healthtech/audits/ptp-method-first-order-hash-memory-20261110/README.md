# Index memory review and bounded order hashing

No corpus, model, labels or remote processes were opened. Dimensions below come
from the existing A14 vector-identity receipt, not a new index load. Prior turn
made a concrete readiness/evidence refresh; protocol question remains pending.

## Existing allocation implications

For the recorded 1553678 passages,1024 float32 dimensions and899838 families:

| Item | Bytes | Interpretation |
| --- | ---: | --- |
| One vector array | 6363865088 | 5.9268 GiB logical array payload |
| Input plus detached copy | 12727730176 | 11.8536 GiB payload if both resident; excludes all overhead |
| One int64 owner array | 12429424 | dtype assumption, not measured deployment allocation |
| Three-view MaxP accumulator | 10798056 | one acquisition arm at a time |
| 16384-row float32 geometry block | 67108864 | view size; norm operations can allocate temporary arrays |

The recorded NPY file has128 additional bytes relative to the raw vector payload.
These are allocation calculations, not RSS, available host memory, GPU usage or
permission to run. Memory-mapped input does not make the detached copy disappear.
ID strings/containers, uniqueness checks, ownership arrays, score buffers, Python,
model weights and library workspaces are additional. Full-index copy/live memory
acceptance remains open. Borrowing caller arrays would break detached-snapshot
behavior and has not been substituted silently.

## Repair and measured trade-off

`passage_order_digest` previously built every (passage,family) tuple, a full JSON
string and encoded bytes. It now serializes at most4096 rows at a time, preserving
the exact compact UTF-8 JSON brackets, separators, escaping, order and digest.
Owner validation remains; source strings are not normalized. Temporary serialized
storage depends on the longest4096 identifiers, not a guaranteed byte cap for
arbitrarily long strings. Existing caller input containers are not removed.

Authored100000-ID observation, inputs allocated before Python tracemalloc:

| Variant | Peak traced bytes | Wall seconds |
| --- | ---: | ---: |
| Legacy (second observation) | 15379328 | 0.5474234 |
| Final4096-row batches | 631639 | 0.6546061 |

Both SHA256 values are identical, recorded in `observation-batched.json`. Final
`measure_authored.py` reproduces this comparison. The first, superseded per-row
streaming observation remains in `observation.json`:100421 traced bytes but1.7968571s
versus legacy0.5848519s. That slowdown motivated bounded batching; it is not hidden.
The final single observation still shows about20% extra time under tracing. Neither
measurement is a stable throughput benchmark or proof of corpus-scale performance.

Validation:12 new cases cover legacy hash equivalence, Unicode/control-character
escaping, empty inputs, invalid owners, exact4096/8192 boundaries and partial batches.
Initial per-row suite426 passed; after batching/boundary changes the final related
suite429 passed. Ruff passed three changed Python files. Ranking arithmetic and
identity manifest formats are unchanged. No actual ranking parity is established.

Next resource decision requires an actual isolated host budget and a chosen
immutable index ownership strategy; do not infer safety from these lower bounds.
Owner family-rejection decision and curator/environment remain pending. R1 actual
checks/generation/fidelity/R3-R6 remain incomplete; Goal ACTIVE.
