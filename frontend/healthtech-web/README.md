# healthtech-web

Local TH/EN no-code frontend for Patent-to-Pilot HealthTech evidence dossiers: named device → import → evidence and exact source → notes → local save/reopen → edited TH/EN export.

```bash
npm start          # http://127.0.0.1:5178/
npm test
npm run test:e2e
```

The dossier screen is a node-canvas workspace (n8n/Make style) with dockable, resizable panels, drag-and-drop with keyboard alternatives, a journey stepper, a guided tour and a TH/EN tutorial video. Rebuild the video from the real app with `node tutorial-video/build.mjs --render` (HyperFrames 0.8.221 and FFmpeg; the video is silent until a licensed music track is supplied).

No build step and no npm dependencies; Node ≥ 22. The unit suite also needs the repository's Python ≥ 3.12 environment and dependencies: it creates a fresh backend dossier and compares generated schemas. Runbook, acceptance matrix, evidence and known limits: [docs/healthtech/ux/implementation/README.md](../../docs/healthtech/ux/implementation/README.md). Specification: [docs/healthtech/ux/](../../docs/healthtech/ux/README.md).

**Solution Scout** (`/scout.html`) is a separate page. You write a problem brief and get two result lanes, own field and other industries. The page also shows a field constellation and quote-checked transfer rationales. It needs the scout backend: `serve_http.py --scout-live-dir … --scout-model-dir … --scout-rationales …`, or `--scout-replay` with the synthetic bundle. Set-up, rights and limits are in the [public demo audit](../../docs/healthtech/audits/ptp-scout-public-demo-20261106/README.md).

Synthetic demo data is always labelled. Nothing here performs live search, provider calls or uploads.

Current-main compatibility and real-source browser checks: [integration audit](../../docs/healthtech/audits/pepo-ui-integration-20261031/README.md). Browser acceptance writes a fresh audit directory; `HEALTHTECH_E2E_OUT` can select an empty destination. Existing acceptance records are preserved.
