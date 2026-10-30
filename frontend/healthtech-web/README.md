# healthtech-web

Local TH/EN no-code frontend for Patent-to-Pilot HealthTech evidence dossiers: named device → import → evidence and exact source → notes → local save/reopen → edited TH/EN export.

```bash
npm start          # http://127.0.0.1:5178/
npm test
npm run test:e2e
```

The dossier screen is a node-canvas workspace (n8n/Make style) with dockable, resizable panels, drag-and-drop with keyboard alternatives, a journey stepper, a guided tour and a TH/EN tutorial video. Rebuild the video from the real app with `node tutorial-video/build.mjs --render` (HyperFrames 0.8.221 and FFmpeg; the video is silent until a licensed music track is supplied).

No build step and no npm dependencies; Node ≥ 22. Runbook, acceptance matrix, evidence and known limits: [docs/healthtech/ux/implementation/README.md](../../docs/healthtech/ux/implementation/README.md). Specification: [docs/healthtech/ux/](../../docs/healthtech/ux/README.md).

Synthetic demo data is always labelled. Nothing here performs live search, provider calls or uploads.
