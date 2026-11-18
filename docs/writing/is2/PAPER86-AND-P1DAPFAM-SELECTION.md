# IS2: what to take from Paper 86 and from P1-DAPFAM (agent selection, 19 Nov 2026)

Owner instruction 19 Nov: "Paper 86 ช่วยเลือกได้เลยจาก repo myIS"; "P1-DAPFAM อ้างอิงเล็กน้อยบน IS2 ได้".
Sources read:
- the published Paper 86 PDF `myDegree/IS/IS_2/paper86_ieee_express.pdf` (sha256 `95be5490…`);
- its reviews `review_paper86.txt`;
- the local clone `myProject/myIS` at `1f9b89e` (2026-09-03; newer GitHub commits not checked);
- for P1-DAPFAM, `docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md`.

Paper 86 is in the same IEEE proceedings as Paper 53 (ISBN 979-8-3195-1044-0/26), so IS2 cites it as published own work.
Do not copy its text verbatim; IEEE holds the copyright. Paraphrase and cite.

## Paper 86 parts selected for IS2

| # | Paper 86 content | Use in IS2 | Why |
|---|---|---|---|
| S1 | **Exposure diagnosis** (Table VI). The selected PatEmbed-large passage system at Top-200, strict OUT, full benchmark: 4,065 of 5,193 relevant pairs (78.3%) absent; 455 of 905 queries with no OUT hit; macro Recall@100 0.188 vs 0.260 under ideal reordering (headroom 0.072) | Ch. 3 (K1b): evidence that the first stage, not the reranker, limits OUT retrieval | Second measurement of the same bottleneck that Paper 53 found (37.1% exposed at Top-100). It comes from a different system and depth, so it is not a replication; say so |
| S2 | **Retriever ordering under three construction recipes** (2026 nine-cell execution, 250 dev queries). PatEmbed (about 0.419 Recall@100) stayed ahead of Qwen3 and Arctic under every recipe; recipe spread ≤ 0.004 per retriever; all intervals include 0 | Ch. 2 (K1a): own evidence that the PatEmbed family was the strongest frozen dense first stage on DAPFAM | Supports the choice of a PatEmbed encoder. State that Paper 86 used **patembed-large**, while Paper 53 used **patembed-base** (distilled from large) |
| S3 | **Encoder-window accounting** (§III-C, §IV-A). Logical passages exceed the 512-token PatEmbed input; 19,145 of 179,910 units needed more than one window | Ch. 2 or methods appendix: report construction and encoder together | Answers a Paper 86 reviewer's point and shapes how B53 reports its TAC rendering |
| S4 | **Archived Final-872 system comparison** (0.442 vs 0.331 Recall@100) | One sentence of context at most, or omit | Historical records incomplete (filter and grades not recovered); several components change at once. Keep it out of the IS2 argument |

Not selected:
- the archived 52-configuration search and the BM25/Arctic "FAST" pipeline details. They are provenance only and their denominators were not recovered;
- the AutoIndex/A0-A3 progress reports in `myIS/docs/progress_report/`. They are development history, not evidence.

`myDegree/IS/IS_2/short_paper/IS2_short_paper_EN.docx` already exists. It was not opened in this round; the owner should
say whether it is the IS2 template or an earlier draft.

## P1-DAPFAM: a short reference only

Proposed text for IS2, one paragraph in Ch. 3 or Ch. 6. Numbers are from `paper1-report/TEST-RESULT-TABLES.md`; the test
was evaluated once:

> A follow-on study tested whether query-side rewriting can bring cross-domain prior art into the candidate pool of a fixed
> dense first stage (PatEmbed-large) on the DAPFAM test split (n = 556 OUT-eligible queries). The pre-registered primary
> contrast, functional-abstraction rewriting fused with the original query versus the original query alone, was
> −0.0135 OUT Recall@200 (95% CI −0.0285 to +0.0012). The result was inconclusive, and the rewrite reduced IN recall by about
> 0.019. Changing the query text did not remove the exposure limit, which motivates changing the first stage itself (B53)
> and training it on cross-domain citations (journal Paper 1).

Rules: no further P1-DAPFAM tables in IS2; the test split stays closed for any selection. B53 uses DAPFAM test queries
only for its own exploratory, evaluation-only analysis (owner decision 19 Nov).

## Resulting IS2 storyline
1. Paper 53 and the committee's comments.
2. Why patembed-base (K1a): external benchmark + PatenTEB/model card + S2.
3. The exposure bottleneck (K1b): Paper 53 at 37.1% plus Paper 86 S1; P1-DAPFAM in one paragraph.
4. B53, where only the first stage changes (K2a), plus B53.0 against the DAPFAM benchmark paper.
5. Examiner value (K2b): proxy measures only.
6. Outlook: journal Paper 1 (BridgeRet) as the follow-on, cited without moving IS2 text into it.
