# S0 · Organization and evidence handoff

**COMPLETE · Documentation deliverable · 25 November 2026.** Start at the [master plan](MASTER-PLAN.md). The incoming commit was `2abc072d` on main. The active program is S0–S5. Identifiers from P0–P5, G01–G08 and earlier studies retain their original meanings.

| Task | Disposition | Acceptance evidence |
|---|---|---|
| S0-T01 · Reconcile prior results | COMPLETE | [Historical task board](../tracking/owner-note-22112026/PHASE_BOARD.md), [P2 matched result](../tracking/owner-note-22112026/receipts/P2-T04_results.md) and the source locators below |
| S0-T02 · Freeze the next questions and data design | COMPLETE | [Prospective freeze](FREEZE.md). New assets and example assignments acquire byte-level identities in S1 |
| S0-T03 · Define parallel execution | COMPLETE | [Master dispatch board](MASTER-PLAN.md) and six individual phase sheets, with disjoint lane responsibilities and independent exits |
| S0-T04 · Reconcile the working entry points | COMPLETE | [README](../../README.md), [documentation map](../README.md), [agent rules](../../AGENTS.md), [handoff](../../HANDOFF.md), [evidence index](../../INDEX-PLAN.md) and [decision register](../maintenance/OWNER-DECISIONS-20261122.md) |
| S0-T05 · Hand back a verifiable package | COMPLETE | Review the committed README assets, Markdown links, phase/task identities, tracker and publication state. The next goal prompt is in the master plan |

## Original-source corrections

Two owner-provided PDFs anchor the IS1 to IS2 transition. Preserve the names, file identities and PDF-page locators below so another account can match its own copies. The repository does not distribute the attachments.

| Source | SHA-256 | Exact locator and permitted interpretation |
|---|---|---|
| `paper53_ieee_express.pdf` | `09d580402a49739baedb2281be16ba0a275a1c5ecdb711dfb21c93c8aba3ddbe` | PDF p. 4, Table II, and p. 5, Fig. 3. Of 692 OUT-positive queries, 257 frozen top-100 pools contained at least one known OUT-relevant family (37.1%). Generic strict OUT nDCG@100 was 0.0626; Patent-aware was 0.0634. These are the authors' reported results. Original-run records were unavailable for independent verification (p. 6). |
| `IS1_ฉบับแก้ไข.pdf` | `9614946d6dd6f4cd2e849e1e9872cc1f0e108eecbe90d2f0316f263e9ae85e14` | PDF pp. 9–10 and 45–46, Table 3, Fig. 4 and conclusion. In a separate post-hoc first-stage check with 725 queries, PatEmbed exposure was 40.8% at depth 100 and 77.2% at 1,000. IS2 proposes reranking deeper pools with four instructions and measuring reading depth to the first known OUT hit. |

The B53 reimplementation has its own 905-query cohort. Keep all three denominators attached to their respective tasks. A bibliographic DOI remains to be verified independently.

## Inherited work and gaps

| Earlier phase | Carry forward | Still open or limited |
|---|---|---|
| P0 · 5/7 complete | Local tracker and control contracts | AFFiNE synchronization incomplete |
| P1 · 6/6 complete | Frozen A3r1 CONTINUE, VAL +0.0213 versus the C0 reference | Exploratory after repeated VAL exposure |
| P2 · 4/7 complete | Complete-content controls and P2-T04 NO_GAIN. ALL R@200 0.44372 vs 0.44998 | Historical P2-T05 confirmation remains NOT_RUN |
| P3 · 1/5 complete, one partial | Thai data contract and law-grouped packet summary | No annex/table DEV examples; no independent semantic interpretation study |
| P4 · 3/5 complete, one partial | Search, Compare, Inspect, provider modes, structural acquisition and selective-revision evidence | Corpus removal and observed clean installation/user tasks open |
| P5 · 1/5 complete | Single design-stage manuscript | Submission, replication and real deployment unverified |

## Reorganization policy

Working entry points refer forward to S0–S5. Dated experiments, archived account handoffs, original writing and external owner inputs remain identifiable and reproducible. The [evidence index](../../INDEX-PLAN.md) maps those artifacts to their purposes. The governance, literature and architecture indexes distinguish past claims from the new work. The scope of this change is planning, navigation and branding. S1–S5 have no new execution receipts at this checkpoint.

**Documentation checks:** six phase sheets, 29 task identifiers and 98 local links/anchors across the root README and plan package were checked. Both SVG files parsed. The three inherited Git receipt identities in the freeze matched the reference checkout. The documentation package did not exercise Workbench or compute a new research score. README structure was informed by the short start path in [uv](https://github.com/astral-sh/uv), example-first usage in [ripgrep](https://github.com/BurntSushi/ripgrep) and local project navigation in [LightRAG](https://github.com/HKUDS/LightRAG).

**Resume:** use the bounded S1/S2 goal in the [master plan](MASTER-PLAN.md#prompt-for-the-next-goal). Success for this phase is a readable, internally linked plan and an unambiguous handoff.
