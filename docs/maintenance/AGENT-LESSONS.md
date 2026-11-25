# Lessons for the next agent account (kept current; last update 25 Nov 2026)

The owner switches Claude accounts when usage runs out. Read [CLAUDE.md](../../CLAUDE.md), then
[HANDOFF.md](../../HANDOFF.md), then this file. These lessons cost real time once; do not relearn them.

## Working with the owner

- Report in plain Thai with repository paths. Code, docs and UI stay English-first.
- Make routine decisions yourself (owner doc `05_DECISIONS_AND_OWNER_AUTONOMY.md` §2). Ask only about money, gated logins
  or data-terms acceptance, destructive data operations, and publishing.
- The owner often adds parallel tasks mid-turn. Run independent ones in their own session or subagent, verify their
  output yourself, then report.
- The owner wants high-impact research, not another diagnosis/boundary paper like Paper 53.
- The owner may shut the PC down at night. Long jobs must run detached on dr-train, with HANDOFF saying where they are.

## Research results that constrain new work

- **AM-7 stage 2a (20 Nov):** an OUT-only recall endpoint is gameable. Simply demoting same-IPC documents (N4) raised OUT
  R@200 from 0.328 to 0.383 while IN fell from 0.491 to 0.315, beating every proposed method. Always report IN and OUT
  together and keep N4 as a counterexample. Co-citation (N5) adds only about +0.01 and covers 45% of tasks.
- **P1-BridgeRet fine-tuning** lost to the zero-shot Qwen3/PatEmbed baselines on all 5 configs (USD 18.54 RunPod).
- **DAPFAM acquisition ideas** already tested NO_GO: see `docs/healthtech/research/paper2-precheck/README.md`.
- **DAPFAM is previously exposed:** B53 evaluated all 1,247 queries. It is not a tuning set and not a pristine TEST.
- **B53 Stage 2 (22 Nov):** 0 of 10 instruction contrasts are significant under every first stage, and Scrambled ≈ Generic.
  Instruction wording is not where the gain is.
- **B53.0 (22 Nov):** our DAPFAM TAC→TAC pipeline matches the DAPFAM paper's published BM25 and Arctic numbers within
  ±0.010 in 11 of 12 cells. Our evaluator is therefore trustworthy for G04.
- **But patembed-base scores above everything in the DAPFAM paper** (nDCG@100 ALL 0.366). It was trained on PatenTEB,
  which has the same source and authors as DAPFAM. **22 Nov audit:** the PatenTEB train/validation splits are not
  released (only test splits are on Hugging Face), and DAPFAM families occur inside PatenTEB data (50 queries and 466
  corpus families in just 3 test files). So PatEmbed is "possibly contaminated" on DAPFAM; never present it as a fair
  zero-shot DAPFAM baseline ([audit](../healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md)).
  - *Correction (22 Nov 2026, owner note 22112026):* the public-test overlap shows a **shared family pool**; it is not
    an audit of the unreleased training data. Training overlap, its size and its effect on DAPFAM scores are
    unmeasured, and the 80/10/10 split does not give an "eight times more likely" contamination odds. Keep PatEmbed as
    a separately reported row with this caveat.
- **G03 A2 (22 Nov):** a learned per-query selector over the same routes captures only 1.5% of the oracle headroom, and is
  PARKED. Three re-weighting/re-slicing mechanisms have now failed; only new candidate sources remain (A3).
  - *Correction (22 Nov 2026, owner note 22112026):* A3 is one acquisition hypothesis, not the last one. Its A3r0
    panel is one Claude, two Qwen and one DeepSeek model (not four independent lineages), and its four smoke calls are
    format evidence only (Haiku truncated at 400 tokens, keywords missing). A3r1 is amended prospectively before any
    effectiveness score.
- **Check masks when you add a route.** The A1 field routes skipped the filing-date and own-unit masks that
  `dense_bridgeret_v3.py` applies. New routes must copy the masks of the route family they join.
  - *Correction (22 Nov 2026, owner note 22112026):* do not write that such a defect "can only have hurt" the
    method. An inconsistent mask changes eligibility, ranking and window contents, so its effect on the score can go
    either way. Disclose the defect, keep the recorded decision, and call the size and sign of the effect unknown
    unless a corrected re-run measures it (memo §4a correction note).
- **G03 DEV harness:** `scripts/research/g03_*.py` reuses the precomputed P1-DEV/VAL route runs (BM25, Qwen3, PatEmbed,
  Arctic; depth 1,000) and the unchanged `eval_bridgeret_dev.py`. CPU only, about 30 minutes for a full arm grid. Its E01
  gate reproduced every single-route number exactly.

## Environment facts

**Owner PC**
- 15.7 GB RAM, Intel UHD only: no CUDA and no Ollama.
- `.venv` (3.12) has no numpy, torch or pyarrow; Workbench code is stdlib only.
- Use the [D27 scope](OWNER-DECISIONS-20261122.md) for authorized installs and dataset downloads. Record exact items, terms and hashes during execution. Other downloads retain their existing approval boundary.

**dr-train** (`ssh chaw@100.77.149.83`)
- Use the V100 only (`CUDA_VISIBLE_DEVICES=1`).
- Models are in `/data/ptp-paper2/models`: Qwen3-Embedding-0.6B, Qwen3-Reranker-0.6B, Arctic.
- The research venv `/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv` has torch and
  sentence-transformers, but no vllm and no fastapi. pyarrow is missing too, so process parquet locally.

**Real-model checks without a local GPU**
- Run `scripts/research/st_openai_embed_server.py` on dr-train CPU (`CUDA_VISIBLE_DEVICES=` empty, `setsid nohup`).
- Forward it to local loopback: `ssh -N -L 18000:127.0.0.1:18000 chaw@100.77.149.83`.
- Then run `scripts/research/g02_real_route_check.py`.
- Afterwards, stop the shim, pull its log and remove its folder (rule 8).

**Pitfalls**
- **Git Bash** rewrites `/paths` in ssh arguments: use `MSYS_NO_PATHCONV=1`.
- `pkill -f <pattern>` over ssh can kill your own remote shell. Use a pattern like `[s]t_openai...`, or `pgrep` then
  `kill`.
- A remote `nohup … &` over ssh keeps the ssh session open; use `setsid nohup … < /dev/null & disown`.
- **Windows:** Python `HTTPServer` sets SO_REUSEADDR, which lets two processes share a busy port. The Workbench binds
  exclusively; keep it so.
- **Numerics:** for MMR use batched matmul with a single similarity matrix (einsum was far too slow). Apply `-inf` masks
  after combining score matrices, otherwise NaN appears.

## Workbench design rules that must survive refactors

- Lexical (FTS5) is the default and the permanent fallback.
- Dense retrieval is opt-in hybrid mode, bound to an index generation. Search receipts are dependencies: citation,
  search_scope, and index_generation.
- A retained (identical) assessment must store its latest search receipt. Otherwise later rechecks redo work; this was
  found with the real model in G02.
- Credentials are environment-variable names only. A paid route needs `spend_cap_usd` > 0 and `max_requests` > 0.
  Unknown cost is "unknown", never 0.
- Evaluator fields (qrels, gold spans, verdicts) never reach runtime records (`workbench/datasets/`).

## Incident, 22–23 Nov 2026: our P2-T02 build exhausted dr-train memory

- The first full P2-T02 content build forked 32 tokenizer workers from a parent holding about 13 GB of claims data.
- Python's garbage collector touched the shared pages, so every worker gradually copied the parent memory.
- The host reached 125 GB used and 0 available, and became unreachable for SSH from about 07:00 Bangkok on 23 Nov.
- dr-train is shared, so other users' services were probably affected.
- The 2,000-unit smoke run could not reveal this.

**Rules from now on:**
- Never fork many workers from a large parent. Send each worker its own chunk, call `gc.freeze()` before forking, and
  recycle workers.
- Run a memory watchdog that aborts below a free-memory floor (P2-T02 uses 24 GiB).
- Never overlap large CPU stages on dr-train.
- Estimate peak memory at full scale (workers × per-worker RSS) before launch, not only from a small smoke run.
- Watch the first minutes of a full launch.


## RunPod and long runs (23–24 Nov 2026)

- **Measure the upload route before choosing a data centre.** The owner PC uploads to EU-SE-1 at about 47 KB/s and to US
  data centres at 3–8 MB/s (4 parallel tar streams).
- **Containers see the host's `nproc` and `/proc/meminfo`.** Use the cgroup quota and limit, and count the working set
  (`memory.current` minus `inactive_file`). Otherwise there are too many workers, or the build aborts falsely on page
  cache.
- **Windows-written file lists are CRLF.** Strip `\r` before `tar -T`, and set `pipefail` so a failed tar is not
  reported as "upload ok".
- **`pkill -f` with a plain pattern can kill your own ssh session.** Use `[p]attern`.
- **A network outage mid-generation pauses the budget ledger on unknown cost.** Reconcile from the provider's usage delta
  and resume; the caller skips finished apps.
- **Rebuilding C0 on another GPU reproduced dr-train closely:** BM25 exactly, dense models at 99.9% per-query identity.
  So rebuild gates with declared tolerances are a workable route when dr-train is down.
- **Wait with bash watchers, not agents** (owner request about token use). Details are in
  [NEXT-ACCOUNT-HANDOFF-20261124.md](NEXT-ACCOUNT-HANDOFF-20261124.md) §4.
