# Evidence-gap matrix — 4 November 2026

Statuses: VERIFIED, PARTIAL, MISSING, NOT_APPLICABLE_WITH_REASON, CONTRADICTED.

| item_id | claim_or_requirement | status | evidence_path | evidence_version | limitation | next_action | dependency | owner_decision_needed |
|---|---|---|---|---|---|---|---|---|
| G-01 | Patent-central research question on an established benchmark | VERIFIED | `PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md` | ff603bb | Closed 8-option task | — | — | no |
| G-02 | Protocol and selections frozen before test | VERIFIED | `par4pc-freeze.json` (sha256 `4600ea36…`) | commit ff603bb | Lexical baseline previously exposed on test | — | — | no |
| G-03 | Primary retrieval result with paired uncertainty | VERIFIED | `par4pc-test-results.json` | this round | Proxy labels; possible PatEmbed contamination | — | — | no |
| G-03b | Replication on a second task | VERIFIED (mixed: not replicated) | `pi4pc-test-results.json`, freeze `1665075` | this round | Same dataset family (PANORAMA) | Optional: a benchmark outside PANORAMA | — | no |
| G-04 | Negative/mixed findings reported | VERIFIED | README, manuscript §7.A | this round | — | — | — | no |
| G-05 | Adaptive vs well-tuned fixed policy under cost | PARTIAL | C4 and the cascade curve | this round | The cascade beats only the hybrid on cost; it does not beat dense alone; a single τ rule | Exploratory: cascade→dense variant on validation only | — | no |
| G-06 | Ablations (query formulation, encoder family, fusion) | VERIFIED | `par4pc-test-results.json` (all 8 methods) | this round | Single run per deterministic config | — | — | no |
| G-07 | Robustness/subgroups | PARTIAL | `par4pc-exploratory-subgroups.json` | this round | Exploratory, not preregistered | Error taxonomy over text features | — | no |
| G-08 | Dataset/qrels provenance, rights, leakage | VERIFIED | `DATASET_QRELS_PROVENANCE.json` | this round | Family-level overlap not checked (no family IDs in PAR4PC) | Optional family check through an external family source | Data with family IDs | no |
| G-09 | Track B device-patent known-link recovery | PARTIAL | manuscript §7.1–7.5 audits | historical | 3 effective groups; `NOT_ESTIMABLE` | Keep descriptive; no confirmatory claim | Larger rights-cleared cohort | no |
| G-10 | Dossier generation field fidelity | PARTIAL | `canary-content-audit.json` | this round | 3 cases / 9 trivial fields; no patent content | Larger source-grounded set if useful | Paid budget (USD 10 authorized) | no |
| G-11 | Local vs API generation comparison (O3) | PARTIAL | earlier local Qwen receipts plus canary | mixed heads | Not matched on the same pack in this round | Run local Qwen3-8B on the same FDA pack on dr-train | GPU | no |
| G-12 | Reproducibility: code, commands, hashes | VERIFIED | `EXPERIMENT_REGISTRY.json` | this round | Same-author rerun only | Clean-clone rerun | — | no |
| G-13 | Official WPI Guide for Authors checked | MISSING | `READINESS.md` | 2026-11-04 | HTTP 403 again; aims and scope confirmed via the Elsevier page | Owner opens the guide in a browser before submission | Access | yes (manual check) |
| G-14 | Declarations (AI use, data, funding, CRediT, competing interests) | PARTIAL | manuscript Declarations | draft | Author decisions pending | Owner fills | Owner | yes |
| G-15 | License for code release | MISSING | GOAL §9 | — | No root LICENSE | Owner chooses a license | Owner | yes |
| G-16 | Independent user/expert/business validation | NOT_APPLICABLE_WITH_REASON | GOAL §1.4 | — | Solo study; future work | — | — | no |
| G-17 | Bridge benchmark | NOT_APPLICABLE_WITH_REASON | `BRIDGE_RIGHTS_COHORT.md` | — | Rights/cohort blocked; not used | — | Data owner grant | no |
