# BE-GATEWAY (B1) | Market Window Dossier

Implementation branch `loe/BE-GATEWAY`, from the assigned PRD revision `23af56eb`. At checkout, verified remote `research/loe-bench` was already at `94591f94`, with `23af56eb` as an ancestor. The branch retains the assigned base for planner review.

## Contract and implementation

The Product Owner can build against the [HTTP contract](../../../product/gateway/CONTRACT.md) and [frozen OpenAPI](../../../product/gateway/openapi.json). `POST /api/v1/tasks` accepts only the released dossier key, as-of date, horizon, language and task-specific selectors. A3 uses fixed templates. Responses distinguish `ok`, `abstained`, `rejected` and `unavailable`. A4 returns the missing-text lookup state. The fixture supports A1–A3 drafts and abstentions, and A4 abstention.

The server resolves the release index tuple before reading evidence. The prompt builder admits selected claim and checklist fields, leaves source titles and URLs out of the model input, excludes reveal-only sources and later or retrospective material, and separates canonical forecast values. B1 verifies claim-ID membership and resolves source references. Cross-field validity and semantic support remain B2 work. [Runbook](../../../product/gateway/README.md)

The shared SQLite ledger uses a dedicated D43 envelope. The gateway serializes admission and ledger settlement inside one leased process. Reservations count against the USD 8 operational threshold inside the USD 10 gross envelope. The ledger persists idempotency, quota consumption and unresolved billing across restarts. Route and tariff configuration are pinned in the DB. The OpenRouter transport is tested against an in-memory HTTP fixture for reported-route and price changes, single exchange, and fallback suppression. Direct-provider charges would depend on validated usage and an approved tariff. The telemetry records model, route, task, prompt version, token counts, cost or uncertainty evidence, and outcome. Prompts and responses are excluded.

## Verification

| Check | Result | Command / observation |
|---|---|---|
| Python gateway | PASS | `py -3.12 -m pytest product/gateway/tests` → 19 passed, exit 0. Final combined gateway and MWD run → 35 passed, 1 skipped, exit 0 |
| Existing MWD suite | PASS | `py -3.12 -m pytest product/mwd/tests` → 16 passed, 1 skipped, exit 0 |
| Repository suite | FAIL (standing exceptions) | `py -3.12 -m pytest` → 2,760 passed, 8 failed, 50 skipped, 1 xfailed, exit 1. All eight are the recorded SACR r2/r3 supervisor budget failures |
| Native gateway | PASS | Python 3.12.10 with Uvicorn, one worker, loopback port 8020 and isolated temporary ledger. `GET /demo/` returned 200. Thai A1 returned 200 `ok` with 2 citations |
| Compose config and build | PASS | Docker Desktop Linux engine 29.8.0, Compose 5.5.1. `docker compose --env-file product/gateway/.env.example -f product/gateway/docker-compose.yml config --quiet` and `up --build -d` |
| Compose HTTP and persistence | PASS | `GET /demo/` returned 200. Thai A1 returned 200 `ok` with 2 citations. After `up -d --force-recreate`, the served OpenAPI matched the frozen contract and the repeated key returned 409 `duplicate_request`. The fixture container was stopped and the volume retained |
| Live providers and paid inference | NOT_RUN | No live requests. Fixture ledger cost USD 0. Typhoon, OpenRouter, OpenAI, Anthropic, Gemini, DashScope, DeepSeek, vLLM and Ollama all remain unqualified |

The first Compose image built successfully, but startup on port 8000 failed because another project already held the port. The package now defaults to port 8019 and accepts a local `MWD_PORT` override. The tested Python base tag `python:3.12.10-slim` resolved to `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`.

## Dependencies

The gateway pins the dependency closure for Python 3.12. The licences below are distribution metadata or the shipped licence files. Docker retains upstream notices. pytest and Pydantic were already repository dependencies.

| Package | Version | Licence | Purpose |
|---|---|---|---|
| fastapi | 0.141.1 | MIT | Typed HTTP API and OpenAPI |
| starlette | 1.7.0 | BSD-3-Clause | ASGI routing and static assets |
| uvicorn | 0.53.0 | BSD-3-Clause | ASGI server |
| httpx | 0.28.1 | BSD-3-Clause | Single-exchange transport and fixture network tests |
| httpcore | 1.0.9 | BSD-3-Clause | HTTP connection layer |
| h11 | 0.16.0 | MIT | HTTP/1.1 |
| anyio | 4.15.1 | MIT | ASGI and HTTP concurrency |
| certifi | 2026.7.22 | MPL-2.0 | CA bundle |
| idna | 3.20 | BSD-3-Clause | Domain name handling |
| pydantic | 2.13.5 | MIT | Request and response models |
| pydantic-core | 2.46.5 | MIT | Validation engine |
| annotated-doc | 0.0.5 | MIT | FastAPI annotation metadata |
| annotated-types | 0.8.0 | MIT | Pydantic annotation constraints |
| typing-extensions | 4.16.0 | PSF-2.0 | Backported typing APIs |
| typing-inspection | 0.4.4 | MIT | Annotation inspection |
| click | 8.5.0 | BSD-3-Clause | Uvicorn CLI |
| colorama | 0.4.6 | BSD-3-Clause | Windows terminal output |
| tzdata | 2026.4 | Apache-2.0 | IANA timezone fallback on Windows |
| pytest | 8.4.2 | MIT | Gateway test runner |
| iniconfig | 2.3.0 | MIT | Test configuration |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | Test dependency version handling |
| pluggy | 1.6.0 | MIT | pytest hooks |
| Pygments | 2.21.0 | BSD-2-Clause | Test output highlighting |

Windows Python 3.12 artifact SHA-256 values from `py -3.12 -m pip install --dry-run --ignore-installed --report <temp-report> -r product/gateway/requirements-test.txt`:

```text
annotated-doc      117bac03a25ede5df5440e855b32d556049ca169ead221505badf432fed4b101
annotated-types    f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0
anyio              6152fdbbf9a77fdec97731721bebf7c4c44f7c29b424b0065826173efc7ed101
certifi            62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775
click              255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360
colorama           4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6
fastapi            bfb91aa2d334c61cb35ba9a116fc123b3d3df31640b801cf57a7a78ec3f603b3
h11                63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86
httpcore           2d400746a40668fc9dec9810239072b40b4484b640a8c38fd654a024c7a1bf55
httpx              d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad
idna               ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c
iniconfig          f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
packaging          d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c
pluggy             e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
pydantic           346a034f080da3755d8e9cb5e00e8b07de1d39e4f6e2c87d8ab7cafa0b269a73
pydantic-core      5e81740c09e310f5aa5cbd3e434a01c154d4bef93241c7877b39f211d2b78ba8
Pygments           2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9
pytest             872f880de3fc3a5bdc88a11b39c9710c3497a547cfa9320bc3c5e62fbf272e79
starlette          67f8e99895493dd2911a03f11314af6ceebeae4e704bb9f43dfc6a9db151c93e
typing-extensions  481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
typing-inspection  65b8397ba37ccbce054456aaccddfc91e6e3083c92824df348d96ca832f3f147
tzdata             c2169a8b0a7a5e9674da5a135ccdfb2b3e671b333ed9fed17b41f73c34476e81
uvicorn            e8dca71ec86dce5f04e333f0d56cdedf942446e6643b9cea1af0d6d3a02cb03e
```

## Planner handoff and project memory

- **B2 BE-GROUND.** Implement typed value and cutoff checks, the exact A2 checklist-to-claim mapping, injection/refusal evaluation and display support review. The overlap heuristic in B1 is adequate only for exercising the interface with deterministic fixture text. Lock the 32-fixture release evaluation with B3 before live inference.
- **B3 BE-CLAIMS.** Supply approved original-language claim text, edition, rights, dependencies and span validation. Integrate through the reserved `reading` schema and retain the lookup response where claims are missing.
- **B4 BE-ORG.** Supply the OTP/allowlist, proxy checks and revocation. Verify restored ledger balance and account for prior commitments, FX, prepaid charges, fees and taxes before live activation. Confirm the approved route and actual billed evidence. Validate the same package on the intended external host after explicit approval.
- **PO-AI.** Integrate the existing reader at the same origin using the fixture contract. The current reader has no AI panel. Preserve the manual evidence and checklist routes and use the fixed machine reasons for localization.

The reusable failure case is a timeout after the ledger has reserved an attempt. Treat that as possible spend, preserve the key, and reconcile the single attempt before dispatch resumes. Compose replacement confirmed the ledger continued to reject the original key. The Planner owns the shared lane handoff and memory at integration.
