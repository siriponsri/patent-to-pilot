# Bridge Rights and Cohort Report

**Checked:** 2026-10-28

## Result

The Bridge-MedDevKG branch remains `BLOCKED_LOCAL`. The pinned public repository was inspected at commit `f3990a207949f25012d1070a08ac303e140387e6`; its README snapshot SHA-256 is `f8518e94eceadb9dd6640128399072243beaf2b039981b498d2635f2862e4b36`.

The repository README describes 434 FDA PMA documents, 698,191 USPTO patents, and 585 expert-verified device--patent pairs. The supplied release audit records a materially different exported surface: 672 rows across 79 device IDs, 585 `is_valid=true` rows across 74 devices, and 549 distinct patent IDs in the 50,000-document corpus. Those figures are supplied audit findings; this run did not download or reexecute the Bridge payload.

## Rights findings

- `LICENSE` and `LICENSE.md` were absent at the pinned commit. A README MIT badge is not a verified data license.
- Released gold rows do not carry per-link disclosure URLs, source dates, or a split manifest.
- The export marks sampled unlisted pairs as `label=0`; those values cannot be treated as verified invalid relationships.
- Training positives overlap the exported evaluation positives, so the release cannot be adopted as an independent final train/test setting without a recovered cohort and split protocol.
- `is_valid` is a completeness flag and `kg_linked` is a pipeline output, not independent device--patent gold.
- The raw Bridge payload, paper PDFs, and evaluator-only material were not downloaded into the repository.

## Cohort decision

The Bridge release is not used as runtime input, evaluator gold, or a redistribution source. The missing rights clause, incomplete provenance, unresolved cohort reconciliation, and absent final split rules are sufficient to block this branch locally.

An independent permitted development branch was acquired instead: three named Abbott cardiovascular products, three selected openFDA PMA records, one public Abbott product disclosure page, and 41 public U.S. patent pages. This branch is not a substitute for Bridge gold and is limited to product-level disclosed relationships; it supports a bounded development run only.

The independent branch is recorded in `results/healthtech/ht-public-cohort-20261028-r1/` with separate `runtime.json` and `evaluator/references.json`, raw/normalized hashes, source registry, groups, split manifest, and data card. Raw third-party pages remain ignored local files.

## Exact next decision

No owner decision is required for the permitted development run. To unblock the Bridge branch later, obtain a source-specific reuse/redistribution grant or a clearly licensed replacement with per-link disclosure provenance, a frozen eligible cohort, and a recoverable group/split manifest. Do not silently relabel the Abbott branch as Bridge or as expert-verified gold.
