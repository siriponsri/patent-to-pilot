# Manuscript writing plan: organization-adaptive candidate acquisition for cross-domain prior-art search

- Written: 2026-11-05. Status: **PLAN**. Numbers are filled only from frozen artifacts.
- Target venue: World Patent Information (WPI). The Guide for Authors still needs an owner check (HTTP 403 for the agent).
- Protocol: [ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md](ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md). PoC: [ORG_ADAPTIVE_POC_PLAN_20261105_EN.md](ORG_ADAPTIVE_POC_PLAN_20261105_EN.md).

## 1. Positioning

- This is a **new, self-contained manuscript**. Every DAPFAM analysis in it, including the exposure diagnosis, is produced by this study's own code and receipts. The owner's earlier unpublished DAPFAM analyses are superseded: they are not cited, named or used as a source of numbers or terminology.
- Prior own work that is cited: the published IEEE paper on near-zero instruction effects in cross-domain patent reranking (Srihangpiboon & Ploysuwan). It motivates the acquisition question: reranking cannot recover relevant families that are absent from the pool.
- One WPI manuscript goes forward. The earlier Track A draft (`MANUSCRIPT_ADAPTIVE_EVIDENCE_ACQUISITION_EN.md`) is folded in as supporting evidence (W1).

## 2. Working title and claims

Working title: *Where cross-domain prior art is lost: organization-adaptive, LLM-assisted candidate acquisition for patent search*

Planned contributions. Each depends on its frozen result and is dropped or reworded if not supported.

1. **Exposure diagnosis (RQ0).** For a strong dense passage retriever on DAPFAM, measure what share of judged cross-domain relevant families never enters the Top-200 pool, and the ceiling that reordering alone can reach. Show the effect of whole-query encoding: multi-window vs single 512-token window.
2. **Acquisition (RQ1).** Test whether LLM cross-domain actions (functional abstraction, IPC-shift, pseudo-document) raise cross-domain exposure at an equal candidate budget, while all-positive recall stays non-inferior.
3. **Adaptivity and organization context (RQ2, RQ3).** Test whether a learned per-query policy keeps most of the gain at a lower LLM call rate, and whether organization-specific policies beat a global one.
4. **Cost.** Report the exposure–cost frontier: LLM calls, tokens, GPU-seconds and latency.
5. **Supporting evidence (W1).** Track A's preregistered PANORAMA results show that the best fixed ranking policy depends on task granularity, which motivates selecting actions per query.

## 3. Section outline and the artifact that fills each part

| Section | Content | Source artifact |
|---|---|---|
| 1 Introduction | Prior-art search practice; cross-domain vocabulary gap; why acquisition and not reranking; contributions | Protocol §1; cited IEEE paper |
| 2 Related work | Patent retrieval benchmarks (DAPFAM, PANORAMA, PatenTEB); agentic patent search (PatEx-Gym, PatentAgentBench); RL query rewriting (DeepRetrieval and its critique); adaptive routing (MBA-RAG, Adaptive-RAG, retriever portfolios); LLM expansion for patents | `RELATED_PAPERS.md`, after the systematic rerun |
| 3 Data and split | DAPFAM; IN/OUT definition; unjudged ≠ negative; component split | Stage 0 audit, `stage0-split-inputs.json` |
| 4 Methods | Fixed actions R1, R2, R2w and R3; LLM actions Q1–Q3 with exact prompts; budgeted merge; bandit policy; organizations; statistics | Protocol §5–§8; Stage 2 freeze file |
| 5 Results 1: exposure diagnosis | Absent share; ideal-reordering ceiling; single-window vs multi-window query | Stage 0/1 dense pools on dev, then test for F\* |
| 6 Results 2: acquisition and adaptivity | H1, H2, H2b, H3 and H-G with paired component-bootstrap CIs; per-organization table; cost frontier | Stage 3 test artifact |
| 7 Supporting evidence | Track A granularity result (PAR4PC vs PI4PC), shortened | `ptp-wpi-research-package-20261104` |
| 8 Practitioner implications and demo | How a search team could use action traces and the cost meter; screenshots from the PoC on public US patents | PoC M2–M4 |
| 9 Limitations | Proxy labels; IPC3 as a cross-domain proxy; simulated organizations; single benchmark; LLM contamination; prior exposure of baselines | Protocol §10 |
| 10 Conclusion | Only supported claims | — |
| Declarations | AI-tool use; data and model licenses (CC BY-NC-SA 4.0 for DAPFAM and PatEmbed); code availability; funding; CRediT | Owner |

## 4. Terminology rules

Only these terms are used in the manuscript, code, audits and PoC for this study:

| Term | Meaning |
|---|---|
| dense passage retriever (R2) | PatEmbed-large, retrieval_OUT prompts, 384/64-term TAC passages, MaxP |
| single-window query / multi-window query (R2 / R2w) | Query encoded as one 512-token window vs 384/64-term windows with a max over windows |
| fixed baseline F\* | Best single fixed action on dev |
| fixed mix M\* | Best fixed combination of actions on dev |
| acquisition policy π | Contextual-bandit policy over actions |
| exposure | Strict-OUT Recall@200 of the candidate pool |
| reordering ceiling | Macro Recall@100 after ideal reordering of the Top-200 pool |
| simulated organization | IPC section A–H |

Labels and profile names from the owner's earlier unpublished work are not used. `tests/test_org_adaptive_terminology.py` enforces the banned list on this study's documents and code.

## 5. Figures and tables (planned)

1. Pipeline: query → actions → budgeted pool → policy, with the cost meter.
2. Exposure bar: judged cross-domain pairs found at ranks 1–100, found at 101–200, or absent; single-window vs multi-window query.
3. Main results table: every action and policy on test, with CIs.
4. Exposure–cost frontier.
5. Per-organization forest plot.
6. Supporting panel: Track A granularity result.

## 6. Honesty rules for a "positive" story

- The headline is whatever the frozen test shows. If H1 fails, the paper becomes the exposure diagnosis plus a negative acquisition result, and the title changes.
- Every gain is shown with its all-positive guard result and its LLM cost.
- The multi-window query is a fixed-baseline improvement chosen before any scoring. It is reported as an improvement to the baseline, never as part of the adaptive method's gain.

## 7. Owner decisions for writing (answered 2026-11-05)

| ID | Decision |
|---|---|
| W1 | Track A goes in the main text as a short section with one figure panel; full tables go in the supplement. |
| W2 | Code is licensed Apache-2.0 (`LICENSE`). `NOTICE` states that data and model weights keep their own terms. |
| W3 | Authors: Siripon Srihangpiboon (first, corresponding) and Tuchsanai Ploysuwan, both of the School of Information Technology, King Mongkut's Institute of Technology Ladkrabang, 1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520, Thailand. Funding: none ("This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."). Competing interests: none. Both statements were confirmed by the owner on 2026-11-05. |
| W4 | Guide for Authors read 2026-11-05; requirements are in `docs/healthtech/audits/ptp-wpi-research-package-20261104/READINESS.md`. |

CRediT roles under W3:
- Srihangpiboon: Conceptualization, Methodology, Software, Investigation, Formal analysis, Data curation, Visualization, Writing – original draft.
- Ploysuwan: Supervision, Writing – review and editing.

## 8. WPI constraints applied to this plan

- **Length:** 3,000–6,000 words. Planned budget:

  | Section | Words |
  |---|---:|
  | 1 Introduction | 600 |
  | 2 Related work | 700 |
  | 3 Data | 400 |
  | 4 Methods | 1,100 |
  | 5–6 Results | 1,400 |
  | 7 Track A | 400 |
  | 8 Implications | 400 |
  | 9 Limitations | 400 |
  | 10 Conclusion | 200 |
  | **Total** | **≈ 5,600** |

  Detailed tables, prompts and per-organization results go in the supplement.
- **Front matter:** abstract up to 250 words; 1–7 single-word-style keywords; 3–5 highlights of at most 85 characters; an optional graphical abstract built from Figure 1.
- **Double-anonymized review:**
  - Use a separate title page.
  - Cite the authors' IEEE paper in the third person.
  - Remove acknowledgments from the manuscript.
  - Use an anonymized code mirror for review; replace it with the public repository after acceptance.
- **Source format:** LaTeX with Elsevier's `elsarticle` class, numbered style, matching bracketed numeric references. Third-party template catalogues are not needed.
- **Declarations:**
  - Competing interests: none (owner, 2026-11-05).
  - Generative-AI use: name the tools and their roles (code, drafting, review) and state that the authors verified all content.
  - Data statement: DAPFAM and PANORAMA are public and cited, not redistributed; aggregates, prompts and code are shared.
