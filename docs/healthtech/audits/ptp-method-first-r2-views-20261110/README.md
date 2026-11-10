# SACR view parsing, compact construction and screening
Implemented strict complete-JSON view parsing with caller-declared byte cap; duplicate JSON keys, extra fields, over-cap counts, empty/nontext or truncated responses fail. Selective null and generic zero/one views are recorded without automatic retry.

Compact serialization uses source-order relations and explicitly attached raw conditions ordered by source position. Failed/empty profiles require anchor fallback; normalization review flags, uncertain attachment or unresolved items abstain from compact serialization.

The screening component compares literal protected phrases, numeric and English polarity inventories and length; new vocabulary is flagged for review. It retains immutable anchor, at most two passing proposals and duplicate/rejected/review outcomes. It recomputes screens instead of trusting caller-supplied success receipts. This is a component, not a complete semantic acceptance rule or full SACR implementation.

54 tests passed in 0.76s, Ruff passed (15 view cases plus existing 39). A deliberate falsification fixture shows "A pushes B" versus "B pushes A" passes lexical checks with semantic_status unknown. Ordinary synonyms and invented mechanisms both raise new-vocabulary review; it is not a trained mechanism detector.

No source benchmark, model generation or retrieval run. The current conservative screen can reject useful abstractions and miss same-vocabulary semantic changes. Do not relabel surviving extractive/anchor-only results as a completed selective-abstraction study. Before experiments resolve the acceptance/review policy in a declared protocol and conduct developer fidelity inspection, not post-score hand repair. Actual R1 isolation/parity still pending curator/environment handoff.

Next inspect existing generation path and complete response/profile orchestration, then synthetic model smoke only after declared configuration/weight/resource checks. Actual data experiments remain gated.
