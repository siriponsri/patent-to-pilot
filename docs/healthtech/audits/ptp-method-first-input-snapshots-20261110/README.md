# Allowed source and manifest byte snapshots

Checkpoint 2026-11-10 09:29:38 Bangkok; base 7ab3719509906480df13989fdfc888de45af19c6. Preparatory engineering only.

bind_input_snapshots now joins the execution declaration with caller-supplied immutable
bytes for all nine manifest identities and the allowed dev query payload. Every manifest
byte hash must match its declared pin. The query manifest and payload are parsed with the
existing strict dev schema; the ordered cohort and each exact UTF-8 source hash must match.
Missing input is retained as None at its declared position. Only MTM primary P is accepted;
this is not a redefinition of DAPFAM inputs. Return values are immutable ordered tuples.

The MTM query loader previously hashed files and then reopened them to decode. It now
checks and parses the same in-memory byte snapshots, reading each file once. The manifest
is checked for dev eligibility before payload read. This removes the hash/decode reread
gap; it does not provide filesystem isolation or authenticate an untrusted supplied pin.

Evidence: initially66 focused tests PASS; after explicit missing-cohort test, all17 SACR
files plus MTM bound-runner tests:239 PASS. Ruff on three changed Python files PASS.
Fixtures cover exact Unicode, changed manifest/payload/source, false missing input,
nonprimary and protected splits, foreign queries, mutable payloads, missing-query order,
single-read loader behavior and rejection before protected payload access. A test-file
lookup under test_mtm_queries.py was absent; existing tests reside in test_mtm_bound_runner.py.

Other manifest contents remain opaque. Matching their bytes does not verify referenced
weights/index arrays or grant fidelity-policy adoption. Existing vector/model preflight
must still attest those referenced artifacts before actual use. The new binding function
does not itself launch callbacks or require callers to use returned snapshots; typed
controller integration remains necessary. A caller must supply only permitted isolated
inputs; this code never discovers or opens mixed label sources.

No actual data/model/GPU jobs or experiments. R1 actual curator isolation/A03/parity,
generation compatibility and fidelity remain open. Next integrate bound immutable sources
into typed stage scheduling, retaining prior failures and current authorization boundaries.
