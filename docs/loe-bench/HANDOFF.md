# LOE-Bench lane handoff

Owner of this file: the main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`; `main` is kept equal to it at each integration. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md). Techniques: [TECHNIQUE-LEDGER.md](TECHNIQUE-LEDGER.md). Documentation index: [README.md](README.md).

## Current state (27 November 2026, Wave 2, development only)

- **Roles (owner-approved).** Claude Opus is main planner and only reviewer. GPT-6.2 Astra high is co-planner. GPT executors use GPT-6.2 Sol xhigh or high, and GPT-6 Luna high only for scripted cards.
- **Primary criteria.** Confirmatory criteria v2: a fixed sequence of H1 M3<B1 at 24 months, then H2 M3<M1, then H3 M3<B1 at 12 months, each one-sided at α = 0.025. The CP1 single endpoint is superseded.
- **Test.** The test is sealed in code (`loe_bench/seal.py`). No confirmatory result exists. Track A inputs are frozen at tag `loe-S0-input-20261127`.
- **Pipeline.** As-of Orange Book (FDA ZIPs plus NBER 1985–2016), active-moiety keys (FIX2c), challenge evidence (E7 plus E7b patent-number relinking) and K07. Rejected techniques: K06, K08, K09, K10 and K19.
- **Development signal (validation only).** At 24 months, M1 and M3 beat B1 by about 0.007–0.010 in AURC80. M3 against M1 is about 0. The graph does not yet add value over the matched model.
- **Disclosed incidents (T4).** A preflight decoded test-period ANDA records for an index, with no outputs. An executor also stopped a process it had not verified as its own. Both are recorded in MEMORY.

## Overnight results (27→28 Nov)

- **T4c.** α = 0.025 by rule. H1 power at 75 event clusters is 50% at +10 pp and 85% at +15 pp, with MDE80 about +14 pp.
- **FREEZE.** FROZEN_FOR_PREREG (config sha256 `3a6a66f9…c68`). The H2 swing is explained by the REG PIV fix.
- **Preregistration v1.** Merged after CP5 and T5b. Owner placeholders and OSF submission remain ([procedure](OSF-SUBMISSION.md)).
- **LLM arm (L1, Qwen2.5-7B on L4).** Ran on development data. Recall is below B1 and M3 at both horizons. L1 is pinned as an exploratory arm.
- **GPU spend.** About USD 0.53 of the USD 20 envelope. Volume `8n6rnzljwg` is kept at USD 2.10 a month, and every pod is deleted.

## Next action

The owner reviews the T5 draft and submits it to OSF. After that comes the G3b freeze, then test unlock with the prereg hash, then confirmatory runs.
