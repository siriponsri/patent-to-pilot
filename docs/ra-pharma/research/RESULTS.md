# R1–R5 research receipt

**The R3 mechanism check passed. The eight IS1 cells and the R4 transfer study remain NOT_RUN.** The branch started at `2085e4be693cdb12cb60deb1e2a4139eea84063a`. The source-audited [eligibility inventory](INPUTS.md) and [prospective protocol](PROTOCOL.md) were published at `b5584589e32bc90b2b38cc43a97240b388342eff` before fixture scoring. The [independent release](PRE-RUN-REVIEW.md) covers the exact fixture freeze, one synthetic capture, and the canonical path.

## R3 observations

The diagnostic covers 11 authored cases. Seven had permitted support and four had known missing support. Six initially offered different read routes and five offered only one. The first read under the rank control supported 2/11. There were zero natural cases.

| Arm | Correct | Issued | Unsupported issued | Abstained | Wrong subject / wrong applicant product | Harmful stops | Passages read |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single, fixed rank | 2 | 2 | 0 | 9 | 0 / 0 | 4 | 12 |
| Fixed specialists | 2 | 2 | 0 | 9 | 0 / 0 | 4 | 12 |
| Learned specialists | 6 | 6 | 0 | 5 | 0 / 0 | 1 | 11 |
| Learned, role check off | 6 | 7 | 1 | 4 | 0 / 0 | 1 | 11 |
| Learned, all scope checks off | 6 | 10 | 4 | 1 | 2 / 2 | 1 | 11 |

All four net correct gains came from the four training-template echoes. Across the seven additional authored cases both fixed and learned specialists scored 2/7. Learned prioritization gained D09 by opening deeper evidence ahead of unrelated candidates and lost D07 by preferring a wrong-product attachment to an acceptable lower-priority source. Verification withheld its assertion, and the reader stopped before the admissible result. The single and fixed arms produced the same decisions and reading actions.

Both ablations followed the same read sequences as the learned arm on 11/11 cases. Role-only removal admitted D11's wrong-role result. Removing all scope checks also admitted D05 and D07 (wrong-product attribution) and D08 (stale edition). The six cases issued by both the learned and either ablation arm had zero unsupported assertions per arm. Fixed and learned shared one issued case, with zero unsupported assertions per arm. The unsupported rows emerged as additional issuances. In D05, the patent example used the same literal finding as the requested applicant result. Scope verification prevented the incorrect outgoing attribution. Edition checks compare authored metadata. The fixture does not estimate legal applicability, user benefit or model transfer.

The preset cap was two reads per case. Candidate scans were 20 per fixed arm and 18 per learned arm, with 1,267 and 1,148 passage bytes respectively. Identical policies reuse the same actual read traces within the harness. Across diagnostic policies this produced 23 distinct execution reads, 38 candidate inspections and 2,415 passage bytes. The arm-summed accounting is 57 reads, 94 inspections and 5,978 bytes. Training executed 20 policy-case evaluations with 20 reads, 40 inspections and 2,137 bytes. There was no candidate-list sort. Trace serialization sorts route names and JSON keys. Recorded wall time was about 0.62 ms for training and 23.56 ms for diagnostic capture, including input JSON reads and excluding the final output write of each timed block. The process timer produced zero at this resolution. Scoring, audit and whole-task CPU/energy are unmeasured. Fixture model tokens, paid API calls, paid bookings, GPU jobs and direct paid spend were zero. Research executor and reviewer harness costs are unmeasured.

## Capture and replay

| Artifact | SHA-256 |
|---|---|
| [Learned skills and training ledger](fixtures/original/skill.json) | `5b6cc5fc7ac963eee9c18b348ff5f4c54f3e24d88d533dde24fc7e0e2973cf44` |
| [Original traces](fixtures/original/traces.json) | `7fb2da744ec93d8e1040ee3eb6c570d1c90b4b5e84093f56c75a6465537aee57` |
| [Seal](fixtures/original/seal.json) | `1435a7dc3c374de697151e70ac36be0beeeb9605363eeaf1f48a2e85b62f34d2` |
| [Per-case and summary results](fixtures/original/summary.json) | `cfaf3de21dea95da578b54bdd1abfd0f376d06f36cb83bd6a8bfe93d3b424f46` |

Read-only reproduction from the Research checkout root under CPython 3.12.

```powershell
rtk proxy python scripts/research/ra_pharma/fixture_run.py verify docs/ra-pharma/research/fixtures/original
rtk proxy python -m pytest -o addopts= -q tests/ra_pharma_research/test_fixture_policy.py
```

The capture, score and verification commands exited 0. Verification checks the freeze, seals, named arms, matched action pairs, caps, provenance, costs and recomputed summary. It does not invoke the runtime reader. One canonical original was produced. No full evidence-contract schema validation was performed. The fixture implements a subset with arm-qualified trace IDs and uses `single` as a fixture-only agent identity.

[Code verification](QA.md) records the regression test, full-suite attempts and standing exception IDs.

## R4 and R5 disposition

No method is promoted. A natural transfer run requires a rights-cleared unexposed packet with independently keyed evidence, group-disjoint assignments by patent family, legal-edition family and letter template, a product-demo exclusion manifest, casewise unknowns, a numeric compute budget and an independent release bound to exact code, lock and output. The depth matrix separately requires an eligible complete ranked corpus and held query set with at least 1,000 unique candidates per query, exact rendering and prompt/model pins. A replacement corpus would start a fresh study. The eight slots, natural transfer, human adjudication and FTO accuracy stay NOT_RUN. The work did not access protected TEST. Product demo families were excluded from method selection.
