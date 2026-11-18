# RunPod pilot for P1-BridgeRet (2026-11-18, owner-approved, cap USD 10)

Pod `3uakq34o52m3se` (ptp-bridgeret-pilot-v1): NVIDIA A40 48 GB, Secure, EU-SE-1, USD 0.59/h (list-gpu-types read), image
`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (torch 2.8.0+cu128). Created 14:48:32 UTC, deleted ~15:06 UTC
(delete-pod 204; list-pods empty afterwards). Expected cost about 0.3 h x 0.59 = USD 0.18; billing read pending (lag).
Billing before: USD 0 over the last 30 days (list-billing).

Data sent: none. The pod downloaded Arctic @95c27414 from Hugging Face (model.safetensors sha256 3d80d472..., equal to
dr-train) and the pilot script (sha256 1491add6...). Inputs are random token ids drawn from the measured TRAIN token-length
histogram (Arctic tokenizer, 2,000 TRAIN queries with "query: ", 16,000 TRAIN passages; 9.1 % / 17.6 % hit the 512 cap).
No DEV/TEST/DAPFAM data left dr-train. Timing only; no retrieval quality.

## Encode (passages/s, max_len 512)
| Attention | fp16 bs64 / 128 / 256 | fp32 bs64 / 128 / 256 | 1M passages, best fp16 |
|---|---|---|---|
| default (sdpa/eager) | 441.8 / 455.8 / 457.0 | 108.8 / 107.8 / 107.3 | 0.61 h |
| xformers + unpad | 623.0 / 664.7 / 669.4 | 153.5 / 154.2 / 153.9 | 0.42 h |

## Full fine-tuning step (fp32 weights, bf16 autocast, AdamW, 1 query + 1 positive + 7 negatives, 512 tokens)
| Config | bq16 | bq32 | bq64 | bq128 |
|---|---|---|---|---|
| no gradient checkpointing (default / xformers no-unpad) | OOM | OOM | OOM | OOM |
| gradient checkpointing, default attention | 1.667 s, 10.2 GB, 11.9 h/epoch | 3.244 s, 16.8 GB, 11.5 h | 6.431 s, 30.2 GB, 11.4 h | OOM |
| gradient checkpointing, xformers no-unpad | 1.740 s, 10.9 GB, 12.4 h | (stopped) | | |
| xformers + unpad | CUDA illegal memory access in backward (first config) | | | |
Epoch = 409,866 TRAIN pairs with text.

## Planning consequence (not a decision)
- Full FT with 7 x 512-token negatives costs about 11.5 A40-hours (about USD 6.8 at 0.59/h) per epoch.
- The negative count dominates (8 documents per query). Options for the owner/pre-declaration amendment: fewer mined
  negatives per query (e.g. 3), recipe selection on the 30k-task subset already declared for the 2x2 diagnostic, then one
  full-TRAIN run of S* only. Encoding Challenge-1M is cheap (< 1 h on an A40, fp16).
