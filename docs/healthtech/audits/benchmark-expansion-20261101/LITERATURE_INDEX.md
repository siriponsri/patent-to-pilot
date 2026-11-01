# Literature index — benchmark expansion

Verified from the linked Pepo source pack on 2026-11-01. This repository copy contains metadata, public source links, use boundaries and unavailable-item notes only. Local reading PDFs remain outside Git and are not redistributed here.

## Reading order

1. R01, R02, R03 for prior-art similarity, DAPFAM family retrieval and PANORAMA examination-choice semantics.
2. R05 and R07 for entity-resolution evaluation; these do not establish current assignee or ownership truth.
3. R08 and R09 for dated assignment semantics and name harmonization.
4. R10, R11, R12, R13, R14, R15 and R16 for incomplete judgments, adaptive retrieval, citation support and cost-quality framing.
5. R04 and R19 for optional claim/passage or professional patent-task context.

## Verified sources

| ID | Work | Public source | Role in this project |
|---|---|---|---|
| R01 | Helmers et al., “Automating the search for a patent's prior art with a full text similarity search” (PLOS ONE, 2019; doi:10.1371/journal.pone.0212103) | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0212103 | Selected-pool expert relevance diagnostic; not device-patent gold |
| R02 | Ayaou et al., “DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross domain patent retrieval” (arXiv:2506.22141) | https://arxiv.org/abs/2506.22141 | Family retrieval and IN/OUT diagnostics |
| R03 | Lim et al., “PANORAMA: A Dataset and Benchmarks Capturing Decision Trails and Rationales in Patent Examination” (arXiv:2510.24774; NeurIPS 2025 Datasets and Benchmarks) | https://arxiv.org/abs/2510.24774 | Closed-candidate option/paragraph selection component |
| R04 | Risch et al., “PatentMatch: A Dataset for Matching Patent Claims & Prior Art” (2021) | https://hpi.de/en/database-group/projects/data-integration-projects/web-science/paar-patent-analysis-and-retrieval/patentmatch/ | Optional claim-passage matching context |
| R05 | Binette et al., “PatentsView-Evaluation” (arXiv:2301.03591) | https://arxiv.org/abs/2301.03591 | Inventor name-disambiguation evaluation context |
| R07 | Kallipoliti et al., “From raw affiliations to organization identifiers” (arXiv:2505.07577) | https://arxiv.org/abs/2505.07577 | AffRoDB/ROR organization matching context |
| R08 | Marco et al., “The USPTO Patent Assignment Dataset: Descriptions and Analysis” (USPTO working paper, 2015) | https://www.uspto.gov/ip-policy/economic-research/research-datasets/patent-assignment-dataset | Assignment-event semantics and incompleteness |
| R09 | Ascione and Sterzi, “Presenting Terrorizer” (arXiv:2403.12083) | https://arxiv.org/abs/2403.12083 | Assignee-name harmonization context |
| R10 | Buckley and Voorhees, “Retrieval Evaluation with Incomplete Information” (SIGIR 2004) | https://www.nist.gov/publications/retrieval-evaluation-incomplete-information | Incomplete-judgment limits |
| R11 | Jeong et al., “Adaptive-RAG” (NAACL 2024) | https://aclanthology.org/2024.naacl-long.389/ | Adaptive retrieval prior art |
| R12 | Jiang et al., “Active Retrieval Augmented Generation” (EMNLP 2023) | https://aclanthology.org/2023.emnlp-main.495/ | Retrieval timing/action prior art |
| R13 | Gao et al., “Enabling Large Language Models to Generate Text with Citations” (EMNLP 2023) | https://aclanthology.org/2023.emnlp-main.398/ | Citation-support framing |
| R14 | Min et al., “FActScore” (EMNLP 2023) | https://aclanthology.org/2023.emnlp-main.741/ | Atomic support metric context; not used as semantic gold |
| R15 | Wadden et al., “Fact or Fiction: Verifying Scientific Claims” (EMNLP 2020) | https://aclanthology.org/2020.emnlp-main.609/ | SciFact component context |
| R16 | Chen et al., “FrugalGPT” (arXiv:2305.05176) | https://arxiv.org/abs/2305.05176 | Budget-aware quality-cost framing |
| R19 | Hu et al., “PatentAgentBench” (arXiv:2610.35031) | https://arxiv.org/abs/2610.35031 | Professional patent-task context; not a substitute for HT-T1 gold |

## Unavailable optional items

- R06 PatentsView benchmark page: official request returned HTTP 403 in the source-pack run.
- R17 CLEF-IP 2013 overview: the publisher endpoint returned HTML rather than a PDF.
- R18 “Technology Life Cycles”: official SSRN landing request returned HTTP 403.

These gaps do not block the acquired Helmers/PANORAMA component work. The index does not grant dataset, paper or code redistribution rights; each source remains subject to its own license and use terms.
