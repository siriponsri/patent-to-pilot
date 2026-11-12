# Graph deterministic extractor v3: design and gate (frozen before any v3 output)

Owner decision 12 Nov 2026: "New extractor round". The round is CPU-only and deterministic; LLM extraction over the corpus stays prohibited.

**Why a new round.** The v2 census found usable relation keys for only 13 of 474 dev queries (2.7%) and 1 of the pilot-20 (`takeover-20261112/graph-census/graph-census-result.json`). The v2 result is retained as a negative.

## Design (`sg_relations_v3.py`, stdlib only)

**Fields.**
- Corpus: title, abstract and claims.
- Queries: the pinned TA text (title plus abstract), passed as the abstract field.
- Units are split at newline, semicolon, and sentence punctuation followed by an uppercase letter, as in v2.

**Verb lexicon.**
- 120 fixed technical action lemmas, chosen without looking at any v3 output.
- Surface forms are generated deterministically: lemma, -s/-es, -ing (with e-drop and a fixed list of consonant doublings).

**Patterns** (case-insensitive, all inside a unit):
1. Cue: `configured|adapted|operable|arranged|designed|capable|used` + `to|for|of` + verb form.
2. Purpose: `for` + verb-ing (e.g. "method for producing X").
3. Infinitive: `to` + verb lemma.
4. Finite: verb + -s/-es (e.g. "the controller stops delivery").

**Operand.**
- After the verb, skip determiners (a, an, the, said, each, one or more).
- Take up to 3 word tokens, stopping at a stopword, punctuation or digit-unit boundary.
- The head is the last token, lowercased, with one trailing plural "s" removed when longer than 3 characters and not ending in "ss".

**Alias key and records.**
- The alias key is `sha256(lemma|head)`. It is lexical only: no semantic equivalence and no compatibility claim.
- At most 16 records per family.
- The record format matches v2: relation_id, family_id, field, spans, alias_key, alias_descriptor, and `semantic_status=UNSCREENED_NO_EDGES_ALLOWED`.

The hub cap stays 100 families per key. Hub keys are skipped by S and G, and are available to S-deep only, as in the frozen Graph protocol.

## Feasibility gate (evaluated once on the v3 census, no qrels and no scores)

- **G1.** At least 50% of the 474 dev queries have at least one usable key: a key with postings and degree ≤ 100.
- **G2.** At least 10 of the frozen pilot-20 queries have structure.
- **G3.** At least 1,000 keys are shared by 2 or more corpus families. Without this, bridges are negligible.

If G1 to G3 all pass, the Graph track proceeds under GRAPH-AUTOMATIC-ROUND-20261112: screening scope and caps, journal stage qualification, screening, then pilot.

If any gate fails, Graph is reported as a negative feasibility arm. No further extractor round follows unless the owner explicitly authorizes one.

The gate thresholds and the lexicon are not changed after the v3 census.

## Resources

One CPU-only job: corpus materialization of v3 postings plus the query census. Bound: worker RLIMIT_CPU 270 s plus controller 30 s, so 300 s is booked with no refund; wall stop 290 s; CPU 1; 1,536 MiB; network off; read-only inputs; no qrels and no model. Postings are kept private remotely; only aggregates are published.
