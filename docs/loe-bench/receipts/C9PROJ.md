# C9PROJ development projection and roster

## Main-planner decision

> Unlinked outcome records. ANDA records that cannot be attributed to any active-moiety group (11 found by C9RUN2) are excluded from labels and listed in the manifest, exactly as FREEZE and C3 treated unattributable records (e.g., C3: 'Fourteen had no admissible group and were excluded from labels'). A row is eligible when its own key resolves and its own window is fully covered; an unattributable record does not make every row ineligible. 'Jointly omit unresolved outcome linkage' applies to rows whose own outcome linkage is unresolved. Report how many rows could be affected if any unlinked ANDA belonged to them (an upper-bound sensitivity count), without changing eligibility.

## Protocol before execution

Use the pinned S0 files and C3's guarded development reader. The approval filter applies to bytes before JSON decoding and ends on 2016-01-01 inclusive. Use each January 1 cutoff from 1995 through 2014, the existing dated NDA and TYPE 1 rules, and the first linked final original ANDA. Both classes require follow-up through the 24-month end in the verified S0 source. Omit a row with keyed linkage ambiguity when the ambiguous approval could affect prior eligibility or the in-window label. Inventory same-application Orange Book leads available by the approval date without upgrading them to labels. For the wholly unattributable records, report the union of eligible rows with a possible prior approval or an in-window approval, the components, and the subset with a potentially changed negative label. This is a timing-only upper bound without assumptions about drug identity.

Rebuild the C2 source features with its FDA edition freshness and publication rules. Use C2's public-at-filing rule for court filing dates and require the contemporaneous Orange Book support for patent relinkage. Withhold later corroborating documents from historical prompt evidence. Use dated NDA actions and dated product records for base evidence. The modern S0 and GSRS bytes serve as retrospective copies and identity crosswalks. Render and tokenize the outcome-blind C9 hash roster on CPU with the pinned production tokenizer. Freeze 32 batches of eight and enforce the 2,048-token cap before publishing the artifacts. Leave the registration lock in place and reject the test authorization variable. [C9 protocol](../C9-PROTOCOL.md) · [C9RUN2](C9RUN2.md) · [C3](C3.md) · [C2](C2.md)

## CPU result and handoff

**PASS, DEVELOPMENT_ONLY.** Branch `loe/C9PROJ` started from fetched `research/loe-bench` at `35e123a3` and merged C9RUN2 at `d0660335`. The export ran at code commit `415fd278a4903c8dbb5aa9c079be6d1103bcdf5b`. This receipt is the executor handoff and project memory entry for C9PROJ. Main-planner review is pending. Training, RunPod execution and prediction are `NOT_RUN`. Incremental spend is USD 0.

| Artifact | Rows | Positive | Negative | Byte SHA-256 |
| --- | ---: | ---: | ---: | --- |
| Private `c9_dev_projection.json` | 10,603 | 729 | 9,874 | `d6a824d3f4ed0a6cd4c8d1c581e70fa3d449a213c386671f0edd7e87356c8e1c` |
| Private `c9_dev_roster.jsonl` | 256 | 20 | 236 | `f77b777415c5246eedee831068ac2c003a4ba354c87af5a8abdd8f7ccdfc316c` |

Both private files are in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/`. The projection manifest fixes the S0 and source digests, eligible rows per cutoff, excluded applications and sensitivity counts. The 2013 and 2014 row counts of 539 and 544 match the corresponding FREEZE development cells. The roster manifest fixes the checkpoint and projection hashes, the ordered key, message and token-ID hashes, and the schedule for both arms. All 256 slots are distinct, so cycling was unnecessary. The longest prompt used 757 of 2,048 tokens with Transformers 4.55.2 and Tokenizers 0.21.4. Independent readback reproduced the projection hash, its 20 cutoffs and positive count, the entire roster byte stream and all derived roster hashes. [Projection manifest](../../../loe-bench/data/C9_DEV_PROJECTION_MANIFEST.json) · [Roster manifest](../../../loe-bench/data/C9_DEV_ROSTER_MANIFEST.json) · [FREEZE report](../../../loe-bench/data/FREEZE_dev_report.json)

### Outcome attribution

The guarded reader admitted 11,753 final original ANDA applications through 2016-01-01. Fourteen lacked a dated admissible group and contributed no label. Eleven of those had no group candidate, spanning 1972-10-25 to 2007-09-19. Three had incompatible undated compositions, with same-application historical Orange Book leads. One other application had a dated assignment and an unresolved alternative group. The linked assignment alone was eligible as outcome evidence. No eligible row intersected the unresolved candidate keys within its prior history or outcome window, so the keyed ambiguity check omitted zero rows.

Across the 11 unattributable applications, the timing-only upper bound is 10,603 eligible rows with a possible prior or in-window approval. The prior-approval bound alone reaches all 10,603 rows because some excluded dates precede the first cutoff. The within-window bound is 1,099 rows, including 1,026 current negatives that could change class. These sets overlap, and the actual affected count remains unknown. Eligibility uses the planner's decision above.

### Verification and recovery

- **PASS.** From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` in the existing C9 Python 3.12 CPU environment passed 239 tests, exit 0. The existing Purple Book file-handle warnings appeared.
- **FAIL, isolated retry PASS.** Root `python -m pytest` under CPython 3.12.10 returned 2,759 passed, 50 skipped, one xfailed and nine failed, exit 1. Eight were the standing SACR r2/r3 budget tests. The additional Workbench loopback timeout passed on isolated retry with `python -m pytest tests/test_ptp_g01_workbench.py::test_http_and_cli_reach_the_same_core`, exit 0. The full suite was run once.
- The initial export stopped before artifact publication when a corroborating document's version supplied a year without a day. The date parser now withholds a source without an explicit day, with a regression fixture. The next export completed. The Bash launch block passed `bash -n`. Its commands remain `NOT_RUN`.

The exporter can be replayed from `loe-bench/` on Windows using the existing pinned private inputs and CPU environment. Give `--out` and `--manifest-dir` fresh existing directories for a replay. [Exporter](../../../loe-bench/scripts/c9_dev_projection.py)

```powershell
$env:PYTHONPATH = '.'
rtk proxy C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9-venv/Scripts/python.exe scripts/c9_dev_projection.py
```

## Training card launch

Execute from the reviewed `loe-bench/` checkout on one NVIDIA L4 24 GB, RunPod Secure Cloud, US-MO-2, between 2026-12-01 00:00 UTC and the core Track A freeze. The 28 November quote was USD 0.69/hour. Refresh the exact placement and itemized quote and obtain the admission approval before pod creation. Use the registered 2.5 GPU-hour and USD 3.50 GPU limits per arm and the approved USD 4.50 all-in envelope within the registered USD 8 cap. Use the matched runtime in the [C9 instructions](../../../loe-bench/c9/README.md#approved-runpod-execution) and the verified [C′ gate](GATE.md).

Stage the pinned checkpoint and private projection at the paths below. Set `C9_ARM_SECONDS` from the approved equal per-arm reservation after accounting for setup, transfer and teardown. Reserve time for the timeout grace period and preserve the logs for both arms. The roster preflight checks the staged inputs against the committed manifests before either arm starts.

```bash
set -euo pipefail
test "$(date -u +%s)" -ge 1796083200
test "$(nvidia-smi --query-gpu=name --format=csv,noheader)" = "NVIDIA L4"
test ! -e /private/c9/trained
test "${C9_ARM_SECONDS:?Set the approved duration per arm}" -gt 0

projection=/private/c9/c9_dev_projection.json
checkpoint=/private/c9/checkpoint
sha=$(python -c 'import json; print(json.load(open("data/C9_DEV_PROJECTION_MANIFEST.json", encoding="utf-8"))["sha256"])')
python -m c9.roster --checkpoint "$checkpoint" --projection "$projection" \
  --projection-sha256 "$sha" --out /private/c9/launch-roster.json
python - <<'PY'
import json
from pathlib import Path

expected = json.loads(Path("data/C9_DEV_ROSTER_MANIFEST.json").read_text(encoding="utf-8"))
actual = json.loads(Path("/private/c9/launch-roster.json").read_text(encoding="utf-8"))
for field, value in actual.items():
    if expected[field] != value:
        raise SystemExit(f"Frozen C9 roster mismatch in {field}")
PY
timeout --kill-after=5s "${C9_ARM_SECONDS}s" python -m c9.train --arm sft \
  --checkpoint "$checkpoint" --projection "$projection" --projection-sha256 "$sha" \
  --output /private/c9/trained 2>&1 | tee /private/c9/sft.log
timeout --kill-after=5s "${C9_ARM_SECONDS}s" python -m c9.train --arm grpo \
  --checkpoint "$checkpoint" --projection "$projection" --projection-sha256 "$sha" \
  --output /private/c9/trained 2>&1 | tee /private/c9/grpo.log
```

Pull the paired directory and both logs, verify the hashes and verify pod deletion. The Track A freeze card owns prediction.
