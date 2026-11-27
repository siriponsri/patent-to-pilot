"""Independent C-prime gate for a custodian's blinded active-moiety histories.

The custodian supplies a JSON object with the pinned S0 manifest digest and a
complete deduplicated terminal projection in "histories". Each history contains
an opaque "drug_cluster", "nme_from" (first cutoff-eligible NME approval date),
and "first_final_anda" (ISO date or null). The projection uses the frozen
FIX2c cohort mapping with outcomes through the S0 observation end. Keep it
outside Git and executor access. No model scores or metric routines are used.

The only gate output is PASS, COVERAGE_FAIL, EVENT_FAIL or TECHNICAL_FAIL.
The main planner manages any documented retry outside this script.
"""
import argparse
from datetime import date
from hashlib import file_digest, sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench.common import add_months
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import edition_coverage


PASS = "PASS"
COVERAGE_FAIL = "COVERAGE_FAIL"
EVENT_FAIL = "EVENT_FAIL"
TECHNICAL_FAIL = "TECHNICAL_FAIL"


def checked_manifest(reference):
    path = ROOT / "data" / reference["file"]
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if sha256(data).hexdigest() != reference["sha256"]:
        raise ValueError("Manifest digest mismatch")
    return json.loads(data)


def verified_cutoffs(history, days, directory):
    for day in days:
        coverage = edition_coverage(history, day)
        if coverage["status"] != "FRESH":
            return False
        source = coverage["source"]
        with (directory / source["file"]).open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != source["sha256"]:
                return False
    return bool(days)


def event_cluster_gate(histories, cutoffs, horizon, end, minimum):
    if not isinstance(histories, list):
        raise ValueError("Expected a list of histories")
    clusters = set()
    found = 0
    for row in histories:
        key = row["drug_cluster"]
        if not isinstance(key, str) or not key or key in clusters:
            raise ValueError("Expected unique opaque cluster keys")
        clusters.add(key)
        nme = date.fromisoformat(row["nme_from"])
        raw = row["first_final_anda"]
        if raw is not None:
            first = date.fromisoformat(raw)
            if first > end:
                raise ValueError("First ANDA date exceeds source observation end")
            found += any(nme <= day < first <= add_months(day, horizon) for day in cutoffs)
    return found >= minimum


def run(projection, ob_dir):
    try:
        return _evaluate(projection, ob_dir)
    except Exception:
        # An exception can contain private paths or values from the projection.
        return TECHNICAL_FAIL


def _evaluate(projection, ob_dir):
    config = json.loads((ROOT / "data/FROZEN_CONFIG.json").read_bytes())
    if config["status"] != "FROZEN_FOR_PREREG":
        return TECHNICAL_FAIL
    sealed = config["sealed_test"]
    refs = config["input_sha256"]
    end = date.fromisoformat(checked_manifest(refs["s0_manifest"])["t0"])
    history = OBHistory.from_records(checked_manifest(refs["ob_manifest"]), ob_dir)
    if end.isoformat() != sealed["outcomes_observed_through"] or sealed["test_first"] != TEST_FIRST.isoformat():
        return TECHNICAL_FAIL
    h = sealed["cluster_gate_horizon"]
    minimum = sealed["min_distinct_event_drug_clusters"]
    if set(sealed["schedule"]) != {"12", "24"} or h != 24 or minimum != 50:
        return TECHNICAL_FAIL
    schedules = {}
    for horizon, schedule in sealed["schedule"].items():
        months = int(horizon)
        days = [date(year, 1, 1) for year in range(TEST_FIRST.year, end.year + 1)
                if add_months(date(year, 1, 1), months) <= end]
        if not days or [day.isoformat() for day in days] != schedule["test_cutoffs"]:
            return TECHNICAL_FAIL
        schedules[months] = days
    for days in schedules.values():
        if not verified_cutoffs(history, days, ob_dir):
            return COVERAGE_FAIL
    data = json.loads(projection.read_bytes())
    if data["s0_manifest_sha256"] != refs["s0_manifest"]["sha256"]:
        return TECHNICAL_FAIL
    return PASS if event_cluster_gate(data["histories"], schedules[h], h, end, minimum) else EVENT_FAIL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projection", type=Path)
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    args = parser.parse_args()
    verdict = run(args.projection, args.ob_dir)
    print(verdict)
    return 0 if verdict == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
