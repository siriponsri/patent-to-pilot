# L1DEV | Exploratory LLM arm

## Protocol recorded before inference

Rebuild the frozen development validation partitions from `42af82df`. The
frozen readers project eligible historical outcome evidence before JSON decoding.
Use outcome evidence locally for cohort eligibility and evaluation. Export the
active-moiety ingredient name, cutoff and horizon. Resolve identified components
with the pinned GSRS name, then preserve the canonical fallback for other
components. Require an exact input allowlist, unique forecast identities and a
verified SHA-256. The GPU receives the label-free rows and the L1 configuration.
[FREEZE](FREEZE.md) · [E4b](E4b.md)

Keep the E4b prompt, parser, model, image, fp16 and greedy decoding. Use fixed
left-padded batches of eight for throughput. Start with the first 200 forecasts
in horizon, cutoff and active-moiety key order. Stop if fewer than 180 pass the
parser. Rank with `p_entry` even on schema-valid abstentions. An invalid output
abstains and ties below all valid probabilities. Use the full frozen roster and
report validity and abstentions. No partial-cohort score.

Use criteria v3 with the same annual 20% review budget and expected boundary
ties. Compute pooled grouped AP and 2,000 paired whole-drug draws against B1 and
M3, with a common seed of 20261127 per horizon. Verify replayed comparator points
and percentile intervals against FREEZE. L1 is secondary exploratory.
[Criteria v3](../PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints)

## Execution and artifacts

**PASS.** L1 generated all 3,244 development forecasts on one L4. All 200
gate responses passed schema validation. The full run yielded 3,244 valid
responses (100%) and 763 schema-valid abstentions (23.52%). Inference took
1,571.88 seconds at 2.064 rows/s. Model load took 14.87 seconds after the
staged snapshot passed all 13 size and digest checks. Peak allocated VRAM
was 14.63 GiB. The sealed test remained closed.

Private artifacts are in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/llm_arm/`.
The remote and local digests matched for the raw output, summary, log and
exit record. The original forecast file was verified before transfer and again
before loading the model. Repository JSON digests use LF bytes.

| Artifact | SHA-256 |
| --- | --- |
| Forecast inputs | `b4fcbb06eac119cb1433c9b7855e0f38160313d1c74da937d1b41b2cf9a57837` |
| Raw model outputs | `2b0d5d04ed00a6040ff49efeae9bcd9145803495e1f0c47c1e2bc94fb2f80741` |
| Run summary | `e477ae22651971695b2f2a1f55ff49d146989844e1d38d775e8edc6ac82c3d30` |
| Run log | `8505eaf56e95c5a7b981f361b92f067b406885e58c1f8011bb9e9624b22d4f6a` |
| Exit record | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| [L1 frozen configuration](../../../loe-bench/data/L1_FROZEN_CONFIG.json) | `e5e5ade357ee5faf83efa0ce24ad25feddacdfcbf49ddd817a6b10e494a9ef16` |
| [Development results](../../../loe-bench/data/L1DEV_results.json) | `c7f85797cda4a16026598ed5f864a4b11aadef0114f9928e14526f425e446463` |

## RunPod ledger and cleanup

The live quote and charged pod rate were both USD 0.69/h. The only pod
created, `8874020m8k6z61`, started at 15:26:02 UTC and returned HTTP 404
after deletion at 15:59:02 UTC on 27 November 2026. The elapsed upper
estimate was 0.551 GPU-hours and USD 0.383 including a disk and retained
storage allowance. This fits the USD 4 and four GPU-hour task caps. The
account-wide prepaid balance fell from USD 27.383895 to USD 27.032918.
The per-pod billing endpoint had no posted row at read-back. Volume
`8n6rnzljwg` remained present at 30 GB in `US-MO-2`. Its storage allowance
remains USD 2.10/month. Estimated cumulative arm spend through closeout was
USD 0.535 including E4b and accrued volume storage. [Ledger](../../../loe-bench/data/L1DEV_runpod_ledger.json)

## Development results

**DEVELOPMENT_ONLY.** L1 ranked fewer event rows into the annual review queue
than both comparators at both horizons. All 2,000 paired whole-drug draws
were defined per horizon. B1 and M3 point estimates and interval bounds
matched the frozen development report within 1e-12 for all three metrics.
The results JSON includes the queue audit and paired intervals for precision
and AP in addition to recall.

| Horizon | Arm | Recall at 20% | Queue precision | Grouped AP |
| ---: | --- | ---: | ---: | ---: |
| 12 months | L1 | 34.92% | 7.31% | .06181 |
| 12 months | B1 | 48.11% | 10.07% | .09189 |
| 12 months | M3 | 61.11% | 12.79% | .18860 |
| 24 months | L1 | 28.59% | 12.10% | .11646 |
| 24 months | B1 | 39.65% | 16.78% | .17288 |
| 24 months | M3 | 49.45% | 20.93% | .22189 |

| Horizon | L1 versus | Paired recall difference, percentage points (95% CI) |
| ---: | --- | ---: |
| 12 months | B1 | −13.19 (−24.45 to −2.05) |
| 12 months | M3 | −26.19 (−34.94 to −15.32) |
| 24 months | B1 | −11.06 (−21.09 to −1.33) |
| 24 months | M3 | −20.86 (−32.09 to −8.91) |

The 12-month roster had 2,161 rows, 90 events and 430 review slots. The
24-month roster had 1,083 rows, 91 events and 215 slots. L1 emitted 552
abstentions at 12 months and 211 at 24 months. All other L1 actions were
`PREDICT_ENTRY`. The ranking used the probabilities for all rows.

## Verification

- **PASS.** `python -m unittest discover -s loe_bench/tests -t .` ran 174 tests from `loe-bench/`.
- The repository `python -m pytest --tb=short -q -p no:cacheprovider` returned exit 1 with only the eight permitted pre-existing SACR r2/r3 supervisor budget failures.
- A hand-checked fixture rejected label keys and a sealed cutoff and verified fractional queue ties and grouped AP. The live pre-upload guard checked every forecast row.

## Failures and limitations

- Transformers reported unused temperature, top-p and top-k generation options under greedy decoding. The lock uses `do_sample=False` and one beam. The unittest run emitted existing Purple Book unclosed-file warnings.
- The validity gate covered the first 200 ordered 12-month rows. Schema validity measures format. L1 used ingredient identity, cutoff and horizon. The model could have learned outcomes that post-date the forecast cutoff during pretraining. The retrospective scores cannot exclude that exposure.
- Batch size eight is fixed for this arm. Cross-hardware output reproducibility was outside this card.

## Next action

The main planner reviews L1DEV and decides how to describe this secondary
exploratory arm in the preregistration. Test authorization remains with the
owner.
