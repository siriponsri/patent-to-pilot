# Existing native baseline exposure

## Descriptive exposure of the existing baseline

These fixed coarse bins were declared before aggregation of the existing sealed
dev per-query metrics. They are not exact first-positive ranks. No retrieval was
rerun and no new method scores were inspected. All nine recomputed macro recall
values match the original published dev receipt.

| Partition | Eligible | First positive 1–10 | 11–100 | 101–200 | None at 200 |
|---|---:|---:|---:|---:|---:|
| ALL | 474 | 308 | 115 | 19 | 32 |
| IN | 450 | 299 | 110 | 21 | 20 |
| OUT | 349 | 37 | 67 | 32 | 213 |

The OUT baseline exposes at least one known positive for 136/349 queries at200;
213/349 expose none. This is distinct from macro Recall@200=0.14772. Unexposed
does not mean semantically irrelevant: judgments are incomplete. IN/OUT eligible
populations overlap. Paper53-inspired paired wins/losses, rescue and uncertainty
analyses are NOT_RUN because no comparator passed the prior gates.

The isolated aggregation used0.575023457 seconds whole supervisor time,1CPU,
512MiB memory limit,0GPU/model calls, no network and no protected-test mounts.
Peak memory was not measured. Four hand-computable validation fixtures passed.
