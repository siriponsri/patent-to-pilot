# BE-MCP | Market Window Dossier read connector

## Handoff

Implementation is ready for the main planner's review on `loe/BE-MCP`. The checkout started clean at the assigned `7cb1c92ea09ebe03d50aa11c09b6473e7b33001b`. The remote research branch had advanced to `d79ced3a` at initial verification. The dispatch base and the pinned public inputs govern this card. The card worktree was the writer of `product/mcp/` and this receipt. Shared lane handoff and memory are planner-owned.

Start with the [local example and owner deployment recipe](../../../product/mcp/README.md). The [release lock](../../../product/mcp/release-lock.json) records the source inventory, projection digest and tool catalog digest. The freeze tag is `loe-track-a-freeze-20261127` and its source manifest is `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d`. The projection bundles 683 dossiers, eight queues and one method card. PO-CURRENT documents the source rights inventory and the remaining owner licence decision. [PO-CURRENT](PO-CURRENT.md)

## Design and conformance

| Contract | Status | Evidence |
| --- | --- | --- |
| M1, six closed read operations | PASS | One registry publishes tool definitions, annotations and input/output schemas. One reader serves all adapters and keeps the exact snapshot key, provenance, native status and bilingual notice on every result page. Typed errors include retryability and safe text. The cutoff, horizon and release are resolved explicitly. The default is Track A t0 on 27 November 2026 at 24 months. |
| Projected data and parity | PASS | The builder pins the normalized public source inventory, verifies Track A freeze metadata and projects allowlisted fields. It omits per-row outcomes, derived role labels, retrospective material, reveal links, and non-reachable sources. The test compares every current rank and probability against both published queues and inspects all projected shards. Synthetic sentinels cover source, claim, unchecked input, queue and URL fields. |
| Bounded reads | PASS LOCALLY | Defaults and cap are 10 and 25 rows. The reader caps 16 KiB arguments and the full 64 KiB MCP result, allowing for added SDK metadata. The cursor binds the release manifest, snapshot, operation, effective filters, language, order and page position. Source and claim title/text remain inside data fields. The two locales share the same bounded format. |
| M2, stdio and Worker | PASS LOCALLY | One official SDK factory supports modern discovery and stateless 2025-11-25 interoperability. Modern HTTP header checks run in the SDK. The Worker uses Cloudflare's stateless handler and two native rate bindings. It rejects unexpected origins and request methods, enforces request limits and logs only tool, reason, release, latency band and count. |
| M5, OpenAPI | PASS LOCALLY | OpenAPI 3.1 generation and served document share the registry. The test validates both documents and invokes all six POST operations. The live document uses the configured Worker origin. |
| M6, skill | DELIVERED | The [skill](../../../product/mcp/skill/mwd-evidence/SKILL.md) provides the evidence lookup, `unknown: verify` behavior, source retention and qualified review rules. Agent invocation statuses are below. |
| M3, `check_draft` | DEFERRED | A future versioned B2 adapter can reuse snapshot selection and claim reading. This card advertises six read tools. |
| Production compatibility | NOT_RUN | The owner runs the deployment and verifies the real remote client evidence path. |

The method card keeps the registered historical results separate from the prospective queue. H1 is +20.37 pp at 24 months, H2 is FAIL and H3 is descriptive after the fixed-sequence stop. The aggregate projection records the scored event-row denominators. Effective capture numerators for the reported contrasts are null because the receipt reports rounded differences and permits fractional tie allocation. L1/L1e scope and schema-valid counts are exploratory. [SCORE](SCORE.md) · [SCORELLM](SCORELLM.md)

Development dossier availability reflects the Time Machine's historical example selection. The projection omits the case roles and keeps dated claims when their linked records qualify. Historical sources with undated publication remain null. Their recorded edition, locator and retrieval date travel separately. Thai and ASEAN lookup tasks retain an unknown status and route the reviewer to the relevant check.

## Dependencies

The committed npm lockfile records resolved versions and integrity digests for direct and transitive packages. These packages were used locally. The public input permissions are recorded separately from the software licences.

| Package | Version | Licence | Use |
| --- | --- | --- | --- |
| `@modelcontextprotocol/server` | 2.4.0 | Apache-2.0 | Official MCP server and stdio transport |
| `@modelcontextprotocol/client` | 2.4.0 | Apache-2.0 | Local stdio transport parity tests |
| `agents` | 0.34.1 | MIT | Cloudflare stateless Worker handler |
| `@cfworker/json-schema` | 4.1.6 | MIT | Runtime argument validation and output test assertions |
| `zod` | 4.6.7 | MIT | Pinned SDK schema dependency |
| `@scalar/openapi-parser` | 0.29.29 | MIT | OpenAPI document validation |
| `typescript` | 6.0.3 | Apache-2.0 | Build |
| `@types/node` | 24.13.2 | MIT | Node types |
| `wrangler` | 4.169.0 | MIT OR Apache-2.0 | Local runtime, bundle and owner deploy recipe |

The first dependency audit flagged Zod 4.4.3. The pin was updated to 4.6.7, and the production audit then reported zero vulnerabilities. The modern SDK adds result metadata after the shared serializer. The first largest-page measurement found a 65,610-byte result, which led to reserving 512 bytes inside the result cap.

## Verification

| Command | Observed result |
| --- | --- |
| `npm test` from `product/mcp` on Node.js 24.19.0 | **10 passed, 0 failed.** Both MCP revisions, stdio/Worker/REST equality, six OpenAPI operations, valid and stale pagination, release mismatch, published tie order, reveal projection, input/result caps, Origin and throttling. |
| `py -3.12 -m pytest product/mwd/tests product/gateway/tests` | **36 passed, 0 failed** in 56.57 s. |
| `py -3.12 -m pytest -q --tb=short` | **8 failures**, all eight standing SACR r2/r3 supervisor budget parametrizations allowed by AGENTS.md. No additional failures were reported. |
| `npm audit --omit=dev` | **0 vulnerabilities** after the Zod pin update. |
| `npx wrangler deploy --dry-run --outdir dist/worker` | **PASS.** 23,379.67 KiB uncompressed (22.83 MiB of the 64 MiB limit), 1,529.62 KiB gzip. Dry run listed the expected 60 and 1,000 per-minute local rate bindings, and exited without deploying. |
| `npx wrangler dev --local --port 18765` | **PASS for the local smoke.** TCP requests to modern `/mcp` and REST `/v1/search_drugs` both returned 200 and identical Semaglutide evidence. The initial concurrent pair took 1,655 ms wall time from the caller just after the local runtime reported ready. |

`node bench.mjs` scanned 11,192 pages across both languages and release modes. It requested 25 rows per page for dossier, sources, checklist, queue and method card reads. Ten calls hit `ROW_TOO_LARGE` for an individual record, as required by the contract. The size error preserves the snapshot and notice. The following are the largest complete pages encountered. The full modern MCP result includes the SDK metadata. The scan uses the in-process Worker handler on Windows with stub rate bindings and application logs suppressed during sampling.

| Language and largest page | Full result | First measured call, CPU / wall | Warm batch CPU mean | Warm wall p95 |
| --- | ---: | ---: | ---: | ---: |
| English checklist, `U:QXS94885MZ`, development 2014-01-01, 12 months | 65,006 B | 78 / 59.21 ms | 2.97 ms | 3.95 ms |
| Thai checklist, `U:31TZ62FO8F`, Track A 2026-11-27, 12 months | 65,130 B | 0 / 3.37 ms | 3.12 ms | 4.70 ms |

Each warm batch used 100 invocations. The local process CPU timer reports coarse per-call values (p95 16 ms in both batches, maxima 32 and 31 ms). Both batch means were below the Workers Free 10 ms invocation budget. The first English call exceeded it locally. The 1,655 ms local first-pair wall time includes local runtime and binding overhead, and excludes time before Wrangler's ready signal. Deployed cold startup, per-invocation CPU and 128 MB isolate memory compliance are **NOT_RUN** and remain open. [Workers Free limits](https://developers.cloudflare.com/workers/platform/limits/)

## Client matrix

| Client | Version | Transport or surface | Status and observed evidence |
| --- | --- | --- | --- |
| Claude Code | 2.1.292 | Local stdio | **Connection PASS.** `claude mcp add --scope project` wrote a scratch project registration. The health check initially reported pending approval. A scratch local setting enabled only the card's server, and `claude mcp get` returned Connected. **Agent evidence path and skill NOT_RUN.** Those need an authorized model session. |
| Codex CLI | 0.172.0 | Local stdio | **Configuration PASS.** `codex mcp get -c` confirmed the transient command and arguments. The persistent `mcp add` flow would write global configuration. **Agent evidence path and skill NOT_RUN.** |
| Claude Desktop, Gemini CLI, OpenBot | Unverified | Local stdio | **NOT_RUN.** Named-client runtime and skill eligibility remain unverified. |
| ChatGPT web, Claude.ai, Claude Desktop, Claude Code, Codex CLI, Gemini CLI, xAI Grok API, OpenBot | Unverified | Remote MCP | **NOT_RUN.** Requires the owner Worker URL and client setup on authorized accounts. |
| Anthropic and OpenAI computer use | Unverified | Browser | **NOT_RUN.** Owner's PO-QA covers M4. |

The local Node SDK exercised the full evidence result path with no model calls. No client model run, paid API call, production login or deployment occurred.

## Planner memory and remaining work

- Keep the two digests distinct. The freeze digest identifies the upstream Track A freeze, while the projection manifest digest identifies this exact MCP release.
- Judge the capped response after SDK serialization. The protocol may add fields beyond the application envelope even when the application uses the same REST and MCP payload.
- The owner licence sign-off, actual Worker URL, deployed CPU/memory/startup and one real client evidence run over each transport remain release gates. See the [owner recipe](../../../product/mcp/README.md#owner-deployment).
- Integrate the receipt into lane handoff and memory on planner approval. This branch is for review and has no deployment or merge.
