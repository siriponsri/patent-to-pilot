# P1-BridgeRet pre-declaration amendment A1 (PROPOSED, not applied; owner decision)

Reason: the RunPod pilot (A40, `paper1-bridgeret/runpod-pilot/RESULT.md`) measured full fine-tuning with 1 positive + 7 mined
negatives x 512 tokens at about 11.5 A40-hours per epoch (about USD 6.8). The pre-declaration fixes "1 epoch over TRAIN"
but not the number of mined negatives k or where the S1-S4 grid is trained. Running the whole grid at full scale would cost
about USD 70 (about 10 configurations), the whole GPU line. No P1-BridgeRet fine-tuning or DEV number exists, so this is a
pre-result amendment.

Proposed changes (statistical impact: none on the confirmatory family; changes the cost and the recipe-search scale):
1. k = 3 mined negatives per query (4 documents per query plus in-batch). Expected about half the step cost
   (about 6 A40-h, USD 3.5 per full epoch; to be confirmed on the first run).
2. Recipe grid (S1-S4, tau, w_OUT) trained on the same salted-hash 30k-task TRAIN subset already declared for the 2x2
   diagnostic (about 0.4 A40-h per configuration); selection on P1-DEV OUT Recall@200 exactly as frozen.
3. S* is then retrained once on full TRAIN with the selected configuration; this full-TRAIN checkpoint is the one frozen
   for TEST. If the full-TRAIN model is worse on P1-DEV than its 30k version, the better of the two (by the same rule) is
   frozen, and this is reported.
4. Hard-negative mining pool from Z-Arctic over Challenge-1M (dense ranks 20-200) plus BM25 top-100, with the frozen
   multi-positive guards.
5. GPU: RunPod A40 Secure (USD 0.59/h at the 18 Nov read) or the dr-train V100 when it is free; fp32 master weights with
   bf16 autocast on Ampere, fp16 autocast on V100, stated per run.

Cost envelope requested (lane B in the light-approval protocol): **P1 fine-tuning up to USD 20** of the USD 75 GPU line
(grid about USD 3-5, S* full run about USD 4-7, 2x2 diagnostic with 3 seeds about USD 3-5, margin for one rerun).
