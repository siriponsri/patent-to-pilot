"""Build the EVP handoff input from the pinned 24-month development export."""
from dataclasses import asdict
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2] / "loe-bench"
PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench")
CUTOFF = date(2014, 1, 1)
HORIZON = 24


def select():
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
    from c3_dev_guard import nda_reader
    from k20t1_run import replay
    import e7_dev_run
    import t4_power
    from loe_bench.dataset import build_samples
    from loe_bench.seal import ENV_NAME, TEST_FIRST
    from loe_bench.t2 import require_development_cutoffs
    from loe_bench.t2_features import _EditionIndex, _edition_selection

    manifest = json.loads((ROOT / "data/FREEZE_DEV_SCORES_MANIFEST.json").read_bytes())
    entry = manifest["exports"][str(HORIZON)]
    raw = Path(entry["path"]).read_bytes()
    if sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("Development score export digest mismatch")
    scores = sorted((row for row in json.loads(raw)["rows"] if row["cutoff"] == str(CUTOFF)),
                    key=lambda row: (-row["M3"], row["key"]))
    require_development_cutoffs([CUTOFF])
    if ENV_NAME in os.environ or replay.DEVELOPMENT_END >= TEST_FIRST:
        raise ValueError("EVP requires development-only inputs without test authorization")
    fallback = replay.read_jsonl

    def guarded_reader(path):
        return nda_reader(path, fallback, projector=t4_power, redact_dates=replay.without_later_approvals)

    with patch.object(replay, "read_jsonl", guarded_reader), patch.object(e7_dev_run, "read_jsonl", guarded_reader):
        entities, builder, _ = replay.inputs(PRIVATE / "raw-20261127", PRIVATE / "ob_editions",
                                             PRIVATE / "piv", PRIVATE / "challenge")
    events = {row["key"]: row["y"] for row in build_samples(entities, [CUTOFF], HORIZON, replay.DEVELOPMENT_END)}
    if len(scores) != entry["cutoff_rows"][str(CUTOFF)] or set(events) != {row["key"] for row in scores}:
        raise ValueError("Frozen score roster differs from reconstructed development roster")
    source, coverage = _edition_selection(builder.history, CUTOFF)
    edition = builder.history.load_source(source)
    index = _EditionIndex(edition, linker=builder.linker)
    challenge = builder.challenge
    queue_size = len(scores) // 5
    selected = []
    seen = {"queued_event": 0, "queued_no_event": 0, "outside_event": 0}
    for rank, row in enumerate(scores, 1):
        key = row["key"]
        inside, event = rank <= queue_size, events[key]
        if not inside and not event:
            continue
        group = "queued_event" if inside and event else "queued_no_event" if inside else "outside_event"
        if seen[group] == (4 if group == "queued_event" else 1):
            continue
        products = index.by_key.get(builder.linker.canonical(key), set())
        patents = [p for p in edition.patents if (p["appl_no"], p["product_no"]) in products]
        witnesses = challenge.lookup(key, CUTOFF).witnesses
        if group == "queued_event" and not (patents and witnesses):
            continue
        seen[group] += 1
        selected.append(dict(key=key, rank=rank, group=group, m3=row["M3"],
                             event=str(entities[key].anda_first) if event else None,
                             products=[p for p in edition.products if (p["appl_no"], p["product_no"]) in products],
                             patents=patents, witnesses=[asdict(w) for w in witnesses],
                             exclusivities=[e for e in edition.exclusivity
                                            if (e["appl_no"], e["product_no"]) in products]))
    if seen != {"queued_event": 4, "queued_no_event": 1, "outside_event": 1}:
        raise ValueError(f"Incomplete selection: {seen}")
    return dict(cutoff=CUTOFF, queue_size=queue_size, roster=len(scores), events=sum(events.values()),
                queue_events=sum(events[row["key"]] for row in scores[:queue_size]),
                orange_book=coverage, cases=selected)


if __name__ == "__main__":
    print(json.dumps(select(), default=str, ensure_ascii=True, indent=2))
