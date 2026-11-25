# Alternative-evidence packet handoff

**Prepared for independent audit.** The Option A scope is data preparation. Scoring and policy execution on this packet are `NOT_RUN`. The packet author worked from `2dff214f` in a separate worktree and owned this directory. The parent owns the prototype, scorer, protocol and shared planning records.

| Lane | Families | Sources and revisions | Units | Answerable | Finite unanswerable | Unadjudicated | Changing pairs | Invariant pairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `th` | 8 | 11 | 40 | 22 | 2 | 0 | 6 | 5 |
| `en` | 4 | 5 | 20 | 12 | 1 | 0 | 3 | 3 |
| `natural-th` | 1 | 1 | 6 | 3 | 0 | 1 | 1 | 0 |
| `natural-en` | 1 | 4 | 4 | 3 | 0 | 1 | 0 | 1 |

Four Thai changing pairs and two English changing pairs keep the literal answer while requiring a different witness. Among Thai changing pairs with exactly one complete seeded chain, the complete side comes first in three and second in three. The two analogous English pairs use opposite orders. The remaining English pair and the Thai natural changing pair both require a missing witness on each side. These are design counts from the exposed seeds and authored assignments.

Runtime consumers may receive only the runtime artifact and the approved tools for opening units. `sources[].text` exists for storage and exact evidence verification. The runner must withhold whole source text and the text, facts and answer of unopened units from the policy interface. Keep `labels.json` and this authorship and audit folder out of policy inputs. Pass test fixtures to engineering while prospective packet labels remain reserved for the independent auditor and evaluator.

## Verification and audit queue

Run `python docs/evidence-scope/alternative-evidence/packet/verify_packet.py` from the repository root. It verifies the pinned LF files, closed schemas, literal source offsets and UTF-8 hashes, references, acyclic family-local graphs, case and pair membership, and label consistency with the authored graph. It checks that a labeled hidden witness has a reference path from the shared seed. It records only structural inventory. It performs no retrieval, ranking, policy or scoring. In particular, the verifier does not measure BM25 reachability.

The packet verifier and Git whitespace check passed. Repository-wide `python -m pytest` started before commit and showed a failing item in partial progress output. The interrupted tool session left the final exit status and failure identity unverified. The packet verifier was rerun successfully after the interruption.

The independent auditor should re-derive the answer and mandatory witness sets from runtime text before comparing them with labels. Check Thai phrasing with a Thai-domain reader where available, the sibling parent links, cross-edition incorporation, neutral questions, equivalent chains, finite combinations, and source rights and text locators for the two natural families. Confirm that author and reviewer roles remain separate. The natural examples are limited statutory excerpt diagnostics and require separate denominators. Both natural unknown cases lack an exhaustive adjudication.

The packet auditor should confirm that the parent prototype's development cohort has no lineage or content overlap. That code and its development data were outside this worktree. The committed baseline comparison and report limits are in the manifest and within the verifier's baseline check.
