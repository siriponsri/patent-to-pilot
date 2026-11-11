# R5 bounded execution evidence

## R5 bounded-run closeout, 11 November 2026

The approved conditional run has reached its stopping gates. SACR candidate 1 and the Graph screening configuration did not qualify for native comparison. Consequently native SACR5/100, pilot20, full dev474 and conditional MTM are NOT_RUN. There is no new retrieval effect estimate, not a measured zero or negative effect. Both protected tests remain closed.

| Stage | Observed result | Time and resources |
|---|---|---|
| SACR synthetic candidate1 | Three EOS calls; critic envelope rejected; separately observed source-coverage and unit omissions; candidate closed | 170.946s whole wall; 2,745 input / 1,442 output tokens; peak allocated GPU17,323,849,216bytes |
| Graph fixed-source attachment | 100 original family texts attached privately; no re-extraction | 2.245s CPU wall |
| Graph exact-critic preflight | Four authored real-tokenizer cases passed; software evidence only | 18.327s CPU wall |
| Graph fixed source100 + alias100 screening | Stopped at21 risk units after21 completed source units; 179 units not screened | 2612.905s whole wall; 21 observed model calls; 63064 input / 22554 output tokens; peak allocated GPU26555098624bytes |
| Human review / accepted graph edges | 0 cards issued / 0 accepted edges; cap gate prevents card release | No human judgments requested |
| Native comparative evaluation | NOT_RUN because prerequisites failed | No new ranking scores or significance tests |

Graph risk reasons: {"ESCALATE": 12, "MALFORMED_OR_UNGROUNDED_CRITIC": 9}. Invalid or ungrounded critic responses are failures of the screening evidence, not validated semantic findings. The remaining escalations are automated risk judgments, not independent expert review. Source-first processing and the prospective risk21 stop left the alias stratum untested; neither a corpus-wide error rate nor alias incompatibility can be estimated from this stopped prefix. No output was repaired or regenerated, and no threshold was changed after observing results.

The SACR profile omitted mechanism/constraint coverage and quantity units independently of the critic's incorrect finding-key names. Fixing that envelope alone would not establish fidelity; no additional candidate was used to reroll the failed profile. Two prospective synthetic candidate slots remain unused. This closes the tested candidate, not the general research hypothesis.

Cumulative charged GPU time is 12309.614s; cumulative fidelity time is 12030.727s. Remaining allowances are 188.581h GPU and 60.658h fidelity. The 57,600-second Graph reservation was released after charging actual whole supervisor time once. Known model calls are a lower bound of84; historical unknown attempts remain retained. Caps stay GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU. Remaining allowance does not reopen failed gates. No paid API, training, corpus re-encoding, Neo4j write or permission change occurred.

Canonical evidence: [R5 execution audit](README.md), [Graph terminal aggregate](graph-screen-result/aggregate.json), and [cumulative ledger](../ptp-mtm-dapfam-resume-20261110/resource-ledger.json). Raw source/model records remain private. Engineering checks include 35/35 tokenizer/callback/EOS cases, the exact-source admission case, and 61 final integrated local tests; these do not certify semantic quality.

The measured native baseline and Paper53-style descriptive exposure remain the only retrieval results. Direct replication of published DAPFAM scores remains NOT_ESTABLISHED because cohort, model and protocol differ. Paired effects, wins/losses, rescue/displacement and uncertainty analyses remain NOT_RUN. The manuscript is an evidence-backed research draft, not submission-ready. Any later methodological revision requires a new prospective specification; protected-test evaluation and submission remain separate decisions.

Earlier planning and closeout records elsewhere are historical. Their old resource figures, permissions and running-state statements do not supersede this current closeout.


Owner approval and exact declarations remain in this directory. `publication-review.json` describes the earlier screened checkpoint be0f342; it is not a manifest of this later closeout. Runtime source hashes bind exact dispatched bytes and retained transport archives.
