# Option A results

**Thai primary NULL. Architecture attribution is diagnostic only.** Both the version-bound assignment selector and the matched Socrates-style premise selector achieved **22/22** scope-complete successes on the authored Thai answerable cohort. The case-weighted paired difference was **0.00 percentage points** with a 95% whole-family bootstrap interval of **[0.00, 0.00]**. All 22 paired outcomes tied. The degenerate interval arises because every sampled family contrast is zero. It provides no population equivalence claim. The frozen positive criterion of at least +5 points with a strictly positive lower interval endpoint was not met.

The [prospective protocol](PROTOCOL.md) and [v2 freeze](freeze.json) were published at `aab1d1aef56f464c9acb7dcded46d02025fb3411`. The independent Planner/Auditor released that exact revision and SHA before launch, and verified the original after capture. The runner executed one canonical original on serial CPU, in order Thai controlled, English transfer, Thai natural diagnostic and English natural diagnostic. It sealed raw traces, launch metadata and subprocess captures before scoring at `2026-11-25T14:51:35.390844+00:00`. There were no worker failures, retries, invalid traces or budget breaches. No protected TEST or credential access, model use, paid booking, remote host, or product demonstration selection entered the run.

## Observed results

| Lane and scope | Families | Answerable success per arm | Finite abstention per arm | Unadjudicated | Valid traces across five arms |
|---|---:|---:|---:|---:|---:|
| Thai controlled primary | 8 | 22/22 | 2/2 | 0 | 120/120 |
| English controlled transfer | 4 | 12/12 | 1/1 | 0 | 65/65 |
| Thai natural diagnostic | 1 | 3/3 | — | 1 | 20/20 |
| English natural diagnostic | 1 | 3/3 | — | 1 | 20/20 |

All five arms reached the same counts. On Thai, the proposed-versus-premise and proposed-versus-zero-split contrasts each had 0 wins, 0 losses, 22 ties, and identical action sequences and outputs in all 22 answerable trials. The two primary arms each answered 22 of 24 adjudicated cases, with **0 wrong-scope answers among the 22 matched answers**. The zero-split ablation has the same matched-coverage readout. All four Thai changing pairs with the same literal answer supplied eight answerable requests, scored **8/8 in all arms**, with paired change 0 points and interval [0, 0]. The simple visible-reference and coverage baselines also reached 22/22.

For English controlled transfer the primary and ablation contrasts likewise had 12 ties, identical action sequences and outputs in all 12 cases, difference 0 points and interval [0, 0]. Each primary arm answered 12 of 13 adjudicated cases with 0 wrong-scope accepts at matched coverage. The smaller same-answer changed-witness diagnostic was 4/4 in all arms. Both natural lanes use a single public-source family with author-adjudicated labels. They have no family-cluster interval. Each arm was correct on the three adjudicated requests and one case was excluded. Original annotation came from a separate preparation agent. Independent engineering audit verified provenance and scoring. Human language, legal, and patent adjudication remain unmeasured.

## Why the held packet did not discriminate between selectors

Across all 45 requests, the five arms opened the same evidence in the same action order. In the Thai controlled lane, 18 of the new selector's 20 acquisitions had exactly one visible reference target. Two had no target and used the common lexical fallback. No Thai acquisition had a choice between two distinct visible targets. The nine English controlled acquisitions likewise each had one target. Among the five Thai natural acquisitions, two had one target and three used the lexical fallback. The English natural lane had no acquisition. This limits the experiment's ability to expose a benefit from the distinguishing selection signal. The matched endpoint and simple reference baseline are evidence about this fixed, annotated packet. The synthetic development trace demonstrates the branch-selection mechanism under deliberately available alternatives.

The Thai pair diagnostics were 6/6 for changed support or conclusion and 4/5 for strict invariance in every arm. The failed invariant pair in `ae-th-seed-storage` kept the correct literal answer but used two different, independently permitted chains after the wording change. Both case scores remained correct. English controlled was 3/3 for changes and 3/3 for invariance. Natural diagnostics were 1/1 for the Thai changing pair and 1/1 for the English invariant pair. No primary case regressed versus the control.

## Actual resource use

| Lane | Actions per arm | Candidate inspections per arm | Outgoing graph reads per arm |
|---|---:|---:|---:|
| Thai controlled | 88 | 358 | 100 |
| English controlled | 44 | 191 | 55 |
| Thai natural | 18 | 77 | 18 |
| English natural | 8 | 24 | 0 |
| Total per arm | 158 | 650 | 173 |

Across five arms the run logged 790 actions, 3,250 candidate inspections and 865 outgoing-edge reads. Captured subprocess wall time was 333.8184 ms summed across lanes, including process startup. Ingestion processed 100,355 bytes over 3.1603 ms summed wall time. Per-query wall, planning and CPU ledgers are in the [machine result](results.json). Windows process CPU readings are coarse relative to these trials. A recorded zero is below the resolution in the measured interval. Whole-process CPU outside timed regions is unmeasured. There were zero model tokens, API calls or direct paid costs, and no ancillary execution.

## Reproduction and closeout

The canonical outputs are under `../_private_artifacts/ptp-alt-evidence-20261125/original/`. The machine result records the hashes for the authorization, sealing, original raw files, individual case results and summaries. The seal SHA-256 is `581aae9774dff83d975278c7d2019b90520a2dc50c56bcbfe67e177d3a4daf50`. All 225 traces validated. Both the executor and the Planner/Auditor rescored originals without replaying the policy. Family and stratum counts, thresholds, exception accounting and applicability limits remain available for S5.

The following verifies the capture and recomputes all scores from the original traces. Run from the repository root. The worker is never invoked.

```powershell
@'
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts/research")
from alt_experiment import ARMS, LANES, LOCK, ORIGINAL, PACKET, audit_capture, digest, read, summarize, verify
verify()
seal = read(ORIGINAL / "raw-seal.json")
assert seal["freeze_sha256"] == digest(LOCK)
for lane in LANES:
    root = ORIGINAL / lane
    assert all(digest(root / name) == expected for name, expected in seal["lanes"][lane].items())
    packet = read(PACKET / lane / "runtime.json")
    label_data = read(PACKET / lane / "labels.json")
    labels = {row["case_id"]: row for row in label_data["cases"]}
    rows, failures, ingestion = audit_capture(packet, labels, root)
    expected = summarize(rows, label_data["pairs"]) | {"trace_failures": failures, "ingestion": ingestion}
    assert rows == read(root / "case-results.json")
    assert expected == read(root / "summary.json")
    print(lane, len(rows), sum(arm["trace_valid"] for row in rows for arm in row["arms"].values()), len(rows)*len(ARMS))
print("seal, original trace validations, paired results and summaries match")
'@ | rtk proxy python -
```

Close Option A as **NULL primary and diagnostic-only contribution**. The original S3 Thai negative and English results stay separate. The [historical IS1/Paper 53 and P2 bridge](../../healthtech/audits/S3-20261125/BRIDGE.md) kept its original scope, with new depth or native retrieval runs NOT_RUN. S4 is independently [ready for review at the Windows local level](../receipts/S4-integrated-verification.md). There was no external product deployment or user study. S5 remains pending.
