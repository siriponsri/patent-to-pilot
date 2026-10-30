# healthtech-web

Local TH/EN no-code frontend for Patent-to-Pilot HealthTech evidence dossiers: named device → import → evidence and exact source → notes → local save/reopen → edited TH/EN export.

```bash
npm start          # http://127.0.0.1:5178/
npm test
npm run test:e2e
```

No build step and no npm dependencies; Node ≥ 22. Runbook, acceptance matrix, evidence and known limits: [docs/healthtech/ux/implementation/README.md](../../docs/healthtech/ux/implementation/README.md). Specification: [docs/healthtech/ux/](../../docs/healthtech/ux/README.md).

Synthetic demo data is always labelled. Nothing here performs live search, provider calls or uploads.
