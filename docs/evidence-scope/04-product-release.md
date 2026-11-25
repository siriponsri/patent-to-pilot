# S4 · Validate and release the Thai-first Workbench

**Status:** NOT_STARTED. **Lane:** Product. **Entry:** the reproducible S2 alpha. **Exit:** evidence for a named distribution state and a handoff to S5. [Master plan](MASTER-PLAN.md) · [S2 Workbench](02-product-workbench.md) · [Research freeze](FREEZE.md)

This phase can proceed while S3 evaluates research. Pin the S2 policy used for the release candidate. Publish its measured engineering and user outcomes separately from retrieval comparisons. An eligible lexical or deterministic release can proceed while an optimized policy is still being evaluated.

## Work packages

| Task | Procedure for the execution agent | Receipt or decision |
|---|---|---|
| **S4-T01 · Define the distribution** | Start with a local, single-user Windows Workbench. Record the exact commit or candidate artifact digest, supported Python version and SQLite FTS5 requirement, dependencies, optional PDF and Thai extras, model policy, installation steps and source-pack rights. Name the supported input formats and what happens to a scanned, encrypted or unreadable PDF. Offer only the modes that work with this installation. | Release manifest identifies code, dependency/model revisions, third-party notices, lawful demo assets, supported operating system and launch command. Real data that must be obtained by the user has a working, permitted import path, separate from a fully offline sample. Source licenses for the app, content and weights have separate entries. |
| **S4-T02 · Exercise a clean install** | Follow the documented installation in a clean supported environment outside the developer's store. Run the doctor and isolated smoke below. From a fresh app data directory launch the UI with a single command, stop it, restart it, and open the same run. Repeat without external providers. Check occupied-port behavior and a missing optional dependency. Capture each exact command, exit status and relevant error. | One reproducible launch and restart on the claimed platform, correct local status, ordinary errors explained, and citations resolving after restart. A missing optional provider can be marked untested without blocking a functioning local release. Offline operation is claimed only for the inputs actually exercised offline. |
| **S4-T03 · Prove two public demo journeys** | Use one rights-cleared Thai law family and one English patent family from S2, each disjoint from scored evaluation families. Run the scripts in the table below through the normal UI with its pinned executor, then inspect its export. Where permitted, archive compact captures and scrub private paths. Use the same locale, corpus snapshots and query for a repeat. | A clean user can select the project, ask in Thai, inspect edges and citations, compare source scopes and reopen the exported evidence on the pinned originals. Mark each claim independently. A screenshot of a prototype cannot complete this task. |
| **S4-T04 · Verify withdrawal, errors and recovery** | Reuse [the selective-revision harness](../../scripts/verify_selective_revision.py) and [prior D3 evidence](../tracking/owner-note-22112026/receipts/P4-T04_revision_comparison.md). Test the actual supported source-change path. If the release supports withdrawal, compare the revised result with a clean rebuild after excluding the withdrawn source. Check old traces in the history view and current citations in the latest view. Test an invalid edge target, unresolved date, stale export and corrupt or missing optional pack. Use a fresh store and the CLI backup option to exercise recovery. | A changed or withdrawn source cannot provide active current support. Historical evidence retains exact source identity and its historical status. A release without withdrawal can ship a documented rebuild-in-new-workspace route if tested end to end. Record D3 as outstanding in that case. |
| **S4-T05 · Decide alpha, public demo or field pilot** | Compare the actual evidence to the levels below. Write the product status, limitations, known issue list, versioned artifact and reproducible instructions. The solo owner can complete the local tasks. For any later real-user pilot, record role, consent, task, cost/time definition and data permissions before observation. Make publication/deployment actions only in the delivery context that authorizes them. | Each supported level has its own evidence. Record whether anything was actually published and the access point if published. A local build, independent user study and business deployment have distinct outcomes. S5 can consume local evidence or a bounded demo, including mixed results or deferred distribution. |

## Clean-install evidence

Use the candidate's documented Python environment in a sandbox or a fresh user profile. Substitute a dedicated QA directory for `<fresh-directory>` and retain it during the restart check. In the repository checkout the existing launcher supports:

```text
python scripts/ptp_run.py --doctor --data-dir "<fresh-directory>"
python scripts/ptp_run.py --smoke
python scripts/ptp_run.py --serve --open --data-dir "<fresh-directory>"
```

The [Windows entry point](../../Start-PTP.cmd) also supports a single launch command from the repository root, e.g. `Start-PTP.cmd --data-dir "<fresh-directory>"` in Command Prompt. Verify whichever entry point the release instructions advertise. The existing [smoke](../../scripts/ptp_run.py) exercises a fictional sample in a temporary store; add separate checks for the S2 journeys. Record host, app version, cold/warm state, elapsed time and local/offline status. A user can stop the local server without terminating an unrelated process.

## Acceptance scripts

| Journey | What the reader does | What the verifier measures |
|---|---|---|
| Thai law revision | Ask about an identified section, inspect its Thai quotation and commencement source, then switch edition or date. Open an explicit reference edge and an inferred relation if available. | Exact version, locator and source text; correct distinction between publication and effective date; expected changed and unchanged conclusions; accessible text alternative for the node/edge display. Ambiguous applicability stays unresolved. |
| English patent explained in Thai | Select a dependent claim, compare it to its named parent, inspect the original English next to the Thai explanation and export. Reopen an edge to a parent feature and one to an added qualifier. | Claim identifiers, original spans and translations point to the same publication and claim context. A feature disclosed in a different example is labelled separately. The export retains enough identity for another local reader to replay the citations. |
| Partial evidence | Remove a permitted test input in a disposable project or import a packet with the critical part omitted. Run the same question. | The missing support is identified; the UI continues to show verified independent support and does not combine an incompatible passage into a definitive answer. |
| Practical task comparison | If another product is used to support a comparison claim, supply the same permitted sources and task, document access tier, language, feature limits, participant and timing protocol. | Report accuracy, time and failures for the completed comparison only. Keep an access-limited competitor feature unknown. Useful market anchors are [FourCorners](https://fourcorners.law/), [DIP IP Search](https://search.ipthailand.go.th/invention-patent) and [LightRAG](https://github.com/HKUDS/LightRAG). |

## Release levels

| Level | Minimum evidence | Permitted status |
|---|---|---|
| **Local alpha** | Reproducible local launch, both language paths on identified fixtures or permitted real sources, at least one resolvable citation per journey, a tested unsupported/partial-answer path, open limitations. | Technical alpha available locally. Continue product work when an external source, observer or optional provider is deferred. |
| **Public-data demo ready** | Clean-install receipt; both journeys validated on disclosed, permitted real sources; scoped changed/unchanged checks; exact locators; rights-cleared distribution or documented lawful import. An authorized release channel and actual link are also required to say it is published. | Record ready, released or partial according to the evidence. Demonstration may be local even when its inputs are public. |
| **Observed field or governance use** | An actual authorized operator uses the real workflow. Report task completion, median time to first verified evidence, wrong-scope acceptance and any observed corrections, with denominators and context. | Business or governance value remains unmeasured until users and observations exist. The local demo can close S4 without a customer or an independent usability study. |

The softer progression gate applies to continued delivery. Missing source rights, cross-version citation errors or text presented as definitive despite missing evidence narrow the shipped scope or defer that feature. A negative research score cannot prevent a qualified Workbench release. Product release evidence cannot establish a research score win.

## Reporting, restart and handoff

Write the proposed future receipt to `docs/evidence-scope/receipts/S4-product-release.md` and record the chosen release level, exact supported paths, evidence links, distribution state, issue ownership and next action. Keep large captures and licensed originals outside Git. Record opt-in provider cost from the ledger if actually measured. Treat unknown cost as unknown.

If the clean-install or source-path check fails, keep the failure and affected version, make the smallest repair, and rerun the failed path plus its dependent journeys from a fresh store. Preserve original reports and already pinned inputs. After S4, give S5 the reproducible launch instructions, release manifest, availability state, graph/export artifact references and the boundary between observed and anticipated impact. This phase plan records no execution or release.

## Dispatch status

| Task | State | Receipt |
|---|---|---|
| S4-T01 | NOT_STARTED | Pending |
| S4-T02 | NOT_STARTED | Pending |
| S4-T03 | NOT_STARTED | Pending |
| S4-T04 | NOT_STARTED | Pending |
| S4-T05 | NOT_STARTED | Pending |
