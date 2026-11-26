# Issuer-shaped handoff conformance

**PASS for six exposed engineering cases. NULL against exact lookup.** Versioned three-specialist handoff and the strong exact composite-key lookup made the same reads and produced the same correct replies and abstentions. The ID-only negative routing control used the same verifier and missed one supported response after opening a different applicant's record.

## Source and scope

The [Thai FDA THAIRIMS operator page](https://drug.fda.moph.go.th/operators-guide/submit-application-drug) lists the tracking-table DOCX example dated 10 September 2024, media ID 673722105321365504. One direct publisher download matched the independent Planner digest. Raw local bytes are 31,521, SHA-256 `cf7a4e45068858898004c37139e3799c7551aa8beea6b7c32c9f54b1f8a2b2e6`. First table, rows numbered including the header, has six rows. Rows 3–4 share the example application in column 1. Round numbers 1–2 occur in column 3, sequence strings `0000` and `0001` in column 2. The initial filing row 2 differs in application. The parser concatenates adjacent Word text runs inside each paragraph and preserves leading zeros. No issuer example text or identifiers are reproduced here. Local inspection serves structure only under the [Thai FDA site policy](https://www.fda.moph.go.th/website-policy/).

All applicant packets, conflicts and drafts were authored stand-ins. The source replay verifies structure, not a particular applicant case. The independent evidence key was defined separately from the runner. The patent stage links the earlier edition-specific claim chart in its own evidence role. It never resolves the applicant attachment request. Sign-off, FTO, regulatory merits and use in a deployed dossier were outside this check.

| Arm | Correct replies | Correct abstentions | Unsupported outgoing | Missed support | Harmful stops | Logical record opens | Catalog checks |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed exact lookup + scoped verifier | 3 | 3 | 0 | 0 | 0 | 3 | 8 |
| Versioned handoff + scoped verifier | 3 | 3 | 0 | 0 | 0 | 3 | 8 |
| ID-only lookup + scoped verifier | 2 | 3 | 0 | 1 | 1 | 6 | 8 |

The exact arms opened the current stand-in in the current and wrong-applicant cases and the first witness in the equivalent-witnesses case. They opened no records for prior round, wrong sequence or missing attachment. The ID-only arm opened a wrong applicant once, a wrong round once, and a wrong sequence twice, including the prior-round mismatch. It also opened the patent under the shared ID, with mismatching role and issuer. The verifier prevented all four misroutes from producing any unsupported reply. Its premature stop with a valid applicant witness still available caused the one missed supported reply. With equivalent witnesses all arms issued the same correct source locator after one open. Leaving the second valid witness unread caused no harm.

## Frozen run and reproduction

[Protocol](PROTOCOL.md) and [key](conformance-key.json) specify the exact scope and judgment. [Freeze](freeze.json) SHA-256 is `90fc4da37bb8c998db612a86760226af679dbed4e93e108b20f2bdc8e9281c0b`. The one retained private trace at `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ra-handoff-20261126/original.json` is 35,684 bytes, SHA-256 `07bdf52a1596872e2404a8322a87000a5b8926bece93725fa414a034486a24be`. The raw DOCX and local JSON outcomes remain there. The separately run evaluator checks the trace hash before reading its frozen key. The trace has the per-case selected record, mismatch fields, reply or attachment request and patent reference. Counts label logical opens of authored stand-in records, not real attachment file I/O.

```powershell
$data = 'C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ra-handoff-20261126'
rtk proxy python scripts/research/ra_pharma/handoff_score.py (Join-Path $data 'original.json') 07bdf52a1596872e2404a8322a87000a5b8926bece93725fa414a034486a24be
```

Capture took 4.94 ms including DOCX, patent provenance and fixture parsing through in-memory trace assembly. CPU was zero at timer resolution. No paid cost, model calls, GPU or submission. The suite exercises Word runs and the duplicate-witness guard directly. The focused suite passed 2/2.

## Boundary for the next architecture question

Exact lookup works when all discriminating scope keys are visible before opening. Preserve it as the baseline and product contract for this class. A fresh, separately frozen controlled comparison can hide some scope and make the next decision materially compete under an interruption cap. An exploratory prefix reconstruction of the older claim trace showed the shared and cached readers reached their same four-read endpoint at different intermediate rates. This observation motivates a fresh safe-completion-at-interruption design and leaves the frozen claim result NULL. The later study needs a separately derived key, shared observations, and a strong nearest-complete choice rule.

## Code gate

The CPython 3.12.10 S4 QA profile used fresh short basetemp ptp-ra-handoff-r1. Full pytest recorded 2,797 passed, 8 failed, 10 skipped and 1 xfailed in 253.95 s, exit 1. The eight failure IDs match the standing SACR exceptions. Private pytest.log SHA-256 4eb1b2cc8bb4274dea47a1c67b9bd3399b885e029da3f6a54047a02a492c2674.
