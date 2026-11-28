# Market Window Dossier MCP

Read the pinned public Market Window Dossier forecasts and dated evidence from a local MCP client, a Cloudflare Worker or an OpenAPI caller. The service is decision support for qualified review.

## Build and use locally

Use Node.js 24 and the npm lockfile. Run the commands from this directory.

    npm ci
    npm run build
    npm test
    node bench.mjs

Register an absolute launcher path so the client can start it from any working directory. Use the appropriate command for your installed client.

    claude mcp add --transport stdio --scope project mwd -- node <absolute-path-to-dist/stdio.js>
    codex mcp add mwd -- node <absolute-path-to-dist/stdio.js>

Try this evidence path.

1. Call `search_drugs` with `{"query":"semag"}`. The default is Track A t0 on 27 November 2026 at 24 months. The result includes Semaglutide, key `U:53AXN4NNHX`, and the available snapshot keys.
2. Copy the returned `snapshot` into `get_dossier`. Supply that molecule key and `claim_ids: ["queue-24"]`.
3. Call `get_sources` with the same snapshot and molecule and `source_ids: ["score-24"]`. Preserve the claim ID and exact locator from the result. Set `language: "th"` for Thai claim and checklist text.

Each tool result has the same evidence page in structured content and in the serialized text fallback. A successful empty page carries the snapshot and both notices. Tool-level errors use `isError` over MCP and the page's `error` object in both interfaces. Copy a `next_cursor` into the same request for the next page. Page size defaults to 10 and supports up to 25 rows within 64 KiB, including both copies of the result. Tool arguments are limited to 16 KiB. MCP has a separate 24 KiB transport ceiling for routing metadata.

The build checks the public input inventory and projection manifest against [release-lock.json](release-lock.json). Both adapters embed identical projected JSON shards. Each shard is checked against the manifest before use. A changed input or projection requires planner review of new digests. `node build-release.mjs --print-digests` prints proposed digests for review. It writes no release.

The development snapshots use examples published in the Time Machine. A dossier's presence reflects the historical demo's curated coverage. Use those dossiers as development examples. The projection excludes outcome fields, reveal sections and links, retrospective context, and outcome role labels. Historical method results retain their separate aggregate research citations. The Track A forecast remains outcome pending. Registered 12- and 24-month score ranks and the 0.20 review capacity come from the release.

## Owner deployment

The owner runs these steps when the planner approves the build. Keep the local install commands above for offline access.

1. Set the Worker name and `PUBLIC_ORIGIN` in [wrangler.toml](wrangler.toml) to the exact owner `https://<name>.<account-subdomain>.workers.dev` address. Set `ALLOWED_ORIGINS` to a comma-separated list of precise browser origins if browsers will call this API. Choose two rate-limit namespace IDs unique in the account.
2. Keep observability disabled or verify account settings capture only the aggregate app fields. Cloudflare processes the connecting address and headers as part of operating the service. The app uses a minute-scoped hash of the connecting address only for its rate bucket. Backend clients can omit Origin.
3. From this directory, run `npm ci`, `npm test`, and `npx wrangler deploy --dry-run --outdir dist/worker`. Confirm the package and configuration. Then run `npx wrangler login` and `npx wrangler deploy` from your own Cloudflare account.
4. Check `/openapi.json` on the returned address. It advertises the configured origin for six JSON POST operations under `/v1/`. Generate an equivalent file with `node dist/generate-openapi.js https://<name>.<account-subdomain>.workers.dev`. Connect a remote MCP client to `https://<name>.<account-subdomain>.workers.dev/mcp` and run the Semaglutide evidence path. Record the deployed revision, digest, UTC time, CPU and client result in the release record.

The Worker uses Cloudflare's stateless MCP handler. It serves revision 2026-07-28 and the 2025-11-25 stateless legacy exchange. Anonymous access is intended for this public, immutable release. Each caller bucket allows approximately 60 requests per minute per Cloudflare location. The location-wide ceiling is approximately 1,000 per minute. Rate-limit responses include a 60-second retry interval. Check the account's daily quota independently. [Worker limits](https://developers.cloudflare.com/workers/platform/limits/) · [rate limits](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)

## Agent skill

Install the [mwd-evidence skill](skill/mwd-evidence/SKILL.md) by copying its folder into the client's supported skill directory. It describes which reads to use, what to cite, and how to report missing evidence.
