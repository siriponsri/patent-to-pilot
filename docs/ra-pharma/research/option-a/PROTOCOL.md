# Option A exposed development protocol

The Planner recorded owner approval for the unchanged-source historical answer task and a solo-operator pilot. This packet is for local development and scorer rehearsal. Fresh confirmation requires new matter families and a separate release. The research branch started clean at `e5e8d61fe3eb9b0671add3179207fc29adff3765`. The separate Planner checkpoint is `45e11723`. [Feasibility decision](../FEASIBILITY.md) · [Planner checkpoint](https://github.com/siriponsri/patent-to-pilot/blob/45e11723/docs/ra-pharma/RESEARCH-FIRST.md)

## Frozen development inventory

Use this order and the attachment aliases in the [operator packet](OPERATOR-PACKET.md). The originals stay in the private first-pilot directory named in the [D31 receipt](../official-correspondence/RECEIPT.md#cost-and-reproducibility). The target is an exposed recited inquiry from Thai FDA letter สธ ๐๘๑๒/๕๑๔๘, 24 June 2539 BE, attested by OCS Opinion 253/2540, May 2540 BE. The incoming original is unavailable. All three PDFs are Thai OCS historical opinions. The historical issue and the two unrelated training examples in the operator prompt have separate provenance.

| Alias | Local file and edition | PDF pages | SHA-256 |
|---|---|---:|---|
| A | `folio-08.pdf`, 166/2519 | 2 | `bf6cf674225af5dee9e44db7de09cce83e568e73a11b59b386c06d4484bcf829` |
| B | `folio-03.pdf`, 253/2540 | 4 | `3d1125dd25dddaf58eccd4a4498edb9f068b855819f11305cbf048902d06c052` |
| C | `folio-04.pdf`, 43/2532 | 1 | `5fc13ac9f1efdf82be7f2ac67a0f407842a5d7f2767964fe9ba1d786f04f0815` |

Local model contexts, when available, use the corresponding entries of `canonical-pages.json` in A/B/C order, with 1-based PDF page delimiters. SHA-256 of the full pinned extraction file is `b8377df7d38941ff8617c2ec8f69800e1e05dbfcfeb9578f8be39a35f47369a5`. Preserve the bytes and page mapping. The extracted Thai text has duplication and spacing artifacts. For disputed readings, use the original PDF. The [D31 protocol](../official-correspondence/PROTOCOL.md#cohort-and-sources) records the local official-material use basis. No PDF redistribution or service transfer is cleared by this packet. Before any import, Planner records per-file permission and service retention terms, signed-in access and visible mode, then checks all seven pages are readable and that citations resolve to the right edition and page or paragraph. Any blocked import stays NOT_RUN with its reason. Keep the rubric, provenance crosswalk and old outputs outside model inputs.

## Semantic scoring

Score the attributed historical response in terms a reviewer can use. Keep citation integrity and support as two separate checks. Accept an exact quote only with matching bytes and location. Accept a paraphrase or alternative citation when the referenced text entails the same proposition for the same issue, scope and edition. Allow several passages to supply a condition jointly. Distinguish the authority's conclusion from views recited in the request, and mark cross-page reasoning explicitly.

| Dimension | Reviewer decision |
|---|---|
| Attribution and disposition | Check issuer, opinion and recited request reference. Is the conclusion or actual procedural response correct and supported? |
| Material qualifications | For each, record supported, missing, contradicted or unverifiable. Count a condition only if the answer or its returned extract conveys it and provides a valid witness. Credit equivalent phrasing and evidence. |
| Issuance and coverage | Record answered, partial, or explicitly abstained. Complete requires correct attribution, disposition and every material qualification supported with no material unsupported assertion. Record unsupported issuance when a claim is presented as usable with inadequate evidence. A clearly marked partial or abstention remains incomplete on a known case. |
| Unknown and missing | Unknown is a property of the reference evidence. Exclude unknowns from correctness and retain them in operational counts. A known missing requirement may support a correct procedural or insufficient-evidence response when the key calls for it. |

Exposed calibration references for 253/2540 are independently readable in the opinion. The p. 1 heading and first paragraph establish attribution. The final paragraph spanning the end of the discussion and p. 4 establishes the limit under the then-existing registration regime and the positive route. The route runs through a prior regulation under sections 80 and 82 setting the registration requirement for the application, label and leaflet, followed by use of the registered label/leaflet by licensees. Read the operative paragraph before the signature together with the preceding reasoning. Record certainty separately for the route and its sequence. A span can support one element while omitting the next. Source locator and edition are in the inventory above. [Worked example and direct PDF](../FEASIBILITY.md#observed-failure)

For prospective scoring, separate coordinator and adjudication. Freeze source-only expected dispositions and material conditions before capture. The coordinator replaces original IDs with random study IDs, resolves citations into neutral PDF locators and strips tool names, layout and timing metadata without altering substantive text. Preserve a sealed raw output and mapping separately. Two Thai reviewers independently score anonymous answers against the frozen rubric, with adjudication and disagreement logged. This pilot's single operator supplies within-operator timing only. On fresh packets use matched blocks with counterbalanced arm order across different matter families to limit recall, and keep preparation, waiting and correction time. Such a pilot provides feasibility evidence.

## Baseline-first sequence

1. Verify hashes and page/citation mapping. Reuse the sealed first-pilot lexical and exact extracts for an exposed side-by-side check. Inspect the old excerpts without executing the D31 runner or scoring with its key. Test supported paraphrases, alternate locators, wrong authority, partial, abstention and unknown with hand-checkable examples.
2. When a suitable local model is available, lock weight hash, inference version, tokenizer, seed, context fit and caps. Run direct full-context with the Thai checklist first in zero-shot, then the same checklist with both fixed examples. Use identical questions, source files, answer budget and generation settings. Plan hybrid Thai lexical plus dense retrieval with fixed reranking and adjacent passage context on the same model in both regimes. Record consumed tokens, retrieval work, calls and latency independently. Establish these baselines before adding any mechanism.
3. Compare the actual products only after access and file-transfer clearance. Use fresh chats, the same attachments, prompt and ten-minute proposed per-issue clock, and at most one generic citation or missing-condition follow-up. Record selected sources, visible mode, timer and fees. Preserve blind scoring. No interface proxy counts as ChatGPT Pro or NotebookLM.
4. Consider one matched support-ledger ablation only if strong baselines leave a meaningful omission and the Planner releases the trial. No D31 case can enter fresh confirmation. No paid calls, pods, new OCS index requests or applicant-facing advice in this scope.

[Sufficient Context](https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems/) motivates checking passage availability separately from evidence use. [NitiBench](https://aclanthology.org/2025.emnlp-main.1739/) motivates a strong Thai long-context/RAG baseline. This development check measures local scoring behavior on known cases.
