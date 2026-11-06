# Cross-Industry Solution Scout: product spec (6 Nov 2026)

- **Status:** SPEC. Nothing is built yet. The owner approved a product-led paper on 6 Nov 2026.
- **Supersedes:** the organization-adaptive screens in [ORG_ADAPTIVE_POC_PLAN_20261105_EN.md](ORG_ADAPTIVE_POC_PLAN_20261105_EN.md). The org-adaptive and LLM-rewriting claims were not carried forward. That plan's architecture, data-layer and wording rules still apply.
- **May change:** a deep-research run on alternative directions is in progress outside the repository. If it finds a stronger scientific core, this product becomes its demonstrator and §6 changes.

## 1. One-line pitch and users

"Paste a technical problem in a paragraph. See which patents from other industries already solve it, where they come from, and why each one may transfer, with every claim traceable to its source text."

The intended users are design assumptions only. No users have been interviewed or tested.

| User (assumed) | Decision the tool supports |
|---|---|
| R&D engineer | Is there an existing solution in another field before we design one? |
| Technology-scouting or open-innovation lead | Which outside fields and patent families deserve a closer look or an outreach? |
| IP analyst | Which far-field documents should enter a prior-art or landscape review? |

The tool never states novelty, validity, infringement or freedom to operate.

## 2. Design decisions and the evidence behind them

Every decision below rests on a pre-declared dev-split result. The DAPFAM test split has not been read.

| Decision | Evidence | Audit |
|---|---|---|
| Input is a short problem brief; no patent needed | A brief loses about 0.03–0.04 Recall@200 against the full patent under the same candidate set | [scout feasibility](../audits/ptp-solution-scout-feasibility-20261105/README.md) |
| Results come in two visible lanes: own field and other fields | The other-fields lane reaches strict-OUT R@200 0.29 against 0.135 for one ranked list, but IN R@200 falls from 0.466 to 0.368. The user sets the split | same |
| The search query is never rewritten by an LLM | Every LLM rewriting tried in Stage 1 and in the scout check lowered recall | [Stage 1](../audits/ptp-org-adaptive-stage1-20261105/README.md), scout feasibility |
| Ranking does not use a field-prediction prior | A learned class prior lowered R@50 by 0.044; even oracle class knowledge adds only 0.06 | [atlas headroom](../audits/ptp-solution-atlas-headroom-20261106/README.md) |
| The field map is descriptive only: it shows where the found families sit and does not steer the ranking | same | same |
| The LLM is used only to explain a candidate, with verbatim quotes that are checked | It keeps the LLM away from the ranking step, where it hurt | — |

The lane gain is mostly definitional, because the mask matches the strict-OUT definition. The product presents it as a user-controlled filter, never as a retrieval improvement.

## 3. Screens

All screens live inside the existing node-canvas workspace in `frontend/healthtech-web`, with TH/EN strings and keyboard alternatives.

| # | Panel | Contents | Rules |
|---|---|---|---|
| S1 | Problem brief | A text box with a 40–120-word hint and an own-field picker: IPC3 codes typed in, or taken from one reference patent | The brief is stored exactly as typed. The own-field codes drive the lane mask and are shown |
| S2 | Two-lane shortlist | "Own field" and "Other fields" columns. Default shortlist of 20 (10 + 10); the split and length are adjustable up to 200 | Each row shows the raw and canonical identifier, kind code, jurisdiction, date, IPC3 codes and score. Unjudged items are never shown as negative |
| S3 | Field map | Counts of other-field hits by IPC section and class, with click-to-filter | Labelled "where the results come from — not a recommendation" |
| S4 | Candidate card and transfer rationale | On request, the local Qwen3-8B writes: what the candidate does; which mechanism might transfer; up to 3 verbatim quotes from the candidate text | Each quote is checked for a literal match against the stored source text. Unmatched quotes are flagged red. Labelled "literal match ≠ semantic support". The user can accept, reject or note each rationale |
| S5 | Dossier hand-off | Selected families go to the existing dossier flow: source inspection, edits and history, then TH/EN export | Source facts, system inference and unresolved items stay separate, as in the current dossier contracts |
| S6 | Run receipt | Encoder time, Qwen calls, tokens, latency and GPU-seconds, plus input and output hashes and the corpus or vector bundle hashes | Shown on screen and saved with the session |

## 4. Architecture (reuse first)

- **Frontend:** new panels in `frontend/healthtech-web`. Node ≥ 22, no build step, no runtime dependencies.
- **Backend:** new routes in `src/patent_to_pilot/healthtech/http.py`, following the existing job pattern:
  - `POST /scout-sessions`: brief plus own-field codes in; both lanes out;
  - `GET /scout-sessions/{id}`;
  - `POST /scout-sessions/{id}/rationales/{family}`;
  - `GET /scout-sessions/{id}/receipt`.
- **Retrieval:**
  - the precomputed-vector path (`vector_http.py`, `PrecomputedVectorRetriever`), plus the IPC3 lane mask moved from `scripts/healthtech/run_dapfam_dense_pool.py` into a tested library function;
  - two lanes merged by the tested `lane_merge` in `dapfam_acquisition.py`.
- **Two modes:**
  - *Replay:* recorded sessions with hashes; runs on a laptop with no GPU.
  - *Live:* PatEmbed query encoding and Qwen3-8B on dr-train through the existing local-execution path and GPU lock.
- **Storage:** the existing SQLite repository. No new ledger; the E2 accounting ledger is never touched. No paid API.

## 5. Data layers

| Layer | Data | Use | Rights |
|---|---|---|---|
| Evaluation (private) | DAPFAM queries, corpus, qrels and vectors | Aggregate numbers only | CC BY-NC-SA. Texts and generated texts stay out of Git and out of any shipped demo |
| Public demo | **Owner decision.** Proposed: a multi-industry subset of US granted patents from PatentsView (CC BY 4.0), title + abstract + first claim, covering all eight IPC sections | Live and replay demos, screenshots, video | Recorded through `rights.py` / `provenance.py` |

The public corpus size depends on encoding cost. DAPFAM's 45k families and 189k passages are the reference point. A 3-query encoding canary measures the cost before any large run.

## 6. Evaluation for the paper (pre-declared, frozen before the test is read)

| ID | Question | Measure | Status |
|---|---|---|---|
| E1 | What does an analyst see at a fixed reading budget, with and without the other-fields lane? | Strict-OUT and IN recall at 20/50/200 on the DAPFAM test, under both the full-candidate and the OUT-only protocol, stated explicitly; the IN/OUT trade-off curve over lane splits | Needs a freeze commit and owner approval to read test once |
| E2 | Does a short brief replicate the small loss against the full patent? | Brief vs full-patent gap on test | Same freeze |
| E3 | Are LLM rationales grounded? | Share of quotes that match literally; failure types. A semantic check by the developer is a labelled proxy with its bias stated | Dev first, on DAPFAM private text; nothing generated is published |
| E4 | What does a session cost? | Latency, tokens and GPU-seconds per session, live mode | Canary, then the full set |
| E5 | Optional: does it hold outside DAPFAM? | E1–E2 replicated on the PatenTEB `retrieval_OUT` test split, excluding the 48 overlapping queries and 376 families | Only if E1 is frozen first; IPC metadata to be checked |

Earlier stop rules still hold. No claim of LLM retrieval gain, organization adaptation or class-prior gain is made.

## 7. Milestones

| M | Deliverable | Acceptance |
|---|---|---|
| M0 | Library: lane mask function, scout session schema, rationale schema with quote-match check; authored fixtures | Unit tests; existing suite green |
| M1 | Backend routes in replay mode | HTTP integration test: create → lanes → rationale → receipt; flagged unmatched quote |
| M2 | Frontend panels S1–S6 | `npm test`, `npm run test:e2e` (Chromium), keyboard paths, TH/EN |
| M3 | Public demo corpus, encoded | Rights record, encoding canary, then full encode with hashes in an audit |
| M4 | Live mode | 3-query canary with tokens, latency and failures recorded under `docs/healthtech/audits/` |
| M5 | Frozen evaluation E1–E4 (E5 optional) | Freeze commit before test; one test run; results as they are |
| M6 | Paper draft and demo video (existing `tutorial-video/build.mjs`) | Owner review; wording rules below |

M0–M2 do not depend on any research outcome.

## 8. Wording rules

- Say: "on DAPFAM, under a frozen protocol, the other-fields lane changed what an analyst sees in the first 20 results by X (95% CI …), at a cost of Y in same-field recall".
- Do not say:
  - "finds all prior art";
  - "validated by users" or "customers";
  - "AI discovers solutions";
  - "replaces a searcher";
  - anything about novelty, validity, infringement or freedom to operate.
- Simulated or assumed users are labelled as such. Developer self-evaluation is labelled as a proxy.

## 9. Owner decisions needed

1. The public demo corpus (PatentsView subset proposed) and the V100 time for encoding it.
2. Approval to freeze E1–E2 and read the DAPFAM test split once.
3. Whether to include E5 (PatenTEB replication).
4. A product name for the paper and the demo.
