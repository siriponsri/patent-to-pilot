# Independent embedding/remote-compute review

Inspected revision: `db0798276e3158b04131b4e910abc0a11511e94c` (read-only). Scope: current local embedding/retrieval implementation and project-owned execution references. No SSH connection, model inference, provider calls, credentials, `.env`, private SSH configuration, GPU inventory, implementation changes or repository writes were performed.

## Confirmed source findings

1. **Remote embedding export/import is not implemented in the inspected paths.** Tracked Git search of `src`, `scripts`, `configs`, and `docs/healthtech` found no `dr-train`, `scp`, `rsync`, `CUDA_VISIBLE_DEVICES`, `faiss`, `memmap`, `np.save` or embedding/vector shard matches. This is a bounded search, not a claim that every project file was read. No project-owned host/user/job/GPU allocation contract was found. Global SSH/key/session files were deliberately not inspected.
2. `src/patent_to_pilot/evaluation/healthtech/local_retrieval.py:223` creates an ONNX session with `CPUExecutionProvider`; `:227` uses the native tokenizer with default `max_length=256`; `:231`–`:240` encode all passed texts, attention-mask mean-pool token outputs and L2-normalize. Existing local model config declares 384 hidden dimensions and mean pooling. Runtime output dtype was not inspected through inference.
3. `SharedRetriever` at `local_retrieval.py:287`–`:294` creates a BM25 index and calls `encoder.encode([patent.text for patent in patents])` for the **entire corpus in one call**. `:297` encodes each query locally; `:298` performs a NumPy matrix-vector product; deterministic tie-breaking is by document ID at `:301`. There is no persisted vector artifact, validated ID mapping, shard checkpoint or injected precomputed-vector path here.
4. `scripts/healthtech/run_real_baselines.py:54` pins the local `onnx/model_quint8_avx2.onnx` path. Its main construction at `:630`–`:632` creates encoder, reranker and retriever locally before looping through methods/queries. The B4 and bounded-controller runners instantiate the same stack (`run_b4_controller.py:167`–`:172`, `run_bounded_controller.py:175`–`:180`). These paths do not consume remote vectors.
5. The current development representation is source-order text with tokenizer truncation, not a long-patent chunked representation. `configs/healthtech/g1_g2_public_cohort_protocol.json:28` declares title+abstract+claims truncated at 256 tokens. There is no claim-aware chunking/offset aggregation in the inspected embedding code. This is an explicit representation limit, not proof of semantic-label failure.
6. DAPFAM currently has a separate BM25 pipeline: `scripts/healthtech/run_dapfam_bm25.py:146`–`:170` reads **opaque `relevant_id` / `query_id` plus `title_en + abstract_en`**, preserving row order; `run()` at `:270` exports parquet inputs to temporary TSV, validates ID coverage, ranks by BM25 and evaluates qrels. It does not adapt those IDs into `PatentRecord`, use dense embeddings or share a vector index. Do not silently treat DAPFAM IDs as canonical US/EP patent publication IDs without an explicit verified mapping.
7. A new dense pipeline can compute/index/export vectors without semantic labels. Labels are needed for retrieval-quality evaluation, not for deterministic encoding, row-integrity/numeric consistency tests, corpus import or product nearest-neighbor retrieval. DAPFAM citation/family qrels can evaluate its declared component task; they do not establish semantic device–patent gold for HT-T1. Missing M23/M25 semantic sources must not globally block a remote compute adapter.
8. **The product dossier backend is also separate from the true dense evaluator stack.** `healthtech/engine.py:106` creates SQLite `FTSIndex`, `:130` performs lexical search, and `:136` calls `policies.fixed_hybrid_rerank` only for HT-B1. `healthtech/policies.py:21` describes that helper explicitly as a lexical/token-overlap approximation, not dense/reranker reproduction. This is transparently labelled current behavior, not a newly proven misrepresentation. The next implementation must expose returned vectors to a shared/injected retrieval seam used by both evaluation and dossier composition; adding a standalone evaluation script alone would not satisfy local application use.

## Verified local model artifacts (byte hashing only)

`data/manifests/healthtech/ht-models-20261028.json` declares:

| Model | Immutable revision | Artifact | Bytes | SHA256 match |
|---|---|---|---:|---|
| sentence-transformers/all-MiniLM-L6-v2 | 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 | ONNX quint8 AVX2 | 23,046,789 | yes |
| same | same | tokenizer.json | 466,247 | yes |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | 233902d25c440f23af6f7d6e94d2946bac0bee0a | ONNX quint8 AVX2 | 23,200,716 | yes |
| same | same | tokenizer.json | 711,396 | yes |

The manifest records Apache-2.0 model-card declarations and local-only weights. These four file hashes were independently recomputed; model quality, remote CUDA support, GPU memory and exact ONNX runtime tensor metadata were NOT_RUN. The encoder config inspected locally has `hidden_size=384`; `1_Pooling/config.json` has mean-token pooling enabled, CLS/max disabled.

For 45,336 corpus vectors at dimension384, float32 final vectors occupy **69,636,096 bytes (66.4MiB)**; 1,247 query vectors occupy **1,915,392 bytes**. In contrast, a single `[45336,256,384]` float32 token-output array is **17,826,840,576 bytes (16.6GiB)** before model/intermediate/input overhead. This is arithmetic from shapes, not a measured allocation/OOM. It explains why batching matters more than moving only the final matrix.

## Concrete implementation work for the next Goal

### A. Freeze a runtime-only encoding bundle on Windows

- Export corpus/query text with stable dataset-scoped opaque IDs and source-text hashes; deterministic order; no qrels, gold, family labels, semantic adjudications, split answers or private/patient content sent to the encoder.
- Include `dataset_revision`, corpus/query manifest hashes, exact text view/normalization, source IDs, parser version and intended-use/controlled remote-transfer decision. Local acquisition rights do not automatically prove remote-processing or public vector-redistribution rights.
- For DAPFAM first retain title+abstract unchanged for a fair BM25/dense comparison. Add a separate chunked long-patent experiment only as a new declared representation; avoid upgrading a method and representation simultaneously while claiming adaptation caused the gain.

### B. Build the resumable remote encoder job

- Freeze model ID/revision, tokenizer files/hash, max sequence length, special-token/query/document prefixes, truncation/chunking, pooling, normalization, dimension, numeric backend, inference dtype and exported dtype. A GPU float16/PyTorch version is not numerically identical to the existing quint8 CPU ONNX path merely because the model name matches.
- Start with the existing 384-dimensional checkpoint as an integration baseline. Use a small GPU canary before full encoding. If changing to a stronger embedding model, keep its vectors/config/cache namespace separate and evaluate as a new model condition; do not silently replace old frozen baseline vectors.
- Batch by observed token/GPU memory limits, with a small initial batch (e.g.16–32), explicit finite CPU/GPU/wall/disk budgets, out-of-memory reduction and durable checkpoints. Do not pass all 45K documents to one ONNX inference call.
- Produce independent fixed-row vector shards (e.g. up to5000 rows; about7.7MB per384-f32 shard) plus explicit row-map files. Write `.partial`, validate, fsync/atomic rename; commit shard manifest only after hash/count checks. Resume completed matching shards; reject changed source/model/order/config. Never fabricate zero vectors or skip failed rows silently.
- Suggested portable format: little-endian float32 `.npy` with `allow_pickle=False`, dataset-scoped ordered `ids.jsonl`, per-row text/config hash and optional chunk map. Manifest includes shape/dtype/dimension/norm policy, ID order hash, per-shard start/end/count/byte SHA256 and parent input/model hashes. Every chunk has parent document ID and token/character offsets, chunking algorithm/overlap/hash; document aggregation rule is declared.

### C. Transfer vectors back and import locally

- Use the existing approved SSH identity/host verification; never disable host-key checking, copy private keys, print tokens, change security/ACL, open inference ports or touch Podi/shared services. Transfer only explicitly named input/vector artifacts under an audit-owned remote job directory.
- Secure SSH/SCP/SFTP transfer can retry whole small shards; do not claim plain SCP supports arbitrary byte-range resume. Verify byte SHA256 after arrival before atomic local promotion. No public Git upload of restricted raw text or derived vectors unless the applicable rights permit it.
- Add a validated precomputed-vector provider/import seam to `SharedRetriever` or a task-neutral vector index abstraction. Validate dataset/config hash, exact ID set/order, unique IDs, shape/dimension/dtype, finite values, nonzero norms, no missing/extra/duplicate rows and shard checksums before search.
- Connect that retrieval abstraction to the dossier backend's currently lexical `run_dossier` path with an explicit named policy/config, keeping lexical defaults, budgets, rights, source IDs, user edits and candidate/disclosure distinctions intact. Do not make benchmark labels visible to the product to manufacture candidate links.
- At this scale use exact local NumPy/memmap cosine/dot retrieval first with deterministic ID tie handling; ANN/FAISS is optional only when scale warrants it and must measure recall versus exact search. Keep BM25 and reranker components available; cross-encoder query–document scores cannot be replaced by a document-only embedding vector.
- Frozen query vectors work only for exactly matching query text/config hashes. For arbitrary new local queries, retain a matching local CPU query encoder or explicitly declare a new remote query-encoding dependency; never compare MiniLM query vectors with another model's corpus vectors.

### D. Gold-free engineering acceptance, then task-specific evaluation

- Local fixture round-trip + deliberately permuted/duplicate/missing IDs and corrupted shard/header/hash/config must reject. Interrupted transfer/remote job resume must not produce duplicate/skipped rows or mix model versions.
- Tiny shared-text sample encoded on local reference and remote chosen backend: compare dimension, finite norms, cosine/distance deviations and tie-aware topK; freeze numeric tolerances appropriate to same-float versus quantized/f16 backend before the full run. Do not demand bit identity between different quantization/backends or silently label them equivalent.
- Full declared corpus/query row counts, one-to-one mapping and checksums; sample numeric consistency; exact local index loaded from returned vectors and produces reproducible rankings without SSH at query time for frozen-query evaluation.
- Run BM25, dense-only, lexical+dense fusion, then common reranker where lawful/practical; same IDs/text views/K and failure denominator. Existing DAPFAM qrels support only the DAPFAM citation/family task. Product association/claim-level semantic studies still need their own authorized source/gold/holdout.

## Exact pending authority/readiness

No remote check was made. Unknown: dr-train host alias/user/job directory, available GPU/device(s), scheduler or reservation ownership, Podi/shared-service occupancy, disk/RAM/dependency/model availability, approved time/resource quota and source-specific transfer rights. Owner intent clearly selects remote embeddings → local vectors; it is not a statement that GPU0 is free or that a shared service may be stopped.

Next implementation can complete exporter/importer/manifest/fixture tests locally while preparing a single concrete remote job/resource request. Before compute, perform only authorized read-only remote inventory using existing identity, identify a free/approved GPU allocation and finite job budget, and avoid kill/reconfigure/install operations on shared services. If allocation/transfer permission is missing, pause only the remote compute branch; do not label all semantic/retrieval work BLOCKED.

## Audit limits

No exhaustive traversal of all historical receipts; no inference or performance timing; no SSH/GPU inventory; no remote config/key inspection; no licensing conclusion beyond recorded local manifest declarations. Historical evidence directories with denied ACL access were not opened or bypassed. The tracked-code search and all files named above were the reviewed boundary.
