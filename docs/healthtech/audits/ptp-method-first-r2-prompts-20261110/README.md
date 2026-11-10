# SACR prompt contract and actual local configuration
Read-only metadata inspection completed successfully without loading models or reading benchmark inputs. model-config-observation.json records exact small-file hashes, selected config fields and installed distribution versions. Model config ceiling 40960 differs from tokenizer 131072; use lower ceiling pending actual capacity checks. No weight-shard or GPU/runtime validation claimed.

Three authored prompts and deterministic source/hash-bound message assembler are implemented. Profile extraction and selective abstraction are distinct from generic paraphrase control; generic cannot receive a requirement profile. JSON user-data separation is not an adversarial model safety guarantee.

39 targeted tests passed in 0.53s, Ruff passed (five prompt cases plus 34 profile/selector regressions). Synthetic only; no generation. Draft contract records capped-call comparison and actual-token accounting, unresolved dtype/resource/output-validation gates. Exact weight identities and generated-view acceptance are still pending. This package does not satisfy R1 or authorize a pilot.

Next implement output acceptance/compact view construction, inspect existing local generation implementation and complete resource/prompt freeze after appropriate checks. Curator/environment response remains pending.
