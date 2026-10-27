# Historical evidence and cleanup

HealthTech became the governing track on 27 October 2026. Earlier Organization-Adaptive R&D, G10/G13 and Transfer-or-Retest documents/results retain their dated scientific meanings. The new root GOAL/PLAN do not retroactively validate those methods or convert their synthetic engineering cases into HealthTech benchmark results.

The pre-migration public commit is [70805d3](https://github.com/siriponsri/patent-to-pilot/tree/70805d30599dda723146390d39308c0faeb61ee7). It was verified as origin/main before recoverable cleanup. Older frozen methodology, run receipts, provider bookkeeping and compatibility code remain at their existing paths. Some handoff links intentionally reference the older snapshot and may point to retired working-tree documents; use the recovery links below.

## Removed active documents

| Retired path | Recovery |
|---|---|
| `docs/product/CLAUDE_ENTREPRENEUR_INVESTOR_V2_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/CLAUDE_ENTREPRENEUR_INVESTOR_V2_TH.md) |
| `docs/product/CLAUDE_MINIMAL_FORMAL_DRAFT_20261027_V1_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/CLAUDE_MINIMAL_FORMAL_DRAFT_20261027_V1_TH.md) |
| `docs/product/CLAUDE_UI_HANDOFF_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/CLAUDE_UI_HANDOFF_TH.md) |
| `docs/product/REQUIREMENTS_DECISIONS_20261027_V1_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/REQUIREMENTS_DECISIONS_20261027_V1_TH.md) |
| `docs/product/REQUIREMENTS_DECISIONS_20261027_V2_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/REQUIREMENTS_DECISIONS_20261027_V2_TH.md) |
| `docs/product/REQUIREMENTS_DECISIONS_20261027_V3_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/REQUIREMENTS_DECISIONS_20261027_V3_TH.md) |
| `docs/product/SYNTHETIC_DATA_V2_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/product/SYNTHETIC_DATA_V2_TH.md) |
| `docs/research/TRANSFER_OR_RETEST_PROPOSAL_20261027_V3_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/research/TRANSFER_OR_RETEST_PROPOSAL_20261027_V3_TH.md) |
| `docs/research/JOURNAL_EVIDENCE_PLAN_20261027_V2_TH.md` | [Original at verified base](https://github.com/siriponsri/patent-to-pilot/blob/70805d30599dda723146390d39308c0faeb61ee7/docs/research/JOURNAL_EVIDENCE_PLAN_20261027_V2_TH.md) |

## Download cleanup

Removed the byte/hash-verified local PLS atazanavir and ritonavir CSV reading copies. The pinned Git LFS pointers matched the acquisition receipt, and HEAD requests to both content URLs returned 200 with matching lengths before deletion. These are reproducible downloads, not unique owner annotations. Source metadata and the original acquisition receipts remain. Recovery must verify the same SHA-256 after download; an upstream URL is not a guarantee of perpetual availability.

Logical removed working-tree bytes: **259,206,157**. Observed volume free-space increase at deletion: **259,223,552 bytes**. The latter includes concurrent system activity. Git history objects were not pruned; tracked-file deletion alone does not reclaim their object storage. Details and exact recovery URLs: [cleanup receipt](cleanup.json).

Original HealthTech Pack, all historical scholarly PDFs/internal Paper 53, local provider journals, untracked/dirty-only owner artifacts and EnterpriseRAG downloads remain. No reset/clean, force push, Git garbage collection or history rewrite was used. Generic source/evidence/store/FTS/provider modules and historical regression fixtures were retained because the new track reuses their behavior.

The first post-cleanup full check exposed four old parser tests depending on the local 137 MB PLS CSV. Those tests now use a 20-row project-authored CSV fixture with the same parser schema. Streaming/locator/search/extraction/hidden-field assertions remain; no test is skipped and no scientific data is substituted into historical result records.
