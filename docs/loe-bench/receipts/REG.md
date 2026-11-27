# REG receipt

## Result

**PASS for the executor deliverable.** [Regulatory rule inventory](../REGULATORY-RULES.md) records code locators, primary-source rules, verdicts and conditional forecast effects. REG was cut from `3f6482237fbc03d3a174bf0c09d1d33b0208dccb`, verified against `origin/research/loe-bench` before the branch was created. The test seal remained intact. No protected dataset, research outcome scoring or model comparison was run.

The sole code change keeps a matched, undated FDA Paragraph IV row `UNKNOWN` unless a dated witness establishes `TRUE`. The E7 and E7b distinction between observed challenge evidence and evidence from the patent clock still applies. Clock scope, waiver, patent counting, filing and stay mechanics, and prompt wording are flagged in the rule inventory for planner disposition.

## Evidence

- The [source ledger](../REGULATORY-RULES.md#primary-sources-opened) records the URLs opened on 27 November 2026, editions, exact rule locators and available SHA-256 digests. The [owner architecture](../owner-source/package-docs/05-ARCHITECTURE-SPEC.md) and [risks and legal scope](../owner-source/package-docs/09-RISKS-ETHICS-LEGAL.md) were checked as design evidence.
- **FAIL before fix, expected.** The [regression fixture](../../../loe-bench/loe_bench/tests/test_e7_challenge.py#L70) reproduced `FALSE` for both a `pre-MMA` row and a blank date.
- **PASS after fix.** Python 3.12.10, from `loe-bench`: `python -m unittest discover -s loe_bench/tests -t .`. 148 ran, exit 0. The suite emitted existing Purple Book file-handle warnings.
- **FAIL with the eight accepted pre-existing failures only.** Python 3.12.10 and pytest 8.4.2, repository root: `python -m pytest`. Exit 1, with 2,760 passed, 50 skipped, 1 xfailed and 8 failed. All eight failures were the four budget variants each in `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`, matching the standing exception in AGENTS.md.

## Failures and limitations

Two alternate U.S. Code URL attempts failed and were replaced with GovInfo section PDFs. Current eCFR section text was readable in web research. Local byte retrieval reached an access interstitial, so the receipt uses the annual GovInfo CFR counterpart for the digests. No external regulatory or patent expert reviewed the result. The first-final-approval endpoint is a triage proxy for market entry. Litigation outcomes, settlements, at-risk launches and authorized generics are outside the model. The open mismatches have no measured prediction effect in this card.

## Next action

The co-planner cross-checks the primary-source mapping and open flags under criteria v3. The main planner reviews REG for integration, records the disposition in the lane handoff and memory, and makes the endpoint and absence of expert adjudication explicit in the manuscript. Any changed feature, comparator or prompt needs its intended endpoint and scope settled before the corresponding evaluation freeze.
