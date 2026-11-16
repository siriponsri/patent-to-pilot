# RunPod encoding pilot: runbook (prepared 2026-11-16, nothing rented yet)

Approval: [owner-runpod-pilot-approval.json](owner-runpod-pilot-approval.json). Hard cap **USD 10**, about USD 2 expected, two pods of at most 45 minutes each. Not granted: full-corpus encoding, spend above USD 10, an API key in the repo or logs, and sending DAPFAM or Paper 1 test data to RunPod.

## 1. What is ready

| Item | Where | Check |
|---|---|---|
| Sample: 6,261 US utility grants, title + abstract + claims (TAC) | dr-train `/data/ptp-paper2/runpod-pilot/sample.jsonl` (48,303,918 bytes) | sha256 `5e9235c052ab063b2eca2b4c6794ada04d9de544de9658538e5a2ea2a1275dc3`; [receipt](results/sample-receipt.json) |
| Bundle for the pod: sample, scripts, V100 reference vectors (1k docs, fp32 + fp16) | dr-train `/data/ptp-paper2/runpod-pilot/bundle/runpod-pilot-bundle.tar.gz`; local copy `data/raw/runpod-pilot-bundle/` (git-ignored) | 39,565,149 bytes, sha256 `feaca15e5af917c8f5155fbaa5939a3f28284fa58c0fdf702caf82d7a0cc5fb1`; per-file `SHA256SUMS` inside |
| Sample builder | [build_pilot_sample.py](build_pilot_sample.py) | stdlib only; local and remote builds are byte-identical |
| Encoder | [encode_pilot.py](encode_pilot.py) | passage rule identical to `dapfam_acquisition.dense_passages` on all 6,261 docs |
| Parity check | [parity_check.py](parity_check.py) | CPU only, numpy |
| Pod script | [pod_run.sh](pod_run.sh) | watchdog, checksums, both encodes, parity, results tarball |
| Decision table | [decision_table.py](decision_table.py) | reads receipts and prints hours and USD for 23M and 33M passages |
| V100 reference (dr-train) | [results/v100-ref-20261116/](results/v100-ref-20261116/) | see section 2 |
| dr-train runner | [run_drtrain_reference.sh](run_drtrain_reference.sh) | guards against colliding with the S8 driver |

### Two deviations from the request

**1. The text comes from the USPTO weekly grant XML, not PatentsView `g_patent`.** `g_patent` has no abstract: its columns are id, type, date, title, wipo_kind, num_claims, withdrawn and filename. No downloaded PatentsView table has abstract or claim text. The owner had already downloaded `ipg180102.zip` (grants of 2 January 2018, public domain, sha256 `a8dca2bb…7d35`), and it carries title, abstract and claims. So the pilot uses the **full TAC construction**, the same fields as DAPFAM, instead of a TA-only proxy.

- Measured density: **4.31 passages/doc** (26,972 passages). This matches the OA-SPLITS planning assumption of about 4.2 (5.5-7.9M docs → 23-33M passages).
- The same documents with TA only give 1.00 passage/doc.

**2. There are 6,261 documents, not 10,000.** One weekly file holds only 6,920 grants, of which 6,261 are utility B1/B2 with all three texts; 630 designs, 22 plants, 7 reissues and 147 sequence listings are excluded.

- The ordering rule is unchanged: sha256(`20261116:<patent_id>`) ascending.
- Reaching 10,000 needs a second weekly file (about 130 MB), which needs owner download approval.
- For throughput this does not matter, because 26,972 passages is plenty.

## 2. V100 reference (dr-train, 2026-11-16, run beside S8)

First 1,000 sample documents = 4,228 passages, run in the existing `python:3.12-slim` image with the pinned venv:

- torch 2.8.0+cu128, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6;
- driver 580.178.04;
- model `datalyes/patembed-large` @ `2d5c0f92…`, weights sha256 `234ea36a…`;
- caps: GPU allocator 8 GiB, batch ≤ 32, no network.

The GPU was **shared with the running S8 SACR batch**, so the rates are lower bounds. For comparison, fp32 on an idle V100 measured 36.5 p/s earlier.

| Mode | Batch | Passages/s (wall) | GPU forward s | Peak reserved | Total wall |
|---|---|---|---|---|---|
| fp32 | 32 | **21.7** | 192.1 | 2.67 GB | 291 s |
| fp16 | 32 | **104.7** | 37.3 | 1.33 GB | 71 s |

Parity, V100 fp32 vs V100 fp16 on the same 4,228 passages ([JSON](results/v100-ref-20261116/parity-v100-fp32-vs-fp16.json)):
- cosine min 0.999995, mean 0.9999997, 0 passages below 0.999;
- 50 queries: top-1 agreement 1.00, overlap@10 1.00, overlap@100 0.999.

GPU use: about 362 s of wall time on the V100. S8 was not touched: SACR b3 kept running, and the run started inside the safe window (batch age 30 min).

## 3. Before renting (owner, once)

1. The RunPod account already exists, with a **USD 57 prepaid balance** (owner, 2026-11-16).
   - **The pilot cap stays USD 10.** The balance does not raise it, and it is no longer a safety net: RunPod would keep billing well past USD 10.
   - Spend is therefore tracked as **balance_before − balance_after**, read from the console (Billing) or the API (MCP), and pods stop before cumulative pilot spend reaches USD 10 (section 6).
   - Keep auto-pay / auto-recharge off, so the balance cannot grow during the pilot.
2. Option (a) or (b) below. The owner has not chosen yet; both stay available.
   - For SSH/scp, add an SSH public key in RunPod → Settings → SSH Public Keys.
   - For option (b), add the public key of this PC, so the agent can copy the bundle.
3. Never paste an API key into chat, the repo or a file. Option (b) uses OAuth instead.

## 4. Pod choices (Community Cloud, in this order)

| Order | GPU | Indicative price (check the live page) | Watchdog | Worst case |
|---|---|---|---|---|
| 1 | RTX 4090 24 GB, Community | about USD 0.34/h | 40 min after the script starts | about USD 0.26 |
| 2 | A100 SXM 80 GB, Community (A100 PCIe if SXM is unavailable) | about USD 1.39/h | 40 min | about USD 1.04 |

- Template/image: **RunPod PyTorch 2.8** (`runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04`).
  - If that exact tag is not listed, pick the closest torch 2.8 / CUDA 12.8 template and write the tag in the spend table. The receipt records the versions anyway.
  - Use the CUDA filter ≥ 12.8.
- Container disk 30 GB. **No network volume**: volumes keep billing after the pod stops.
- Expose TCP 22 (SSH) and 8888 (Jupyter).
- Stop at the end = **Terminate** (`runpodctl remove pod`), not Stop.

## 5. Running one pod

### (a) Owner clicks in the RunPod console

1. **Write down the balance** (Billing page) as `balance_before` and check the start rule in section 6. Then deploy: Pods → Deploy → Community Cloud → the GPU from section 4 → template above → container disk 30 GB → Deploy. **Note the time.**
2. Upload `data/raw/runpod-pilot-bundle/runpod-pilot-bundle.tar.gz` to `/workspace`, in one of three ways:
   - Connect → JupyterLab → upload button; or
   - `scp -P <port> -i <key> runpod-pilot-bundle.tar.gz root@<public-ip>:/workspace/` (port and IP are under Connect → "SSH over exposed TCP"); or
   - `runpodctl send runpod-pilot-bundle.tar.gz` on the PC, then `runpodctl receive <code>` in the pod terminal.
3. In the pod terminal (Jupyter → Terminal, or SSH):
   ```bash
   cd /workspace && tar xzf runpod-pilot-bundle.tar.gz && PRICE_PER_HOUR=0.34 bash runpod-pilot/pod_run.sh rtx4090 40
   ```
   Use `a100sxm` and the A100 price for the second pod. The script starts a self-terminate watchdog, verifies checksums, installs the pinned transformers/tokenizers/numpy/safetensors, downloads the pinned model (about 1.3 GB), and runs:
   - fp16 on the whole sample with a batch sweep 32-512;
   - fp32 on the first 1,000 docs;
   - parity against the V100 fp32 reference;
   - the decision table.

   Expected 10-20 minutes in total.
4. Fetch `/workspace/results-<label>.tar.gz` and its `.sha256` (Jupyter download, scp, or `runpodctl send`) to `docs/healthtech/research/paper2-precheck/runpod/results/`.
5. Terminate immediately: `runpodctl remove pod $RUNPOD_POD_ID` in the pod, or Terminate in the console.
   - Check in the console that the pod is gone and the balance stopped moving.
6. A few minutes after terminating, read the balance again as `balance_after`. Fill in the spend table (section 6) and `runpod-spend.json`: pod spend = balance_before − balance_after.

### (b) Agent via the RunPod MCP (hosted OAuth, per-action approval)

1. The owner adds the hosted server to Claude Code with `claude mcp add --transport http runpod https://mcp.runpod.io/`, then runs `/mcp` → runpod → Authenticate and signs in to RunPod in the browser.
   - The server holds the session token; no key enters the repo, logs or chat.
2. The agent reads the account balance through the MCP (`balance_before`), lists the GPU types and live prices, and checks the start rule (section 6). It then asks for approval of **each** action: create pod, then terminate pod. The owner approves each tool call.
3. The agent scp's the bundle (SSH key from step 3.2), runs the same `pod_run.sh` command over SSH, and fetches the results. It then calls terminate, confirms through the MCP that the pod is gone, reads `balance_after`, and records the spend.
   - If the MCP cannot return the balance, the owner reads it from the console before and after.
4. Tool names differ between server versions. The agent must list them after connecting and never guess.

## 6. Cost guard and spend table

**Spend is measured, not estimated.** Pilot spend = `balance_before` (read before the first pod) − the current balance, from the console Billing page or the API. With the USD 57 balance, the balance itself does **not** stop anything at USD 10, so the guards below are what enforce the cap.

Guards:
- per pod: watchdog 40 minutes after the script starts, plus about 5 minutes of deploy, so at most 45 minutes;
- the console reminder: Terminate at Deploy + 45 minutes no matter what;
- **start rule: do not deploy a pod if cumulative spend + hourly rate × 0.75 > USD 9** (USD 1 margin for rounding, image pull and billing lag);
- **running stop:** while a pod runs, cumulative spend = (balance_before_pilot − current balance) + the running pod's elapsed minutes × rate / 60. If that reaches USD 9.5, terminate at once, even mid-run. This is deliberately conservative: it may double-count while the balance updates live;
- after each pod, wait until the balance stops moving (a few minutes) before reading `balance_after`;
- no network volumes and no stopped (not terminated) pods; both keep billing;
- terminate every pod before the pilot is closed, and check that the pod list is empty.

With the indicative prices, both pods at their worst case cost about USD 1.30, far below the cap.

| # | Deploy → Terminate (date/time) | GPU / image tag | USD/h | balance_before | balance_after | Pod spend (before − after) | Cumulative pilot spend | Start rule (cum + rate × 0.75 ≤ 9)? |
|---|---|---|---|---|---|---|---|---|
| 1 | | RTX 4090 Community | | (≈ 57.00) | | | | |
| 2 | | A100 SXM Community | | | | | | |

Cumulative pilot spend = balance before pod 1 − balance after the last pod. Record the same numbers in `runpod-spend.json`.

## 7. Decision table: picking the full-encoding option

After both pods, run (from the results folder):

```bash
python decision_table.py "V100 fp16 (dr-train, shared)=0=v100-ref-20261116/receipt-fp16.json" \
  "RTX 4090 fp16=<USD/h>=<4090>/out-rtx4090-fp16/receipt-fp16.json" "A100 fp16=<USD/h>=<a100>/out-a100sxm-fp16/receipt-fp16.json"
```

Measured so far:

| Option | Passages/s | Hours, 23M | Hours, 33M | USD, 23M | USD, 33M |
|---|---|---|---|---|---|
| V100 fp32, dr-train, shared with S8 (DAPFAM dtype) | 21.7 | 295 | 423 | 0 | 0 |
| V100 fp16, dr-train, shared with S8 | 104.7 | **61** | **88** | 0 | 0 |
| V100 fp16, dr-train, idle (estimate: shared × 1.68, the idle/shared fp32 ratio; not measured) | about 176 | about 36 | about 52 | 0 | 0 |
| RTX 4090 fp16, Community | pilot | = 23e6 / rate / 3600 | = 33e6 / rate / 3600 | × USD/h | × USD/h |
| A100 SXM fp16, Community | pilot | same | same | same | same |

Reading the table:
- **fp16 vs fp32.** On the V100, fp16 is 4.8× faster and gives practically identical vectors (cosine ≥ 0.999995, identical top-10). The 175-250 V100-h planning figure assumed fp32. With fp16, dr-train alone takes about 61-88 h (shared) or about 36-52 h (idle, estimate) at USD 0.
- **Is RunPod worth it?** Only if its calendar-time saving is worth more than its USD cost. Full encoding on RunPod is not covered by the USD 10 pilot cap; it would need a new budget approval.
- **Method choice for the owner.** Whether the Paper 2 corpus may use fp16 while DAPFAM used fp32 should be pre-declared before encoding. Two inputs for that decision:
  - the parity numbers above;
  - the cross-GPU parity from the pilot: 4090/A100 fp32 vs V100 fp32, and fp16 vs V100 fp32.

## 8. Data rules

- Only public-domain USPTO grant text and the PatEmbed-large weights go to RunPod. The weights are downloaded by the pod from Hugging Face at the pinned revision; CC BY-NC-SA 4.0 model, research use.
- No DAPFAM data, no Paper 1 test data, no qrels.
- No API key in files or logs.
- Results that come back (receipts, parity JSON, vectors of public text) are fine to keep. Commit receipts and JSON only, not `.npy` files.
