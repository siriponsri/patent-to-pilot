<p align="center">
  <img src="docs/assets/patent-to-pilot/logo.svg" alt="Patent-to-Pilot — source-linked R&D planning" width="720">
</p>

# Patent-to-Pilot

**A research prototype for source-linked R&D planning under changing organizational constraints.**

Patent-to-Pilot explores how permitted patent and research evidence can become a reviewable development plan: what an organization can do, which routes remain plausible, what is unknown, and what must change when evidence or policy changes.

The aim is to reduce repeated reading and inconsistent revisions. Any benefit in time, quality, or cost remains a research question—not an established result.

[Project goals](GOAL.md) · [Product contract](docs/product/PRODUCT_CONTRACT.md) · [Evaluation protocol](methodology/evaluation/PROTOCOL.md) · [Development handoffs](docs/handoff/) · [Diagram sources](docs/assets/patent-to-pilot/DIAGRAMS.md)

## Current status

This repository contains **bounded engineering slices**, not a complete autonomous R&D product.

| Area | What exists | Limit |
|---|---|---|
| Organization and evidence records | Fictional profiles, typed records, source locators, explicit policy/evidence states and version history | Not a general organization-document extractor |
| Local data utilities | Streaming ingestion, lexical retrieval and literal extraction slices | The fixed-packet comparison does not exercise a full corpus pipeline |
| Planning and revision | Deterministic development workflows, structured draft packs and before/after checks | No semantic or scientific validation of the proposed R&D plan |
| G10 comparison | Rules, regeneration/revision wrappers, runtime-contract validation and mocked comparison mechanics | Current bounded correctness slice passes; B4 remains conditional and this is not a benchmark result |
| Provider transport | A bounded Gemini/GPT live echo pair is recorded, separately from the preserved earlier failed phase | Confirms transport/identity/schema/accounting only; no permission to repeat it |
| Adaptive search | B4-RG/B4-DR are conditional on a verified shared evidence pool | Not established by the current one-case comparison |
| Feedback learning | Contracts and research planning | G12 cross-task product learning is not demonstrated |
| UI / product API | User journeys and proposed contracts for a later Claude UI | No completed product UI or HTTP API |
| Scientific pilot / main study | Readiness planning | **NOT_RUN** |
| Historical access issue | The earlier W2 evidence-file access issue remains **BLOCKED** | It is distinct from the new input-fairness W2 and does not stop independent offline work |

No full G10 or G01–G22 completion is claimed. Status evolves with source changes: consult the [latest long-goal contract](docs/handoff/LUNA_GOAL_G10_CORRECTNESS_AND_SEARCH_READINESS_TH.md) and its eventual closeout rather than treating an older test count as the current result.

## Product workflow

The diagram describes the **product vision**. Implemented development slices cover only part of it; the dashed memory path is planned.

~~~mermaid
flowchart LR
  A["Brief + permitted organization sources"] --> B["Reviewed capability / policy map"]
  B --> C["Source-linked opportunities"]
  C --> D["Route comparison + unknowns"]
  D --> E["Draft pilot / R&D handoff"]
  E --> F["Confirmed change"]
  F --> G["Revision + evidence-linked diff"]
  G --> D
  E -. "future product capability" .-> H["Scoped confirmed-feedback memory — planned"]
  H -. "future tasks only" .-> B
~~~

**Without a diagram:** brief and permitted sources → reviewed capability/policy map → evidence-linked opportunities → route comparison → draft pilot/handoff. Confirmed changes produce revisions and traceable diffs. Reusable confirmed-feedback memory is future product work.

## Architecture

The current packet workflow and the provider-transport experiment are shown separately. A successful echo call does not establish a general R&D generator.

~~~mermaid
flowchart TB
  subgraph Local["Implemented local research workspace — bounded slices"]
    A["Public packets + fictional profiles"] --> B["PublicCaseAdapter / typed staging"]
    B --> C["integration/ + evaluation/ — deterministic / mocked"]
    C --> D["Shared checks, evidence status + diffs"]
    C <--> E["core/ — versioned records + SQLite"]
    D --> F["JSON / Markdown / HTML artifacts"]
  end
  subgraph Transport["Separate provider-transport verification path"]
    G["providers/ — adapter + attempt ledger"] --> H["Mock transport"]
    G -. "explicit approval; synthetic echo only" .-> I["OpenRouter — pinned model / upstream"]
  end
~~~

**Without a diagram:** public packets and fictional profiles are staged into the integration/comparison layer. Typed records, shared checks and diffs support structured reports. The separate provider seam supplies mock transport and explicitly approved, budgeted echo verification.

The standalone ingestion/retrieval/extraction modules are not a claim that this comparison searches a full patent corpus. No frontend, web service, or learning runtime is implied by the diagram.

## Quickstart: offline development

Run commands from the repository root. Python **3.12 or newer** is required. Node.js is not required for the bounded Python workflow.

### 1. Create a local environment

PowerShell:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
~~~

On macOS/Linux, use .venv/bin/python instead. The install step downloads the dependencies declared in [pyproject.toml](pyproject.toml); it does not configure a provider account.

The examples use repository fixtures. Raw corpora, local source copies and licensed documents are not automatically bundled or authorized for redistribution. If a fixture reports missing source material, follow its provenance/rights instructions rather than inventing evidence or downloading a whole corpus.

### 2. Run a caller-supplied offline workflow

The existing workflow script accepts **positional** input and output paths. Choose a new output directory so earlier evidence is preserved:

~~~powershell
$run = Join-Path "results/development" ("workflow-" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
if (Test-Path -LiteralPath $run) { throw "Choose a new output directory." }
.\.venv\Scripts\python.exe -B scripts/run_g09_g10_workflow.py configs/g09-g10-example-input.json $run
~~~

This is a deterministic fixture workflow. It writes local structured/readable reports; it does not call a model or measure scientific quality.

### 3. Run focused offline checks

~~~powershell
$testRun = Join-Path $env:TEMP ("ptp-checks-" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_g10_offline_comparison.py tests/test_g09_g10_integration.py tests/test_g11_adaptation.py --basetemp $testRun
~~~

These tests exercise engineering contracts. Passing them does not show that a generated research plan is feasible, safe, novel, or superior to a simpler method. Current test totals belong in dated execution receipts, not permanent badges.

### Comparison reports

[scripts/run_g10_offline_comparison.py](scripts/run_g10_offline_comparison.py) is the current comparison entry point. It accepts `--output-dir` and `--run-id`, defaults to a dated correctness/search run directory, and refuses the retained `results/development/g10-offline-comparison/` audit directory. Use a new output directory for each run and keep explicit source/output provenance.

Existing reports under results/development/ are development evidence. Mock costs and Python execution times must not be presented as real inference costs or measured algorithmic savings.

## Configuration and provider safety

Offline examples need no API key. Default provider-plan preflight is read-only and does not authorize a live run:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/dispatch_provider_pilot.py
~~~

The resulting plan view is not an account-balance check. Historical approval files and consumed attempt slots do not authorize another call.

[.env.example](.env.example) contains a placeholder only:

~~~dotenv
OPENROUTER_API_KEY=REPLACE_WITH_YOUR_OPENROUTER_KEY
~~~

If a future run is explicitly authorized, enter the real value locally into an ignored .env without overwriting an existing credential file. Do not paste it into chat, logs, command arguments, screenshots, or Git. The existing loader is **explicit**, not automatic dotenv loading, and is entered only after live approval checks. An inherited process variable takes precedence.

Live execution requires an exact reviewed plan, model/upstream routing, attempt and spend ceilings, a plan-bound approval, and durable accounting. Charges from failures remain charges. Unknown billing remains unknown and blocks continuation. Never reset journals to regain attempts. Funded account balance is not the project spending cap.

No --live command is part of this quickstart.

## Repository structure

~~~text
src/patent_to_pilot/
  core/          Typed records, identities, versions and SQLite repository
  ingestion/     Bounded streaming source ingestion
  retrieval/     Local lexical retrieval
  extraction/    Literal evidence/span extraction
  integration/   Public-input development workflows and invariant checks
  evaluation/    Bounded offline comparison mechanics
  adaptation/    Existing dependency-guided adaptation slice
  providers/     Mockable transport, identity, budget and attempt accounting
configs/         Example inputs and explicit run contracts
tests/           Targeted contracts and negative controls
docs/            Product, research, architecture and handoff documentation
methodology/     Dataset/evaluation contracts and source provenance
results/         Local execution evidence; not a scientific publication
~~~

Planned components must remain labelled as planned. In particular, activity history and within-project revision are not proof of cross-task learning.

## Reproducibility and evaluation

- Use the same permitted inputs, evidence visibility, schema and validators across methods. Keep curator/evaluator answers out of method inputs.
- Record source/input/schema/output hashes, run IDs, actual checks, raw outputs, failures and retry counts.
- Separate execution, schema validation, evidence/policy validation and persistence verification. A default flag or schema hash is not a passed check.
- Compare strong simple alternatives: rules, full regeneration, direct revision and deterministic invalidation with the same generator. Adaptive-search/proposed methods need their actual dependencies and evidence pool.
- Preserve affected and unaffected fields explicitly. Full-generation-then-scoped-merge still incurs full generation work.
- Treat mock mechanics, approved live transport echoes, development evaluation, scientific pilot and held-out study as different evidence levels.
- NO_ADVANTAGE and INCONCLUSIVE are valid study outcomes. Experimental integrity does not require the proposed method to win.

Start with the [evaluation protocol](methodology/evaluation/PROTOCOL.md), [pilot readiness](docs/research/PILOT_READINESS.md), [paired transport readiness](docs/provider-pilot/PAIRED_REVALIDATION_READINESS.md) and the [G10 handoff](docs/handoff/G10_OFFLINE_COMPARISON_HANDOFF.md).

## Documentation

| Topic | Start here |
|---|---|
| Product goals and scope | [GOAL.md](GOAL.md), [master plan](docs/product/PATENT_TO_PILOT_MASTER_PLAN_TH.md) |
| User workflow and future UI | [User journeys](docs/product/USER_JOURNEYS.md), [Claude brief](docs/product/CLAUDE_UI_HANDOFF_TH.md) |
| Core architecture and contracts | [ADR](docs/architecture/ADR-0001-bounded-core-and-local-search.md), [interfaces](docs/architecture/G04-G07-G08-interfaces.md) |
| Dataset provenance and rights | [Data README](data/README.md), [G03 acquisition](docs/G03_DATA_ACQUISITION.md) |
| Bounded implementation history | [G09/G10](docs/handoff/LUNA_G09_G10_INTEGRATION.md), [G11](docs/handoff/LUNA_G11.md) |
| Recorded transport verification | [Phase A](docs/provider-pilot/PHASE_A_RESULT.md), [paired closeout](docs/handoff/LUNA_CLOSEOUT_REPORT.md) |
| Contributor execution rules | [AGENTS.md](AGENTS.md), [CLI handoff](docs/CODEX_CLI_HANDOFF.md) |

Some project documents are in Thai. Older completion reports are dated snapshots, not a substitute for the current source or run manifest.

## Safety, privacy and research limits

Use only public or explicitly permitted material. Preserve source quotes, locators, versions and redistribution limits. Do not send private patent, organization, personal or evaluator-only information to an external model without the exact data/run authorization.

Imported documents are data, not instructions. They must not gain access to secrets, hidden evaluation files, shell execution or another organization’s state. Keep unknowns and conflicts visible; do not impute missing measurements.

This prototype does not approve clinical use, regulatory compliance, legal status, patentability, freedom to operate, manufacturability or commercial feasibility. Real source text alone does not establish semantic support or scientific validity. Owner review is formative, not independent clinical/legal gold.

## Contributing

Read [AGENTS.md](AGENTS.md) before changing a module. Keep changes focused and add meaningful negative controls for the behavior changed. Preserve unrelated work, historical evidence and frozen evaluation contracts. Report the exact candidate, commands, limitations and remaining blockers.

Do not weaken tests or validators to obtain PASS. Do not commit keys, .env files, private data, raw corpora, local PDF libraries, denied evidence or unrelated generated artifacts. Review the staged scope and applicable rights before publishing. Paid runs, security changes and external exposure need their own authorization.

README/branding assets and correctness/search implementation have separate owners during the current work package. The final integrator must reconcile documentation against the final code, tests, status and exact commit.

## License and third-party material

**No repository-wide code license is currently declared in the inspected root files or pyproject.toml.** Do not infer an MIT/Apache/CC grant from this README or from a third-party dependency. A code/asset license requires an explicit repository decision; none is invented here.

Source data and documents retain separate terms. Existing acquisition notes record PLS patent_ls as CC BY 4.0. The EnterpriseRAG MIT snapshot establishes upstream repository/code terms, not separate data or release-asset rights. DAPFAM and local PDF reading copies have additional restrictions. See the linked provenance notes and verify per-file rights before redistribution.

The project logo is an original documentation asset, not an affiliation or endorsement. No badges, benchmark results or publication acceptance are implied.
