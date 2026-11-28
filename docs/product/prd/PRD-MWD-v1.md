# Market Window Dossier: product plan and PRD v1.0

Prepared by the main planner (Claude Opus 5.5) with the co-planner (GPT-6.2 Astra high) on 28 November 2026 for the **Product Owner (Claude Sonnet 5.5, medium effort)** under owner decision D42. Status: **v1 for owner review.** The co-planner's full input, with every link, is in [COPLANNER-INPUT.md](COPLANNER-INPUT.md). Product truth lives in [PRODUCT.md](../../../PRODUCT.md) and the visual system in [DESIGN.md](../../../DESIGN.md). This PRD governs what ships in v1.0 and in what order. Release scope comes from the approved [endgame plan](../../loe-bench/ENDGAME-PLAN.md#product-v10-claude-builds-the-product-gpt-executors-build-the-data-pipelines).

## 1. Problem and users

Thai and ASEAN generic makers commit to bioequivalence studies one to three years before launch. They need to know whether a US-style market window will still exist when they launch, and which molecules deserve their scarce freedom-to-operate (FTO) evaluators. Market Window Dossier ranks molecules by the chance of a first final US generic approval within 12 or 24 months, caps the queue at a fixed review capacity (1 in 5), and hands each selected case to an FTO evaluator as a dated, traceable dossier.

| User | Job | What they read |
|---|---|---|
| BD/R&D lead at a generic maker (primary) | Choose which molecules go to patent review this quarter | Review queue, decision summary, market window |
| FTO evaluator (primary, scarce) | Check patents, exclusivity and Thai status for a handed-off case | Patents tab, FTO hand-off checklist, references |
| IS2 committee and journal reviewers (secondary) | Judge whether the product's claims match the registered evidence | Landing page evidence panel, time machine, verify-the-forecast |

Decision support only. Qualified counsel determines freedom to operate. The disclaimer text is fixed in the endgame plan and appears unchanged on screen and in every PDF.

## 2. What exists (verified state, 28 Nov 2026)

| Component | Path | State | Receipt |
|---|---|---|---|
| Dossier builder, schema, C8 audit | `product/mwd/` | Merged. 32 development dossiers, 1,720/1,720 claims traceable | [PRD1](../../loe-bench/receipts/PRD1.md) |
| Evidence pilots C6/C7 | `product/evp/`, `docs/product/evidence/` | Merged. C6 3/5 documented restrictions; C7 17/17 family leads; Thai status 0/6 verified | [EVP](../../loe-bench/receipts/EVP.md) |
| Web app (F2 design), landing page | `product/demo/`, `product/site/` | Merged. Development data only, TH/EN | [UIBUILD](../../loe-bench/receipts/UIBUILD.md) |
| Windows desktop app (Tauri, unsigned) | `product/desktop/` | Merged. Installer outside Git in `_private_artifacts/mwd-desktop/` | UIBUILD |
| Current-queue adapter, snapshot refresh, PDF hook | `product/mwd/current.py`, `refresh.py` | Merged. 651 dossiers committed under `product/demo/data/current/` and wired into the app with search and launch-date window (branch `loe/PO-CURRENT`, pending planner review) | [PRODV1-DATA](../../loe-bench/receipts/PRODV1-DATA.md), [PO-CURRENT](../../loe-bench/receipts/PO-CURRENT.md) |
| F2 report renderer (print and PDF) | `product/demo/assets/dossier-print.js`, `product/mwd/render.py`, `pdf_check.py` | Built on branch `loe/PO-PDF` (PRD R2), pending planner review. Page one is the decision summary; long tables are in appendices | [PO-PDF](../../loe-bench/receipts/PO-PDF.md) |
| Track A scorer and release kit | `loe_bench/score_release`, `build_release` | Merged. Real readouts NOT_RUN until Nov 2027 and Nov 2028 | [SCORER](../../loe-bench/receipts/SCORER.md) |
| Track A freeze | tag `loe-track-a-freeze-20261127` | Frozen 28 Nov 11:18:44 UTC; OSF update 4 approved 11:30:06 UTC | TRACKA-FREEZE |

The freeze is verified, so the current queue is now unblocked for the product.

## 3. Claims the product may make

Every number shown must come from a receipt. Track method evidence, product readiness and publication readiness separately (section 8).

| Allowed claim | Source | Wording rule |
|---|---|---|
| M3 found 66.85% of first generic approvals within 24 months while reviewing 1 in 5 drugs; the label-only baseline B1 found 46.48% (H1 PASS, +20.37 pp) | SCORE receipt, OSF p2smd | Say "found" or "recall at fixed capacity". Never "accuracy" |
| The added value of the evidence graph was not confirmed (H2 FAIL) | SCORE | Show it on the Method page; do not hide it |
| Qwen2.5-7B with the same evidence found 12.36% in the tested setting | SCORELLM | Tested setting only; no general claim about LLMs |
| Prospective forecasts as of 27 Nov 2026 are frozen and timestamped; outcomes are pending | Track A freeze, OSF update 4 | Show PENDING until the scorer runs in Nov 2027 |
| Thai and ASEAN status is unknown unless verified | EVP | Show the next question to ask DIP or Thai FDA, never an inferred status |

Forbidden: FTO or legal conclusions, investment advice, user counts, time savings, customers, prices, or any comparison with a competitor presented as measured.

## 4. v1.0 requirements (ship by 15 Dec 2026)

**Owner requirement answers (28 Nov 2026, night).**
- v1.0 serves both audiences, demo first: the IS2 committee gets a complete product with the four wow demos, and the structure stays ready for real pilot users after v1.0.
- Users search the 651-drug current queue by name and choose a planned launch date that maps to the 12- or 24-month window. No new forecasts are computed, so every shown forecast stays the frozen Track A forecast.
- The Thai layer shows "unknown" with the next question: search terms, the agency to ask (DIP, Thai FDA) and the responsible person. No manual or automated Thai status collection in v1.0.
- Public hosting is Cloudflare Pages on a free `*.pages.dev` address under the owner's Cloudflare account (changed from GitHub Pages on 28 Nov; no custom domain).

Priority: P0 blocks the release, P1 is expected, P2 ships if time allows.

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| R1 | P0 | **Current queue** as of 27 Nov 2026 in the app, beside the historical time machine | 651 histories per horizon (12 and 24 months), 130 review slots, reference date shown, boundary ties explained, label "Track A t0 forecast, outcome pending". The UI reads `product/demo/data/current/index.json`. C8 audit re-run on the committed set with zero future-dated claims |
| R1b | P0 | **Search and launch-date window** | Search by active moiety or display name across the 651 drugs (TH/EN, case-insensitive, partial match). A planned launch date selects the 12- or 24-month window that covers it and says so; a date beyond 24 months shows "outside the forecast horizon" instead of a number |
| R2 | P0 | **PDF dossier from the real queue, in the F2 report design** | Same drug, date, language and version as the screen. Thai checklist lists search terms, WO and priority numbers (empty when unverified), the agency, the task owner and the missing status. Disclaimer identical to the screen. Page one carries the decision, endpoint (first final US generic approval, not launch, demand or Thai permission), horizon, uncertainty and next action; long evidence tables move to an appendix (one current export runs to 59 pages in Thai). Screen and PDF fields match for drug, jurisdiction, date, horizon, version, forecast, disclaimer and open tasks. Renders TH and EN for the top 10 queued drugs per horizon plus one boundary or unknown case, with Thai glyphs and page breaks inspected |
| R3 | P0 | **Honest landing page** with confirmed results | Evidence panel shows recall 66.85% always beside precision 26.62% at 20% capacity, H1 PASS, H2 FAIL, L1e exploratory, and Track A frozen with outcomes PENDING with links to OSF and receipts. No number without a receipt |
| R4 | P0 | **Public web deployment on Cloudflare Pages** (D-W approved; `*.pages.dev`, no custom domain) | Disclaimer on every page; works with no runtime CDN; checksums published; planner review before the first public push |
| R5 | P0 | **Windows installer** rebuilt on v1.0 data | Clean-machine test: install, offline use, PDF export, uninstall. SHA-256 published. Unsigned unless the owner buys a certificate |
| R6 | P1 | **Wow demo 1: time machine before the reveal** (historical solifenacin miss) | Guided path: open the dossier, choose what to send to a specialist, reveal the outcome and the later FDA letter. Also exercise one catch and the false alarm. Deep links, print and language switching never reveal early; any export made after the reveal is marked as revealed |
| R7 | P1 | **Wow demo 2: equal budget, who finds more** | 1-in-5 slot animation revealing B1 46.48%, M1 65.49%, M3 66.85%, L1e 12.36%, then M3 precision 26.62%. Reduced-motion fallback is a static table |
| R8 | P1 | **Wow demo 3: current queue to Thai hand-off in one click** | Pick a t0 drug, switch language, open one source, export the PDF. Thai status shows the next question, not an answer |
| R9 | P1 | **Wow demo 4: verify the forecast** | Show OSF update 4, match the digest of the downloaded prediction file, run the scorer on the known-answer fixture next to the Track A table marked PENDING. No leaderboard |
| R10 | P1 | **Snapshot refresh** for a maintainer | Documented command writes a dated snapshot with fetch date, versions, SHA-256, rows added and removed, failed sources. The t0 snapshot stays available. No promise of monthly updates |
| R11 | P1 | **Accessibility and language QA** | WCAG 2.2 AA contrast, full keyboard operation, `lang` switching, print layout; checked at 1440, 1280 and 1024 px and in the desktop window |
| R13 | P0 | **Rights inventory of shipped files** | Every shipped file lists its field sources, redistribution and commercial-use terms, version and hash. Restricted inputs (such as NBER) ship only as a recipe or link. Each shipped artifact shows its version, and the release states that the app, installer and scoring kit carry the frozen Track A bytes |
| R12 | P2 | Repository hygiene | Remove the 3 duplicate images (DOCS2 inventory); Apache-2.0 NOTICE covers `product/` (D-L); NBER data ships as a recipe |

**Not in v1.0:** auto-clear, investment recommendations, Thai price prediction, a general-purpose chatbot, AI forecasting, biologics, or any workaround for Thai registry restrictions.

## 4b. AI assistance and platform (D43, proposal for owner approval)

The owner wants a real product in which AI does useful work: API providers first for the demo, then a local model on a server, through one interface compatible with Typhoon, OpenRouter, GPT, Claude, Gemini, Qwen and DeepSeek. Codex executors build the backend. AI never forecasts: in the tested setting an LLM found 12.36% of events against 66.85% for M3 (SCORELLM). AI reads, explains and drafts. M3 ranks.

**AI tasks (owner chose all four).**

| ID | Pri | Task | Acceptance criteria |
|---|---|---|---|
| A1 | P0 | **Thai summary and explanation of the open dossier** | Every sentence cites one or more claim IDs from that dossier. A deterministic validator rejects a sentence with no citation, a citation to a missing claim, or a number or date not present in the cited claim; rejected sentences are replaced by "unknown: verify". Output is marked "AI draft" |
| A2 | P0 | **Hand-off letter draft** in Thai to an FTO evaluator, DIP or Thai FDA | Built from the FTO checklist: what to check, which source, which agency and which person. Same citation validator. The user edits before export; the PDF records model, provider, prompt version and date |
| A3 | P1 | **Questions about the open drug** | Answers only from that dossier's claims, with citations; otherwise says the evidence does not answer it. Not a general chatbot |
| A4 | P1 | **Patent claim reading aid** | Quotes claim text verbatim with patent number, claim number and source edition, then lists the elements to check. Labelled "AI-assisted reading; a patent professional must verify". Needs an open claim-text source (a data card for Codex) |

No LLM output is ground truth (standing rule 12). Quality is measured with deterministic citation and value checks plus a planner spot-check of a fixed sample, never an LLM judge. The full design is in the [co-planner AI platform memo](COPLANNER-AI-PLATFORM.md); the binding points are:

- **Grounding.** The server loads only the released dossier's claims for that snapshot and horizon, excluding outcome and reveal fields. Each output item is one proposition with claim IDs, resolved server-side to source, version, SHA-256 and locator. Numbers and dates are compared as typed tuples (entity, predicate, value, unit, jurisdiction, date role), with Thai digits and Buddhist Era dates normalized. Forecast numbers are injected from canonical fields, never taken from model text.
- **A3 in the trial.** Common questions map to fixed templates that the user confirms; unmatched free text stays on the device.
- **A4.** Copies original claim text from an approved claim node with character spans, shows parent claims, and returns a lookup task when the text, a dependency or the rights are missing.
- **Untrusted input.** Source text and titles are data. The model gets no tools, network, secrets or ability to send anything.
- **Frozen evaluation (before release inference).** 32 open development fixtures, 8 per task (5 answerable, 3 must-abstain), including unknown Thai status, a US/Thai swap, a changed horizon, a missing parent claim, a conflicting edition and an injected instruction. Gates: 100% resolvable citations, 100% matching numbers and dates, 100% exact A4 quotations, 12/12 correct abstentions, at least 4/5 answerable per task, and planner review of every displayed proposition with zero decision-changing errors, legal conclusions or reveal leaks. Supporting papers: ALCE ([Gao et al. 2023](https://arxiv.org/abs/2305.14627)) for citation completeness versus relevance, AIS ([Rashkin et al.](https://doi.org/10.1162/coli_a_00486)) for human support judgment, and [Greshake et al.](https://arxiv.org/abs/2302.12173) for indirect prompt injection. Competitors for the AI features (PatSnap Eureka, Clarivate Derwent, IQVIA AI Assistant) are external references; no head-to-head exists.
- **Wording.** Letters are drafts for review, never auto-sent, with no invented signatory, registration number or official response. A4 never states infringement, validity, enforceability, clearance or Thai approval, and never presents a translation as the authoritative claim.

**Platform (planner proposal for web, desktop, a future mobile app and an organization trial).**

```
 Web app (Cloudflare Pages)   Desktop app (Tauri)   Mobile (later: PWA or Tauri mobile)
            \                    |                     /
             one shared front end: product/demo (F2, static HTML/CSS/JS)
                                 |  HTTPS, JSON
                     MWD AI Gateway (FastAPI, Codex)
       grounding on dossier claims · citation validator · budget ledger · audit log
                                 |  one OpenAI-compatible client
   Typhoon · OpenRouter · OpenAI · Anthropic · Gemini · Qwen · DeepSeek · local vLLM/Ollama
```

- **One front end, three shells.** The existing static app stays the only UI code. GitHub Pages serves the public web app, Tauri wraps it for Windows (and later macOS), and a responsive layout plus a web-app manifest prepares the mobile path without a second code base.
- **One gateway.** A small Python FastAPI service holds provider keys server-side, so keys never reach a browser. A provider is a preset of base URL, model name and key name; switching provider or moving to a local model changes configuration, not code. The gateway reuses the project budget ledger (`src/patent_to_pilot/budget/`) to stop calls at the envelope and logs model, tokens, cost and prompt version per call.
- **Where it runs (owner, 28 Nov).**
  1. *Public web (Cloudflare Pages, `*.pages.dev`)*: the queue, sources and printable dossier, with no AI and no keys. A "Use AI with your organization" link opens the trial origin.
  2. *Organization demo, phase 1*: one Docker Compose package (gateway, web app, persistent SQLite ledger) runs on the owner's machine for a team demonstration, bound to localhost. Without a domain there is no public AI endpoint (owner, 28 Nov), so colleagues see the AI live on the owner's screen.
  3. *External server, phase 2*: the same package deploys to an external server such as dr-train. Any dr-train step follows the remote-work rules and the [artifact runbook](../../maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md) and needs a dated owner approval. dr-train's approved V100 is also the first candidate for local AI.
  4. *Desktop (Tauri)*: the bundled reader and PDF stay offline. An online window opens the gateway origin with the open case preserved. No Python sidecar.
  Browser "bring your own key" is dropped: CORS gives no key secrecy, and keys stay only on the gateway host.
- **Sign-in.** For the localhost demo, one allowlisted account: the owner's own email (kept outside Git, in the gateway's local configuration). Email one-time-code sign-in for invited colleagues (3–5, 5 requests per user per day) waits until a domain exists on Cloudflare, where Cloudflare Access one-time PIN behind a Cloudflare Tunnel is the chosen route (owner, 28 Nov).
- **Providers.** One Chat Completions client with per-provider presets (Typhoon, OpenRouter, OpenAI, Anthropic, Gemini, Qwen, DeepSeek, vLLM, Ollama). Live compatibility and Thai quality are NOT_RUN for every provider; only a provider-model-task tuple that passes the frozen gates is enabled. Typhoon's free tier collects usage data, so it receives public dossier data only and no user free text (owner, 28 Nov).
- **Local AI later (v1.1).** Serve an open model such as Typhoon or Qwen with vLLM or Ollama, which expose an OpenAI-compatible endpoint. The gateway changes its base URL; the model needs recorded rights, sizing and its own Thai evaluation.
- **Subscriptions instead of API keys.** Consumer ChatGPT Plus or Claude Pro plans are for one person through the official apps; routing a shared product through a personal subscription is not offered and is not planned. The legitimate subscription route is the reverse: expose MWD as a read-only MCP connector that each user adds to their own ChatGPT or Claude account. That is a candidate for v1.1, pending an owner decision, and its answers would sit outside the gateway's validator.

**Budget.** A D43 envelope of USD 10 gross until the end of 15 Dec 2026 (Bangkok), separate from the research envelopes, with an operational stop at USD 8 or 200 attempts, and a pause on unknown billing or a price or route change. The co-planner's indicative estimate for 200 attempts on `openai/gpt-4o-mini` through OpenRouter is USD 0.15 in tokens (price to be verified live).

**Open owner decisions.** A domain on Cloudflare (needed before colleagues can use the AI remotely); the dr-train deployment date; the MCP connector for v1.1.

## 4c. MCP connector and AI-agent access (owner request, 28 Nov 2026)

The owner asked for an MCP connector that AI agents can use, naming computer-use agents, Grok and "OpenBot" as examples. Each user's own agent or subscription does the writing; MWD supplies dated, cited evidence. The connector holds no model and no keys, so it costs no API budget.

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| M1 | P1 | **Read-only MCP server** over released public data: `search_drugs`, `get_queue` (as of, horizon, capacity), `get_dossier` (sections, claims), `get_sources` (issuer, edition, locator, SHA-256), `get_fto_checklist`, `get_method_card` (registered results with denominators, H2 FAIL, pending Track A) | Every result carries claim IDs, source locators, the as-of date, mode (development or Track A t0), and the fixed disclaimer. No outcome or reveal fields in the current view. Tool descriptions state that MWD gives decision support, not an FTO or legal opinion |
| M2 | P1 | **Two transports from one tool definition** | Local stdio for desktop agents (Claude Desktop, Claude Code, Codex CLI and other local MCP clients). Remote Streamable HTTP on Cloudflare Workers at a free `*.workers.dev` address (no domain needed), serving only public data with no sign-in, rate-limited, for remote clients such as ChatGPT connectors, Claude custom connectors and the xAI (Grok) API's remote MCP tools |
| M3 | P2 | **`check_draft` tool** | An agent submits its own draft text with claim IDs; the deterministic B2 validator returns per-sentence pass, fail or unknown with reasons. This keeps external answers checkable even though MWD does not control the agent's text |
| M4 | P1 | **Agent-ready web UI for computer-use agents** | Semantic HTML, stable accessible names and roles for every control, URL deep links for each queue, dossier, tab and language, no information available only in canvas or images. A scripted computer-use walkthrough (open queue, search a drug, open a dossier, export the PDF) passes |
| M5 | P2 | **OpenAPI description** of the same read-only endpoints | For agents that use function calling without MCP |

Client compatibility is a test target, not a claim: each named client is recorded PASS, FAIL or NOT_RUN in the receipt with its version. Remote clients' terms and data handling belong to each user's own account. **OpenBot** ([repository](https://github.com/nightly-labs/openbot), [site](https://openbot.run/); 0.81.1, 28 Nov 2026) is a local-first desktop workspace by Synthetify Labs that runs other vendors' agent CLIs (Codex, Claude Code, Grok CLI, Gemini and others). Its changelog documents adding MCP servers as a local command or a remote address, and it uses `SKILL.md` skills in the Codex folder layout. It is a test client for both M2 transports. Its licence is PolyForm Noncommercial 1.0.0, so use inside a company needs a commercial OpenBot licence (the owner's decision), and its agents run with full access, so test it only against the read-only MWD connector.

| M6 | P2 | **MWD agent skill** (`SKILL.md`, Codex folder layout) | Tells an agent which MWD tools to call, to keep claim IDs and the disclaimer, to say "unknown: verify" when evidence is missing, and never to give FTO or legal conclusions. Tested in Claude Code, Codex CLI and OpenBot |

## 5. Plan and cards for the Product Owner

Each card is small enough for one Sonnet 5.5 medium session. The Product Owner works on `loe/<card-id>` branches cut from `research/loe-bench` in its own worktree, writes a receipt in `docs/loe-bench/receipts/`, and asks the main planner for review before merge. Data-pipeline changes in `product/mwd/` or `loe_bench/` go to a GPT executor through the planner (owner decision, 28 Nov).

| Order | Card | Covers | Depends on | Target |
|---|---|---|---|---|
| 1 | PO-CURRENT | R1 and R1b: commit current-queue data, wire the current view with search and launch-date window, re-run C8 | Freeze (done) | 30 Nov |
| 2 | PO-PDF | R2: F2 report renderer for the real queue | PO-CURRENT | 3 Dec |
| 3 | PO-LANDING | R3 and R12 | none | 3 Dec |
| 4 | PO-WOW | R6–R9 | PO-CURRENT | 8 Dec |
| 5 | PO-QA | R11 and R10 docs | PO-PDF, PO-WOW | 10 Dec |
| 6 | PO-SHIP | R4, R5 and R13: deploy, installer, clean-machine test, checksums | PO-QA, planner review | 13–15 Dec |

Backend cards for Codex (D43), dispatched by the planner once the owner approves section 4b:

| Order | Card | Executor | Covers | Target |
|---|---|---|---|---|
| B1 | BE-GATEWAY | GPT-6.2 Sol high | FastAPI gateway, typed task API, provider presets, D43 ledger envelope with the USD 8 stop, audit log, Docker Compose package that runs on the owner's machine, fixture provider (no paid call in tests). Contract frozen by 30 Nov | 3 Dec |
| B2 | BE-GROUND | GPT-6.2 Sol xhigh | Dossier-claim grounding and the deterministic citation and value validator for A1–A3, with a fixed evaluation sample | 5 Dec |
| B3 | BE-CLAIMS | GPT-6.2 Sol high | Open claim-text source and adapter for A4 (rights recorded) | 8 Dec |
| B4 | BE-ORG | GPT-6.2 Sol high | Localhost binding and single-account allowlist for the owner demo; a documented Cloudflare Tunnel + Access (email one-time PIN) recipe ready for when a domain exists; per-user limits and revocation; a deployment recipe for an external server such as dr-train (no remote step without owner approval) | 9 Dec |
| B5 | BE-MCP | GPT-6.2 Sol high | Section 4c M1, M2, M5, M6 (M3 after B2): shared tool layer, stdio server, Cloudflare Workers remote server with a deploy recipe the owner runs from their own account, OpenAPI, client test matrix | 8 Dec |

The Product Owner covers M4 in PO-QA (accessible names, deep links, a computer-use walkthrough).

The Product Owner builds the AI panels (PO-AI: A1–A4 in the dossier view, the "AI draft" label, the editor for the hand-off letter) against the B1 fixture provider, so UI and backend proceed in parallel.

Token economy for the Product Owner: read this PRD, PRODUCT.md, DESIGN.md and the card's receipts only; do not re-read research protocols; reuse `product/demo/app.js` patterns; run only the product tests (`py -3.12 -m pytest product/mwd/tests`) plus a headless screenshot check per card.

## 6. Roles and governance (D42)

| Role | Who | Scope |
|---|---|---|
| Product Owner | Claude Sonnet 5.5, medium | Owns `product/` UI, `PRODUCT.md`, `DESIGN.md`, `docs/product/`; builds the UI, report design and wow demos; keeps this PRD's status table current |
| Main planner and only reviewer | Claude Opus 5.5 | Writes and revises this PRD with the co-planner, reviews every product branch, integrates, reports to the owner in Thai |
| Co-planner | GPT-6.2 Astra high | Product methodology, evidence and competitor critique; roadmap and metrics |
| Data-pipeline and backend executors | GPT-6.2 Sol high or xhigh (Codex) | `product/mwd/` builders, adapters and audits, and the AI gateway backend (D43), dispatched by the planner |
| Owner | Siripon Srihangpiboon | Approves outward-facing steps not already covered by D-W, certificates, pricing and any user study |

## 7. Evidence and competitors

No head-to-head comparison with any commercial product exists. The only measured comparison is inside LOE-Bench. Sources marked † appear in the project's literature receipts ([LITB](../../loe-bench/receipts/LITB.md)). The co-planner supplied the others; they are external references, and the planner has not re-verified their links.

| Competitor or benchmark | What MWD can honestly claim | Status |
|---|---|---|
| [Clarivate Cortellis](https://clarivate.com/life-sciences-healthcare/training-support/cortellis/product-intelligence-release-information/) US Generic Forecast | Forecasting alone is already sold. MWD shows a fixed queue, its dated evidence and a registered scoring rule | External reference |
| [IQVIA Ark Patent Intelligence](https://www.iqvia.com/solutions/industry-segments/generics/ark-patent-intelligence) | MWD names the family identifier it found and the local check still open; coverage is unmeasured | External reference |
| [DrugPatentWatch](https://www.drugpatentwatch.com/p/index.php) | MWD gives a probability for a defined approval horizon, not an estimated launch date | External reference |
| [Evaluate](https://discover.evaluate.com/loss-of-exclusivity-report-download), [GlobalData](https://www.globaldata.com/marketplace/dataset/pharma-regulatory-milestones-tracker-/) | Price and demand context stays labelled apart from the forecast; a listed expiry does not settle Thai legal status | External reference |
| [FDA Orange Book viewer](https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book) (manual lookup) | Lookup time saved is an untested hypothesis for a future timed task | Untested hypothesis |
| Beall et al. entry-date method† ([PubMed](https://pubmed.ncbi.nlm.nih.gov/30502781/)) | Quarter-error and recall at fixed capacity have different denominators; not reproduced head-to-head | External reference |
| LOE-Bench B1, M1, M3, L1e ([SCORE](../../loe-bench/receipts/SCORE.md), [SCORELLM](../../loe-bench/receipts/SCORELLM.md)) | M3 66.85% vs B1 46.48% at 24 months and 20% capacity (+20.37 pp, 95% CI 14.37–26.16); M1 65.49%; precision 26.62%; H2 failed; L1e 12.36% exploratory | Measured head-to-head |

| Requirement | Primary paper and what it supports |
|---|---|
| R1 current queue | Hopefl et al. 2025† ([doi:10.1111/cts.70365](https://doi.org/10.1111/cts.70365)): define the event and risk set precisely; a submission C-index cannot benchmark approval recall |
| R6 time machine | Cramer et al., COVID-19 Forecast Hub ([doi:10.1038/s41597-022-01517-w](https://doi.org/10.1038/s41597-022-01517-w)): separate when a forecast was issued from when its target became observable |
| R2 dossier and PDF | Schwartz et al., facts-box trials ([PubMed 19221371](https://pubmed.ncbi.nlm.nih.gov/19221371/)): a short first-page summary aids number comprehension; transfer to Thai pharmacists is untested |
| R8 FTO hand-off | First-generics cohort of stays, approvals and launches ([PubMed 33982425](https://pubmed.ncbi.nlm.nih.gov/33982425/)): keep legal, regulatory and market events distinct in the hand-off |
| Thai layer | Tenni et al. ([doi:10.1186/s12992-024-01053-9](https://doi.org/10.1186/s12992-024-01053-9)): Thai access conclusions depend on local assumptions; no status evidence for our cases |
| R10 snapshot refresh | NBER Orange Book dataset construction ([PMC10731339](https://pmc.ncbi.nlm.nih.gov/articles/PMC10731339/)): editions change; keep prior editions and diffs |
| R9 verify the forecast | Reich et al. ([doi:10.1073/pnas.1812594116](https://doi.org/10.1073/pnas.1812594116)): archive original predictions and score against a specified outcome edition at maturity |
| R4, R5 web and installer | Chirigati et al., ReproZip ([USENIX TaPP 2013](https://www.usenix.org/conference/tapp13/technical-sessions/presentation/chirigati)): clean-environment replay as the release test |

## 8. Readiness metrics (separate decisions)

- **Can the product ship?** Dossiers reachable out of 651 per horizon, expected review slots, matching screen/PDF pairs out of pairs tested, resolvable claims out of claims (C8 on the shipped bytes; 100% required; zero future-dated as-of inputs), unsupported decision-changing statements (one blocks sign-off), open Thai tasks with an owner, and completed distribution and restore checks. The Product Owner records PASS, FAIL, BLOCKED or NOT_RUN per release candidate; the main planner reviews before release.
- **Does a user benefit?** Not measurable in v1.0. Correct unaided hand-offs, critical misinterpretations and time to a correct referral need C10 (EC-KMITL approval) or a separately authorized pilot. Scripted walkthroughs before approval are engineering evidence only.
- **Does the method work?** Registered recall at 20% capacity, precision and paired gains (SCORE). Track A readouts on 27 Nov 2027 (12 months, descriptive) and 27 Nov 2028 (24 months).
- **Is a publication ready?** Tracked in the writing lane, not here.

## 9. After v1.0 (options, not commitments)

The co-planner ranked these options. Thresholds are proposed go/stop rules to agree before any trial. A continuing service needs a named maintainer independent of the owner by 31 January 2027.

| Rank | Option | Success metric | Kill or narrow when |
|---|---|---|---|
| 1 | v1.1 one-page referral | After ethics approval, ≥ 8/10 readers identify the US endpoint, the local unknown and the responsible role unaided | Any reading as legal clearance; below 8/10 after one revision |
| 2 | v1.1 local portfolio shortlist (names in, nothing uploaded) | ≥ 45/50 names on a public fixture resolved, every ambiguous name flagged, no input transmitted | Any silent wrong identity |
| 3 | v1.2 snapshot differences for a successor | Two dated diffs reproduced with t0 hashes preserved | No successor, or any overwrite |
| 4 | v1.2 paid onboarding pilot. **Pricing hypothesis: THB 15,000 per team.** Needs owner approval; no outreach is authorized | 2 of 5 qualified teams accept and 1 completes a hand-off | 0 of 5 accept, or cost exceeds the fee on both pilots |
| 5 | v2.0 verified Thai status for 20 predeclared cases | ≥ 16/20 with an official record and reviewer sign-off | No lawful access or accountable reviewer |

## 10. Risks

| Risk | Control |
|---|---|
| Claims: 66.85% read as the chance a drug launches, or a low rank read as clearance | Recall always beside precision with denominators; H2 failed and L1e exploratory; the same wording on landing page, app, PDF and demo |
| Data rights: the public bundle republishes restricted rows | R13 rights inventory; recipes for restricted inputs; withhold and disclose any uncleared field |
| Thai evidence: a family match or an inaccessible register read as absence | Show denominators (family leads 17/17, Thai members 0/17, Thai status 0/6); one DIP or Thai FDA task per question |
| Operation after January 2027 | A consenting maintainer restores the public version and runs the fixture before 31 Jan; otherwise a fixed reference edition with no update promise |
| Interface trust: development and prospective data confused, or a stale edition missed | Mode and cutoff on every page; the t0 Orange Book edition (10 July 2026) and 628/651 UNKNOWN challenge states shown with the next action |
