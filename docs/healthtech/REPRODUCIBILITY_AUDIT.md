# Reproducibility audit — HealthTech migration

Audited published base: `5152ba450324e783d4c8d50e35bc986568d2ced8` The original [verification receipt](verification.json) remains an immutable dated record. This audit corrects coverage selection and a local test dependency; it does not change the governing HealthTech thesis or claim new scientific results.

## Why 262 differed from 185

All 17 test modules were already tracked/published. `--suite all` collected the whole tests directory (262 cases); the original default `--suite public` explicitly selected 12 modules (185 cases). No missing or untracked test modules explain the difference. The five omitted modules were:

| Module | Cases omitted from original public cohort |
|---|---:|
| `tests/test_provider_env_file.py` | 23 |
| `tests/test_provider_identity.py` | 17 |
| `tests/test_provider_paired.py` | 10 |
| `tests/test_provider_pilot.py` | 18 |
| `tests/test_provider_recovery.py` | 9 |

Total omitted: **77**. Original clean coverage included all 27 new HealthTech cases, 24 provider-adapter cases and 5 cross-process budget cases, but omitted the additional env/identity/pilot/recovery/paired controls above. That was insufficient as the final public security coverage. Local compile count 73 versus clean 72 comes from an untracked historical demo script compiled locally; it is not an untracked test or part of the 77 cases.

## Actual failure and scoped correction

Running every published module in the original clean snapshot produced **254 passes, 8 failures, 0 skips**. All eight failures were in `test_provider_paired.py` because behavior tests read `results/development/provider-pilot/live.sqlite3`, an intentionally unpublished local historical journal. The other 69 cases omitted from the original public cohort did not need that local journal.

Paired behavior tests now generate an isolated temporary prior journal through the real ledger with mock-only transport, then bind to its hash. The published plan/payload contract test still checks the original fixed hashes. No provider runtime, frozen config, budget guard or existing journal was changed; no historical journal or raw provider receipt was added to Git. Public selection now names all 17 published modules.

## Corrected clean verification

**262/262 passed, 0 failures, 0 skips**, from an exact staged Git archive with no local journals, corpora, `.env`, `.git` or untracked tests. This includes **27 HealthTech cases** and **106 provider/budget/security cases**. Compilation of 72 published Python files passed; checked sources were unchanged; guarded test process recorded zero network and real credential-file access attempts. Source/tree identity, per-module counts and exact command are in [audit JSON](REPRODUCIBILITY_AUDIT.json).

```powershell
rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-output>
```

The default public cohort and `--suite all` now cover the same 17 modules in this published checkout. `all` remains local pytest discovery, so future unrelated local test files are not silently added to the explicit public list.

Two existing dry-run commands were also executed from the clean snapshot with exit 0: `python -B scripts/run_provider_pilot.py --dry-run --spend-cap 0` → `DRY_RUN_NOT_EXECUTABLE`; `python -B scripts/dispatch_provider_pilot.py` → `READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL`. They are historical transport/config preflights, not HealthTech API integration or live/scientific validation.

The new GOAL/PLAN/README scope and 27-paper review remain unchanged. Literature notes explicitly limit themselves to source-linked targeted reading; scientific benchmark, real public-case/user evaluation, adaptive advantage and manuscript readiness remain unproven. Future work is specified in [Luna handoff](LUNA_PRELIVE_HANDOFF_TH.md), with a **3910-character** [prompt](LUNA_PRELIVE_PROMPT_TH.txt), including LF newlines. The future long run and dataset acquisition were not started here.
