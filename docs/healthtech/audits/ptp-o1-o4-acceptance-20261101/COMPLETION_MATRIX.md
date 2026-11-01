# Patent-to-Pilot O1-O4 completion matrix — current head

Candidate: `891f3b3`  
Runtime-equivalent candidate: `ab7ad348ff2fb3ec8e02a52a49ccddd1657504fd`  
Reviewed implementation candidate: `80da253969f7973cc630ce03ac83da9900f16628`

This matrix is an audit aid for the existing goal. It does not convert prior
receipts into current reruns, turn unknowns into zeros, or promote descriptive
evidence into scientific or commercial validation.

The current-head delta after `ab7ad34` is documentation and audit-only. The
O4 offline controller rerun and the matched fixed/adaptive frontier are bound
to the current candidate in
`docs/healthtech/audits/ht-o4-offline-current-head-20261101/CHECKPOINT.json`
and `docs/healthtech/audits/ht-o4-matched-offline-current-head-20261101/CHECKPOINT.json`.

| Requirement | Status | Authoritative evidence | Boundary / missing proof |
|---|---|---|---|
| UI -> HTTP jobs, source inspection, history, edit/reopen, export | `COMPLETE_CURRENT_HEAD_ENGINEERING` | `npm run test:integration:http`; frontend `74/74`; [`ht-o1-local-http-20261031`](../ht-o1-local-http-20261031/README.md) | Browser acceptance uses the local product harness; no paid-provider claim |
| PatEmbed-base + multilingual-e5-base remote encoding and Windows import | `COMPLETE_PRIOR_RUNTIME / CURRENT_CONTRACTS_PASS` | [`ht-research-product-20261031`](../ht-research-product-20261031/README.md); current focused O2 contracts exit `0` | Full remote encoding was not rerun after the runtime window; existing manifests remain the source of truth |
| Resumable shards, hashes, dimensions and shared retrieval engine | `COMPLETE_PRIOR_RUNTIME` | O2 verification receipt, bundle manifests and six device dossier-engine runs | No new remote allocation or model download in current continuation |
| Local Qwen3-8B frozen-evidence generation | `COMPLETE_PRIOR_RECEIPT` | [`generation-canary.json`](../ht-o3-local-model-preflight-20261031/generation-canary.json) | 3/3 schema-valid prior receipt; current checkout does not claim a new local inference run |
| API Qwen3-32B comparison | `BLOCKED_LOCAL` | [`o3-gate.json`](../ht-research-product-20261031/o3-gate.json) | Missing complete R1 journal/completeness anchor, current credit, fresh route/pricing binding and outbound prompt rights |
| Canonical budget ledger and duplicate-ledger guard | `COMPLETE_ENGINEERING / LIVE_BINDING_PENDING` | R1 continuation audit and current O3 contract suite | Real journal path and writer-quiescence evidence are not present in this candidate |
| USD100/V100 resource boundary and no-reset rule | `RECORDED_AUTHORIZATION / LIVE_CREDIT_PENDING` | `GOAL.md`, `PLAN.md`, benchmark expansion pack, current-head checkpoint | USD100 is a cumulative ceiling, not proof of available credit; no spend, top-up or ledger reset is claimed |
| Candidate vs disclosed-link validation | `COMPLETE_ENGINEERING` | O3 generation payload tests and source-backed provenance receipts | Does not create semantic gold or legal relevance |
| Three real device cases through product path | `COMPLETE_PRIOR_REAL_CASE_ENGINEERING` | [`ht-o4-remote-http-generation-browser-20261031`](../ht-o4-remote-http-generation-browser-20261031/REPORT.md) | Prior MitraClip/Tendyne/TriClip receipt; current-head synthetic route is separate |
| Adaptive vs fixed/multi-query/heuristic scientific comparison | `PARTIAL / MATCHED_OFFLINE_DESCRIPTIVE` | [`ht-o4-matched-offline-current-head-20261101`](../ht-o4-matched-offline-current-head-20261101/README.md); [`COMPUTATIONAL_STUDY_PROTOCOL_20261101_TH_EN.md`](../../research/COMPUTATIONAL_STUDY_PROTOCOL_20261101_TH_EN.md) | Abbott B0b is strongest observed condition and B4 ties B1/B3; only two exact-patent groups, no final holdout, product-disclosure labels are non-semantic, and no powered confirmatory claim |
| Group uncertainty and failure analysis | `PASS_DESCRIPTIVE_NOT_ESTIMABLE` | [`luna-long-run-20261029-m12-group-uncertainty-20261029`](../luna-long-run-20261029-m12-group-uncertainty-20261029/README.md) | Three effective groups are below predeclared threshold five |
| Business value evidence | `OPERATIONAL_POTENTIAL_ONLY` | Manuscript business-value section and three-case machine receipts | No external user validation, human-time measurement, WTP, revenue or ROI |
| Solo pilot protocol/task set/rubric/result form/consent | `COMPLETE_FOR_FUTURE_USE` | `docs/healthtech/business/` package and owner one-time input | No participant route is active in this round |
| WPI venue fit and submission preparation | `PASS_SCOPE_CHECKED / GUIDE_RECHECK_REQUIRED` | [`wpi-venue-check-20261101`](../wpi-venue-check-20261101/README.md) | Journal-specific author page returned HTTP 403 locally; owner must recheck before submission |
| Reproducible artifacts and rights boundary | `PARTIAL_READY_FOR_OWNER_REVIEW` | Benchmark binding, private-artifact receipts, rights manifests and manuscript supplement | Restricted payloads/private journals remain outside Git; unresolved dataset rights remain excluded |
| Tested commit / push / PR / merge lifecycle | `COMPLETE_TESTED_COMMIT / PUSH_MERGE_PENDING` | Current branch `891f3b3`; targeted controller `5/5`, matched frontier zero failed devices, prior full Python/frontend/HTTP/benchmark receipts | Push, PR review and main merge remain intentionally pending owner review and external gates |

## Owner-only external gates

The shortest owner action is to provide or expose through the permitted channel:

1. the real current R1 canonical journal or sanitized all-attempt export;
2. the current authorized account-credit/billing snapshot without credentials;
3. confirmation of the rights-cleared outbound prompt manifest and current route/pricing binding, if the paid comparison is still desired; and
4. a journal-author-page review plus final author/declaration details before submission.

No existing USD8 authorization is being requested again. Until the first three
items are evidenced, the paid API branch remains closed and offline work remains
valid independently.
