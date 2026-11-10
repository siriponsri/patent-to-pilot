# R1 MTM baseline parity declaration

Status: DECLARED_PENDING_ISOLATION_AND_INPUT_PINS; NOT_RUN. This is an integrity comparison, not a new retrieval method or evidence of effectiveness. No protected subset is authorized.

## Fixed scope
Initial scope is the complete frozen MTM P dev cohort, primary main/X plus main/U as a mask diagnostic. Use the exact historical P-dev query bytes, immutable corpus projection preserving passages/order, existing bound vectors, original PatEmbed encoder/prefix/MaxP implementation, depth 200 and batch size 64. No changes to model, queries, eligibility, numeric precision, topk behavior or candidate universe. T/A and sensitivity views require separately recorded extensions; P/main parity does not prove them.

Historical reference files are out/rankings-main-X-P-dev.jsonl and out/rankings-main-U-P-dev.jsonl under the existing MTM deployment root. Curator must verify filenames, independent hashes and relationship to original receipts before release into the isolated evaluator. No wildcard copying of test rankings. Candidate files come only from the bound prospective wrapper. Do not use a candidate output as its own reference.

## Entry gates and pins
Before launch: curator isolation attestation and immutable allowed mounts; complete staged dev metadata/query bundles; no unresolved unexpected missing query; A14 receipt/identity and projection correspondence; exact original and deployed source hashes; model/tokenizer/source versions and available torch/CUDA versions; V100 authorization/live process check; no concurrent writer/job; updated pushed handoffs. Capture launch code SHA and all actual hashes in an immutable run manifest before encoding. This declaration does not replace those pins. Physical isolation cannot be asserted from a flag/hash.

Run only run_mtm_dev_bound.py, main/U-X, P-dev, reused vectors. One declared attempt, no automatic retry. Use a new versioned job/output directory, setsid/nohup and durable status log. The remote job must receive a fresh archive of the pushed revision. Preserve failure logs and partial output. If the reference torch/CUDA environment cannot be established, report it as an unresolved parity limitation; do not silently change precision or numerical implementation.

## Independent ranking bundles
The evaluator accepts two independently pinned bundles, each containing rankings.jsonl copied byte-for-byte from its declared reference/candidate file, and manifest.json with exact keys:

    format: ptp-mtm-dev-rankings-v1
    split: dev
    view: P
    lane: X or U (compare separately)
    corpus_view: main
    sha256: full ranking payload digest
    queries: number of available query-text rows

Each row has exactly query_id and families (ordered unique IDs, at most 200). Manifest hashes are independently reviewed and passed to compare_mtm_dev_rankings.py together with pinned metadata/query manifests. Protected/wrong-view/lane/corpus manifests are rejected before payload access. Unknown IDs, duplicate rows/families, omitted available queries and extra label fields fail closed. No qrels are needed.

## Acceptance fixed before actual results
Require exact ordered list equality for every available dev query in both lanes. Report full cohort, available, predeclared missing and both-empty counts separately. Missing-query ledger entries are not successes; they remain in the full benchmark denominator for later effectiveness evaluation. Do not pass when both outputs omit an available query. Empty lists are permitted and visible, not silently dropped.

Report exact prefix equality at 20/100/200, whole-list equality, order-only differences, membership differences and length differences. All differences at any rank through 200 fail strict parity, even if hit metrics would be unchanged. No tolerance, cherry-picked subset or score-based exception. The comparator returns nonzero for mismatch and writes the aggregate failure receipt without IDs. Score equality is not claimed because historical ranking files do not contain raw scores.

If parity fails, preserve both outputs and diagnose only dev inputs. Potential numerical cutoff ties, source-line endings, query-prefix differences, order/owner mapping, eligibility masks and environment differences are hypotheses, not excuses to relabel failure. A repair is a new declared version/attempt; never overwrite or automatically retry. No SACR outcome-driven tuning follows a failed integrity gate.

## Separate A03 and remaining limits
Run exact-mask dev gold eligibility with the staged dev evaluator and projected corpus. Report ineligible/indeterminate incidence and keep the frozen denominator; do not silently repair/drop labels. Matching rankings does not prove eligible gold, historical tokenizer attestation, semantic fidelity, effectiveness or native DAPFAM real-data parity. R1 completion requires the relevant independent gates, not just this receipt.
