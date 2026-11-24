# P1-T05/P1-T06: A3r1 Stage B and full evaluation (checkpoint, 24 Nov 2026)

**Protocol:** A3r1 (frozen at P1-T03), the pilot GO in [P1-T04](P1-T04_pilot_generation.md), and the RunPod addendum
[A3R1-FULL-EVAL-RUNPOD.md](../../../healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md) (D24).
**Private outputs:** `../_private_artifacts/g03-a3r1-full-runpod/` (results and evals archives sha256-checked, plus the
pod log).

## Stage B (owner PC, OpenRouter, envelope E1R)

- **Model:** m\* = `deepseek/deepseek-v4-flash-0731`, 800 max tokens, reasoning off.
- **P1-DEV:** 25,626 apps (2,000 pilot reused). **VAL:** 1,919 apps.
- **Outcome:** all `ok`, with 0 content_unusable and 0 failed.
  - 8 attempts timed out during a network outage, with unknown cost. They were reconciled from the OpenRouter usage
    delta (USD 0.000901 in total) and retried.
- **E1R committed after Stage B:** USD 3.853 over 33,685 attempts (limit USD 50).

## Full evaluation (RunPod)

- **Pod:** `ij0lefy6i5ds68`, RTX PRO 4500 Blackwell, Secure US-KS-2, USD 0.72/h. Run 22:25–00:47 UTC, about
  USD 1.7, charged to R2. The pod is deleted.
- **Gates (all passed):**
  - `ledger`;
  - `cpu`: corpus, query text, BM25/Qwen3/PatEmbed P1-DEV, archived VAL L/Q/P re-evaluated, v0 F\* on P1-DEV and VAL,
    populations;
  - `enc`: re-encoded PatEmbed on P1-DEV and VAL.
- **Integrity:** the A3r1 harness F\* equals v0 F\* on both P1-DEV and VAL.

## Frozen decision

- **F3\*** (best P1-DEV ALL R@200, frozen tie rule) = `alloc-L0-Q1-P1-H1-K1`: one window each of Qwen3, PatEmbed,
  H (LLM-HyDE on PatEmbed) and K (BM25 on LLM text). P1-DEV ALL R@200 is 0.4451, against F\* 0.4231.
- **Principal, VAL F3\* − F\*** (cluster bootstrap by art unit, B = 10,000, seed 20261119):

| Metric | Δ | 95% CI | n | wins / losses |
|---|---|---|---|---|
| **ALL R@200** | **+0.0213** | [0.0146, 0.0280] | 1,999 | 290 / 161 |
| IN R@200 | +0.0189 | [0.0082, 0.0293] | 1,698 | 147 / 92 |
| OUT R@200 | +0.0225 | [0.0130, 0.0321] | 1,957 | 152 / 78 |

- **Decision: CONTINUE.** LLM routes improve ALL R@200, and IN/OUT are non-inferior (protocol v1 §7 rule).
- **Descriptive, P1-DEV F3\* − F\*:** +0.0220 [0.0200, 0.0240], with 4,037 wins and 2,183 losses.

## What this does and does not show

- **This is DEV-phase exploratory evidence.** F3\* was selected on P1-DEV. VAL has now been looked at **four times in
  G03** (disclosed).
- **F\* is built on the C0 routes.** P2-T02 has since shown that complete-content single routes are stronger (Arctic C1,
  BM25-full). So A3r1 is not yet compared with the strongest simple controls. P2-T04 onward must include them.
- **LLM query expansion is a candidate-acquisition route (D2).** It is not the proposed structural method. `method_evidence`
  stays NOT_YET_DEMONSTRATED for the paper's main claim. A3 becomes an **exploratory gain** to carry into the matched
  comparison.
