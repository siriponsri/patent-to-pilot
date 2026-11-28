# Market Window Dossier gateway

The gateway serves the released development reader and the B1 assistance API on one origin. The packaged fixture produces deterministic drafts and abstentions with no inference calls. The existing reader opens at `/demo/`. The Product Owner integrates the AI panels against the [HTTP contract](CONTRACT.md).

## Windows with Docker Desktop

Start Docker Desktop in Linux containers mode. From the repository root:

```powershell
docker compose --env-file product/gateway/.env.example -f product/gateway/docker-compose.yml up --build
```

Open [the dossier reader](http://127.0.0.1:8019/demo/) or [the interactive API documentation](http://127.0.0.1:8019/docs). The example environment file contains only empty key names. The Compose service uses the fixture provider and binds to loopback. Set `MWD_PORT` to another available local port if needed.

## Windows with Python 3.12

From the repository root, in a fresh PowerShell terminal:

```powershell
py -3.12 -m venv "$env:LOCALAPPDATA\mwd\venv"
$mwdPython = "$env:LOCALAPPDATA\mwd\venv\Scripts\python.exe"
& $mwdPython -m pip install -r product/gateway/requirements.txt
$env:PYTHONPATH = (Resolve-Path src).Path
$env:MWD_PROVIDER = "fixture"
$env:MWD_LEDGER_PATH = "$env:LOCALAPPDATA\mwd\fixture-ledger.sqlite3"
& $mwdPython -m uvicorn product.gateway.app:create_app --factory --host 127.0.0.1 --port 8019 --workers 1 --no-proxy-headers --no-access-log
```

With either launcher, run this from a second PowerShell terminal. A fresh fixture ledger within the D43 dates returns `state: ok`, Thai text and referenced claim IDs.

```powershell
$headers = @{ "Idempotency-Key" = [guid]::NewGuid().ToString() }
$body = @{
    dossier_id = "U:82VFR53I78"
    snapshot = "2012-01-01"
    horizon = 12
    language = "th"
    task = "A1"
} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8019/api/v1/tasks -Method Post -Headers $headers -ContentType application/json -Body $body
```

## Ledger and operation

Compose stores the dedicated D43 SQLite database in the `mwd-fixture_ledger` volume. Use one worker and one gateway per ledger. The process lease covers startup recovery and concurrent requests. Stop the gateway before backup, restore or operator reconciliation. Preserve the named volume across container replacement. Use a separate persistent ledger for the eventual qualified route. Keep any existing D43 commitments in the dedicated live ledger before reopening paid traffic.

The shared `BudgetLedger` records each attempt, reservation, observed tokens, charge evidence and outcome. The gateway applies the USD 8 operational stop inside the USD 10 gross envelope, 200 attempts, five admitted attempts per Bangkok day per identity, one outstanding attempt per identity and an exclusive expiry of 16 December 2026 00:00 Bangkok. Fixture calls exercise these rules at zero cost. History holds hashed identities and keys, never prompts or draft text.

After timeout or restart with an outstanding reservation, dispatch pauses. Use the provider's billing record to reconcile through the shared ledger's `reconcile(entry_id, cost_usd, evidence=...)` while the gateway is stopped. The attempt and idempotency record survive reconciliation. A different configured route, tariff or a detected upstream mismatch requires planner and operator review of the ledger and route. B1 exposes no reset endpoint.

## Provider qualification

The factory serves `fixture` by default. The presets define the candidate model, endpoint, key environment variable, caps and non-streamed text capability in [providers.py](providers.py). Each candidate below has live status **NOT_RUN**.

| Preset | Live status |
|---|---|
| Typhoon | NOT_RUN |
| OpenRouter | NOT_RUN |
| OpenAI | NOT_RUN |
| Anthropic | NOT_RUN |
| Gemini | NOT_RUN |
| Qwen / DashScope (set workspace endpoint) | NOT_RUN |
| DeepSeek | NOT_RUN |
| vLLM (set served model) | NOT_RUN |
| Ollama (set served model) | NOT_RUN |

B2/B4 can supply a qualified server-side `Route` with measured compatibility, locked tariff evidence and gross cost treatment, construct the transport with `live_provider`, and compose it into `create_app` with the B2 validator, qualified task IDs and trusted identity dependency. Setting a preset name or providing a key alone enables no real provider. The OpenRouter client pins an upstream and sets price ceilings and fallback controls. It checks the reported model, provider and charge. Direct providers must supply model and usage. Their charges are estimated from the verified tariff. Direct-provider tariff changes that the API response cannot attest require operator verification before dispatch. [OpenRouter routing](https://openrouter.ai/blog/insights/model-routing/) · [OpenRouter response fields](https://learn.openrouter.ai/courses/first-request/read-the-response).

The development identity stub provides a single shared test identity. B4 must place the gateway behind an access-controlled origin, strip client identity headers at the proxy, inject the verified stable identity, pass trusted direct peers and the HTTPS public origin, and block direct access. Use the socket peer for the proxy check and run Uvicorn with `--no-proxy-headers`.

## Tests

```powershell
py -3.12 -m pip install -r product/gateway/requirements-test.txt
py -3.12 -m pytest product/gateway/tests
py -3.12 -m pytest product/mwd/tests
```

The existing MWD suite uses the repository's base dependencies from `pyproject.toml`. See the [B1 receipt](../../docs/loe-bench/receipts/BE-GATEWAY.md) for measured results and remaining release work.
