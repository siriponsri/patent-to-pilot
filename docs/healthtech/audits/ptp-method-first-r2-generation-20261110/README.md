# SACR one-attempt generation adapter
Inspected existing run_qwen_query_actions.py generation: local_files_only, fp16, CUDA:0, eager attention, nonthinking chat template and greedy generation. The existing MTM yes/no reranker is a different path; do not infer its SDPA configuration applies to generation.

Implemented injected model/tokenizer one-attempt adapter: rendered input-token limit before GPU transfer/model invocation, explicit no sampling/one beam/output cap/EOS IDs, prompt-prefix integrity check, EOS vs token limit vs no EOS/byte limit classification, exact response hash and strict profile/view dispatch. EOS at the exact output cap counts complete; capped unfinished JSON is unusable. No stripping/fence salvage/retry. Context/token/byte limits validated; no model loading occurs in this module.

Private artifact reservation is written before generation. Exclusive destination cannot resume/overwrite. Failure receipt omits exception text and reports model-call count UNKNOWN if the call failed/interrupted; no fabricated token/cost count. Raw generated text belongs in private generation.json only, never Git. A reserved attempt without terminal receipt remains unresolved, not permission to retry.

62 synthetic tests passed in 0.68s, Ruff passed (eight new cases plus 54 regressions). Local torch is absent; tests inject fake torch/tokenizer/model backed by NumPy. This is explicitly not backend/model/GPU verification. Actual tokenizer behavior, model weights/dtype/resource limits, inherited generation settings and failure lifecycle still need runtime validation before any pilot.

No model/GPU job, actual generated text or benchmark data read. Semantic acceptance and actual R1 integrity remain open. Next capture full local weight identity and effective decoder settings, declare bounded synthetic smoke, then real dev work only after curator/environment handoff.
