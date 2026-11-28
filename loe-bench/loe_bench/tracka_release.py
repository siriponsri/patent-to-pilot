"""Read the public Track A release and verify its frozen inputs."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import file_digest, sha256
import json
from math import isfinite
from pathlib import Path
import re

from .common import read_jsonl
from .llm_arm import parse_response


T0 = date(2026, 11, 27)
DEADLINE = datetime(2027, 1, 31, 23, 59, tzinfo=timezone.utc)
HORIZONS = (12, 24)
CORE = ("B1", "B3", "M1", "M3")
PRIOR = ("P1-RSF-OPEN", "P2-COX-OPEN")
LLM = ("L1", "L1e")
C9 = ("C9-SFT", "C9-GRPO")
VERSION = "1.0.0"
MANIFEST = "release.json"
FREEZE = "freeze-manifest.json"
IDENTITY = "identity.json"
ARMS = "arm-dictionary.json"
ROSTER = "roster.jsonl"
SCORER = "scorer-version.json"
DIGEST = re.compile(r"[0-9a-f]{64}")
FILENAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
TRACKA_FREEZE_SCHEMA = "loe-track-a-freeze-v1"


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def code_digest(path):
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def dump(path, value):
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def safe_name(name):
    require(isinstance(name, str) and FILENAME.fullmatch(name), f"Invalid filename: {name}")
    return name


def frozen_pins(freeze):
    if freeze.get("schema") != TRACKA_FREEZE_SCHEMA:
        return freeze["files_sha256"]
    require(freeze["t0"] == T0.isoformat() and freeze["roster"]["canonical_file"] == ROSTER,
            "Invalid Track A freeze roster or cutoff")
    predictions = freeze["predictions"]
    require(set(CORE) <= predictions.keys() <= set(CORE + PRIOR + LLM + C9),
            "Invalid Track A freeze arm inventory")
    pins = dict(freeze["upstream_private_sha256"])
    require(pins.get(ROSTER) == freeze["roster"]["sha256"], "Inconsistent roster freeze pins")
    for arm, record in predictions.items():
        name = safe_name(record["file"])
        require(record["status"] == "ADMITTED" and name not in pins,
                f"Invalid or duplicate frozen prediction for {arm}")
        pins[name] = record["sha256"]
    return pins


def verify_file(folder, name, expected):
    path = folder / safe_name(name)
    require(isinstance(expected, str) and DIGEST.fullmatch(expected), f"Invalid SHA-256 for {name}")
    require(path.is_file() and not path.is_symlink(), f"Missing regular release file: {name}")
    require(digest(path) == expected, f"SHA-256 mismatch: {name}")
    return path


def row_id(row):
    return row.get("key", row.get("drug_key", row.get("entity"))), row["t0"], row["horizon_months"]


def ordered_rows(path, expected, horizon=None):
    rows = list(read_jsonl(path))
    ids = [row_id(row) for row in rows]
    target = expected if horizon is None else [key for key in expected if key[2] == horizon]
    require(ids == target, f"Roster order or row count differs in {path.name}")
    return rows


def ordered_llm_rows(path, expected, input_sha256):
    rows = list(read_jsonl(path))
    require([(row["t0"], row["horizon_months"]) for row in rows] == [(t, h) for _, t, h in expected],
            f"Roster order or row count differs in {path.name}")
    # TRACKA-CORE exported the L1 prompt identities in canonical roster order.
    # Both arms carry that same projection, with ingredient names in place of keys.
    identities = [{key: row[key] for key in ("entity", "horizon_months", "t0")} for row in rows]
    projected = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
                        for row in identities).encode("utf-8")
    require(sha256(projected).hexdigest() == input_sha256, f"Frozen L1 input identities differ in {path.name}")
    return rows


def probability(value, arm):
    require(type(value) in (float, int) and isfinite(value) and 0 <= value <= 1,
            f"Invalid frozen probability for {arm}")
    return float(value)


def model_scores(arm, payload):
    native = probability(payload["native"], arm)
    if arm == "B3":
        require(native in (0, 1), "B3 must use its binary expiry rule")
    calibrated = probability(payload["calibrated"], arm) if arm in ("B1", "M1", "M3") else native
    return native, calibrated, True


def llm_scores(arm, row):
    completion = row.get("completion", row.get("raw_text"))
    if completion is not None:
        require(isinstance(completion, str), f"Missing captured text for {arm}")
        parsed = parse_response(completion)
        require(parsed["valid"] == row["valid"] and parsed["p_entry"] == row["p_entry"],
                f"Frozen parsed prediction differs from completion for {arm}")
    require(type(row["valid"]) is bool, f"Invalid availability flag for {arm}")
    if row["valid"]:
        p = probability(row["p_entry"], arm)
        return p, p, True
    require(row["p_entry"] is None, f"Malformed completion has a probability for {arm}")
    return -1.0, 0.5 if arm in C9 else None, False


@dataclass
class Release:
    folder: Path
    manifest: dict
    manifest_sha256: str
    scores: dict
    keys: tuple


def read_release(folder, expected_freeze=None):
    manifest_path = folder / MANIFEST
    manifest = load(manifest_path)
    require(manifest["schema"] == 1 and manifest["t0"] == T0.isoformat(), "Unsupported release")
    require(manifest["freeze"] in ("pending", "frozen"), "Unknown freeze state")
    files = manifest["files_sha256"]
    for name, expected in files.items():
        verify_file(folder, name, expected)
    require({ROSTER, FREEZE, IDENTITY, ARMS, SCORER} <= files.keys(), "Missing release manifest entries")
    if expected_freeze is not None:
        require(files[FREEZE] == expected_freeze, "Freeze manifest differs from the external pin")
    freeze = load(folder / FREEZE)
    if manifest["freeze"] == "frozen":
        stamped = datetime.fromisoformat(manifest["osf_timestamp"])
        require(freeze.get("freeze") != "pending" and manifest["osf_manifest_sha256"] == files[FREEZE]
                and manifest["freeze_tag"] and stamped.utcoffset() is not None and stamped.date() >= T0,
                "Missing or inconsistent freeze attestation")
        require(manifest["analysis"] == "exploratory" or
                (manifest["analysis"] == "replication" and stamped < DEADLINE), "Invalid Track A analysis type")
    frozen_files = frozen_pins(freeze)
    native_freeze = freeze.get("schema") == TRACKA_FREEZE_SCHEMA
    if native_freeze:
        require(manifest["freeze"] == "frozen" and manifest["freeze_tag"] == freeze["git_tag"],
                "Release tag differs from the Track A freeze")
    for name, frozen_name in manifest["frozen_files"].items():
        require(name in files and files[name] == frozen_files.get(frozen_name),
                f"Release does not match the freeze manifest for {name}")
    require(ROSTER in manifest["frozen_files"], "Roster is absent from the freeze manifest")
    scorer = load(folder / SCORER)
    require(scorer["version"] == VERSION, "Use the scorer version shipped with the release")
    for name, expected in scorer["source_files_sha256"].items():
        require(code_digest(Path(__file__).with_name(safe_name(name))) == expected,
                f"Installed scorer differs from the release for {name}")
    roster = list(read_jsonl(folder / ROSTER))
    expected = [row_id(row) for row in roster]
    require(all(isinstance(key, str) and key and t == T0.isoformat() and h in HORIZONS
                for key, t, h in expected), "Invalid roster identity")
    keys = tuple(key for key, _, h in expected if h == 12)
    require(keys and keys == tuple(sorted(set(keys))) and
            expected == [(key, T0.isoformat(), h) for h in HORIZONS for key in keys],
            "Frozen roster must have the same ordered unique keys at both horizons")
    dictionary = load(folder / ARMS)
    require(set(dictionary) == set(CORE + PRIOR + LLM + C9), "Unknown or missing entries in arm dictionary")
    scores = {h: {} for h in HORIZONS}
    for arm, source in dictionary.items():
        require(source["status"] in ("INCLUDED", "NOT_RUN", "WITHHELD"), f"Unknown arm status: {arm}")
        supplied = source["files"]
        if native_freeze:
            admitted = freeze["predictions"].get(arm)
            require((source["status"] == "NOT_RUN") == (admitted is None),
                    f"Incorrect freeze availability for {arm}")
        if source["status"] != "INCLUDED":
            require(arm not in CORE and not supplied, f"Invalid omitted arm: {arm}")
            continue
        horizons = (24,) if arm in C9 else HORIZONS
        require(set(supplied) == {str(h) for h in horizons}, f"Invalid horizons for {arm}")
        single_file = len(horizons) == 2 and supplied["12"] == supplied["24"]
        for h in horizons:
            name = supplied[str(h)]
            require(name in manifest["frozen_files"], f"Prediction not covered by freeze manifest: {name}")
            if native_freeze:
                require(manifest["frozen_files"][name] == admitted["file"],
                        f"Prediction is pinned to another arm: {arm}")
            if native_freeze and arm in LLM:
                rows = ordered_llm_rows(folder / name, expected, frozen_files["L1DEV_inputs.jsonl"])
            else:
                rows = ordered_rows(folder / name, expected, None if single_file else h)
            if single_file:
                rows = [row for row in rows if row_id(row)[2] == h]
            if arm in CORE + PRIOR:
                group = CORE if arm in CORE else tuple(a for a in PRIOR if dictionary[a]["status"] == "INCLUDED")
                if native_freeze:
                    scores[h][arm] = [model_scores(arm, row) for row in rows]
                else:
                    require(all(set(row["arms"]) == set(group) for row in rows),
                            f"Arm columns differ from arm dictionary for {name}")
                    scores[h][arm] = [model_scores(arm, row["arms"][arm]) for row in rows]
            else:
                scores[h][arm] = [llm_scores(arm, row) for row in rows]
    require((C9[0] in scores[24]) == (C9[1] in scores[24]), "C9 must be supplied as a matched pair")
    return Release(folder, manifest, sha256(manifest_path.read_bytes()).hexdigest(), scores, keys)
