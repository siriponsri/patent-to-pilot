# MTM dev phase 3b: citation-reuse gating probe, result NO_GO

- **Status:** PASS (run). **Gate decision: NO_GO.** Citation chasing (3c) is not built. This is a negative feasibility result.
- **Split:** dev labels only (1,985 queries). Test targets were never read. For test rows, only the query family IDs were used, to exclude them as citers.
- **Declared before the run:** in the [methods log](../../research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md), entry 3b (`3792f6d`), including the go/no-go rule.

## Data (BigQuery tm06)

- **SQL:** `scripts/healthtech/sql/tm06_device_sea_citation_edges.sql`, sha256 `05241b9f…`.
- **What it selects:**
  - citing grants: US B1/B2 device grants (CPC A61B/F/G/H/J/L/M/N) granted 2001–2016;
  - edges: their examiner (SEA) citations to US publications, mapped to the cited family.
- **The run** ([tm06.receipt.json](tm06.receipt.json)):
  - job `79b05fec-deb9-4b21-b963-641be6177205`, PASS, not served from cache, 125.8 s;
  - dry-run estimate 31.48 GiB; the owner raised the per-query cap to 34 GiB for this run;
  - 33,801,102,209 bytes processed and 33,801,895,936 billed, within the project's free tier as far as its billing setup allows;
  - 1,344,435 distinct edges (citing family, citing grant date, cited family).
- **The private edge file** (sha256 `c2218eea…`) stays in `_private_artifacts` and on dr-train.
- **Analysis:**
  - code: `scripts/healthtech/analyze_mtm_citation_probe.py` at `50eec39`, run on dr-train CPU, exit=0;
  - output: [dev-phase3b.json](dev-phase3b.json), sha256 `0d0735f1…`.

## Results (dev)

An edge counts for query q only if its citing grant is dated on or before T(q), the query's priority date. The query's own family and every benchmark query family are excluded as citers.

| Measure | Value | Meaning |
|---|---|---|
| (i) **Reach** | **30.3%** of 1,985 queries | The share with at least one target cited by any earlier device grant. This is an *upper bound* for citation chasing with unlimited neighbours. |
| (ii) **Co-citation inter-connection** | **3.1%** of the 892 queries with 2 or more targets | Targets of the same query are almost never co-cited by one earlier device grant. |
| (iii) **Popularity null** (lane X, main view, no query text) | hit@20 **0.6%**, hit@100 **2.1%**, hit@200 **3.7%** | Ranking by earlier device-citation counts barely finds targets. X reaches 18.0 / 31.3 / 38.8%. |
| (iv) **Outside-corpus share** | **87.1%** of 449,168 distinct cited families | Most references that device examiners cite are not in the MTM corpus. |

**Gate (fixed before the run):**

- **The rule:** reach ≥ 48.8% (X hit@200 + 10 points) **and** popularity-null hit@200 < reach/2.
- **The outcome:** reach is 30.3%, below the 48.8% threshold, so the gate is **NO_GO**.

## Findings

1. **Examiner reuse across earlier device grants is too weak to drive candidate generation here.**
   - Even with unlimited neighbours, earlier device grants cite a query's cross-field target for only 30% of queries. Dense retrieval already exposes 38.8% at depth 200.
   - Targets are rarely co-cited (3.1%).
   - Both results match the literature:
     - citation chasing works only when targets are densely inter-connected (Gobeill et al., TREC-CHEM 2010: 70% inter-connection on USPTO chemistry vs 8% on CLEF-IP);
     - citation-graph expansion did not raise recall on CLEF-IP (Mahdabi & Crestani, TOIS 2014).
2. **The corpus enrichment flagged in the [phase-3 audit](../ptp-medtech-tm-phase3-audit-20261109/README.md) is not trivially exploitable.**
   - A citation-popularity ranking with no query text reaches only 3.7% at depth 200.
   - The benchmark therefore does not reward "being a cited document" on its own.
   - This supports the validity of the MTM corpus design. The planned cited-distractor view is still worth adding as a robustness check for 3d.
3. **Most chased references would fall outside the corpus (87%).** Under the open-candidate protocol, they would take rank slots as unjudged documents. That is a further practical reason against 3c here.

## Limits

- Citing grants are limited to US device grants from 2001–2016 and to US cited publications. Non-device citers, non-US documents and literature are not covered.
- Reach treats any visible citer as a possible neighbour. A text-based neighbour search would reach fewer targets, so the true value of 3c would be lower.
- Inter-connection is measured as co-citation by an earlier device grant. Gobeill et al. used direct citation between targets.
