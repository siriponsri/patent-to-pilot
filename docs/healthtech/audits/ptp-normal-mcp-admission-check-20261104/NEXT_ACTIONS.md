# Next actions

These steps apply only after the owner issues a new goal prompt that explicitly authorizes the paid E2 canary. None of them is authorized in the current Normal round.

1. Recheck `main` HEAD, the dirty patch hash, running writers (including the Codex app-server), and the canonical ledger hash. Stop if anything changed without an owner explanation.
2. Done 2026-11-04: the one-character credit-hash erratum (`…80408e9e9a5…` → `…80408f9e9a5…`) was fixed in all five files. Use `87ca37f6789519fdd1184afaa157423fedea33b61b6a3eb80408f9e9a5f06c5d`.
3. Within one 300-second window:
   - run the existing non-billable dispatch-key collector (`providers/metadata_observation.py`, `GET /api/v1/key`) with the key loaded by the adapter, never printed;
   - call MCP `get-credits` and `list-model-endpoints` for `qwen/qwen3-32b`;
   - confirm that `creator_user_id_sha256` and `workspace_id_sha256` still equal `666994c4…e367c` and `50a0e4a8…b0d2`;
   - write the account observation with the dispatch `key_scope` and join it with `credit_from_metadata()`.
4. Recheck writer quiescence, then reserve and dispatch only the bounded three-case E2 canary through the canonical ledger (USD1 prospective cap). Stop and preserve state on any unknown billing outcome; never retry it.
5. dr-train is reachable and idle. Any GPU job needs its own owner authorization and must not disturb other users' processes.
