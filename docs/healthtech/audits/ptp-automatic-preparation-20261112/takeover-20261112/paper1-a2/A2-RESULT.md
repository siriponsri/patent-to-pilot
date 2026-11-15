# Paper 1 amendment A2: dev design result (descriptive; not carried to test)

Pre-declaration: A2-PREDECLARATION.md (commit 2cd881c, written before any A2 computation). Run once locally,
inputs hash-verified, B0 reproduces S5 exactly. CPU 133.9 s metered (local-cpu-measurements.jsonl). Dev only; the
test qrels remain sealed. Aggregates: dev-design.json; per-query values stay private.

Selection rule outcome: NO_ADMISSIBLE_TAIL_FUSION_ON_DEV. Every T-FA(k) loses more than 0.010 IN Recall@200 vs B0
(k=50 -0.075, k=100 -0.046, k=150 -0.021), and none beats B0 on OUT (0.134 / 0.137 / 0.146 vs 0.148).
Per the pre-declared rule A2 is NOT carried to test; no other variant is tried (that would be outcome-driven).

Descriptive dev Recall@200 (OUT / IN):
- B0 0.148 / 0.514
- T-FA(150) 0.146 / 0.493; T-GR(150) 0.153 / 0.508; T-SACR(150) 0.152 / 0.508; T-shuffle(150) 0.148 / 0.498.

Reading (dev, descriptive, no significance): FA's extra families sit below B0's positives. Protecting B0's head does
not stop the loss, because B0 positives at ranks 151-200 are displaced and FA adds few new OUT positives (arm-only 5,
reference-only 8 at k=150). FA behaves much like the word-shuffle control and worse than the GR and SACR tails.
The S5 "15 rescued vs 32 displaced" pattern was not usable complementarity. This is a negative design result.
