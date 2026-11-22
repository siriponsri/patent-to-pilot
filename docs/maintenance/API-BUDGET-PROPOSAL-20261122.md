# OpenRouter API budget proposal (22 Nov 2026), for owner approval

**Status:** **E1 APPROVED by the owner on 22 Nov 2026** (USD 8.00, 35,000 requests; OWNER-DECISIONS D9). E2 is not
approved. Nothing has been spent yet: only free catalogue and credit reads were made.

**Account state (read 22 Nov 2026 via OpenRouter `get-credits`):** total credits USD 10.00, used USD 1.63, **remaining
≈ USD 8.37**. This balance is a hard ceiling unless the owner adds credits.

## 1. What the money is for

| Task | Goal | Why an LLM | Paid? |
|---|---|---|---|
| **T1. G03 amendment 3: LLM query expansion as new acquisition routes** (owner decision D2: keep pushing acquisition) | Generate short hypothetical prior-art texts and keyword queries per P1-DEV/VAL request. Embed them with PatEmbed and Qwen3 on the dr-train V100 and search them with BM25, as new routes in the existing G03 harness, at the same B = 4 budget and with the same final scorer. Principal contrast: best allocation with LLM routes vs F\*. | G03 showed that re-allocating the same routes cannot reach the +0.079 oracle headroom, because gains need candidates the current routes never surface. LLM-generated pseudo-documents are the established way to add such candidates (Query2doc, HyDE). Patent-specific evidence exists (CPC-aware LLM expansion; agentic prior-art search). | **Yes:** this proposal (envelope E1) |
| T2. G05 Thai Gazette contextual retrieval (later) | Reproduce the paper's contextual 200-word chunks + hybrid control (the paper used DeepSeek V4 Flash for context; per our audit doc 04 §3.1) | Required for a fair, paper-matched transfer control | Later: a separate envelope E2, sized after counting chunks |
| T3. Workbench chat profiles (G06 demo) | Check that 2–3 chat profiles work end to end | Product capability check only | Tiny: inside E1 (≤ USD 0.20) |

Embeddings and reranking stay **local on dr-train** (PatEmbed, Qwen3-Embedding-0.6B, Qwen3-Reranker-0.6B), costing USD 0.
RunPod is not needed for E1.

## 2. Models: research fit and live prices (OpenRouter, 22 Nov 2026, USD per 1M tokens, input / output)

| Model (OpenRouter id) | Price | Batch price | Why it fits the research |
|---|---|---|---|
| `qwen/qwen3-32b` | 0.08 / 0.28 | — | Same open-weight **Qwen3 family** as the owner's research profile (`model_profiles.json`: Qwen3-8B generator, Qwen3 embeddings). Reproducible: open weights can later be self-hosted. |
| `deepseek/deepseek-v4-flash-0731` | 0.0443 / 0.30 | 0.048 / 0.144 | **Paper-matched for G05:** the Thai Gazette NLLP 2026 paper's recommended contextual profile uses DeepSeek V4 Flash. Cheap and strong. |
| `anthropic/claude-haiku-5.5` | 0.10 / 0.50 | 0.05 / 0.25 | The owner's **API economical profile** (`model_profiles.json` api_economical). Strong instruction following for structured JSON. |
| `qwen/qwen3.7-flash` | 0.03 / 0.13 | — | Cheapest current Qwen model. Tests whether a very small, cheap expander is enough (cost-effectiveness question raised by Expandorini, Sadeghi & Lin 2026). |
| `anthropic/claude-sonnet-5.5` (optional) | 2.00 / 10.00 | 1.00 / 5.00 | The owner's **API stronger profile**. Only a small sensitivity sample (E12 "model strength"); Query2doc reports that gains grow with LLM capability. |

**Rules for every call:**
- reasoning off (`reasoning_effort: none`), so thinking tokens are not billed;
- `max_tokens` ≤ 400;
- temperature 0, seed fixed;
- every response saved for replay;
- token usage logged in the G02 provider ledger.

Prices change, so re-read `list-models` before each run.

## 3. Cost estimate for T1

**Per query:**
- input ≈ 850 tokens (instructions + title/abstract/first claim, truncated);
- output ≈ 360 tokens (3 short hypothetical prior-art abstracts of about 100 words + 1 keyword query).

**Stage A, pilot:** 2,000 P1-DEV queries per model (selection uses P1-DEV only).

| Model | Pilot cost (2,000 queries) |
|---|---|
| qwen3.7-flash | ≈ $0.15 |
| deepseek-v4-flash (batch) | ≈ $0.19 |
| qwen3-32b | ≈ $0.34 |
| claude-haiku-5.5 (batch) | ≈ $0.27 |
| claude-sonnet-5.5 (batch), 300 queries only (optional) | ≈ $0.80 |
| **Pilot total** | **≈ $1.75** |

**Stage B, full run:** with the one model selected on the pilot, P1-DEV (26,575) + VAL (2,000) ≈ 28,600 queries ≈ 24M input
+ 10M output tokens.

| Selected model | Full-run cost |
|---|---|
| qwen3.7-flash | ≈ $2.1 |
| deepseek-v4-flash (batch) | ≈ $2.6 |
| claude-haiku-5.5 (batch) | ≈ $3.8 |
| qwen3-32b | ≈ $4.8 |

**Total T1:**
- pilot $1.75 + full run $2.1–4.8 + T3 $0.2 = **about $4–7**;
- add a 20% margin for retries and failed requests, counted when attempted (G02 ledger rule).

## 4. Proposed envelopes

| Envelope | Scope | Cap | Request cap | Stop rules |
|---|---|---|---|---|
| **E1 (ask now)** | T1 (G03 amendment 3, pilot + one full run) + T3 | **USD 8.00** (fits the current balance) | **35,000 requests** | Stop after the pilot if no LLM route improves P1-DEV pool recall (decision written before Stage B). Stop at USD 6 spent if Stage B is not finished, then report. Never retry only the proposed arm. |
| E2 (later) | T2 Gazette contextual chunks | to be sized (likely USD 10–25) | to be sized | Separate owner approval after the chunk count |

Approving E1 does not approve E2 or RunPod.

## 5. Sources

- Query2doc: L. Wang, N. Yang, F. Wei, EMNLP 2023 (aclanthology.org/2023.emnlp-main.585). BM25 +3–15%; dense gains
  smaller; larger LLMs help more.
- HyDE: L. Gao et al., "Precise Zero-Shot Dense Retrieval without Relevance Labels", ACL 2023 (arXiv 2212.10496).
- Jagerman et al., "Query Expansion by Prompting Large Language Models", arXiv 2305.03653 (2023). Model size matters.
- "CPC-aware neural patent retrieval with LLM-assisted query expansion", Springer 2026
  (doi 10.1007/s42488-026-00165-8). First-stage Recall@50 0.40 → 0.46 on patents (Turkish aviation).
- PatEx-Gym, arXiv 2610.33503 (2026): agentic prior-art search; prior-art discovery stays hard even for frontier models.
- Sadeghi & Lin, Expandorini (SIGIR-AP 2026 preprint): a cost-aware comparison of 13 LLM query-expansion methods across
  22 LLM configurations.
- Suyasri, Akarajaradwong, Chaksangchaichot, "An Empirical Study of Evidence Retrieval for RAG over the Thai Royal
  Gazette", NLLP 2026 (aclanthology.org/2026.nllp-1.19). Contextual 200-word chunks + hybrid is the best trade-off.
  The DeepSeek V4 Flash context generator comes from the owner's audit (doc 04 §3.1), not re-verified here.
- Prices: OpenRouter live catalogue (`list-models`), 22 Nov 2026.

**Caveat:** the search results above were summaries. The exact numbers should be checked in the PDFs before they are cited
in the paper.
