# Next-account handoff — 24 Nov 2026 (updated 08:00: A3r1 finished, P1 closed)

> Historical dispatch. Use the [current handoff](../../HANDOFF.md) and [RA Pharma master plan](../ra-pharma/MASTER-PLAN.md) for new work. The operating procedures below retain their original scope.

The previous Claude account stopped at the owner's request because its weekly limit was near. This file is the entry
point for the next account. Report to the owner in **plain Thai**. Code, docs and the paper stay English-first.

## 1. Read first, in this order

1. [CLAUDE.md](../../CLAUDE.md): standing rules, in force.
2. [HANDOFF.md](../../HANDOFF.md): current state, phase table, money, running and pending work.
3. [PHASE_BOARD.md](../tracking/owner-note-22112026/PHASE_BOARD.md): the live board. Update it only with
   `python scripts/tracking/ptp_tracker.py`.
4. [OWNER-DECISIONS-20261122.md](OWNER-DECISIONS-20261122.md): D1–D25. D20–D25 are new (RunPod R1/R2, volume, A3r1 on
   RunPod, full evaluation, policy v2.1).
5. [AGENT-LESSONS.md](AGENT-LESSONS.md) and the RunPod lessons in §4 below.
6. The owner note `docs/owner/owner-note-22112026/00_START_HERE.md` (owner-local; read only, never edit).

Then run `git status` and `git log -5`. The last pushed commit is on `main` (it ends this handoff).

## 2. Ordered task list for the next account

**Steps 1–2 below are DONE** (24 Nov, 08:00). Stage B is complete. The A3r1 full evaluation ran: frozen rule
**CONTINUE**, VAL +0.0213 [0.0146, 0.0280]
([receipt](../tracking/owner-note-22112026/receipts/P1-T05_stage_b_and_full_eval.md)). **Start at step 3.**

1. **Check Stage B (P1-T05).**
   - Look at `../_private_artifacts/g03-a3r1/stageb2-P1-DEV.log` and `stageb2-VAL.log` (last line `END ...`).
   - If incomplete or interrupted, re-run (it skips finished apps; envelope E1R):
     ```bash
     C=docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json; I=../_private_artifacts/g03-a3/inputs
     for b in P1-DEV VAL; do python scripts/research/g03_a3_llm_expand.py --config $C --queries $I/queries-dev-val.jsonl \
       --apps-file $I/apps-$b.json --block $b --model deepseek/deepseek-v4-flash-0731 \
       --ledger-root ../_private_artifacts/g03-a3r1/ledger --concurrency 8; done
     ```
   - If the ledger pauses on unknown cost (network timeouts), reconcile from the OpenRouter usage delta as on 24 Nov:
     `PYTHONPATH=src python -m patent_to_pilot.budget.ledger reconcile --envelope E1R --entry <id> --cost-usd <x> --by agent --evidence "<how computed>"`.
2. **A3r1 full evaluation (D24, envelope R2).**
   - Follow [A3R1-FULL-EVAL-RUNPOD.md](../healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md) and the runbook section
     "Full evaluation after Stage B" in [A3R1-RUNPOD-RUNBOOK.md](../healthtech/research/g03-dev/A3R1-RUNPOD-RUNBOOK.md):
     F-1 `--check-only` (exit 0 required), stage, one US pod, `g03_a3r1_runpod.sh full`, pull, receipt, delete the pod.
   - It yields F3\* and the frozen VAL decision (CONTINUE / REVISE / PARK). **It is the fourth G03 look at VAL**; disclose
     it.
   - **Confirm with the owner that pods may be opened again before creating one** (on 24 Nov the owner asked to defer pod creation).
3. **Merge D25 (policy v2.1).**
   - Branch `worktree-agent-a6d18c2dded3f86f2`, commit 56267477.
   - Run the full gate:
     `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main(['-q']))"`.
     Only the 8 known SACR r2/r3 failures are accepted.
   - Run `python scripts/ptp_run.py --smoke`; it must pass.
   - Merge, then update P4-T04 in the tracker.
4. **Finish the D19 package (WIP).**
   - Branch `worktree-agent-aa1038afae41aaf77`, commit ffae7a99. It is not verified: run its tests and the gate, then
     review `P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md` (C1 only for PatEmbed/Qwen3).
   - Its cost estimate must fit what remains of R2. Ask the owner before creating pods.
5. **Then P2-T04** (screen the bounded relation-search mechanism against close matched controls). It must now beat the
   **new** baselines: Arctic C1 and BM25-full, plus PatEmbed/Qwen3 C1 if D19 runs.
6. **P4-T05** (clean-install and user test with the owner), **P3-T03** (Thai text transfer; packets-v1 are ready;
   disclose the WangchanX→NitiBench 75% section exposure), and **P5** writing from real numbers only.
7. When dr-train returns: copy the Thai data (D18), then run the deferred descriptive P2-T02 fusion and
   deeper-control checks.

## 2a. dr-train is back (24 Nov, about 11:00 Bangkok) and the plan for it

- **State:** the admin rebooted it at about 06:48 on 24 Nov. It has 125 GB RAM (118 free), the **V100 is free**, `/data`
  has 979 GB free, and no process of ours runs there.
- **Cause of the outage was our job.** On 22–23 Nov the P2-T02 content build forked 32 tokenizer workers from a parent
  holding about 13 GB. Python's reference counting and garbage collector made every worker copy the parent memory, so
  the host reached 125/125 GB and all users lost the machine for about a day.
  - Record: [P2-T02-RUN-NOTES.md](../healthtech/research/p2-coverage/P2-T02-RUN-NOTES.md) §4 and
    [AGENT-LESSONS.md](AGENT-LESSONS.md).
  - **Rules for any dr-train job:**
    - give each worker its own chunk, and run `gc.freeze()` before forking;
    - use 8–16 workers at most;
    - run a MemAvailable watchdog of at least 24–30 GiB that kills only our job;
    - estimate peak memory (workers × RSS) at full scale before launching;
    - run large CPU stages one at a time.
- **Done on 24 Nov (owner approved in the action decision):**
  1. Deleted the 21 GB partial content build in `/data/ptp-paper2/p2-coverage/content`.
  2. Copied `thai-data` and `packets-v1` to `/data/ptp-paper2/thai-data/` (chmod go-rwx). The sha256 checks of both
     passed.
  3. Uploaded the P2-T02 RunPod outputs to `/data/ptp-paper2/p2-coverage-runpod/` and started the deferred descriptive
     checks (deeper original-query control and fusion with A = Arctic C1, L = BM25-full). This is CPU only, with 8
     workers and a 30 GiB watchdog. **DONE (18 min, no memory issue)**; the results are in the P2-T02 receipt: deeper
     retrieval adds 0 at R@200, and fusion F\* is unchanged (0.4230) with Arctic C1 / BM25-full substituted.
- **Owner choice:** D19 (PatEmbed/Qwen3 complete content) runs on **RunPod**, not dr-train.
- **Suggested dr-train use next:**
  - free CPU jobs (evaluations, fusion, analyses);
  - P3-T03 Thai text-transfer runs on the V100 (one job at a time; GPU lock; `CUDA_VISIBLE_DEVICES=1`; memory fraction
    ≤ 0.12);
  - pull and prune after each phase (rule 8).
  - Heavy multi-hour GPU or large-memory builds go to RunPod.

## 3. Where things are

| What | Where |
|---|---|
| P2-T02 outputs (runs, evals, gates, logs) | `../_private_artifacts/p2t02-runpod/` |
| A3r1 pilot outputs, relays, gate | `../_private_artifacts/g03-a3r1-runpod/` |
| A3r1 ledgers (pilot + Stage B) | `../_private_artifacts/g03-a3r1/ledger/A3r1/<model>/{P1-DEV,VAL}.jsonl` |
| Staging trees | `../_private_artifacts/{p2t02-runpod-stage,g03-a3r1-runpod-stage}/` |
| PatentsView sources (17 GB, verified) | `data/raw/uspto/`, hard-linked as `../_private_artifacts/pv-links/` |
| Rebuilt LF corpus text (sha `287ef7e0…`) | `../_private_artifacts/p2t02-local-check/texts-v1/` |
| Thai data + packets-v1 | `../_private_artifacts/thai-data/` (packets in `packets-v1/`) |
| dr-train archives | `../_private_artifacts/dr-train-archive/{20261121,20261122-g03}/` |

## 4. RunPod lessons (23–24 Nov)

- **Use US data centres only.** The owner PC uploads to EU-SE-1 at about 47 KB/s, but to the US at 3–8 MB/s over 4
  parallel tar streams.
- **Stock:**
  - Community pods often vanish between the stock read and the create.
  - Secure RTX PRO 4500 (US-KS-2, USD 0.72/h, 94 GB RAM) worked once.
  - Secure A100 (US-MD-1, USD 2.19/h) worked.
- **Image** `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`. It needs:
  - `apt-get install -y time`;
  - `pip install --break-system-packages "transformers==4.55.2" "tokenizers==0.21.4" "numpy==2.2.6" "scikit-learn==1.7.2" scipy "huggingface_hub<1.0"`.
- **Upload pitfalls:**
  - Untar with `--no-same-owner`.
  - File lists written by Windows Python are CRLF: strip `\r` (`tr -d '\r'`) before `tar -T`.
  - Use `set -o pipefail`.
  - Resume uploads by comparing sizes, then verify sha256.
- **Inside a container:**
  - `nproc` and `/proc/meminfo` show the host. Read the cgroup (`/sys/fs/cgroup/cpu.max`, `memory.max`,
    `memory.current` minus `inactive_file`).
  - The P2-T02 scripts already do this.
- **Detaching jobs:**
  - Launch with `setsid -f bash -c "... > log 2>&1 < /dev/null"`.
  - Never `pkill -f <pattern>` that matches your own ssh command line; use the `[p]attern` form.
- **Watchers:** use bash loops, never an agent. That keeps token use low, at the owner's request.
- **After every run:** pull the results, delete the pod, check that `list-pods` is empty, and read the balance.

## 5. Prompt to paste into the next account

```text
Continue the Patent-to-Pilot project (repo C:\Users\User\Desktop\myProject\patent-to-pilot) from another Claude account.
Read, in order: CLAUDE.md, HANDOFF.md, docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md, the live board
docs/tracking/owner-note-22112026/PHASE_BOARD.md, docs/maintenance/OWNER-DECISIONS-20261122.md (D1–D25),
docs/maintenance/AGENT-LESSONS.md. Then run git status and git log -5. Report to me in plain Thai.

A3r1 is finished (P1 closed: frozen rule CONTINUE, VAL +0.0213). dr-train is back and the deferred P2-T02 checks are
recorded (see §2a). Start at step 3 of the ordered task list in NEXT-ACCOUNT-HANDOFF-20261124.md §2: merge the D25 policy v2.1 branch after the full gate, finish and verify the D19
package and run it on RunPod (owner choice; ask me before opening pods), then continue with P2-T04 against the new
complete-content baselines. Follow the dr-train memory-safety rules in §2a for any dr-train job.

Standing rules:
- never open TEST data;
- freeze before any number;
- no spend outside the recorded envelopes (E1R for OpenRouter, R1/R2 for RunPod);
- state each pod's hourly price before creating it, and delete pods after use;
- commit only your own files with explicit paths;
- update HANDOFF and the tracker at every major event;
- never read or print .env or API keys;
- keep token use low: bash watchers, not agents, for waiting.

Ask me with a clear multiple-choice question before any decision that is mine.
```
