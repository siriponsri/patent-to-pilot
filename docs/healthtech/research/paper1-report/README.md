# Paper 1 report tooling

- `render_paper1_test_report.py` (standard library only): turns an evaluator `summary.json` (dev or test) into the Markdown tables R1-R7 that the manuscript placeholders refer to. It formats existing numbers only, re-applies the frozen gatekeeping rule as a consistency check (exit code 2 on any mismatch), and reads generation/retrieval costs from the settlement receipts. Missing receipts are shown as `_PENDING_`.
- `dev-S5-tables.md`: the tables rendered from the real S5 dev evaluation (descriptive; no verdicts).
- Synthetic test input and its rendering (fake values, for tests only): `tests/fixtures/paper1_report/`.
- Tests: `python -m pytest -q tests/test_render_paper1_test_report.py`.

After the single S8 test evaluation:

```bash
T=docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112
python docs/healthtech/research/paper1-report/render_paper1_test_report.py $T/paper1-s8-eval/terminal-observation.json --dev $T/paper1-s5-eval/terminal-observation.json --receipts $T --out docs/healthtech/research/paper1-report/test-S8-tables.md
```

Then fill the `[[R…]]` placeholders in `../PAPER1-MANUSCRIPT-DRAFT.md` and keep one conclusion branch (rule in its section 9).
