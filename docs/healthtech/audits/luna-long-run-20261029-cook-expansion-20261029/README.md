# Cook Zenith cohort expansion

- Run ID: `luna-long-run-20261029-cook-expansion-20261029`
- Status: `PASS_OFFLINE_DEVELOPMENT_WITH_THIRD_COMPANY`
- Scope: bounded local acquisition, typed provenance, three-company composite, and offline HT-B0a/B0b/B1/B2/B3 at `K=10`.
- Provider calls: `0`; paid cost: `$0.00`.

## Objective

Add a third source-backed company group to the typed Boston Scientific/Stryker package using an official Cook Medical product patent-marking source, while preserving evaluator/runtime separation, raw and canonical identifiers, source hashes, and a predeclared untouched company holdout.

## Source and cohort

Cook acquisition:

- Official page: `https://www.cookmedical.com/patents/`
- Linked list: `US-Patents-List-for-US-website-2025.2.pdf`, updated `6January2025`, six pages.
- Products: Zenith Flex AAA Endovascular Graft, Zenith Renu AAA Ancillary Graft Converter, Zenith Dissection Endovascular Stent.
- Regulatory anchors: PMA `P020018` and `P180001` from openFDA.
- Cook parent: `3` devices, `4` patents, `5` disclosed pairs, `7` unjudged distractors.
- Cook family mapping: `UNKNOWN_NOT_ASSUMED`.

Composite:

- `8` devices, `24` patents, `31` disclosed pairs, `161` unjudged distractors.
- `3` company groups: Boston Scientific, Cook Medical, and Stryker Neurovascular.
- Final holdout: the full Stryker Neurovascular company group (`3` queries).
- Development view: Boston Scientific plus Cook Medical (`5` queries).
- Composite cohort SHA-256: `9f78187b6dbe4c6f7d7967da1a5f96af35e2b0297edf16bab423072d92b25536`.

## Verification

- Cook parent provenance: `PASS`; `5/5` disclosed pairs covered by typed `cook-medical-patent-marking`.
- Composite provenance: `PASS`; `31/31` pairs covered across three independent disclosure sources, with `0` unresolved policies.
- Runtime views contain no disclosure references, evaluator evidence, family labels, or split answers.
- Focused tests: `39 passed`; compile checks passed.
- Offline baselines completed for both development and final holdout with zero failed queries, zero provider calls, and zero paid cost.

See [REPORT.md](REPORT.md), [verification.json](verification.json), [baseline-summary.json](baseline-summary.json), [rights-matrix.json](rights-matrix.json), and [NEXT_ACTIONS.md](NEXT_ACTIONS.md).
