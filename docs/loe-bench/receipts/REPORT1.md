# REPORT1 | Thai IS2 full-history report draft

**Disposition: DRAFT_READY_FOR_CRITIQUE.** GPT-6.2 Sol high served as the owner-approved substitute drafter. This receipt holds the executor handoff and memory for REPORT1. The main planner owns the lane handoff, memory, final audit and typesetting.

## Checkout and deliverables

- Fetched `origin/research/loe-bench` and verified that `8d470b87` is an ancestor. Cut `loe/REPORT1` from the fetched `cd590661`. The dedicated worktree was clean before the branch cut. The worktree inventory showed no other REPORT1 checkout, the remote task branch did not exist at intake, and neither deliverable existed at the base.
- [Thai report](../../writing/is2/report/REPORT-TH.md) includes the cover, executive summary, reading guide, dated chronology, the four research phases, product, resource accounting, limitations and next work, glossary, decision log, evidence record list and IEEE-style references. The chronology separates earlier and later project records and distinguishes development, exploratory and confirmatory results.
- [Figure requests](../../writing/is2/report/FIGURE-REQUESTS.md) contains twelve briefs with report anchors, a purpose, aggregate data and source paths, and draft Thai captions. The existing Thai effects figure and product screenshots are identified for reuse.
- The draft records C′ H1 PASS, H2 FAIL and H3 descriptive. Track A freeze and outcomes, C9 predictions and outcomes, prior-method results and the C′ AUC supplement are pending. The Thai report and captions are the assigned IS2 deliverables. This English receipt records their status for the project.

## Sources inspected

| Scope | Primary records reviewed |
|---|---|
| Governance and history | Root `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, `INDEX-PLAN.md`; lane [plan](../PLAN.md), [handoff](../HANDOFF.md), [memory](../MEMORY.md); [owner decision register](../../maintenance/OWNER-DECISIONS-20261122.md); [IS2 slide brief](../../writing/is2/mwd/SLIDES-PREP.md), [Thai and English short-paper materials](../../writing/is2/mwd/); RA Pharma historical record and research handoff. Applied the repository documentation skill and the local Thai natural-writing skill. |
| IS1 / Paper 53 and B53 | Original-source reconciliation in [S0](../../evidence-scope/00-organization.md), B53 stage 1 and 2 aggregate receipts, B53.0, PatenTEB correction and the comparability audit. The [conference program](https://isai-nlp2026.aiat.or.th/program) confirms the Paper 53 listing. The dispatch supplies the historical GEPA direction and the [method paper](https://arxiv.org/abs/2507.19457) supplies the definition. Original per-run material was unavailable in the source reconciliation. |
| Retrieval and acquisition | Paper 1 aggregate table, BridgeRet grid and RunPod ledger, AM-7 Stage 2a tables and protocol, DAPFAM pre-check ledger, G03 amendments and decision memo, P1-T04/T05 and P2-T02/T04 receipts. |
| Workbench and RA Pharma | G01/G02 status, S-series board, S3 and Option A aggregates, S4 verification, RA Pharma plan, Thai inquiry audit, architecture and feasibility handoffs, commercial observation, D36/D38 reviews, B1E Planner review and D39 disposition. |
| LOE-Bench | [Preregistration](../PREREGISTRATION.md), update sheets, GATE, FREEZE, SCORE and SCORELLM aggregates, C2/C3b/C4b, C9 protocol and training receipts, TRACKA-CORE and [prior-arm specification](../PRIOR-ARMS-SPEC.md). The live OSF DOI and registration page were unavailable through web fetch. Registration verification in the draft rests on the repository's accepted records. |
| Product and cost | PRD1, UIBUILD, EVP, BridgeRet and R1/R2 execution and billing records, and the D40 RunPod envelope and handoff. |

Each numeric prose block or table has an HTML source comment. Its path resolves to tracked repository evidence. Reference indices and section numbering are editorial. The report keeps historical DAPFAM denominators separate, identifies the repeated exposure to development VAL, preserves the corrected A1 mask interpretation and uses only published aggregate C′ findings.

## Verification and open items

- **PASS** Markdown evidence and link audit. All 122 source comments resolve to 71 tracked paths. Local links and report anchors resolve. Numeric prose blocks and tables carry source comments. The Thai report has no em dash, middle dot or flagged padding verbs. The figure brief count is 12.
- **PASS** Document count. PyThaiNLP 5.4.0 `newmm` yields **12,044 tokens** in the Thai report, including tables, glossary and references. Strip HTML tags, comments and link targets, set `keep_whitespace=False`, and count tokens containing a Unicode alphanumeric character. Treat page count as pending typesetting.
- **Two `[ต้องตรวจสอบ]` entries.** The first is the reconciled all-activity historical R2 total. Individual posted and estimated charges remain in the report with their basis. The second is the full staff-time and local compute cost. Neither is inferred from billed GPU and API items.
- **NOT_RUN** Code suite, figure rendering and PDF layout. This card changes Markdown only. It used the aggregate evidence already in Git and did not access protected TEST, sealed judgments or per-row C′ material.
- PyThaiNLP and its dependency were installed to a temporary directory for token counting. PyThaiNLP 5.4.0 (Apache-2.0 code, CC0-1.0 data/models) wheel SHA-256 `9239753df877202da1a50dd2842d9569eff764034f31f20222b3df4def5df193`. tzdata 2026.6 (Apache-2.0 wheel metadata) SHA-256 `0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec`. The packages and cache stay outside Git.

## Next action

Hand `loe/REPORT1` to the GPT-6.2 Astra high co-planner for critique. Prioritize evidence scope, numerical traceability, completeness of the historical account and Thai readability. Claude then audits, reconciles the handoff and memory, and designs the figures and final PDF. The executor does not integrate this branch.
