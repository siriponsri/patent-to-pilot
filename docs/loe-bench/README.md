# Market Window Dossier documentation

Market Window Dossier is the working name for the D41 pharma market-research workflow. It helps teams judge whether demand will remain at launch, before they commit to bioequivalence or comparative trials. For scarce freedom-to-operate (FTO) evaluators, it prioritizes review and supplies a dated evidence pack and verification checklist. Qualified counsel assesses freedom to operate. [Owner-approved plan](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

Enter an ingredient, form, jurisdiction, decision date and planned launch date. The planned workflow forecasts the market window, assembles competition and patent evidence, fills Thai and ASEAN status rows, generates an evaluator checklist and produces a one-molecule report. Its Thai decision page is followed by bilingual technical sections. [User flow, components C1–C10, report hierarchy and schedule](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

LOE-Bench remains the research benchmark. The frozen benchmark results are from development only. The confirmatory test remains sealed and has no result. The workflow above is the approved build scope. [Development results and next steps](HANDOFF.md).

| Need | Where to look |
|---|---|
| Design, roles and task cards on `research/loe-bench` | [Program plan and dispatch board](PLAN.md) |
| Decisions and continuation | [Lane handoff](HANDOFF.md) · [Lane memory](MEMORY.md) |
| Task evidence and review status | [Task receipts](receipts/) · [Technique ledger](TECHNIQUE-LEDGER.md) |
| Frozen inputs and source editions | [Track A S0 manifest](../../loe-bench/data/S0_INPUT_MANIFEST.json) · [openFDA snapshot manifest](../../loe-bench/data/MANIFEST-20261127.json) · [Orange Book editions](../../loe-bench/data/OB_EDITIONS.json) · [Paragraph IV editions](../../loe-bench/data/PIV_EDITIONS.json) · [Purple Book files](../../loe-bench/data/PURPLEBOOK_FILES.json) · [NBER edition manifest](../../loe-bench/data/E8_NBER_MANIFEST.json) and [licence limits](receipts/E8.md) |
| Thai demo and patent challenge source feasibility | [Thai open data](THAI-OPEN-DATA.md) · [Challenge sources](CHALLENGE-SOURCES.md) |
| Thai-layer inputs | [RA Pharma board](../ra-pharma/MASTER-PLAN.md) · [Evidence contract](../ra-pharma/EVIDENCE-CONTRACT.md) · [Workbench entry point](../../CLAUDE.md#5-where-things-are) |
| IS2 authors, writing and deadlines | [Independent Study 2](../writing/is2/README.md) |
| Original owner package | [Preserved source documents](owner-source/) · [Source hashes](owner-source/SOURCE-SHA256.txt) |
| Earlier Patent-to-Pilot programs | [Repository evidence index](../../INDEX-PLAN.md) |

Claude Opus 5.5 is the main planner and sole reviewer. GPT-6.2 Astra high co-plans methodology. GPT executors work in separate worktrees and use the model assigned to each card. [Roles and executor protocol](PLAN.md#roles).

Run the local unit suite from the repository root with Python 3.

```sh
cd loe-bench
python -m unittest discover -s loe_bench/tests -t .
```

See the [D41 documentation receipt](receipts/DOCS2.md) and [deletion inventory for planner review](receipts/DOCS2-DELETION-INVENTORY.md). The [D40 documentation review](DOCS-REVIEW.md) records the earlier navigation audit.
