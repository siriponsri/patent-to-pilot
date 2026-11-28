# Planner responses to the external review

Main planner (Claude Opus 5.5). Each round of external review by the co-planner (GPT-6.2 Astra high) is answered here with a fix, a disclosure or evidence. The research track closes only when a fresh round reports NO REMAINING DOUBT (owner decision, 28 Nov 2026, 21:46).

## Round 1 ([review](EXTERNAL-REVIEW-R1.md), answered 28 Nov 2026, 22:24 Bangkok)

| ID | Severity | Response | Where |
|---|---|---|---|
| R1 | BLOCKING | **Fixed.** The 0a5ff7f5 signature is relabelled a completed milestone for historical results, archive and records. Final closure is OPEN with a new blocking checklist row for this review. Succession gets its real disposition: owner-accepted best-effort custody, deployment due before 27 Nov 2027, an operations item rather than a closure condition, with late self-service scoring valid in the meantime. | [Checklist](../RESEARCH-COMPLETION.md) status line, succession row, two closure rows; [JOINT-SIGNOFF](../JOINT-SIGNOFF.md) status clarification |
| R2 | MAJOR | **Fixed.** US-only now rests on M3 as the sufficient ground. The decision states that materiality is undecided: the fixed-calendar +0.20 pp is a ceiling effect, the earlier-readout route was not simulated, measured and simulated denominators differ, burden straddles the limit, and the measured-rate rerun was omitted on purpose. +11.95 pp at +1.36 pp stays descriptive. | [Decision](../JURISDICTION-DECISION-RULE.md#final-decision-planner-28-november-2026-2209-bangkok-by-the-system-clock) |
| R3 | MAJOR | **Fixed (22:45, TRACKA-READOUT2 merged).** The first published 12-month result controls H3, identified by the SHA-256 of `results.json` and of its FDA source manifest. The workflow stores it as GitHub release assets (no 90-day expiry) and the 24-month run discovers and verifies it automatically. A missing or invalid original yields a labelled `REVISED_VINTAGE` with both dates, never a silent substitution. Fixture tests cover discovery, digests, the missing original and a synthetic FDA revision (10 versus 11 event rows); a synthetic GitHub dispatch passed. **Disclosed:** production release writes, issue writes and Worker deployment are NOT_RUN until the first maturity; the addendum is committed publicly but not filed on OSF (an optional owner filing). | [Receipt](../receipts/TRACKA-READOUT2.md), [addendum](../TRACKA-READOUT-ADDENDUM.md), [guide](../HOW-TO-SCORE-TRACK-A.md) |
| R4 | MAJOR | **Fixed with dated limitations (22:45).** [Measure map](../TRACKA-MEASURE-MAP.md) quotes the filed text (OSF keys 72-20, 72-59, 72-61; U1–U4) for each measure's scope. `tracka_secondary` v1.0.0 adds ten-bin ECE, probability-only AURC80 and E-AURC, distinct event-drug capture, flag and referral workload, decision loss and auto-clear safety with the registered interval, with known-answer tests. NOT_ESTIMABLE from the public freeze: the legacy 90% confidence policy (threshold and per-row calls not in the package), predictor missingness and cross-cutoff drift (one t0). The primary scorer, frozen forecasts and filed records are unchanged. | [Receipt](../receipts/TRACKA-READOUT2.md) |
| R5 | MAJOR | **Fixed (disclosure).** The benchmark card now separates public aggregate verification, controlled export recomputation (REPRO-C1) and exact source-to-result replay (NOT_RUN), and states the time-dependent OSF gate in the historical SCORE entrypoint. | [Benchmark card](../BENCHMARK-CARD.md), access and limits |
| R6 | MINOR | **Fixed.** Both documents now say the rule and the window were committed first, and the detailed manifest arrived with the counts, so the counts are descriptive. | [Decision](../JURISDICTION-DECISION-RULE.md), [JURIS-COUNT planner note](../receipts/JURIS-COUNT.md#planner-provenance-note-28-november-2026-2223-bangkok) |

Next: a fresh round 2 (EXTREV-R2) verifies all six responses against the frozen record.

## Round 2 ([review](EXTERNAL-REVIEW-R2.md), answered 28 Nov 2026, 22:54 Bangkok)

| ID | Severity | Response | Where |
|---|---|---|---|
| R1 remainder | (partial) | **Fixed.** The handoff close-out row now says OPEN and names the milestone. The superseded checklist instruction is dated and points to the external review row as the only remaining gate. | [Handoff](../HANDOFF.md), [checklist](../RESEARCH-COMPLETION.md) |
| R2 remainder | (partial) | **Fixed.** The jurisdiction table says the burden straddles the 1 h limit. The handoff no longer calls the increment immaterial or asks for a rerun; it names M3 as the sufficient ground and the earlier-readout route as unevaluated. | [Decision](../JURISDICTION-DECISION-RULE.md), [handoff](../HANDOFF.md) |
| N1 + R3 remainder | BLOCKING | **Fixed (23:12, TRACKA-READOUT3 merged).** Formal H3 now comes only from canonical discovery in the registered scope (repository, version DOI, OSF freeze digest). Supplied, omitted and wrong-pin archives are `UNVERIFIED_INPUT` and `DESCRIPTIVE_ONLY` with `reached=false`; with identical FDA bytes the only formal H3 is the original +33.33 pp [+20.00, +57.14]. A revised vintage is formal only through a negative discovery record (scope, locations, UTC query times) that the 24-month publication pins. | [Receipt](../receipts/TRACKA-READOUT3.md), [readout](../../../loe-bench/loe_bench/tracka_readout.py) |
| N2 | MAJOR | **Fixed.** Release-notes-only recovery verifies; conflicting release and issue pins, a second conflicting issue, a disagreeing manifest pin, missing publication pins and altered asset bytes are each refused, leaving H3 descriptive with the disposition recorded. | [Receipt](../receipts/TRACKA-READOUT3.md), [vintage](../../../loe-bench/loe_bench/tracka_vintage.py) |
| N3 | MAJOR | **Fixed (fixture).** Both horizons publish scoped first-result release assets with four digests in the notes and issue. After deleting the transient directory the fixture retrieved the exact original 24-month JSON, manifest, report and draws, including 12 missed clears with the original upper bound and FAIL disposition. **Disclosed:** production release and issue permissions are NOT_RUN until deployment; a synthetic GitHub run passed 15 tests with production jobs skipped. | [Receipt](../receipts/TRACKA-READOUT3.md), [run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46163617027) |

Next: a fresh round 3 (EXTREV-R3) verifies the round-2 responses.

## Round 3 ([review](EXTERNAL-REVIEW-R3.md), answered 28 Nov 2026, 23:19 Bangkok)

Resolved by the reviewer: R1, R2, N3. Partially resolved: R3, N1, N2, carried into the new findings below.

| ID | Severity | Response | Where |
|---|---|---|---|
| R3-A (with R3, N1 remainder) | BLOCKING | **Fixed (23:38, TRACKA-READOUT4 merged).** The formal family at each horizon is the first canonical publication in the registered scope, created only by the live-fetch publication path. Runs with a caller-chosen snapshot or without publication are `PROVISIONAL` for the whole family (`publication_eligible: false`); runs after a first publication are `REPLAY` with a difference report. Regressions cover two covered snapshots with a fixed 12-month publication and with documented absence, the single canonical family, and a second canonical attempt becoming REPLAY. Production publication NOT_RUN until deployment. | [Receipt](../receipts/TRACKA-READOUT4.md), [run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46165897749) |
| R3-B (with N2 remainder) | MAJOR | **Fixed.** All trusted issue witnesses are collected and validated before absence is classified; agreeing witnesses permit the predeclared fallback, conflicting or malformed ones give `DISPUTED` with H3 descriptive and every locator recorded. Tests cover agreeing, conflicting and malformed issue-only cases. | [Receipt](../receipts/TRACKA-READOUT4.md), [vintage](../../../loe-bench/loe_bench/tracka_vintage.py) |
| R3-C | MINOR | **Fixed.** The owner-action list marks the Zenodo deposit and restore as done and links the DOI and RESTORE-DOI. | [Checklist](../RESEARCH-COMPLETION.md) |

Next: a fresh round 4 (EXTREV-R4).

## Round 4 ([review](EXTERNAL-REVIEW-R4.md), answered 28–29 Nov 2026, 23:49 Bangkok)

Resolved by the reviewer: N2, R3-A, R3-B, R3-C. Partially resolved: R3, N1 (carried into R4-A).

Planner design to end the custody regress (assigned to TRACKA-READOUT5, Sol xhigh):

| ID | Severity | Planned response |
|---|---|---|
| R4-A | BLOCKING | **Blind capture before scoring.** A scheduled capture job, triggered automatically by the Worker cron on or after maturity, fetches the FDA sources, computes no outcomes, and publishes the raw bytes and their digests as a scoped capture release. The formal family may use only the **first capture release on or after maturity**. Scoring, retries and late runs read those preserved bytes and never refetch. A failed publication after scoring therefore cannot change the input. If no capture can be established for a horizon, the family is descriptive only. |
| R4-B | MAJOR | **Independent provenance.** Capture and result files receive GitHub artifact attestations (Sigstore), recorded in the public Rekor transparency log with repository, workflow, commit and time, so evidence survives deletion of the release, tag or issue. Discovery checks the attestation. The trusted-custodian and retention assumptions are stated. If continuity cannot be established, the disposition is UNRESOLVED_CONTINUITY and H1–H3 are descriptive only. |
| R4-C | MAJOR | Compute the legacy 90% policy from the public thresholds and calibrated probabilities: realized coverage, policy AURC80 where coverage reaches 80%, E-AURC with its coverage condition. Fixture-test against the frozen action rules. Correct the measure map and guide. |
| R4-D | MINOR | Add a dated clarification file that links the current guide and canonical result location. The Zenodo landing-page description can only be edited from the owner's login, so the paste-ready text goes into the 06:00 owner brief. The timestamped ZIP stays intact. |

**Round 4 outcome (29 Nov, 00:18, TRACKA-READOUT5 merged).** R4-A: the capture step saves the FDA index and raw exports before outcome resolution; only the first attested capture within the admission window (maturity plus a predeclared weekday grace period) can feed the formal family; the two dated fictional editions that gave H1 PASS and FAIL now yield one formal result, retries reuse the capture digest, and a missing capture gives `UNRESOLVED_CONTINUITY`. R4-B: capture and result attestations bind scope, bundle digest, workflow identity, run and commit; altered metadata, conflicting digests, missing archives and modified bytes are rejected; a custody hold is prescribed. R4-C: `tracka_secondary` v1.1.0 reproduces the legacy actions; public answered counts 578/637/527 (12 m) and 571/597/592 (24 m) of 651 meet 80% coverage, none meet full coverage. R4-D: [clarification](../ZENODO-CLARIFICATION.md) delivered; the Zenodo description edit is an owner action. Production capture, attestation and publication remain NOT_RUN until 27 Nov 2027. [Receipt](../receipts/TRACKA-READOUT5.md)

Next: EXTREV-R5.


## Round 5 ([review](EXTERNAL-REVIEW-R5.md), answered 29 Nov 2026, 00:32 Bangkok)

Resolved by the reviewer: N1, R4-A, R4-C, R4-D (repository part). Partial: R3 and R4-B, both through R5-A.

| ID | Severity | Response |
|---|---|---|
| R5-A | BLOCKING | **In progress (TRACKA-READOUT6, Sol xhigh).** One shared promotion gate for fresh and resumed 24-month drafts: rediscover the 12-month result with the same witness rules, reconcile it with the staged H3 reference, and keep the draft unpublished while any conflict persists. Tests: the reviewer probe, an uncontested retry publishing the original bytes, and a staged-reference mismatch. |
| R5-B | MINOR | **In progress (same card).** One documented maintainer issue body with the result and manifest digests; the Worker and the reader accept the same format, and an incomplete marker no longer stops dispatch. |

**Round 5 outcome (29 Nov, 00:46, TRACKA-READOUT6 merged).** R5-A: fresh and resumed drafts share one promotion gate that rediscovers the 12-month result and reconciles it with the staged H3 reference; a conflict or mismatch keeps the draft unpublished, and the uncontested retry publishes the original bytes. R5-B: one maintainer issue body with digests is accepted by both the Worker and the reader; an incomplete marker is logged and dispatch continues. Production publication NOT_RUN until 2027. [Receipt](../receipts/TRACKA-READOUT6.md)

Next: EXTREV-R6.

## Round 6 ([review](EXTERNAL-REVIEW-R6.md), answered 29 Nov 2026, 00:55 Bangkok)

Resolved by the reviewer for first publication: R3, R4-B, R5-A, R5-B. No blocking finding remains.

| ID | Severity | Response |
|---|---|---|
| R6-A | MAJOR | **In progress (TRACKA-READOUT7).** Post-publication rule: the first 24-month aggregate keeps its bytes, decisions and date. Every replay or recovery report states "formal as verified at publication on <date>" and, separately, a current re-run of the 12-month witness check (VERIFIED_CONSISTENT, or CURRENT_DISPUTE or UNRESOLVED_CONTINUITY with locators). A later dispute is reported for custodian reconciliation and never rewrites the published family. |
| R6-B | MINOR | **In progress (same card).** Failed recovery reports the actual discovery reason and locators; the missing-capture message is reserved for a missing capture. |

**Round 6 outcome (29 Nov, 01:08, TRACKA-READOUT7 merged).** R6-A: replay and recovery state the publication-time formal status with its date and a freshly re-run 12-month witness check with locators; published bytes never change. R6-B: failed recovery reports the actual discovery reason and locators. The only change in `score_release.py` is report-rendering text; computations are unchanged. [Receipt](../receipts/TRACKA-READOUT7.md)

Next: EXTREV-R7.

## Round 7 ([review](EXTERNAL-REVIEW-R7.md), answered 29 Nov 2026, 01:17 Bangkok)

Resolved by the reviewer: R6-A, R6-B; forecasts, manifest, tag and primary statistics pass.

| ID | Severity | Response |
|---|---|---|
| R7-A | BLOCKING | **Accepted; planner error.** The planner approved a report-only edit to `score_release.py` without checking that the release kit pins installed source hashes. **In progress (TRACKA-READOUT8, Sol xhigh):** restore every pinned file byte for byte, move the rendering into an unpinned readout module, and add a regression test using the real published source-pin map. Rerun the DOI smoke check and the round-6 probes. |

**Round 7 outcome (29 Nov, 01:32, TRACKA-READOUT8 merged).** All 25 pinned source files match the published pins; `score_release.py` is restored to blob `7ea6b666` (planner-verified identical to the pre-READOUT7 bytes). The READOUT7 rendering now lives in the unpinned readout module and is written before the run-manifest digest. A regression test and a CI check use the real published pin map. DOI smoke check at 12 months before maturity: `PENDING`, exit 0, in ordinary and recovery modes; round-6 probes pass. [Receipt](../receipts/TRACKA-READOUT8.md)

Next: EXTREV-R8.
