# P0–P2 gap audit: HealthTech Solution Scout

**Date:** 16 November 2026 · **Branch:** `claude/prod-p0-evidence-bedc49` · **Base:** `1819533`
**Measured against:** owner product plan section 9 (MVP packages) and section 10 (offline scenarios). The plan is owner-local and untracked, so this audit quotes only the acceptance items it checks.

Status words:
- **EXISTS**: the code does it and a test proves it.
- **PARTIAL**: some of it is there, or it works without a test that proves the acceptance item.
- **MISSING**: no code for it.

"Before" means commit `1819533`. "After" means this branch after the D3 commit `f375899`. Everything below was run during this audit; no old receipt was reused.

## 1. Test runs (exact counts)

Command: `python -m pytest -p no:cacheprovider tests/<file>.py` (Python 3.12.10, pytest 8.4.2), and `npm test` in `frontend/healthtech-web` (Node 24.19.0).

| Suite | Before | After |
|---|---|---|
| `test_core` | 6 passed | 6 passed |
| `test_healthtech` | 27 passed | 27 passed |
| `test_healthtech_http` | 7 passed | 7 passed |
| `test_healthtech_scout` | 7 passed | 7 passed |
| `test_healthtech_scout_http` | 6 passed | 6 passed |
| `test_scout_frozen` | 7 passed | 7 passed |
| `test_healthtech_history_migration` | 4 passed | 4 passed |
| `test_healthtech_source_acquisition` | 8 passed | 8 passed |
| `test_healthtech_source_authorization` | 9 passed | 9 passed |
| `test_healthtech_runtime_export` | 2 passed | 2 passed |
| `test_healthtech_integration_contract` | 4 passed | 4 passed |
| `test_healthtech_content_audit` | 3 passed | 3 passed |
| `test_healthtech_repairs` | 37 passed, 1 skipped | 37 passed, 1 skipped |
| `test_healthtech_vector_http` | 2 passed | 2 passed |
| `test_healthtech_cook` | 11 passed | 11 passed |
| `test_healthtech_philips_dossiers` | 6 passed | 6 passed |
| `test_healthtech_multicompany` | 5 passed | 5 passed |
| `test_healthtech_philips_cohort` | 4 passed | 4 passed |
| **Product Python subtotal** | **155 passed, 1 skipped** | **155 passed, 1 skipped** |
| `test_healthtech_p0_scenarios` (new, D2) | 17 passed, **24 failed**, 1 xfailed | **41 passed**, 1 xfailed |
| Frontend `npm test` (unit) | 83 tests: 82 pass, 1 skipped | 83 tests: 82 pass, 1 skipped |

The skip in `test_healthtech_repairs` (line 274) needs a pinned local tokenizer that is not on this machine. The full-repository run is in section 6.

## 2. P0 Evidence foundation

Acceptance in the plan: three authored public/fictional sample projects each produce a JSON and an MD dossier, with no invented product association and exact source provenance. Replaying the same inputs gives the same IDs; only declared timestamp fields may differ.

| P0 item | Before | After | Where (code + test) |
|---|---|---|---|
| Typed records + synthetic demo | EXISTS | EXISTS | `healthtech/contracts.py:108` `SourcePayload`, `:123` `EvidenceItem`, `:156` `PatentCandidate`, `:208` `DossierVersion`; `examples/healthtech/synthetic-device/`; `test_healthtech.py::test_end_to_end_is_offline_bounded_and_does_not_promote_candidates` |
| Public named-device intake normalization (with ambiguity) | **MISSING**. `DeviceQuery` (`contracts.py:44`) takes a raw and a canonical ID as given; there is no name normalization, no ambiguity state and no `unresolved_intake`. | EXISTS | `healthtech/foundation.py:80` `resolve_device_intake` (statuses `resolved` / `unresolved_intake` / `not_found`; manufacturer copied, never guessed); tests S01 (7 cases) |
| Source version/hash capture | EXISTS | EXISTS | Hash bound at build: `contracts.py:117`; evidence re-check `provenance.py:9` `check_evidence`; byte snapshots `evaluation/healthtech/source_acquisition.py`; tests `test_healthtech.py::test_runtime_rejects_leakage_and_false_source_claims[bad_hash]`, `test_healthtech_source_acquisition.py` (8) |
| Same snapshot gives the same record (replay) | **PARTIAL (bug)**. `sources.source_payload` stamped wall-clock `created_at`, so rebuilding the same snapshot changed `input_hash`. The public cohort adapters (Abbott, Cook, Philips) use this helper. | EXISTS | `healthtech/sources.py:11` (`created_at` defaults to midnight UTC of `source_date`; it can be passed explicitly); test `test_replay_same_input_gives_same_ids_and_input_hash` |
| Patent-ID resolution | EXISTS (document level) | EXISTS | `contracts.py:22` `canonical_patent_id` (keeps jurisdiction, leading zeros and kind; unknown syntax fails closed); tests S03 (5 resolve + 3 reject cases), `test_healthtech.py::test_normalization_preserves_kind_leading_zeros_and_jurisdiction` |
| Patent family grouping (`PatentFamily`) | **MISSING** in the product path. Family grouping existed only in the evaluator (`evaluation/healthtech/retrieval.py`). | EXISTS | `foundation.py:215` `group_candidates_by_family` (only with a sourced family record; a document claimed by two families fails closed); test S03 family |
| Allowed source snapshot storage | EXISTS | EXISTS | Rights-gated, hash-verified staging in `evaluation/healthtech/source_acquisition.py`; rights matrix `healthtech/rights.py`; history `healthtech/history.py:49` `save_version`; tests `test_healthtech_source_acquisition.py`, `test_healthtech_source_authorization.py` (9) |
| Candidate-link types | **PARTIAL**. `PatentCandidate.association_status` has two values only (`retrieved_candidate`, `disclosed_link`, `contracts.py:163`). There was no `company_name_match` and no `reviewer_confirmed` link. | EXISTS (helper level) | `foundation.py` `CandidateLink` (`retrieved_candidate`, `company_name_match`, `source_disclosed`, `reviewer_confirmed`; each type needs its basis), `:154` `company_link`, `:170` `candidate_links`; tests S02. The stored `PatentCandidate` schema is unchanged on purpose (the frontend pins it). |
| Source span viewer | EXISTS | EXISTS | Backend `history.py:165` `source_view`; frontend locator checks `frontend/healthtech-web/tests/unit/locator.test.mjs` (5 tests); evidence "inspect" links in `app/src/ui/screens.js` (`evidenceScreen`) |
| 3 sample projects → JSON + MD, no invented association | **PARTIAL**. Only one authored synthetic project was in `examples/` (the Abbott, Cook and Philips cohorts are real-source and need local snapshots). | EXISTS | Fixture `tests/fixtures/healthtech_scenarios/scenarios.json` (projects alpha, beta, gamma); test `test_three_authored_projects_export_json_and_md_current[alpha/beta/gamma]` (all candidates stay `retrieved_candidate`, every evidence item re-checks, MD and JSON round-trip, 0 provider calls) |
| Deterministic replay IDs | **PARTIAL**. With a caller-given `run_id` the step and dossier IDs repeat, but the HTTP layer uses `uuid4` job IDs (`healthtech/http.py:316`) and there was no content-derived run ID or replay comparison. | EXISTS (engine level) | `foundation.py:548` `replay_run_id`, `:556` `replay_fingerprint`; declared volatile fields: `created_at`, `started_at`, `ended_at`, `elapsed_seconds`; tests `test_replay_*`. The HTTP job ID is still random (idempotency key covers retries). |

## 3. P1 Search workbench

| P1 item | Status (after) | Evidence |
|---|---|---|
| Pinned lexical (+ optional dense) candidates | EXISTS | `engine.py:90` `run_dossier` (FTS5 lexical; optional precomputed dense provider); `test_healthtech.py`, `test_healthtech_vector_http.py` |
| Optional bounded agent tool interface | PARTIAL | Fixed policies HT-B0a…HT-B3 and a provider gate in `http.py`; no agent action interface in this product path |
| Click every candidate to the exact source | EXISTS | `source_view` + frontend source route; `test_healthtech_http.py::test_local_http_job_is_idempotent_and_supports_history_source_and_exports` |
| Visible search actions | EXISTS | `AcquisitionEvent` per action (`contracts.py`), exported as `acquisition_events.jsonl`; frontend `validateRunArtifacts` test in `backend-contract.test.mjs` |
| Filter by family / domain / cutoff | PARTIAL | Frontend filter is free text over ID, source and status (`screens.js`, `evidenceScreen`); grouping by family is now available as `group_candidates_by_family` but not shown in the UI; no domain or cutoff filter; Scout has own-field/other-field lanes |
| Missing dates flagged | PARTIAL → helper EXISTS | `foundation.py:315` `date_gaps` (missing filing/publication date, cutoff unknown, after cutoff; nothing imputed); test S05. Not yet wired into `run_dossier`, because `PatentInput` has no bibliographic date fields. |
| Capped cost | EXISTS | `AcquisitionBudget` hard caps; `test_healthtech.py::test_zero_budget_dispatches_no_search`, `::test_returned_candidate_cap_is_hard_even_across_repeated_queries`; paid cost is fixed at 0 in this path |
| No gold accessible | EXISTS | `engine.py:80` rejects evaluator-only sources; `DossierInput` forbids extra fields; `test_healthtech.py::test_runtime_rejects_leakage_and_false_source_claims` |
| Tool/model timeout handled | **MISSING → EXISTS** | Before: a `TimeoutError` from the search or vector tool crashed `run_dossier` (only `ValueError`/`RuntimeError` were caught). After: it is recorded once as `vector_search_timeout` / `local_search_timeout`, the run is marked `run_failure`, it is not retried, and lexical results are kept (`engine.py:146`, `:163`); test S10 |

## 4. P2 Evidence matrix / Dossier

| P2 item | Status (after) | Evidence |
|---|---|---|
| Source-linked per-feature table | PARTIAL | Frontend feature links are user-authored overlay data (`screens.js`, `featureLinks`); there is no backend `TechnologyFeature` record |
| Inference / unknown labels | EXISTS | `EvidenceItem` kinds and verification states (`contracts.py:123`; inferences cannot be promoted); `test_healthtech.py::test_literal_span_and_field_checks_reject_semantic_promotion_and_type_coercion`; frontend `scout.test.mjs` "keeps facts, inference and unresolved apart" |
| Export (MD + JSON) | EXISTS | `engine.py:301` `export_markdown`, `:355` `serialize_dossier`; frontend `export.test.mjs` (5) |
| Reviewer comment | PARTIAL | Frontend notes (`overlay-store.test.mjs`); backend `user_edits` (`history.py:145` `append_user_edits`). There is no typed `ReviewerDecision` per evidence item in the dossier path (`product/contracts.py` has one, unused here) |
| Source removed → dependent evidence withdrawn/unknown; nothing unrelated changes | **MISSING → EXISTS** | `foundation.py:390` `withdraw_source`: evidence from the source becomes `unresolved`, disclosed links that depended on it go back to `retrieved_candidate`, the source payload is kept, and a new history version is written. Tests S07 and M2 (withdrawal changes only descendants; withdrawing a source with no descendants changes no evidence or link) |
| Conflicting sources shown, not resolved by the system | MISSING → EXISTS | `foundation.py:355` `detect_field_conflicts` (no winner chosen); test S06 |
| No numeric values inferred from absence | PARTIAL → helper EXISTS | Field checks are type-exact (`provenance.py`); `foundation.py:519` `quantity_mentions` keeps the value as written and flags missing or ambiguous units (F, C, M, decimal comma); test S09 |
| Scoped revision after a constraint change | PARTIAL | `foundation.py:443` `carry_forward` (keeps user edits and history chain) and `:479` `dossier_diff` (added/removed/changed/unchanged by ID); test S08. **Still a gap:** tightening the cutoff rejects the whole input instead of blocking only the affected routes (strict `xfail` test `test_s08_tightened_cutoff_blocks_only_dependent_routes`) |

## 5. P3 and P4 (brief)

- **P3 Adaptive Lab:** MISSING in the product. There is no harness registry, patch proposal or rollback in `healthtech/`. Research harness work is on another branch (`claude/paper2-harness-0d504a`, not merged).
- **P4 Production hardening:** MISSING, except local pieces: atomic file history with version conflict checks (`history.py`, `test_healthtech_http.py::test_provider_gate_and_version_conflict_are_fail_closed`), a loopback-only HTTP server with CORS checks, and rights gating. There is no authentication, no Postgres or migrations, no multi-user scoping, no backups and no rate limiting.

## 6. Scenario suite (D2) and what changed (D3)

File: `tests/test_healthtech_p0_scenarios.py` with the fixture `tests/fixtures/healthtech_scenarios/scenarios.json`. All data is fictional (patent numbers have leading zeros, URIs are `urn:synthetic:`). The oracles are IDs, values, offsets, sets and counts; no LLM is used.

| # | Scenario | Before | After |
|---|---|---|---|
| — | 3 sample projects → JSON + MD | pass (3) | pass (3) |
| S01 | Ambiguous device names | fail (7) | pass (7) |
| S02 | Manufacturer ≠ assignee | 1 pass, 5 fail | pass (6) |
| S03 | Patent family duplicates | 9 pass, 1 fail | pass (10) |
| S04 | Only an archived regulatory source | 1 pass, 1 fail | pass (2) |
| S05 | Missing filing date | fail (1) | pass (1) |
| S06 | Conflicting sources | 1 pass, 1 fail | pass (2) |
| S07 | Source withdrawal | fail (2) | pass (2) |
| S08 | User constraint change | fail (1), xfail (1) | pass (1), **xfail (1, gap kept)** |
| S09 | Numeric unit ambiguity | 1 pass, 1 fail | pass (2) |
| S10 | Model/tool timeout | fail (1) | pass (1) |
| M1 | Irrelevant document added → accepted links unchanged | pass (1) | pass (1) |
| M2 | Withdrawal invalidates only descendants | fail (1) | pass (1) |
| R | Replay IDs / fingerprint | fail (2) | pass (2) |
| | **Total** | **17 pass, 24 fail, 1 xfail** | **41 pass, 1 xfail** |

D3 code changes (stored schemas for `DossierVersion`, `RunManifest` and `AcquisitionEvent` are unchanged, and the frontend schema-equality test still passes):

1. New `src/patent_to_pilot/healthtech/foundation.py` (pure helpers, no I/O).
2. `engine.py`: `TimeoutError` from the lexical or vector search is recorded once and is not retried.
3. `sources.py`: deterministic `created_at` in `source_payload`.

Full-repository run after D3 (`python -m pytest -p no:cacheprovider -o addopts="" -q tests`, 212 s): **2274 passed, 8 failed, 6 skipped, 1 xfailed**. All 8 failures are research tests, not product tests: `test_sacr_r2_smoke_supervisor.py` (4) and `test_sacr_r3_smoke_supervisor.py` (4), `test_budget_cannot_use_nonfinite_inflated_or_erased_cost`. Both files give the same 4 failed / 5–6 passed against an export of the unchanged base `src/` (`git archive 1819533 src`). So they were already failing and are not caused by this branch. Leaving out the new scenario file, the rest of the repository has the same result as before.

## 7. Still open (needs a decision or later work)

1. **Route-level blocking on a cutoff change** (plan J06): today the whole input is rejected. This changes engine semantics, so it needs an owner decision. A strict xfail test records it.
2. **Wiring the helpers into the HTTP API and the UI:** intake disambiguation screen, family rows, source-state banners, withdrawal button, date flags, conflict panel. The helpers return plain typed records ready for this.
3. **Bibliographic dates on `PatentInput`:** needed before `date_gaps` can run inside `run_dossier`. Real dates need sourced patent metadata, which means a download, which needs owner approval.
4. **Typed `ReviewerDecision` per evidence item** for `reviewer_confirmed` links (P2 reviewer comment). `CandidateLink` already requires the decision ID.
5. **Public named-device intake on real records:** the resolver works on any `DeviceRecordRef` list. Feeding it openFDA records needs approved source snapshots.
6. P3 and P4 are not started in this path.
