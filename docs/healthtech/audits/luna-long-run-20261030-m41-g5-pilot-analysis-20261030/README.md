# HT-M41 deterministic G5 pilot-task analysis

- Run ID: `luna-long-run-20261030-m41-g5-pilot-analysis-20261030`
- Date: `2026-10-30` (Asia/Bangkok local execution)
- Parent evidence: `docs/healthtech/audits/luna-long-run-20261030-m40-philips-g5-pilot-20261030/`
- Implementation/tested code commit: `65386b72404d3b4b0b3b67a72bcb6ef06003a4b5`
- Status: `PASS_G5_PILOT_ANALYSIS_ENGINEERING_ONLY`

## Scope

Added a deterministic analyzer for hash-bound HT-G5 task receipts. The analyzer
accepts successful or sanitized failed receipts, rejects duplicate case IDs,
unsafe artifact paths, missing artifacts, and hash mismatches, then writes a
machine-readable summary and Markdown report without loading raw restricted
source payloads.

## Actual aggregate result

The analysis covers one Cook task receipt and three Philips task receipts:

- `4/4` engineering tasks passed.
- Engineering execution time: total `0.4829s`; median `0.1197s`; min
  `0.1144s`; max `0.1292s`.
- Artifact hashes: `20/20` passed.
- Candidate counts: `9` disclosed links, `0` retrieved-only candidates, `9`
  total candidates across the four receipts.
- External projection status: `BLOCKED_LOCAL` for all four receipts.
- Provider calls: `0`; network calls: `0`; paid cost: `USD 0.00`.

The packet now links this aggregate engineering analysis while preserving the
boundary that these seconds are not participant task time or a service-level
claim.

## Verification

- Analyzer regression: `3 passed`.
- Existing G5 runner and Philips dossier regression: `8 passed`.
- Direct full repository suite: `454 passed`, 2 warnings.
- Guarded `verify_offline.py --suite all`: `454/454` passed, `0` network
  attempts, `0` credential-file read attempts, `0` provider calls, and
  `USD 0.00` paid cost.
- Targeted compile: pass.
- Input receipt and source hashes are recorded in [`verification.json`](verification.json).
- The copied aggregate result is [`analysis.json`](analysis.json).
- Full raw task outputs remain under the established ignored `results/` paths.

## Boundaries

- This is engineering dry-run analysis, not participant, usability, commercial,
  or willingness-to-pay evidence.
- Product-level disclosed links are not semantic relevance gold; unlisted pairs
  remain `UNJUDGED`.
- No provider request, restricted payload transfer, or paid inference occurred.
- Semantic device-patent labels, live HT-B4, Bridge, deployment, outreach,
  clinical/FTO, public raw-data release, and Claude UX/UI remain blocked or
  paused.

## Next action

Keep the G5 packet in `ENGINEERING_DRY_RUN_READY_NOT_VALIDATED` state. Obtain an
owner-authorized rights-cleared semantic judgment source, validate it through
M23/M25/M24, and only then rerun frozen controls without changing the
denominator, holdout, grouping, or `UNJUDGED` policy.
