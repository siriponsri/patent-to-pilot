# Interruption comparison result

**NULL at the two-read cap. The forecast completed fewer safe rows after the first read.** Across 12 authored Thai dossier packets, the candidate, nearest-complete and fixed rule each completed 15/24 requested rows after two opens per case. The primary forecast minus nearest-complete contrast was 0 rows, with three dossiers gaining one, three losing one and six ties. All arms correctly abstained on six known-missing rows, missed three answerable rows at the cap and issued zero unsupported rows. All figures are scoped to this deliberately balanced controlled comparison.

| Layout, three dossiers each | Forecast after 1 / 2 opens | Nearest-complete after 1 / 2 | Fixed domain after 1 / 2 |
|---|---:|---:|---:|
| Valid bundle | 0 / 6 | 3 / 3 | 3 / 3 |
| Stale bundle | 0 / 3 | 3 / 6 | 3 / 6 |
| Direct | 3 / 6 | 3 / 6 | 3 / 6 |
| Unresolved | 0 / 0 | 0 / 0 | 0 / 0 |
| Total safe rows | 3 / 15 | 9 / 15 | 9 / 15 |

The forecast selected a locator first in nine dossiers. In the valid-bundle layout, observing the locator unlocked a compatible two-result report. In the stale-bundle layout, the observation exposed a mismatched sequence, and the forecast switched to the valid known direct report while one read remained. Greedy and fixed readers opened the direct report first and then the initially opaque report. The latter was current in the stale-bundle layout and stale in the valid-bundle layout. This establishes a real difference in actions and opposite effects across the two mechanism strata. It supplies no estimate of how common those strata are in dossiers outside this fixture.

| Cost or adverse action | Forecast | Nearest-complete | Fixed domain |
|---|---:|---:|---:|
| First-open raw bytes across 12 dossiers | 3,748 | 5,149 | 4,210 |
| First-decision descriptors / ranked options | 33 / 57 | 33 / 24 | 33 / 15 |
| Total opens | 24 | 24 | 24 |
| Raw UTF-8 bytes opened | 9,159 | 10,389 | 9,399 |
| Total descriptors / ranked options | 60 / 81 | 54 / 36 | 54 / 30 |
| Mismatching report opens | 3 | 9 | 6 |
| Empty locator opens | 3 | 0 | 3 |

The common 32,862-byte runtime packet took 0.45 ms to read, verify and decode. Policy execution across all arms took 1.33 ms before the output write. Both timed CPU counters returned zero at timer resolution. Descriptor checks and ranked options are implementation counts, not measured per-arm latency. The forecast carries more planning work and different raw-byte costs. Every dossier used the full cap, so answerable rows left unresolved are misses at budget. There was no early terminal exit. Direct assumptions of 1 and 0.5 and locator weight 0.8 are authored forecast weights. There was no learning, calibration or model execution.

## Freeze, release and evidence integrity

The [prospective protocol](PROTOCOL.md) fixed the single primary and first-action prefix before any original. Base was `a523e5422a2faef046772d6fcfd02d3990d5e61c`. The Planner independently verified the six pinned constituent hashes, source-scoped runtime inputs, one exact empty output path and create-only capture, then released one exposed engineering original and score bound to [freeze](freeze.json) SHA-256 `d59d2b1bac6fea2460d2eacb1280ef84c7c1d1a5b733cc2d4701d909908ad494`. A separate preparatory check compared the key against the scoped contents of all 39 unique authored records for all 24 requests. The evaluator never provided the key to the worker. The raw SHA-256 was recorded before evaluation. The original was executed once. The Planner independently reconstructed full and prefix results and verified the referenced source hashes and byte lengths directly from the original.

| Private artifact under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-interruption-dev-20261126/` | Bytes | SHA-256 |
|---|---:|---|
| `runtime.json` | 32,862 | `8fd3e6fa6a7d54e8524c517d3cd8a18ca93be0623ccdbea82fb05811c6eb9edb` |
| `key.json` | 3,087 | `6bfcda4e78433eab180358191a63e5d06d7b1a84de91f59e71f159c710332a88` |
| `original.json` | 58,412 | `48e8a9e37868c17883ac58483333ec73977f89a34d3ba7df7cca6a788b85b16f` |
| `seal.sha256` | 79 | `7006efb4c64b4c47d54c74173e2f50e36fe7240fad452a4e8f32d15f5304f4dd` |
| `outcomes.json` | 26,959 | `67306062afccf8e17a13d9bc3a399be413a833547b7e81ef149bb3faac5ce33e` |

Read-only reproduction from the Research checkout. The command opens the sealed trace and evaluator key, without invoking the runtime.

```powershell
$data = 'C:/Users/User/Desktop/myProject/_private_artifacts/ptp-interruption-dev-20261126'
rtk proxy python scripts/research/ra_pharma/interruption_score.py $data 48e8a9e37868c17883ac58483333ec73977f89a34d3ba7df7cca6a788b85b16f
```

No paid service, model, GPU, protected TEST or product demonstration was used. No reserved or legal/field outcome is released. Retain the simple scope-aware control for the measured fixture. Follow-up efficiency claims require independently checkable, rights-cleared development observations about actual locator validity, useful action budgets and interruptions. The exposed original stays fixed.

## What the initial observations could identify

The valid- and stale-bundle generator branches both expose one exact report for the first row, one opaque report advertising only the second row, and a locator advertising both rows. Their visible request and role fields are identical in structure. After removing opaque identifiers, names and shuffled presentation order, the two layouts have the same initial decision state. The key has three of each layout. The runtime has neither the layout name nor a legitimate interpretation of the random ID as a layout marker.

With two opens and this fixed action catalog, whichever of the two reports is opened first, a direct plan can finish at most one row in the valid layout and two in the stale layout. After an opaque-report miss in the valid layout the remaining action can still open the exact first-row report. The locator-first plan can finish two in the valid layout and one in the stale layout. The latter limit follows because the newly observed stale descriptor offers no support and only one action remains. Thus both routes achieve at most 1.5 completed rows on an equally weighted mixture without predictive initial features. A first action cannot preselect the hidden report and there is no additional initial action available. Changing the mixture or giving the reader a real signal about locator validity would change the opportunity. This is an explanation from the frozen generator, with no re-execution, extra scoring or modification of the measured endpoint.

## Code gate

Both focused tests passed. CPython 3.12.10 in the S4 QA profile, fresh short basetemp ptp-interrupt-dev-r1, ran the full suite before code commit. Result was 2,799 passed, 8 failed, 10 skipped and 1 xfailed in 253.08 s with raw exit 1. All eight failure IDs match the standing SACR exceptions. Private pytest.log SHA-256 5b0888870eda24387375d8262a163c869a05db013eb6fdc2bdd3dbb184d50c12. The subsequent registry preflight changed documentation only.
