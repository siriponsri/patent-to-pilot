# P2-T02 run notes: coverage control (implementation, smoke, gates, job)

**Protocol:** [P2-T02-COVERAGE-CONTROL-PROTOCOL.md](P2-T02-COVERAGE-CONTROL-PROTOCOL.md), frozen at `bd30d3f7`. It was
not changed.
**Status (23 Nov 2026, 01:00 UTC): BLOCKED. dr-train is unreachable, and our content build is the likely cause. See §4.**
- The first full launch (22 Nov, 22:54 UTC) passed the C0 gate on the full P1-DEV runs.
- It then exhausted dr-train's memory in stage 1 (content build): the last reading was 125 of 125 GB used, 0 available.
- The builder and the queue have been fixed **locally only**; the fix is not yet deployed. The job must be killed and
  relaunched when the host is back.
- **No P2-T02 result number exists.** The only numbers here are smoke and reproduction-gate checks.
**Spend:** USD 0. V100 (device 1) only, under the shared GPU lock with memory fraction 0.12. No download, no paid call.
**Blocks:** P1-DEV only. Every script refuses other blocks; VAL and TEST are never read.

## 1. What was implemented

Scripts are kept in two places:
- locally in `scripts/research/`;
- on dr-train in `/data/ptp-paper2/p2-coverage/code/` (sha256 in `logs/code.sha256`).

| Script | Role |
|---|---|
| `p2t02_build_content.py` | §3 content: title + abstract + all live claims of the **same publication** as the unit text. C1 flat windows and C2 structural passages from identical token ids. Also the BM25 full text, stats and manifest. |
| `p2t02_encode.py` | Arctic on the V100, with the z-arctic settings. Three modes: `validate` (id path vs the stored C0 vectors), `queries` (P1-DEV) and `passages` (C1/C2, sharded checkpoints). |
| `p2t02_retrieve.py` | CPU exact inner product, max-p to units, then the `dense_bridgeret_v3.py` date and own-unit masks at unit level, tie-break and top 1000. |
| `p2t02_analyse.py` | Four modes: `gate` (C0 evaluator reproduction); `samerun` (C0 retrieval reproduction); `decide` (frozen contrasts and decision, plus the descriptives); `fusion` (descriptive F\*-style check). |
| `p2t02_queue.sh` | The whole pipeline as one resumable detached queue. It ends with `P2T02_DONE` or `P2T02_FAILED:<stage>`. |

Unchanged reused code, run in place:
- `bridgeret/code/eval_bridgeret_dev.py` (evaluator, fed `<(zcat run.tsv.gz)`);
- `bridgeret/code/bm25_bridgeret.py` (BM25-full, over a serialised dir whose `passages.jsonl` is the untruncated full
  text and whose `queries.jsonl` links to `ser-arctic-v1/queries.jsonl`);
- `g03-dev/code/g03_route_acquisition.py` (fusion grid, `--routes` substitution).

The cluster bootstrap and the F\* selection rule are copied verbatim from `g03_decide.py`.

### Implementation choices where the protocol is silent (all declared, none tuned)

- **Window size.** A "512-token window" is CLS + **510 content tokens** + SEP, which is 512 model positions. The C0
  serialiser also counts the special tokens inside its 512 cap, so the dense model sees at most 512 positions, as for C0.
- **Same tokens in C1 and C2.** Each segment (title+abstract, and each claim) is tokenized once without special tokens.
  C1 and C2 are cut from those identical ids, and the encoder receives the ids directly.
  - Check 1: the id path is bitwise identical to the text path on 256 C0 passages.
  - Check 2: joined-text vs per-segment tokenization differed by 0 tokens on the smoke sample.
- **C2 parent context.** A claim group over 510 tokens is cut as follows:
  - the first window is the group's first 510 tokens (it already begins with the independent claim);
  - every further window is the independent claim's first 64 tokens followed by the next 446 group tokens.
  - The repeated tokens are counted as overhead (`c2_parent_context_overhead_*` in `content/stats.json`).
- **C2 edge cases (counted):**
  - passage 0 (title+abstract) longer than 510 tokens is cut flat;
  - a dependent claim whose reference does not resolve joins the nearest preceding group;
  - a dependent with no preceding group opens its own group.
- **Claim order and the independence rule** are those of `build_bridgeret_texts.py` and `bridgeret_query.py`:
  - order is by claim number, ties by file order;
  - cancelled and empty rows are dropped;
  - a claim is independent when it has no `dependent` field and does not match the dependency regex.
  - The parent is the first referenced claim number that exists in the document, followed up to its root.
- **Same-publication rule.** Claims are keyed by the texts-v1 `doc` (rep_doc): `PG…` rows come only from `pg_claims_*`
  and `P…` rows only from `g_claims_*` (asserted). The derived first independent claim is checked against the texts-v1
  claim: 0 mismatches in the smoke.
- **Queries** are unchanged: `ser-arctic-v1/queries.jsonl`, P1-DEV, prompt `query: `, batches of 64 in file order, text
  path identical to `dense_bridgeret.py`.
- **Deeper-original-query control.** Under the G03 action model, one route at windows 1–2 (depth 400) is RRF-ranked and
  cut to the final depth of 200. Its R@200 therefore equals window 1 by construction. The smoke confirms delta 0 with
  CI [0, 0]. It is reported as declared (`deeper_original_query_control` in `results.json`); read it with that caveat.
- **Fusion check.** It runs only if `decide` reports a qualifying arm (protocol §5: "with the qualifying arm
  substituted"). It rebuilds the B = 4 grid with the qualifying route(s) substituted, applies the G03 F\* rule, and
  compares the result with the original F\* (`alloc-L0-Q2-P2-A0`) and with RR. It is descriptive only.
- **An unsettled case is recorded, not resolved.** If C2 qualifies against C0 but C1 does not and C2 − C1 does not
  credit structure, the frozen text does not name the baseline. `decide` then writes `UNSETTLED … (owner decision)`.

## 2. Smoke and reproduction gates (before launch)

Smoke run: `SMOKE=1 P2T02_ROOT=/data/ptp-paper2/p2-coverage/smoke bash code/p2t02_queue.sh`
- 2,000 corpus units and 128 P1-DEV queries;
- forced fusion over those 128 apps;
- every stage ran end to end and reached `P2T02_DONE` (22 Nov, 12:12–12:19 UTC).

| Check | Result |
|---|---|
| **C0 evaluator gate.** The existing `runs/z-arctic` and `runs/bm25` `run-P1-DEV.tsv.gz` go through this pipeline's evaluator path and are compared with `summary-P1-DEV.json`. | **PASSED, exact on every metric.** Arctic ALL R@200 0.29793 (n 26,547); BM25 0.21743 (n 26,547). |
| Encoder path (`validate`, 256 C0 passages) | The id path is bitwise equal to the text path (share 1.0). Cosine to the stored C0 vectors: min 0.99992, mean 0.999997. |
| C0 retrieval reproduction (`samerun`, 128 queries, identity aggregation over the 1M C0 vectors) | **Exact.** 128,000 of 128,000 rows are identical (rank, unit and score string). |
| Content build (2,000 units) | All assertions held:<br>• equal content: C1 tokens = C2 tokens − overhead, per unit;<br>• units are contiguous and covered;<br>• passage lengths ≤ 510.<br>0 first-claim mismatches; 0 units without claims. |
| Smoke encode speed (V100, fraction 0.12, BS 64) | C1 about 384 passages/s; C2 about 539 passages/s. Peak GPU memory 1.57 GiB. |

The smoke outputs are kept in `/data/ptp-paper2/p2-coverage/smoke/` (358 MB). Their metric values are meaningless,
because only 2,000 units were indexed.

## 3. The full job

**Location:** dr-train `/data/ptp-paper2/p2-coverage/`. **Relaunch only after the §4 recovery steps.** The queue is
launched with:
```bash
cd /data/ptp-paper2/p2-coverage
setsid nohup bash /data/ptp-paper2/p2-coverage/code/p2t02_queue.sh > logs/queue.log 2>&1 < /dev/null & disown
```
- **Log:** `logs/queue.log`, plus one log and one `/usr/bin/time -v` file per stage in `logs/`.
- **Sentinel:** `P2T02_DONE` (success) or `P2T02_FAILED:<stage>`.
- **Resumable:** re-running the same command skips stages that are already finished (encoder shards are checkpointed).

**Stages, in order:**
1. Gate.
2. Content build (CPU).
3. BM25-full (CPU, background).
4. Validation and query encoding (GPU).
5. C0 retrieval reproduction over all 25,626 P1-DEV queries (CPU, background).
6. Encode C1 (GPU), then retrieve C1 (CPU, background).
7. Encode C2 (GPU), then retrieve C2.
8. Evaluate.
9. `decide` writes `results.json`.
10. Fusion (conditional) writes `fusion/fusion.json`, or `fusion-not-run.json`.

**Outputs:**
- `results.json`: arm table, contrasts, decision, deeper control, candidates and recovery, cost;
- `gate.json`, `samerun.json`, `validate-c0.json`;
- `content/{stats,manifest}.json`;
- `runs/<arm>/run-P1-DEV.tsv.gz`;
- `evals/<arm>.json`.

**Ordering after the fix:**
- BM25-full runs in the background during the GPU encodes;
- the C1 and C2 retrievals run one after the other, only after BM25-full has finished;
- so no two large CPU stages overlap (C0 reproduction stays in the background; it needs about 6 GB).

**Expected duration from relaunch** (an extrapolation from the smoke rates, not a measurement):
- content build about 0.5 h;
- C1 encode about 3 h (about 4.0M passages);
- C2 encode about 3 h (about 6.0M passages);
- CPU retrieval, evaluation and analysis about 1 h;
- BM25-full runs alongside the encodes.
- **Total about 7–8 h** after relaunch. With the tokenizer limited to 16 workers, the build may take about 0.5–1 h.

**After completion (rule 8):**
- pull `results.json`, the gate files, `content/{stats,manifest}.json`, `logs/` and `evals/` to local;
- the large intermediates (`content/*.u32`, `content/ser-full/`, `enc/*/passages.f16.npy`, the smoke folder) can then be
  deleted once the coordinator has accepted the result.

## 4. Incident: the first full launch exhausted dr-train's memory (22–23 Nov 2026)

**What happened.** The timeline from `logs/queue.log` and `logs/build.log`:

| Time (UTC) | Event |
|---|---|
| 22 Nov 22:54:57 | `P2T02_START` |
| 22:56:01 | `STAGE0_GATE_PASSED`. Full P1-DEV, exact: Arctic ALL R@200 0.29793, BM25 0.21743; all metrics equal `summary-P1-DEV.json`. |
| 22:56:01 | `STAGE1_BUILD_START` |
| +126 s | Claims scan finished: 999,997 docs with live claims and 88,170 cancelled rows, which matches the P2-T01 audit. |
| +221 s to +1,064 s | Tokenization reached chunks 20 to 180 of 200, slowing down steadily. |
| about 23:00 onwards | SSH timeouts began; Tailscale still showed the host as active, via relay. |
| 23 Nov 00:54:55 | A short SSH reached the host once:<br>• `free -g`: **125 GB used, 0 available, buff/cache 1**;<br>• `p2t02_queue.sh` (PID 1536690) and the build main process (PID 1546555) were still alive;<br>• about 35 tokenizer worker processes each showed about 13 GB RSS;<br>• no GPU process of ours was running (the GPU stages had not started);<br>• the queue log still ended at `STAGE1_BUILD_START`. |

**Cause (our code).** `p2t02_build_content.py` forked 32 tokenizer workers from a parent that held the whole
claims table, about 13 GB of Python objects.
- Copy-on-write sharing does not hold for Python objects: reference counting and, above all, the children's cyclic
  garbage collector touch the inherited objects, so each worker gradually copied the parent heap.
- With 32 workers this exceeded the host's 125 GB.
- The 2,000-unit smoke could not show this, because its claims table was tiny.
- The host is **shared with other users' services**, which were probably affected while memory was exhausted. This
  should be reported to the owner.

**Fix (local only, not yet deployed or tested on dr-train).** It changes memory use only, not content.
- Script hashes after the fix: `p2t02_build_content.py` sha256 `f953dff5f5809f9b599a5115dbf7956b242d626a319432a690dc41ba35c79d74`; `p2t02_queue.sh` sha256 `2f76431d42fc223dfd9c1885cb2260841fd077b4b6637b50778e98bf9f8c6c5f`.
- Changes in `p2t02_build_content.py`:
  - each chunk's corpus rows and claim rows are pickled into its job, so workers never read the parent's table;
  - the parent heap is frozen with `gc.collect(); gc.freeze()` before forking, and workers run with GC disabled;
  - the tokenizer uses 16 workers (`--tok-workers`, separate from the 32 claims-scan workers) with
    `maxtasksperchild=8`;
  - a **memory watchdog** terminates the pool and exits with status 3 (the queue then prints `P2T02_FAILED:build`) if
    `MemAvailable` falls below 24 GiB (`--min-free-gib`);
  - `MemAvailable` is now printed in the progress lines.
- `p2t02_queue.sh` no longer overlaps the large CPU stages (§3).
- The content definition, windows, encoder, retriever, evaluator and analysis are unchanged.

**Recovery steps when dr-train is back** (in Git Bash, prefix `MSYS_NO_PATHCONV=1`):
1. `free -g` and `ps -u chaw -o pid,rss,etime,cmd | grep -E "[p]2t02|[b]m25_bridgeret"`. If the build is still alive
   (or hung after an OOM kill of a pool worker), stop our processes only:
   `kill 1536690 1546555`, then `pkill -u chaw -f "[p]2t02_build_content"`. Confirm that memory is freed.
2. Check other users' services are back. Report the incident to the owner.
3. Copy the fixed scripts:
   `scp scripts/research/p2t02_*.py scripts/research/p2t02_queue.sh chaw@100.77.149.83:/data/ptp-paper2/p2-coverage/code/`
   On dr-train, run `sed -i 's/\r$//'` on them. Compare `sha256sum` with the hashes above.
4. Remove the partial build: `rm -rf /data/ptp-paper2/p2-coverage/content`. Move the first launch's logs aside:
   `mv logs logs-launch1-oom`.
   - Keep `gate.json` and `evals/arctic-c0.json` / `evals/bm25-c0.json`; they are valid, and the queue skips the gate when
     `gate.json` has passed.
5. Optional: re-run the smoke (`SMOKE=1 …`, after `rm -rf smoke`). It does not exercise memory, so also watch the first
   10 minutes of the full build's `MemAvailable` lines in `logs/build.log`.
6. Relaunch with the §3 command. Watch the following:
   - the build's `MemAvailable` lines (they should stay far above 24 GiB);
   - `logs/encode-c1.log`, which should show `GPU lock acquired`, `memory fraction 0.12 set on Tesla V100-SXM2-32GB`, and
     after about 12 min the first `shard 1/… done` line.
   The sentinel is `P2T02_DONE` in `logs/queue.log`.
