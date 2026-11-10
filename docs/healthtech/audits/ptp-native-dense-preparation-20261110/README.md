# Native DAPFAM dense preparation

Status: IMPLEMENTED_COMPONENT / BASELINE_NOT_RUN. Parent sole repository writer.

Inspection of historical `run_dapfam_dense_pool.py` found `torch.topk` selected a subset before lexical tie sorting. This cannot guarantee lexical membership when equal family scores cross the cutoff. No evidence that a historical scientific result changed is asserted; old runner/results remain intact.

New `research/native_dense_ranking.py` computes full-universe MaxP and lexicographic sorting before truncation. It rejects nonfinite scores, invalid owners, duplicate IDs and missing-family passages. Synthetic evidence:9 ranking tests plus13 native evaluator tests,22 total PASS. Boundary-tie permutation and hand/reference negative-score cases covered. No GPU/model calls or benchmark scoring.

Remote read-only inspection located existing PatEmbed-large at the approved research-product job's models/patembed-large directory. GPU compute-process query was empty at inspection; launch admission must recheck. Only filenames were inspected, no mixed query/label contents read. Existing vector hash was verified in the previous preparation checkpoint; model config/tokenizer/weights and as-run passage helper binding still require fresh manifest verification.

Next: implement mandatory-vector-reuse native runner, bind exact historical corpus/passages/model and staged TA query hashes, freeze query prefix/normalization and metrics before outcomes, prepare isolated runtime/evaluator mounts with supervisor and cumulative resource admission. No encoding of corpus or baseline launch authorized by a component test alone. Existing owner bounded baseline authority remains applicable after gates.
