# PoC and portfolio plan: organization-adaptive cross-domain prior-art search

- Written: 2026-11-05. **Status: PLAN. Nothing has been built or run yet.**
- 6 Nov 2026: the organization-adaptive screens are superseded by the [solution-scout product spec](SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md). The architecture, data-layer and wording rules below still apply.
- Research protocol (draft, not frozen): [ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md](ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md).
- Goal: a working local demo that a reviewer can run and inspect, and a portfolio case study whose numbers come only from the frozen test in that protocol.

## 1. What the demo must show

| Screen | What it does | Backed by |
|---|---|---|
| Organization profile | Pick a simulated organization (an IPC section, or the "cardiovascular-device" demo organization) or build one from a list of the organization's own patents. Shows the IPC3 profile vector. | Protocol §6 |
| Agent trace | For one query family, shows each action the policy chose, why it chose it (feature values and estimated gain vs cost), and which families each action added to the pool | Protocol §5; existing bounded controller `src/patent_to_pilot/healthtech/controller.py` |
| Cross-domain finds | Pool results grouped into "same field" and "other field" by IPC3 overlap. Each result has its identifiers, kind code, date, jurisdiction and an exact source locator. | Existing evidence and locator contracts |
| Feedback → adaptation | Relevant / not relevant / unsure buttons. Feedback updates only that organization's policy state, which is versioned and can be reset. A learning curve shows the effect replayed on dev data. | Protocol §5 (π-org) |
| Cost meter | Qwen calls, tokens, latency and GPU-seconds per query, against a per-query budget | Protocol RQ4 |
| Dossier hand-off | Sends selected families into the existing device dossier workspace (MITRACLIP, TENDYNE and TRICLIP context) | Existing `frontend/healthtech-web` dossier flow |

Unjudged results are shown as "not judged", never as "not relevant". Simulated organizations carry a visible "simulated" label.

## 2. Architecture (reuse first)

- **Frontend:** extend `frontend/healthtech-web` (Node ≥ 22, no build step, no runtime dependencies). Add new panels to the existing node-canvas workspace; do not start a new app.
- **Backend:** extend `src/patent_to_pilot/healthtech/http.py`. The new routes are `POST /search-sessions`, `GET /search-sessions/{id}`, `POST /search-sessions/{id}/feedback`, `GET /org-profiles` and `POST /org-profiles`. They reuse the job pattern of `POST /jobs`.
- **Controller:** widen the existing bounded action set (`technical_search`, `feature_search`, `stop`) with `functional_abstraction` and `ipc_shift`. Keep its guarantees: no URLs, no arbitrary tools, no evaluator fields, and no answer leakage into actions.
- **LLM runtime has two modes:**
  - *Live mode:* Qwen3-8B on dr-train behind the existing local-execution path and GPU lock, reached through an SSH tunnel.
  - *Replay mode:* the demo replays recorded traces, with their hashes, so it runs on a laptop with no GPU.
- **Storage:** the existing SQLite repository for sessions, feedback and policy versions. Never add a second ledger, and never touch the E2 accounting ledger.

## 3. Data for the public demo vs the evaluation

DAPFAM is CC BY-NC-SA 4.0, and its texts stay private. The demo therefore uses two layers:

1. **Evaluation layer (private):** DAPFAM queries, corpus and qrels. It only produces the frozen aggregate numbers shown on the results card.
2. **Public demo layer:** US patent full texts and identifiers from public sources for the cardiovascular-device organization, plus the Track B devices. Their rights and provenance are recorded through the existing `rights.py` and `provenance.py` checks. Public demo traces are recorded on this layer only.

Generated query texts derived from DAPFAM are never shipped in the demo or the repository.

## 4. Milestones and acceptance

| M | Deliverable | Acceptance (all must pass) | Depends on |
|---|---|---|---|
| M0 | Contracts and fixtures: session, action, trace, feedback and org-profile schemas, with authored fixtures | Unit tests for schema round-trip and controller bounds; the existing suite stays green | — |
| M1 | Backend routes in replay mode | HTTP integration test covering session create → trace → feedback → policy version bump; resetting returns to the base policy | M0 |
| M2 | Frontend panels: profile, trace, cross-domain finds, feedback, cost meter | `npm test`, `npm run test:e2e` on Chromium, keyboard alternatives for drag-and-drop, TH/EN strings | M1 |
| M3 | Live mode with Qwen3-8B on dr-train | A 3-query canary on the public demo layer, with tokens, latency and failures recorded under `docs/healthtech/audits/<run-id>/` | M1; protocol Stage 0 canary |
| M4 | Results card filled from the frozen test | Every number traces to the Stage 3 test artifact; negative or null results are shown as they are | Protocol Stage 3 |
| M5 | Portfolio package: case-study README (problem → prior work → method → frozen result → limits), a 2–3 minute screen recording using the existing `tutorial-video/build.mjs` pipeline, and an architecture diagram | Owner review; no claims beyond the protocol's results and limitations | M2–M4 |

M0–M2 do not depend on the research outcome, so they can run in parallel with protocol Stages 0–2.

## 5. Portfolio wording rules

- Say: "on the DAPFAM benchmark, under a frozen protocol, the adaptive policy changed cross-domain exposure by X (95% CI …) at Y LLM calls per query". Use the real numbers, whatever their sign.
- Do not say:
  - "adapts to your company";
  - "validated by users";
  - "finds all prior art";
  - "replaces a patent searcher";
  - any statement about novelty, validity, infringement or freedom to operate.
- The simulated organizations, the unjudged policy and the single-benchmark limit appear on the results card itself, not only in a footnote.
