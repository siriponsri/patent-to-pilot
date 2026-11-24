# P2-T02 D19 local readiness, 24 Nov 2026

**Status:** local staging PASS. Combined full gate accepted. Model execution, C1 scores and billing are NOT_RUN.
**Authority:** D19 and D22, with launch and the USD 20 follow-up cap approved in D26. D19 remains inside R2.

The P1-DEV staging CLI rebuilt the filtered claims archives from the existing local sources. It verified the
origin manifests for the common inputs and the prior C0 relay gates. The exact stage
`../_private_artifacts/p2t02-d19-stage-20261124/` took 1,771.1 seconds and kept 21,609,708 of 167,971,637
claims rows in 54 archives. The stage contains the reduced P1-DEV art-unit map and excludes the mixed split metadata.

The independent verification checked the allowed paths, exact file membership and staged byte digests in both
manifests. It rebound the one pre-run runner correction after the filter stage and recorded it in the stage report.
The Qwen3 relay matched the prior provider checksum. The locally archived PatEmbed relay has a computed checksum and
its preserved C0 gate record. A provider checksum sidecar for that relay is unavailable locally.

| Stage record | SHA-256 |
|---|---|
| `stage-report.json` | `77e91bf6834ca4dff752c8741f94ce897ef50d3c0f59b9e3cab093dbed5d2e3d` |
| `tree/data/ptp-paper2/MANIFEST-d19-qwen3.sha256` | `5b13031f26bb91a858e7b2b801ee51a361d24ad6ad1bc02817795af68e13e8e8` |
| `tree/data/ptp-paper2/MANIFEST-d19-patembed.sha256` | `60fb3886cb1193cf70ce9482635d8640046fe32a309b85a0112cc7818fb093ac` |
| `tree/data/ptp-paper2/p2-coverage/code/p2t02_d19_runpod.sh` | `d050bb1c1f9b0f5a0f2a3e90992e4870ea8c1396845defdc431bb10974866885` |

Verification results are in the same private stage directory under `verification.json`.

## Package fit and dispatch policy

The integrated checkout ran the full pypdf/PyThaiNLP gate with 2,707 passed, eight skipped, one known xfail and all
eight expected SACR supervisor failures. The D19 targeted gate passed 11 fixtures and Bash syntax passed.
Verified implementation `d30d9d51` integrates WIP declaration `ffae7a99`, and was merged at `563b10a8`.

Use the least-cost eligible US stock that can run within the reservation. The live catalog check showed the eligible
A100 SXM at USD 2.19/hour compute and no lower-cost shape meeting the runbook requirements. The initial dispatch is
PatEmbed on one Secure A100, with USD 0.03/hour budgeted for the 150 GB ephemeral disk and a four-hour operating
deadline. Reserve USD 9.50 for the pod including teardown and reprice Qwen3 using accrued charges and remaining
capacity. This changes execution order only. Qwen3 and PatEmbed retain their separately frozen gates and decisions.
The provider bills temporary disk per second at the published running rate.
[RunPod pricing](https://docs.runpod.io/pods/pricing).
