# Native DAPFAM dense preparation

Current status: NATIVE_BASELINE_DEV_MEASURED. Parent sole repository writer. Earlier NOT_RUN sections below are historical preparation records.

## Actual native baseline and isolated evaluation

One query-only GPU run completed exit0 in40.455s supervisor time (5.829s query encoding,9.985s ranking); sampled cgroup memory peak1,960,681,472bytes.474queries,45,336families,188,944existing passages,zero corpus encode calls. Runtime model/input/output hashes verified. GPU conservative cumulative charge182.3919865s including prior failed SYN003; no ledger reset. Test remains closed.

| Partition | Eligible queries | nDCG10 | nDCG100 | Recall100 | Recall200 |
|---|---:|---:|---:|---:|---:|
| ALL |474|.17239|.20893|.25222|.34262|
| IN |450|.20691|.27972|.39413|.51370|
| OUT |349|.02328|.04490|.09732|.14772|

All474 explicit top200 rankings verified,0missing/empty eligible rankings. Ideal ranking uses all known partition positives; full candidate corpus retained. Native TA query differs from historical claims-inclusive R2; these are not a reproduction of its scores. Published papers also use different cohorts/models/fields/cutoffs; no superiority or direct published replication claim.

Evaluator v1 FAILED before input processing: package __init__ transitively imported pydantic absent from bare image.0.700525s CPU-only, preserved in evaluator-terminal-v1.json. Diagnosed packaging-only correction mounted the existing dependencies read-only in a fresh v2 job; no installs or baseline rerun. V2 completed7.977811s,CPU2/memory4GiB/noGPU/no network,no model/test mounts; evaluator-isolation-v2.json records readback. Total evaluator attempt wall8.678336s.20 targeted evaluator/native fixture tests passed before execution.

Aggregate source `dev-metrics-v1.json` SHA256 `6ebffc7f48c821c1b1fe2236243a91526f1ee3b9eee6d6d98ae29932b2f726ec` verified against evaluator stdout. Private per-query outputs remain only in remote evaluator v2 `out/attempt/private-per-query.json`; their digest is in the aggregate receipt. No query IDs/labels/text published. Runtime and evaluator containers both terminal; no live jobs.

Next: SACR source-order repair/declaration and single authorized smoke; durable solo fidelity ledger/screening; predeclared S/G sample/card allocation and bounded feasibility. Baseline alone does not pass those gates or establish benefit. Preserve B0 configuration rather than tuning it to paper scores.

## Native runner implementation checkpoint

`scripts/healthtech/run_dapfam_native_baseline.py` now requires pinned runtime manifest/corpus/native TA queries, existing vector hash and model weights/config/tokenizer hashes. No corpus encode branch; only474 TA queries encoded with the retrieval_OUT prefix, exact newline body preserved, batch32/fp32. Full-family deterministic MaxP, exclusive destination, offline loading and private query-vector output. Completion receipt written last; partial outputs are retained on failure. Existing shared GPU lock retained. Actual external supervisor/mount/resource admission still pending; do not invoke directly on host.

24 targeted tests PASS: native runner hash/exclusive-output guards, global tie ranking, native evaluator. CLI help PASS without model allocation. These do not prove actual runtime execution or numerical parity on GPU. Metric manifest freeze and evaluator integration remain pending.

Historical as-run runner recovered from `code/scripts/healthtech/run_dapfam_dense_pool.first-run.py`: SHA256 `559f52e2dacf657a28d3a474dd995cd73f477497af1ce3efb9a77d7515b1121e`, matches stage0 receipt. Historical acquisition helper SHA256 `f99e1e292e2eddb3f008e2f952edd9bfc76537aa129b67fec2976882846ea977`. Current `dense_passages` AST equals historical `arm03_passages` after explicit function/ARM03-to-DENSE constant renaming and removal of docstring; canonical AST SHA256 `ec581e78854105f282118977ea846b98fa7fdbec1cc46fd34c5c98788fd291df`. Constants inspected:384/64 and identical document prefix. `_nfkc_whitespace` exact AST match. MeanPoolEncoder changes are explicit device argument/default cuda and replacement of hardcoded cuda with that variable; pooling/normalization/tokenization logic unchanged. New runner passes cuda explicitly. No claim of byte-identical current encoder source.

Read-only lookup incidents: initial runner path did not exist (actual filename has `.first-run`); initial direct AST-name lookup failed because helper was renamed. Follow-up located and compared actual files, with no benchmark rerun. A local rg expression failed shell quoting and was corrected. Model configuration/tokenizer hashes observed and pinned; weight hash remains historically pinned and must be freshly checked at runtime. No protected data read, corpus re-encoding or new model calls.

Inspection of historical `run_dapfam_dense_pool.py` found `torch.topk` selected a subset before lexical tie sorting. This cannot guarantee lexical membership when equal family scores cross the cutoff. No evidence that a historical scientific result changed is asserted; old runner/results remain intact.

New `research/native_dense_ranking.py` computes full-universe MaxP and lexicographic sorting before truncation. It rejects nonfinite scores, invalid owners, duplicate IDs and missing-family passages. Synthetic evidence:9 ranking tests plus13 native evaluator tests,22 total PASS. Boundary-tie permutation and hand/reference negative-score cases covered. No GPU/model calls or benchmark scoring.

Remote read-only inspection located existing PatEmbed-large at the approved research-product job's models/patembed-large directory. GPU compute-process query was empty at inspection; launch admission must recheck. Only filenames were inspected, no mixed query/label contents read. Existing vector hash was verified in the previous preparation checkpoint; model config/tokenizer/weights and as-run passage helper binding still require fresh manifest verification.

Next: implement mandatory-vector-reuse native runner, bind exact historical corpus/passages/model and staged TA query hashes, freeze query prefix/normalization and metrics before outcomes, prepare isolated runtime/evaluator mounts with supervisor and cumulative resource admission. No encoding of corpus or baseline launch authorized by a component test alone. Existing owner bounded baseline authority remains applicable after gates.
