# SACR generation contract v0 draft

Status: PROMPTS_IMPLEMENTED_NOT_RUN. Neither a pilot declaration nor semantic approval. Actual R1 isolation/parity, complete weight identities and generated-view acceptance remain required.

## Observed local configuration
Read-only CPU metadata inspection at 2026-11-10 00:52:51 UTC found local Qwen3-8B with Qwen3ForCausalLM, hidden size 4096, model max_position_embeddings 40960 and config dtype bfloat16. Tokenizer model_max_length is 131072. Installed torch is 2.8.0+cu128, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6, accelerate 1.6.0. The config's transformers_version 4.51.0 is serialization metadata, not the installed version.

File hashes and observation limits are in ../audits/ptp-method-first-r2-prompts-20261110/model-config-observation.json. Weight shards were not hashed, model/tokenizer was not instantiated, and CUDA capacity was not probed. The model config's lower 40960 limit governs the draft ceiling; tokenizer's 131072 is not evidence that the local model supports that length. Config dtype is not a claim that V100 bfloat16 execution is supported.

## Three fixed prompt artifacts
- prompts/sacr_profile_v0.txt: common source-grounded requirement extraction, at most eight blocks/eight conditions each, strict profile contract.
- prompts/sacr_selective_v0.txt: one selective abstraction proposal from exact allowed source plus validated but fallible profile; relational compact view remains deterministic.
- prompts/sacr_generic_views_v0.txt: up to two ordinary faithful paraphrases without profile access. This is a strong ordinary control, not a deliberately corrupted condition/polarity baseline.

The assembler binds exact UTF-8 source hash, prompt bytes and serialized messages. Source text is one JSON-encoded user-data field, separate from system instructions; this is not proof of immunity to model prompt injection. Generic/profile calls reject extra supplied profiles. Selective calls require structurally valid, nonempty/nonfailed profiles; this does not approve profile semantics. No hidden metadata or source enrichment is accepted by the interface.

## Proposed bounded decoding and accounting
For the initial implementation draft: one common profile call and at most one view-generation call per query/view-family, no retries; greedy decoding, do_sample=false, num_beams=1, enable_thinking=false through the pinned local chat template, batch size one. Validate the chat-template switch on synthetic input before adoption. No temperature sampling or implicit inherited generation defaults. Proposed maximum 8192 rendered input tokens and 4096 generated tokens per call, including prompt/profile overhead. Reject over-limit calls and preserve fallback records; never silently truncate allowed source or a JSON response. Input+output cap 12288 is below the observed model ceiling but is not a memory or speed guarantee.

Use V100-compatible numerical settings only after checking the existing local generation path. Weight shard hashes, exact dtype/loading implementation, tokenizer/chat-template behavior, per-query timeout, total pilot wall/GPU/memory envelope and stop handling still require pre-run freeze. A configured time/token cap is not measured performance. Do not launch by treating this draft as a completed resource plan.

Both factorial view families share one cached profile for their selectors; account for that extraction in each arm requiring it, and show amortized reuse separately. Each family receives one view-generation call with the same input/output caps. Generic produces up to two generated views; invariant-preserving produces one generated view plus one deterministic compact view. These have equal call/view caps, not necessarily equal actual tokens or compute. Report realized costs rather than claiming exact budget equality. Anchor is always retained; duplicate views are logged without replacement generations.

## Remaining output acceptance gate
Require strict response schema, complete JSON, source/profile binding, declared length caps, unchanged anchor, duplicate detection and logging of every failure. Whole-profile failure uses immutable anchor ranking. For individual invalid generated views, discard only that view; do not retry.

The validator must detect loss of explicit protected information and unsupported normalized mechanisms/parameters without treating lexical preservation as semantic proof. Normalization review flags and uncertain removals cannot be silently marked safe. The exact automated rejection and unresolved-review policy is still pending implementation; until fixed and fidelity-audited, this generation contract is not runnable as a scientific method. Manual per-query repair after seeing retrieval results is prohibited. Do not quietly replace SACR with extraction-only or anchor-only behavior and call that a completed test of selective abstraction.

## View-component checkpoint
Strict response parsing, compact construction and conservative lexical screening are now implemented in research/sacr_views.py. Caller supplies byte/character caps; token limits still require tokenizer enforcement. New vocabulary and uncertain profile transformations are REVIEW_REQUIRED, not approved. Compact uses raw conditions and abstains on unresolved profile items. The explicit role-reversal test demonstrates lexical PASS is insufficient. English polarity matching is a limited guard, not language-general logic. Numeric literal inventories can conservatively reject harmless reformatting/repetition. The scientific acceptance/review policy remains open; do not use this component alone as a full SACR run or silently substitute extractive-only behavior.

## One-attempt adapter checkpoint
The existing query-generation path uses local fp16/eager attention, not the reranker's SDPA setting. research/sacr_generation.py now binds one attempted generation to an exclusive private reservation, input/output/context/byte limits and strict complete-response handling. EOS-at-cap is complete; unfinished capped output is not repaired. Exceptions preserve generic failure metadata and unknown call count. Tests use a fake backend because local torch is absent. Actual model loading, weight hashes, effective inherited decoder settings, timeout/peak-memory handling and semantic acceptance are still pre-run gates; no Qwen smoke has run.

## Actual weight/decoder observation checkpoint
The CPU inspection at code acf03860fb5ee30dc5f2dc1c1c4cb484f63a2e91 hashed all five local weight shards, 16,381,516,776 bytes, and matched prior config/tokenizer observations. See ../audits/ptp-method-first-r2-weights-20261110/identity.json and decoder-observation.json. Installed GenerationConfig resolves greedy/one-beam overrides with EOS [151645,151643] and pad 151643; inherited temperature .6/top_k 20/top_p .95 are sampling-only and produced a warning under greedy settings. CPU tokenizer nonthinking template succeeded on one authored 34-token fixture. No weights loaded or generation run; this is not model-source authentication or a GPU capacity result. Runtime must bind these identities before the separately declared synthetic model smoke.
