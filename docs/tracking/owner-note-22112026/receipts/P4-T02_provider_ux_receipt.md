# P4-T02 receipt: local, API and self-hosted modes are clear and usable

**Task:** P4-T02, "Make local, API and self-hosted modes clear and usable" (owner note 22 Nov 2026). Acceptance text:
show the active execution mode, the exact model and the missing capability; configure credentials securely once; a
missing optional endpoint does not block local search.
**Date:** 23 Nov 2026. **Cost:** USD 0. No live API call, no paid call, no model download, no network access beyond
loopback was made to build or test this.
**Registry note:** the registry lists the required artifact as `P4-T02_provider_ux_receipt.md`; the lead asked for this
file name. This file is the P4-T02 receipt.
**Status fields:** `product_readiness`: execution mode, exact model, missing capabilities and credential presence are
visible, tested at API level and checked once in a browser. `method_evidence`: none (provider availability is not method
superiority). `publication_readiness`: not affected.

## What the owner sees

- **Header label** on every page: `Mode: Local only · lexical search`, or for a hybrid project
  `Mode: Self-hosted endpoint · <exact model id> · hybrid`. If the hybrid model cannot be used (no key, not allowed,
  last check failed), the label says `hybrid requested, <model> unavailable → lexical`. Hovering shows the full sentence.
- **"N optional capabilities missing"** button in the header opens the Providers page.
- **Providers page → Execution mode** (new, above the G02 profile states):
  - *Active mode* card: mode (Local only / Self-hosted endpoint / API provider), exact `model_id`, served model name and
    digest from the last check, where the endpoint is (this computer / another machine / named API), and what the last
    run actually used (retrieval effective, paid model calls, remote calls, fallback reason).
  - *Capabilities* table: Search/Compare/Inspect and bounded relation search (always available, local), then embedding,
    chat and reranker (optional; available / unavailable with the reason / not configured), and PDF ingestion. It states
    honestly that no Search/Compare/Inspect step uses chat or rerank output yet.
  - *Missing capabilities*: plain sentences, each ending with "local search, compare and inspect still work", e.g.
    `OPENROUTER_API_KEY not set → API calls that need it are unavailable (template openrouter-…); local search, compare
    and inspect still work.`
  - *Credentials* table: variable name, state (`Set` / `Set for your Windows user — restart the Workbench` / `Not set`),
    which profiles and templates use it, and a "How to set it once" panel.

## Credentials: set once, name only

- The Workbench stores and shows **only the variable name** and a present/absent flag. There is **no route that accepts a
  key** (`POST /api/credentials` is 404 by design).
- One-time setup path (shown per variable, containing the name only): in the owner's own PowerShell window,
  `$k = Read-Host "Paste NAME (input is hidden)" -AsSecureString; [Environment]::SetEnvironmentVariable("NAME",
  [Net.NetworkCredential]::new("", $k).Password, "User"); Remove-Variable k`, then restart the Workbench with
  `Start-PTP.cmd`. The key goes through a hidden prompt into the Windows user environment; it never reaches the server,
  the browser, shell history, SQLite, logs or a repository file. A remove command is shown too.
- "Set for your Windows user — restart" is detected by a presence check of `HKCU\Environment` (the value is read only to
  test non-emptiness and is discarded at once; nothing is returned or stored).
- A key pasted into the profile's "Credential variable name" field is refused (HTTP 422) **without echoing it**: names
  must match `[A-Za-z_][A-Za-z0-9_]*`; an all-upper-case name is always accepted, and otherwise known key prefixes
  (`sk_`, `hf_`, `ghp_`, …) or long mixed lower-case/digit tokens are rejected (`providers.looks_like_secret`).

## Mode classification (no network)

| Profile endpoint | Mode |
|---|---|
| `anthropic_native`, or a host of OpenRouter, OpenTyphoon or Anthropic | API provider (named) |
| Loopback (Ollama, vLLM/TEI/llama.cpp on this computer) | Self-hosted endpoint, "server on this computer" |
| Any other host (e.g. a GPU box) | Self-hosted endpoint, "another machine"; the existing paid-remote-route policy still applies |

A project's active mode is Local only in lexical mode. In hybrid mode it is the mode of its embedding profile when that
profile is usable (ready check, key present, remote allowed, envelope recorded); otherwise Local only with the reason.
The view opens **no connection**: reachability is the last recorded connection check, and the page says so.

## Files

- `src/patent_to_pilot/workbench/modes.py` (new): mode classification, profile blockers, capability and missing lists,
  credential presence and setup steps.
- `src/patent_to_pilot/workbench/server.py`: read-only routes `GET /api/execution-mode`,
  `GET /api/projects/{pid}/execution-mode`, `GET /api/credentials`.
- `src/patent_to_pilot/workbench/providers.py`: `looks_like_secret` guard on `credential_ref` (value never echoed).
- `src/patent_to_pilot/workbench/static/app.js`, `index.html`, `app.css`: header mode label, missing-capabilities
  button, Execution mode panel with credentials and setup steps.
- `tests/test_p4_t02_execution_modes.py` (new, 8 tests).

## What was verified

All tests run with `loopback_only` (any non-loopback connection attempt fails the test) and with
`OPENROUTER_API_KEY`, `TYPHOON_API_KEY` and `ANTHROPIC_API_KEY` removed from the test process (the registry lookup is
replaced by a stub).

1. Default project: mode Local only, model none, missing list names each unset key and the missing embedding model, and
   every line says local work continues.
2. **Every optional endpoint missing or unreachable**: OpenRouter and Anthropic profiles without keys, and Ollama embedding,
   Ollama chat and an OpenAI-compatible reranker pointed at a closed loopback port. The mode view makes no provider call
   (transport patched to fail the test). Checks record `unavailable` / `blocked` (the keyless check is blocked before any
   socket opens). Search, Inspect, Compare and a full run then all succeed with 0 paid and 0 remote calls.
3. **Self-hosted endpoint going away**: a loopback Ollama-format double serves embeddings; the check passes, an index is
   built and hybrid is switched on. The mode shows Self-hosted endpoint with the exact `fake-embed`, served name
   `fake-embed:latest` and digest. The double is then stopped: Search, Inspect and Compare still succeed; the run records
   `lexical_fallback` with "dense channel failed", and the mode view's last-run line shows it.
4. API-provider and remote self-hosted classification (OpenRouter, OpenTyphoon host, a non-loopback host).
5. Secrets: with a fake value in `OPENROUTER_API_KEY`, the value appears in no response of `/api/providers`,
   `/api/credentials`, both execution-mode routes or `/api/capabilities`, in no byte of the store directory (SQLite, WAL,
   files), and not in stdout/stderr; state is `set`. Pasted keys are refused with 422 and not echoed.
6. Restart-needed state and setup commands carry the name only; a non-name is refused.
7. The page serves the mode panel and label.

**Gate.** `python -c "...sys.path.append(<main checkout>/.venv/Lib/site-packages)...pytest.main(['-q'])"`:
2,661 passed, 8 skipped, 8 failed; the 8 failures are exactly the known SACR r2/r3 supervisor budget tests. After that
run, the secret-shape guard was narrowed so all-upper-case names such as `HF_TOKEN` are always accepted; the P4-T02,
G01, G02 provider, OpenRouter-profile and P4-T01 suites were re-run on the final code: 50 passed, 1 skipped (the skip is a PDF test under the system Python without pypdf).
`python scripts/ptp_run.py --smoke`: 15/15 PASS, "no remote connection attempted".

**Browser check.** The worktree server on a temporary store (`--data-dir` in the agent scratchpad, port 8791) was opened
in the browser pane: the header showed `Mode: Local only · lexical search` and the missing-capabilities button; the
Providers page showed the Execution mode panel, capabilities, missing list and credentials. The real environment of
that server showed `OPENROUTER_API_KEY` and `TYPHOON_API_KEY` as "Set (name only shown)" and `ANTHROPIC_API_KEY` as not
set; no value was displayed. No console errors.

## What was not verified

- No live API or self-hosted model call was made (no envelope was used; none was needed). Real-provider behaviour of the
  connection check remains as recorded under G02.
- The PowerShell setup command was **not run** (it would change the owner's user environment). It is standard .NET
  (`Environment.SetEnvironmentVariable(..., "User")`); the owner should run it once and restart the Workbench.
- The restart-needed detection was tested with a stub, not against a real registry change.
- No Typhoon Workbench template was added: the exact OpenTyphoon model id was not confirmed in this task. The credential
  is listed by name and classified as an API provider if a profile points at `api.opentyphoon.ai`.
- Not observed with a non-developer user (that is P4-T05).
