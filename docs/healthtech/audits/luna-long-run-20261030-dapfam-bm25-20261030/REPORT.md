# DAPFAM BM25 diagnostic report

The full offline run completed successfully after local DuckDB installation. It ranked `45,336` patent-family candidates for `1,247` DAPFAM queries using title plus abstract BM25 with `k=100`.

The run produced `1,247` ranking records and evaluated only the `49,869` supplied qrel pairs. All-qrels macro Recall@100 was `0.21398467432950194`, micro Recall@100 was `0.2136868707128244`, and macro nDCG@100 was `0.19229519072532472`.

The output is a descriptive citation-based retrieval diagnostic. It is not semantic device-patent gold, not a clinical or legal conclusion, not exhaustive recall, and not evidence of HT-B4 benefit. Unlisted pairs remain unjudged. The main HealthTech next step remains owner-authorized semantic judgment-source intake through M23, M25, and M24.
