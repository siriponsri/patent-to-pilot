# LOE-Bench lane handoff

Owner of this file: the main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`; `main` is kept equal to it at each integration. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md). Techniques: [TECHNIQUE-LEDGER.md](TECHNIQUE-LEDGER.md). Documentation index: [README.md](README.md).

## Current state (27 November 2026, Wave 2, development only)

- **Roles (owner-approved).** Claude Opus is main planner and only reviewer. GPT-6.2 Astra high is co-planner. GPT executors use GPT-6.2 Sol xhigh or high, and GPT-6 Luna high only for scripted cards.
- **Primary criteria.** Confirmatory criteria v2: a fixed sequence of H1 M3<B1 at 24 months, then H2 M3<M1, then H3 M3<B1 at 12 months, each one-sided at α = 0.025. The CP1 single endpoint is superseded.
- **Test.** The test is sealed in code (`loe_bench/seal.py`). No confirmatory result exists. Track A inputs are frozen at tag `loe-S0-input-20261127`.
- **Pipeline.** As-of Orange Book (FDA ZIPs plus NBER 1985–2016), active-moiety keys (FIX2c), challenge evidence (E7 plus E7b patent-number relinking) and K07. Rejected techniques: K06, K08, K09, K10 and K19.
- **Development signal (validation only).** At 24 months, M1 and M3 beat B1 by about 0.007–0.010 in AURC80. M3 against M1 is about 0. The graph does not yet add value over the matched model.
- **Disclosed incidents (T4).** A preflight decoded test-period ANDA records for an index, with no outputs. An executor also stopped a process it had not verified as its own. Both are recorded in MEMORY.

## Running (overnight 27→28 Nov; the owner returns 28 Nov 06:00 Bangkok)

- **T4c:** power and type-I for recall@20%. It selects α by the pre-declared rule.
- **FREEZE:** reconciles the H2 swing (T1v3 −1.1 pp vs K22 +5.5 pp), builds the canonical deterministic runner, and writes `FROZEN_CONFIG.json`.

## Overnight autonomous plan (owner-authorized "continue")

1. Review and merge T4c and FREEZE.
2. Dispatch T5, the preregistration draft on GPT-6.2 Sol high, built on criteria v3. It must include the exposure disclosure, the H2 fragility note, the no-expert limitation, the auto-clear finding and the α choice.
3. Have the co-planner (Astra) critique T5, then the main planner revises and reviews.
4. Prepare the G3b Track A prediction-freeze script, without running it on outcomes.
5. Write the owner packet in Thai: what to submit on OSF and how.

Do not create PREREG_LOCK.json, unseal the test, or rent a GPU without owner approval.

## Next action

The owner reviews the T5 draft and submits it to OSF. After that comes the G3b freeze, then test unlock with the prereg hash, then confirmatory runs.
