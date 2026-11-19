# Patent-to-Pilot research and innovation roadmap (v1, 19 Nov 2026)

Strategic source: owner file `owner-note-19112026/PTP_IS2_Paper53_Research_Program_University_Impact_2026-11-19.md` (adopted 19 Nov,
`paper1-bridgeret/owner-decisions-20261118.json` 'later'). This file is the repo-side map. It **adds** to GOAL.md, PLAN.md and
MASTER-PLAN.md and replaces nothing in them. Their older sections stay as history and as contracts.

> From a near-zero reranking result to an evidence-grounded AI discovery system.

## 1. Program map

```
Paper 53 / IS1 (Diagnose) ──► B53 / IS2 core (Intervene) ──► P1 BridgeRet (Discover) ──► Solution Scout (Translate)
                                       │                     P2 CEDS (Acquire) ────────►        ▲
                                       │                     P3 EG-SHE (Repair) ─ flag ─────────┘
                                       └──── stakeholder proxies / demo ─────────────────────────┘
```

The research logic runs in this order, but the implementation is **not a waterfall**:
- IS2 does not wait for Papers 1–3.
- P2 does not wait for P1 to win.
- P3 starts on synthetic and DEV traces.
- The product always runs on a static baseline.

## 2. Lanes, status and next evidence (labels: evidence ladder in `is2/COMMITTEE-RESPONSE-DRAFT.md` §3)

| Lane | Scientific identity | Status 19 Nov | Evidence label | Next evidence |
|---|---|---|---|---|
| **IS2 / B53** | Does changing only the first stage change OUT exposure and the instruction contrasts of Paper 53? | Stage 1 FROZEN (`plans/B53-PREDECLARATION.md`, 274af5de); running on dr-train (F0–F7 encodings, BM25, RRF) | DESIGNED → MEASURED | Stage-1 table; 1,000-pair reranker timing; Stage 2 declaration; B53.0 MTEB check |
| **P1 BridgeRet** | Rejection-grounded fine-tuning for unseen cross-domain prior art | manifest-v2 + Challenge-1M frozen; DEV baselines measured; Qwen3 hard negatives mined (97,059 TRAIN tasks); RunPod grid S1–S4 on 30k (≤ USD 20) starting | MEASURED (DEV) / NOT_RUN (TEST) | S* on DEV → full-TRAIN S* → owner go for the single P1-TEST look |
| **P2 CEDS** | Evidence-deficit-guided budgeted Search/Visit/Select | harness and arms E0–E3 tested with doubles only | ENGINEERING VALIDATED / SYNTHETIC | real retrieval backend on P2-DEV (family-disjoint from P1-DEV); matched-budget E0–E3 |
| **P3 EG-SHE** | Repair stages where evidence shows repairable headroom | design only | DESIGNED / NOT_RUN | typed patch grammar + replay runner on synthetic traces; E4/E5/E7b controls |
| **Solution Scout** | Replayable cross-industry evidence dossier | local TH/EN prototype; P0 gap audit 41/42 scenarios (1 recorded gap) | ENGINEERING VALIDATED | static 60–90 s demo path with provenance labels; commercial-licence stack only (no CC BY-NC models in the product) |

## 3. Gates (owner decision 19 Nov: light gates)

Only four things need the owner:
1. opening any protected TEST (P1/P2/P3-TEST; one look, explicit go);
2. spend beyond an approved envelope (current: RunPod P1 fine-tuning ≤ USD 20);
3. new data downloads or licence changes;
4. external release (submission, publication, slides shown outside the committee).

Everything else proceeds and is logged in HANDOFF/INDEX-PLAN: DEV runs, local CPU/V100 jobs, code, docs, and the B53 local run
within the 19-Nov approval. Scientific integrity rules stay in force:
- pre-declare before computing;
- one settle per job;
- no TEST data for selection;
- no claim without a receipt.

## 4. Deliverables by horizon

| Horizon | IS2 | Papers | Product / university |
|---|---|---|---|
| Now (Nov 2026) | B53 Stage 1 results; committee-response matrix; K1a v2; IS2 short paper draft (faculty template) | P1 S* on DEV | demo storyboard; portfolio one-pager |
| Next | B53 Stage 2 (reranking), B53.0; IS2 report + 12-slide deck | P1-TEST (owner go) → P1 manuscript; P2-DEV pilot | stable demo build |
| Potential | — | P2 and P3 manuscripts (venues: `journal/VENUES.md`) | teaching benchmark / tech-transfer pilot, subject to institutional approval |

## 5. Non-negotiables
- B53 is a re-implementation, not a replication of Paper 53.
- Paper 86 is the owner's unpublished work (withdrawn from IEEE); it may be used in IS2 only.
- Paper 53's DOI is pending (conference 20 Nov 2026); until the DOI exists it is described as "accepted".
- arXiv:2605.24297 was withdrawn on 5 Nov 2026 and is not used as evidence.
- No claim of university IP, deployment, user benefit or publication without the documents.
