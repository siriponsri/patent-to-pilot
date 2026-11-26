# IS1 inputs and eligibility

**R1 complete for the available evidence. Zero of eight requested cells are eligible for a new benchmark run.** The independent source check used the owner-local Paper 53 PDF, IS1 PDF and Paper 53 LaTeX. It did not open any protected evaluation file. The research checkout began at published revision `2085e4be693cdb12cb60deb1e2a4139eea84063a`.

## Source identity and interpretation

| Source and version | SHA-256 | Locator and observation |
|---|---|---|
| Paper 53 author PDF, `paper53_ieee_express.pdf` | `09d580402a49739baedb2281be16ba0a275a1c5ecdb711dfb21c93c8aba3ddbe` | PDF p. 3 Table I gives the four arms. PDF p. 4 Table II and p. 5 Fig. 3 report 257/692 with a known OUT family in the frozen top 100. PDF pp. 5–6 describe missing execution records. |
| IS1 revised owner PDF, `IS1_ฉบับแก้ไข.pdf` | `9614946d6dd6f4cd2e849e1e9872cc1f0e108eecbe90d2f0316f263e9ae85e14` | PDF pp. 9–10, 45–46, Table 3 and Fig. 4 report 40.8% at 100 and 77.2% at 1,000 on a separate 725-query post-hoc first-stage exposure check. The promised depth-by-instruction rerank was future work. |
| Paper 53 LaTeX `revision_05/source/main.tex` | `400fc3d0a32ebe8080d0c97637516c33701f06284edd2d307d289227e19fd701` | Lines 65–66 define binary OUT gain, full-known-OUT ideal and query macro average. Lines 81–84 identify missing original artifacts and previous-exploration exclusions. Lines 102–105 give instructions. Lines 110–116 give TAC, truncation, tie rules and the missing deeper ranking. |

The source-transcribed bodies are available in [the B53 reranker](../../../scripts/healthtech/b53_rerank.py). UTF-8 lengths and SHA-256 identify the bodies before wrapper construction.

| Body | Bytes | SHA-256 |
|---|---:|---|
| Generic | 74 | `004c64eb0d64f4fc1ee4c01849d7c0715dd8f062b16fa80425aa52abd2c3ae72` |
| Patent-aware | 144 | `e69975dfe544eb1e4d60b20f409cadfa39aeb7b82233de8ff215aea1b01ea531` |
| Claim-focused | 638 | `919935e52be81036e57e71e40d61ff16fdce2d3522f3fe46ea1cc2ecb15d2110` |
| Scrambled | 638 | `58eda584da107abc36bb9ae606cbf1e25e72122859881f67c08eaf6c86c59ee3` |

The first three bodies match the LaTeX and normalized PDF text. Scrambled uses the source recipe, splitting Claim-focused on whitespace and shuffling with seed 42 before joining with single spaces. [B53 Stage 2](../../healthtech/research/plans/B53-PREDECLARATION.md) reports historical re-tokenized counts of 13/28/113/113 versus Paper 53's 13/29/119/113. That discrepancy and the absent executable snapshot leave original runtime/token identity unresolved. B53's native relevance gain and qrel-filtered execution are historical implementation choices. The new protocol follows the Paper 53 binary definition and schedules queries without labels.

## Admissibility

| Inventory | Prospective eligibility | Reason |
|---|---|---|
| Paper 53 original 692 queries | Historical aggregates | Missing query keys, mapped qrels, candidate and rank artifacts, executable rendering and evaluation, and per-query outputs. Full target-family disjointness was unestablished. |
| IS1 725-query depth check | Historical aggregates | Separate candidate exposure cohort. No admitted manifests, matched reranked traces or scoring rights for a new run. |
| DAPFAM plus PatEmbed, B53 905-query reimplementation | Historical aggregates | Evaluation-only reimplementation on exposed inputs. Rights confined to historical research use. Shared universe is documented and model training overlap is unresolved. |
| Challenge-1M / P1 / P2 | Historical aggregates | Previously exposed DEV or different protocol and outcomes. Metrics and cohorts have their own receipts. |
| S1 controlled, S3 and Option A | Historical results and engineering context | Previously evaluated, small controlled dossiers with different units. Option A had identical evidence sequences across all 45 requests. |
| P3 Thai auxiliary packets, NitiBench, WangchanX | Historical auxiliary context | Different task unit, generated-question or specialist overlap, and incomplete legal-edition adjudication. No matched new patent-family pool. |
| S2 and RA Pharma product families | Excluded | Product display authorizations and research selection are separate. Require positive manifest anti-join before any natural selection or held execution. |
| New authored R3 fixtures | Eligible for engineering verification | Fictional independent identifiers and project-authored bytes. No natural case, rank-1,000 pool or independent reserved adjudication. |

See the [source/rights ledger](../../evidence-scope/research/RIGHTS.md), [historical cohort freeze](../../evidence-scope/FREEZE.md), [overlap audit including its correction](../../healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md), [depth bridge](../../healthtech/audits/S3-20261125/BRIDGE.md) and [Option A](../../evidence-scope/alternative-evidence/RESULTS.md). No corpus, model or dataset was downloaded or relicensed for this audit.

An admissible replacement study needs permitted unexposed families, versioned text and queries, at least 1,000 family-unique candidates per query, known OUT links assembled outside the runner and a matched baseline on those same bytes. A lexical first stage is feasible in principle without learned retrieval weights. It still requires a concrete rights-cleared corpus, independent adjudication and a scoped compute envelope. Natural RA transfer separately needs independently grouped patent, legal-edition and letter-template DEV cases and an exact lock release. Those packages are absent from this handoff.

The [IS1 successor admission package](successor/README.md) selects EPO Linked Open EP Data conditionally. Official live source and scale preflight passed. The reserved split remains blocked on provable family exclusions.
