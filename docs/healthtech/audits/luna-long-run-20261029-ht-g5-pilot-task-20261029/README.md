# HT-G5 offline pilot task

- Run ID: `luna-long-run-20261029-ht-g5-pilot-task-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_OFFLINE_ENGINEERING_TASK`
- Implementation commit: `4b811892eea2112df8a9f49738fc474ec2300b47`
- Scope: one local engineering dry-run over the real Cook Zenith dissection dossier

## Objective

Turn the prepared HT-G5/HT-W16 task packet into an executable local workflow that
inspects one permitted source field, distinguishes the dossier's association
statuses, corrects one seeded user-edit field, publishes a durable version-2
history record, and verifies the rights boundary for an external projection.

## Outcome

The committed runner completed the real Cook case
`HT-DEV-COOK-ZENITH-DISSECTION-STENT` using the allowed FDA field
`pma_number`. It produced a sanitized receipt plus local-only history and
exports. The workflow selected version `2`, preserved parent version `1`, and
recorded two disclosed product-level candidates. Engineering execution time was
`0.1291642999931355` seconds; provider calls, network calls, and paid cost were
`0`, `0`, and `USD 0.00`.

The local-research export contains the full local snapshot only inside ignored
results. The product-display projection wrote no payload and returned
`BLOCKED_LOCAL` for Cook marking and Google-derived patent sources. The committed
receipt contains no raw patent body.

## Verification

- Focused regression: `2 passed`.
- Targeted compilation: runner and test compile successfully.
- All five receipt-recorded artifact hashes match their generated files.
- History chain: versions `[1, 2]`; selected export: version `2`.
- Source inspection: `openfda-pma-p180001-base`, field `pma_number`, rights check `PASS`.
- No participant, user, purchase, repeat-use, or commercial observation was collected.

Machine-readable details are in `verification.json`; continuation guidance is in
`NEXT_ACTIONS.md`. The ignored local result is
`results/healthtech/ht-g5-pilot-task-20261029-r2/`.
