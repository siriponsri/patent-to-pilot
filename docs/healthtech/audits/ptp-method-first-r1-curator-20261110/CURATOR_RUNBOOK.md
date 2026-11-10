# Curator handoff: MTM dev isolation and asset preparation

Status: REVIEWABLE PROCEDURE; REAL EXECUTION NOT_RUN. This is for an owner-designated curator, not an instruction for the development agent to parse mixed protected metadata.

## Operational decision
Designate a curator/operator and an isolated development execution environment. A different folder under the same unrestricted account is not isolation. Do not change existing ACLs, hooks or global settings. If no isolated environment is available, hold actual data work and continue specification work. No protected evaluation is authorized.

The curator processes the mixed source in their own authorized environment. Do not send its rows, test IDs/targets or test rankings to the agent. Never publish raw corpus/query/label material to Git. Staging uses CPU only.

## Reviewed source and code
Use a fresh archive of the pushed commit containing this procedure, recording its full SHA. Preserve frozen source and archived line endings. The original A14 report is docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/vector-identity.json; its reviewed SHA256 is recorded in this package's verification.json. Preparation verifies this complete report and extracts its bare identity object. If source hashes differ because of archive/newline changes, preserve and investigate the failure; do not change expected hashes merely to pass.

## Curator commands
Linux source paths below come from the existing deployment and tracked launcher. Set CODE to the absolute extracted pushed-code directory and REPORT_SHA to the independently reviewed digest from verification.json. Destinations must be new. These commands are not to be executed in a development-agent session.

```bash
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
STAGE=/home/chaw/patent-to-pilot-jobs/mtm-curator-staging-20261110-v1
REPORT=$CODE/docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/vector-identity.json

"$PY" "$CODE/scripts/healthtech/stage_mtm_metadata.py" \
  --source "$J/inputs/queries-meta.jsonl" \
  --runtime-root "$STAGE/runtime" \
  --dev-eval-root "$STAGE/dev-evaluation" \
  --protected-root "$STAGE/protected" --trusted-curator

"$PY" "$CODE/scripts/healthtech/prepare_mtm_dev_assets.py" \
  --source-corpus "$J/inputs/corpus.jsonl" \
  --dev-queries "$J/inputs/queries-P-dev.jsonl" \
  --metadata-root "$STAGE/runtime/dev" \
  --identity-report "$REPORT" --identity-report-sha256 "$REPORT_SHA" \
  --view P --expected-missing-count 0 \
  --output-root "$STAGE/assets-P" --trusted-curator
```

Zero missing queries is the initial staging expectation. If source evidence establishes missing P queries, preserve the failed attempt and record the reason/count before separately versioned preparation. Do not regenerate queries, silently lower the denominator, tune prompts or overwrite staging. Missing IDs stay private in the query manifest.

Both commands print counts/hashes/status only. Sources remain untouched. Preparation writes its completion receipt last; incomplete output is unusable. Acknowledgment flags and receipts do not establish isolation.

## Transfer and mount contract
Transfer only these inputs into the designated isolated environment with immutable read-only mounts:
- runtime/dev (metadata and manifest).
- assets-P (projected corpus, exact dev queries, identity and receipts).
- Existing passage-vectors-f32.npy, pinned model directory and pushed code.
- Dev evaluation bundle only into a separate evaluator process/environment, never retrieval runtime.
- Historical P-dev main/U-X rankings only into the evaluator for parity comparison.

Exclude mixed metadata, runtime/test, protected output, original role-bearing corpus, test rankings and broader job-root mounts. Retain originals with the curator; do not delete or move sole-copy evidence. Mounting the whole original job root read-only still exposes protected inputs and is insufficient.

The curator sends only: code SHA; hash/count-only asset-receipt.json; metadata/dev-evaluator manifest and archived runner-source digests; isolated-environment description and allowlisted mounts; confirmation that protected sources are unavailable to the development identity and inputs immutable; destination paths and confirmation of no conflicting writer/job. Do not send credentials or labels.

## After handoff
The development agent verifies allowed paths/receipts without probing protected files, predeclares baseline parity, rechecks V100 authorization and live jobs, and checkpoints both handoffs. A03 uses audit_mtm_dev_eligibility.py with runtime/dev, dev-evaluation and projected corpus. The baseline uses run_mtm_dev_bound.py with independent hashes and existing vectors. Launch with setsid/nohup, durable logs, one job and a fresh pushed archive.

No test execution/scoring, training, re-encoding or new pulls. Actual parity must compare complete dev population and ranking order at declared depths. Fixture PASS and successful runtime exit are not parity evidence. Main-only parity does not validate sensitivity views or real DAPFAM replication.
