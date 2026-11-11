# R1 failure attribution from retained audit and pinned validators

11 November 2026. Reuses the completed
[retained failure audit](../ptp-sacr-unstarted-continuation-20261111/retained-failure-audit.json).
No regeneration, output repair, new semantic adjudication or repeated corpus audit.
The audit reports all56 normal-return assessments reproduced exactly. This is
historical retained-output evidence, not a fresh replay of private outputs today.

Current source hashes for sacr_quote_profile.py, sacr_profile.py and sacr_views.py
match their pins in the continuation candidate-declaration.json. Thus the code
paths inspected here correspond to the audited validator/renderer revision.

| Observed category | Count | Attribution supported by code and retained audit |
|---|---:|---|
| Source quotation absent or ambiguous | 9 | resolve_quote rejects zero matches or more than one exact occurrence, including overlaps. The aggregate does not split absent from ambiguous; do not claim nine fabricated quotations. |
| Blocks not in source order | 1 | validate_profile rejects decreasing first-source positions. This is proposal ordering failure under the frozen contract, not evidence of a broken literal resolver. |
| Generation output limit | 3 | Incomplete generation was rejected. It does not establish what a longer completed response would have said. No refill/retry. |
| Condition raw text not source backed | 1 | validate_profile requires raw_text to occur inside the selected source snippets. Literal mismatch is established; semantic condition attachment is not thereby adjudicated. |

These14 rejected profiles plus7 other compact lexical flags produced21 distinct
required risk cases and exceeded the predeclared20-case ceiling. The remaining35
compact outputs being unflagged did not establish semantic fidelity. Two historical
interrupted attempts and42 never-started sample entries remain separate from the56
normal-return audit; their cost/coverage limitations are not erased.

## Renderer versus proposal

The old compact_view concatenates each relation_text with its attached raw_text
conditions. If a relation already contains the same literal condition, that
composition can repeat it. Its code also does not append context_items. These
are confirmed implementation properties, not a per-query attribution of every
observed lexical difference. The retained audit counts6 numeric-flag queries
(2 removed and40 added occurrences) and2 polarity-flag queries (1 removed and2
added occurrences); groups may overlap. It does not prove that all added numbers
were model hallucinations or all differences were caused by the renderer.

The prospective interval-union renderer addresses repeated references to the
same occurrence while preserving distinct occurrences. R3 separates deterministic
literal retrieval from model abstraction, role, type and attachment assertions.
Those assertions still need source fidelity screening and sentinel review;
exact extraction alone cannot prove correct semantic selection or attachment.

## Remaining uncertainty

Splitting the nine quotation failures into absent/ambiguous or attributing each
lexical difference would require a narrower analysis of retained private
input/output pairs. The existing audit already proves the frozen stop decision;
do not repeat it merely to produce another identical PASS count. Revisit specific
pairs only if a concrete design decision needs that additional distinction.
No source-semantic accuracy, retrieval loss or universal method failure follows
from these categories.
