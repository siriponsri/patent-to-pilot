<p align="center"><img src="docs/assets/logo.svg" width="88" height="88" alt="Market Window Dossier logo"></p>

<h1 align="center">Market Window Dossier</h1>

<p align="center"><strong>Pharma market research from a pre-development launch-window forecast to an FTO hand-off report, built on dated open regulatory evidence</strong></p>

<p align="center">
  <a href="LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-1f2a44?style=flat-square"></a>
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-1f2a44?style=flat-square">
  <img alt="Status: development, test sealed" src="https://img.shields.io/badge/status-development%20%C2%B7%20test%20sealed-0f766e?style=flat-square">
</p>

<p align="center">
  <a href="#the-problem">Problem</a> ·
  <a href="#what-the-dossier-answers">Dossier</a> ·
  <a href="#loe-bench-the-benchmark-underneath">LOE-Bench</a> ·
  <a href="#how-evidence-stays-honest">Evidence rules</a> ·
  <a href="#current-status">Status</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#project-records">Records</a>
</p>

---

## The problem

Generic and biosimilar developers in Thailand and the region face two problems:

1. **Too few FTO evaluators.** Each candidate molecule needs a freedom-to-operate review. Qualified evaluators are scarce, and Thai patent pendency adds uncertainty: some pharmaceutical patents have taken 14 to 15 years to grant.
2. **Demand that is gone at launch.** Development decisions are made years before launch, often without serious market research. By the time a product is ready, competitors may already hold the market. FDA data show generic prices about 54% below the pre-entry brand price with two competitors and 79% below with four ([FDA](https://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/generic-competition-and-drug-prices)).

## What the dossier answers

Market Window Dossier runs **before** a bioequivalence study or comparative trial is committed. The user enters a molecule, dosage form, jurisdiction, decision date and planned launch date. The dossier answers three questions on its first page:

- How much competition could we face at our planned launch?
- Which assumption changes the commercial case most, for example a six-month delay?
- What must an FTO evaluator verify before we commit?

<p align="center">
  <img src="docs/assets/market-window-flow.svg" alt="Market Window Dossier flow. Inputs feed four stages: a launch-window forecast, a patent evidence pack, Thai and ASEAN status, and the dossier itself. Each stage reads from an as-of evidence store. Forecasts have been tested on development data; the sealed retrospective test and the prospective Track A freeze are pending." width="100%">
</p>

| Dossier section | Reader | Content |
|---|---|---|
| 1. Decision page | BD and R&D | On-time and delayed launch scenarios, the decisive assumption, open issues and the next action, in Thai |
| 2. Market window | BD | First-generic timing, demand baseline, price basis and launch-date sensitivity |
| 3. Competitive landscape | BD | Approved applicants, verified marketed producers and assumed entrants, kept separate |
| 4. Patent and exclusivity landscape | FTO evaluator | Listed patents by type, exclusivities, challenges and litigation, each linked to its record |
| 5. Thailand and ASEAN | FTO evaluator | Registration, patent-family leads and the latest verified status, or "unknown: verify at DIP" |
| 6. Evaluator hand-off | FTO evaluator | Missing specifications, national register checks and the claims to compare first |
| 7. References and reproducibility | Everyone | Claim-level citations with source, public date, locator and hash; search scope and failed lookups |

Every claim is labelled **known**, **unknown** or **not applicable**, and **observed**, **model estimate** or **scenario assumption**. A failed lookup reads as unknown, never as a guess. The section design follows the WIPO [*Guidelines for Preparing Patent Landscape Reports*](https://www.wipo.int/publications/en/details.jsp?id=3938) and the WIPO [FTO search guide](https://www.wipo.int/edocs/pubdocs/en/wipo_pub_1062.pdf).

> **The dossier is decision support, not an FTO or legal opinion.** Freedom to operate remains undetermined until qualified counsel assesses the product, the intended activities and the relevant claims in each jurisdiction.

## LOE-Bench: the benchmark underneath

LOE-Bench tests the forecasts behind the dossier. It asks whether a first generic will reach the US market within 12 or 24 months. Inputs are restricted to public FDA records available on the forecast date. A three-state evidence graph (M3: OPEN, BLOCKED, CONTESTED) competes with a strong drug-age baseline (B1) and a matched flat model (M1) on identical rows.

The primary endpoint models scarce evaluator capacity: **the share of later first-generic events captured when a reviewer can check only 20% of the list.** Three hypotheses are tested in a fixed sequence:

| Step | Hypothesis | Horizon |
|---|---|---|
| H1 | M3 beats B1 | 24 months |
| H2 | M3 beats M1 | 24 months |
| H3 | M3 beats B1 | 12 months |

Each step is one-sided at α = 0.025, uses a paired bootstrap that resamples whole drugs, and is tested only if the previous step succeeds. Exploratory analyses add an LLM given the same as-of evidence, competition at launch (at least three approved generic applicants within 36 months) and a Medicaid demand forecast. Each is declared before the test opens.

## How evidence stays honest

| Rule | What it prevents |
|---|---|
| **As-of inputs only.** A source counts at a cutoff only if a dated capture or publication shows it was public by then. Patent and exclusivity features come from historical Orange Book editions, never from today's file with backdated fields. | Hindsight leakage |
| **Sealed test.** Code refuses any metric on cutoffs from 2017 onward until the hash of the registered preregistration is supplied. | Tuning on the test set |
| **Disclosed exposure.** An early smoke run scored three baselines on part of the test window. The preregistration states exactly what was seen. | Hidden test reuse |
| **Prospective Track A.** Forecasts for currently unchallenged drugs are hashed, tagged and registered before any outcome exists. | Retrospective bias |
| **Matched arms and a technique ledger.** Shared improvements go to M1 and M3 under the same budget. Every idea, including rejected ones, is logged in the [technique ledger](docs/loe-bench/TECHNIQUE-LEDGER.md). | Unfair comparisons and forking paths |

Methods follow the FDA guidance [*Multiple Endpoints in Clinical Trials*](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials) (2022) for the fixed sequence and [Field and Welsh 2007](https://doi.org/10.1111/j.1467-9868.2007.00593.x) for the cluster bootstrap.

## Current status

| Item | State |
|---|---|
| Development results (validation only) | At the 20% review budget: H1 **+9.80** points [+0.14, +19.65], H2 **+5.49** [−2.00, +11.25], H3 **+13.00** [+3.27, +23.17] ([FREEZE receipt](docs/loe-bench/receipts/FREEZE.md)) |
| Confirmatory result | **None yet.** The test stays sealed until OSF registration |
| Preregistration | v2 in preparation; OSF submission planned for 7–13 December 2026 |
| Prospective Track A | Inputs frozen at tag `loe-S0-input-20261127`; forecasts frozen before 31 January 2027 |
| Dossier generator | In development; first complete one-molecule dossier due December 2026 |

The [program plan](docs/loe-bench/PLAN.md), [lane handoff](docs/loe-bench/HANDOFF.md) and [task receipts](docs/loe-bench/receipts/) record every decision, failure and data source.

## Quick start

LOE-Bench uses the Python 3.12 standard library, with optional NumPy.

```sh
cd loe-bench
python -m unittest discover -s loe_bench/tests -t .
python -m loe_bench.openfda_fetch --out ../../_private_artifacts/loe-bench/raw
python -m loe_bench.run_profile --raw ../../_private_artifacts/loe-bench/raw --out data/profile.json
```

Raw downloads stay outside Git. Each fetch writes a SHA-256 manifest; compare it with [`data/S0_INPUT_MANIFEST.json`](loe-bench/data/S0_INPUT_MANIFEST.json).

The earlier Thai-first regulatory Workbench remains available as a local Windows reader and supplies the Thai-context layer. Run [Start-PTP.cmd](Start-PTP.cmd), or `python scripts/ptp_run.py --serve --open`. [Thai open-data feasibility](docs/loe-bench/THAI-OPEN-DATA.md)

## Data and licensing

The [Apache License 2.0](LICENSE) covers the source directories listed in [NOTICE](NOTICE). Data terms differ by source:

- FDA and CMS files are public.
- The Rai et al. Hatch-Waxman court table is CC0.
- The NBER Orange Book Dataset restricts redistribution and commercial use. This repository publishes only code and download instructions for it.

Protected test records and evaluator labels stay outside the runtime. [Data boundaries](data/README.md)

## Authors

Siripon Srihangpiboon, Artificial Intelligence for Business Analytics program, and Asst. Prof. Dr. Tuchsanai Ploysuwan (advisor), School of Information Technology, King Mongkut's Institute of Technology Ladkrabang.

## Project records

- [Agent instructions](AGENTS.md) · [Claude instructions](CLAUDE.md) · [Root handoff](HANDOFF.md)
- [Owner decisions (D40, D41)](docs/maintenance/OWNER-DECISIONS-20261122.md) · [Evidence index](INDEX-PLAN.md)
- [Owner's original package](docs/loe-bench/owner-source/) · [SciSpace evidence review](docs/loe-bench/owner-source/scispace/)
- Earlier programs (IS1 retrieval, S0–S5, RA Pharma) are kept as history in the [evidence index](INDEX-PLAN.md).
