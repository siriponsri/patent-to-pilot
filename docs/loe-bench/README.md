# LOE-Bench documentation

LOE-Bench is the active Patent-to-Pilot program under D40. It forecasts first generic and biosimilar approvals using open regulatory records and refers uncertain cases for human review. RA Pharma provides the Thai-context demo layer. Wave 2 results are development evidence. The confirmatory test is sealed, with no confirmatory result. [Owner decision D40](../maintenance/OWNER-DECISIONS-20261122.md#d40--loe-bench-becomes-the-active-program-27-november-2026).

| Need | Where to look |
|---|---|
| Design, roles and task cards on `research/loe-bench` | [Program plan and dispatch board](PLAN.md) |
| Decisions and continuation | [Lane handoff](HANDOFF.md) · [Lane memory](MEMORY.md) |
| Task evidence and review status | [Task receipts](receipts/) · [Technique ledger](TECHNIQUE-LEDGER.md) |
| Frozen inputs and source editions | [Track A S0 manifest](../../loe-bench/data/S0_INPUT_MANIFEST.json) · [openFDA snapshot manifest](../../loe-bench/data/MANIFEST-20261127.json) · [Orange Book editions](../../loe-bench/data/OB_EDITIONS.json) · [Paragraph IV editions](../../loe-bench/data/PIV_EDITIONS.json) · [Purple Book files](../../loe-bench/data/PURPLEBOOK_FILES.json) · [NBER edition manifest](../../loe-bench/data/E8_NBER_MANIFEST.json) and [licence limits](receipts/E8.md) |
| Thai demo and patent challenge source feasibility | [Thai open data](THAI-OPEN-DATA.md) · [Challenge sources](CHALLENGE-SOURCES.md) |
| Original owner package | [Preserved source documents](owner-source/) · [Source hashes](owner-source/SOURCE-SHA256.txt) |
| Earlier Patent-to-Pilot programs | [Repository evidence index](../../INDEX-PLAN.md) |

Claude Opus 5.5 is the main planner and sole reviewer. GPT-6.2 Astra high co-plans methodology. GPT executors work in separate worktrees and use the model assigned to each card. [Roles and executor protocol](PLAN.md#roles).

Run the local unit suite from the repository root with Python 3.

```sh
cd loe-bench
python -m unittest discover -s loe_bench/tests -t .
```

See the [documentation review](DOCS-REVIEW.md) for the D40 navigation changes and findings awaiting planner review.
