# Current-head local Qwen patent-candidate run

Recorded: 2026-11-03T18:05:29.479178+00:00 (2026-11-04, Asia/Bangkok)

## Outcome

The current-head local generation branch completed a real guided
`Qwen/Qwen3-8B` run over the frozen rights-cleared patent-candidate pack for
three named devices. All three outputs were schema-valid and were verified on
Windows against the exact pack, exact message hashes, source IDs/locators, and
the frozen classification contract.

This is a reproducible generation and citation-binding result for the three
case studies. It is not a semantic accuracy score, retrieval endpoint, final
holdout, local/API superiority result, user validation result, revenue/ROI
evidence, or publication acceptance result.

## Candidate and private artifacts

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: intentionally dirty; owner/Claude/Luna/research changes preserved.
- Private input pack: `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-local-qwen-patent-pack-20261103-r2/evidence-pack.json`
- Pack SHA-256: `918f615210546b65111cbc683181dc43886ace2267f16c19d62c31175ea6607b`
- Private receipt: `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-local-qwen-patent-run-20261104-r1/generation-receipt-guided.json`
- Receipt SHA-256: `7072197565f26a0b88ae80aeddd08eff3c933f69f6632714fcc296a6713dc6fd`

The pack contains three cases: MitraClip with 35 candidates, Tendyne with 20
candidates, and TriClip with 28 candidates. Each case contains five evidence
rows. Source payloads, evaluator labels, qrels, hidden oracles, raw HTML, and
provider credentials were excluded from the model-visible payload. Unlisted
links remain unjudged.

## Runtime and result

- Host: `dr-train`; approved GPU: `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089` / Tesla V100-SXM2-32GB.
- Model revision: `Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218`.
- Configuration: float16, eager attention, non-thinking, guided JSON with `lm-format-enforcer`, eight CPU threads, `max_new_tokens=512`, `max_findings=4`.
- Run interval: `2026-11-03T17:55:54.959492+00:00` to `2026-11-03T17:58:42.303497+00:00`.
- Model load: `4.2612637099809945` seconds.
- Peak GPU allocated/reserved: `18,452,102,144` / `18,865,979,392` bytes.
- Peak process RSS: `4,891,336,704` bytes.
- Total prompt/output tokens: `7,301` / `1,448`.
- Total per-case generation latency: `162.96131139574572` seconds; mean `54.32043713191524` seconds.
- Provider calls: `0`; paid cost: `USD0.00`.

| Case | Prompt tokens | Output tokens | Latency seconds | Schema |
|---|---:|---:|---:|---|
| HT-DEV-MITRACLIP | 2,397 | 483 | 54.320655 | PASS |
| HT-DEV-TENDYNE | 2,470 | 494 | 55.192556 | PASS |
| HT-DEV-TRICLIP | 2,434 | 471 | 53.448101 | PASS |

## Independent verification

The verifier at `verify_receipt.py` was run against the private Windows pack and
receipt. It passed with no model-output printing and verified:

- pack hash and receipt-to-pack binding;
- exact message hashes for all three cases;
- case IDs, evidence IDs, candidate IDs, source IDs, locators, and allowed classifications;
- schema validity and parse-error absence;
- zero provider calls and zero paid cost.

The runner and payload source hashes match the prior exact-head staging record:

- `run_qwen_generation_evidence_pack.py`: `d3f195e81959db3bf35661b9b0fc3a6593a0ad8a1e7b8a234a47fbeedee63d9c`;
- `generation_payload.py`: `bfdab9abc030eb84908e38b591d0df315a5edac0a3c5dfbcb9747743793e4c93`;
- `local_execution.py`: `25ed4283936885352054c5cd5d10d5f4c78fcf8bbe26762dc7da9ee7a5a35e0d`.

## Failure accounting

Two pre-model failures are retained in `FAILURES.json`:

1. The first launch used remote `/usr/bin/python3`, which lacked `pydantic` and stopped before model import. No model load, GPU compute, provider call, ledger mutation, or paid cost occurred.
2. The next launch pre-created the output path. The runner correctly stopped with `FileExistsError` before model load. No GPU compute, provider call, ledger mutation, or paid cost occurred.

These failures are not converted into zero-cost model attempts and no historical
cost is inferred. The successful run used the existing remote `venv` with the
dependency set bound by the prior exact-head receipt.

## Resource cleanup and boundaries

The input pack and successful output were staged only for remote processing,
then copied to private Windows storage and removed from the remote transient
paths. After completion the approved V100 was idle again, the cooperative lock
was released and remained a zero-byte marker, and the existing `serve_http.py`
PID `1745699` retained its original start time and was not touched.

The canonical E2 API journal was not changed. Paid API remains independently
gated by current scoped credit/limit evidence; this local run does not satisfy
or bypass that gate. Continue to keep local generation and paid API as separate
protocols until a paired paid run is actually admitted.

## Deterministic operational evaluation

The sanitized evaluator
docs/healthtech/audits/ptp-local-qwen-patent-run-20261104/operational-evaluation.json
was run against the same receipt and frozen pack. It found 12/12 exact
source/locator bindings and 12/12 classification-contract matches, with no
errors. The model emitted 12 of 15 available evidence rows, giving an
operational evidence-coverage rate of 80%. All three cases exposed at least
one unresolved item, so unresolved visibility was 3/3. The counts were ten
source facts and two product-level disclosed-link findings.

These are deterministic source-binding and workflow-coverage measures. They do
not establish that a finding is semantically correct, that a retrieved
candidate is a disclosed link, or that the local model is better than an API
model or any retrieval policy.

