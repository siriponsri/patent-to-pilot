# Takeover CPU accounting amendment (12 Nov 2026)

Claude Code session `local_016eefb9` took over the automatic dual-track goal from the blocked prior session.
Owner decisions are recorded verbatim in [owner-cpu-amendment.json](owner-cpu-amendment.json).

## What changed

| Item | Value |
|---|---|
| Cumulative CPU cap | 28,800 s -> 57,600 s (amendment, no reset) |
| Unmeasured automatic preparation, 07:00:41.145 -> 07:30:39.320 +07 | 1,799 s x 12 logical CPUs = **21,588 s**, `UPPER_BOUND_NOT_MEASURED` ([evidence](preparation-window-evidence.json)) |
| Charged before amendment | 25,592.84637781 s (unchanged) |
| Charged after amendment | 47,180.84637781 s |
| Remaining | **10,419.15362219 s (~2.89 h)** |
| GPU-stage host CPU | telemetry only, not charged to the CPU cap (original R5-R7 definition, owner choice) |
| Journal | generation 5 -> 6, idle, scope and attempt history unchanged |
| Ledger | `2d041977...a927` -> `f07dcc5f...cbe5`; local canonical ledger mirrors the journal |

The owner did **not** approve the 4 h estimate; it is not used anywhere.

## Code

- `src/patent_to_pilot/research/automatic_cpu_booking.py`: `cpu_cap` (accepts 28,800 or 57,600 only with the single amendment record), `cpu_used`, and the one-time `amend_cpu_cap_and_book_preparation` transaction (replay and second amendment rejected; upper bound must equal ceil(window) x CPUs).
- `automatic_live_admission.py`: the cap is read from the ledger; GPU stages (`synthetic`, `fidelity`, `pilot`, `full_dev`) keep `cpu_seconds` as an RLIMIT safety bound but consume no CPU cap.
- `automatic_dispatch_journal.py`: claims no longer reserve CPU; settlement records `host_cpu_seconds_telemetry` and the ledger total `gpu_stage_host_cpu_telemetry_seconds`. Exceeding the declared CPU safety bound still stops the study.
- `scripts/healthtech/meter_local_cpu.py`: local CPU metering (Windows GetProcessTimes, direct child).
- Closed R7 code (`r7_dispatch_journal.py`) still requires the 28,800 s cap and will refuse to run on the amended ledger. This is intended: R7 is closed.

## Evidence

- [apply_cpu_amendment.py](apply_cpu_amendment.py) ran once (`applied_now: true`). [amendment-receipt.json](amendment-receipt.json), [amendment-verification.json](amendment-verification.json), [post-amendment-inspection.json](post-amendment-inspection.json) (independent read-only check: generation 6, active null, no reservations, GPU idle, local ledger matches).
- Before the transaction, the remote dependency files `r6_dispatch_journal.py`, `r6_admission.py` and `mtm_runtime.py` were confirmed byte-identical to local (LF). The new module's source was sent in the payload and its hash recorded in the receipt.
- Tests: 31 targeted, then 134 across the automatic, R6/R7 journal, SACR, Graph and KM suites, all PASS.

## Takeover-session CPU (metered, not yet booked)

3 metered commands, 3.562500 s CPU in [local-cpu-measurements.jsonl](local-cpu-measurements.jsonl). These will be booked together with a 100 s conservative allowance for unmetered shell and inspection work in this session segment (R7 precedent), before the next CPU-only dispatch. No model calls, GPU jobs or corpus reads in this step.
