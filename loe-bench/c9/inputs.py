"""Build C9 inputs from admitted, bounded projections and freeze their bytes."""

import hashlib
import json
import re
from datetime import date
from pathlib import Path

from loe_bench import c9, l1e_prompt
from loe_bench.common import add_months
from loe_bench.llm_arm import parse_response

ROOT = Path(__file__).resolve().parents[1]
SPEC_SHA256 = "e865e719e7fcbd8fa636164270c4c3959d007cb9357cbedb59d7802b8951f28f"
SPEC_PATH = ROOT / "data/C9_SPEC.json"
SHA256 = re.compile(r"[0-9a-f]{64}")
TRAIN_FIELDS = {"drug_key", "forecast", "original_nda", "type1", "covered_through",
                "resolved_linkage", "first_final_anda", "provenance"}
TRACK_FIELDS = {"drug_key", "forecast", "provenance"}
RECORD_FIELDS = {"source_id", "version", "sha256", "locator", "record_date", "available_on"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_bytes(path, expected, *, lf=False):
    raw = path.read_bytes()
    if lf:
        raw = raw.replace(b"\r\n", b"\n")
    if digest(raw) != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return raw


def specification():
    spec = json.loads(checked_bytes(SPEC_PATH, SPEC_SHA256, lf=True))
    prompt = spec["prompt"]
    for path, expected in (
        (prompt["contract_path"], prompt["contract_lf_sha256"]),
        (prompt["renderer_path"], prompt["renderer_lf_sha256"]),
        ("loe-bench/loe_bench/llm_arm.py", prompt["parser_source_lf_sha256"]),
        (spec["s0"]["input_manifest"], spec["s0"]["manifest_lf_sha256"]),
    ):
        checked_bytes(ROOT / path.removeprefix("loe-bench/"), expected, lf=True)
    return spec


def schedule(spec, dry=False):
    cfg = spec["training"]
    if dry:
        return 2, cfg["prompts_per_batch"], 1
    count = cfg["prompt_batches"]
    repeats = cfg["optimizer_updates_per_batch"]
    if count * repeats != cfg["optimizer_updates_per_arm"]:
        raise ValueError("frozen update count does not match the schedule")
    return count, cfg["prompts_per_batch"], repeats


def jsonl_bytes(rows):
    return b"".join(canonical(row) + b"\n" for row in rows)


def _unique_fields(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate input field")
    return obj


def strict_json(raw):
    return json.loads(raw, object_pairs_hook=_unique_fields)


def write_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def write_jsonl(path, rows):
    with path.open("xb") as stream:
        stream.write(jsonl_bytes(rows))


def day(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("expected YYYY-MM-DD date")
    return parsed


def dated_records(records, latest):
    if not isinstance(records, list) or not records:
        raise ValueError("source provenance is required")
    for record in records:
        if record.keys() != RECORD_FIELDS or not SHA256.fullmatch(record["sha256"]):
            raise ValueError("expected source ID, version, SHA-256, locator and dated proof")
        if any(not isinstance(record[k], str) or not record[k].strip()
               for k in ("source_id", "version", "locator")):
            raise ValueError("source proof is incomplete")
        if max(day(record["record_date"]), day(record["available_on"])) > latest:
            raise ValueError("source proof is dated after its admission boundary")


def validate_row(row, *, training):
    if row.keys() != (TRAIN_FIELDS if training else TRACK_FIELDS):
        raise ValueError("unexpected projection fields")
    if not isinstance(row["drug_key"], str) or not row["drug_key"].strip():
        raise ValueError("a frozen active-moiety key is required")
    forecast = row["forecast"]
    cutoff = day(forecast["t0"])
    if type(forecast["horizon_months"]) is not int or forecast["horizon_months"] != c9.HORIZON_MONTHS:
        raise ValueError("C9 accepts only 24-month horizons")
    if cutoff not in (c9.TRAIN_CUTOFFS if training else {c9.S0}):
        raise ValueError("cutoff outside the admitted C9 projection")
    if not isinstance(forecast["entity"], str) or not forecast["entity"].strip():
        raise ValueError("an ingredient display name is required")
    proof = row["provenance"]
    if proof.keys() != ({"as_of", "outcome"} if training else {"as_of"}):
        raise ValueError("unexpected provenance fields")
    dated_records(proof["as_of"], cutoff)
    prompt = l1e_prompt.build_prompt(forecast)
    return (row["drug_key"], cutoff), prompt


def select_training(rows):
    eligible = {}
    seen = set()
    for row in rows:
        key, prompt = validate_row(row, training=True)
        if key in seen:
            raise ValueError("duplicate drug and cutoff in training projection")
        seen.add(key)
        cutoff = key[1]
        end = add_months(cutoff, c9.HORIZON_MONTHS)
        if end > date(2016, 1, 1):
            raise ValueError("outcome window ends after the C9 boundary")
        nda, type1 = day(row["original_nda"]), day(row["type1"])
        event = None if row["first_final_anda"] is None else day(row["first_final_anda"])
        coverage = None if row["covered_through"] is None else day(row["covered_through"])
        if ((event is not None and event > end) or (coverage is not None and coverage > end)):
            raise ValueError("outcome projection must be clipped to its training window")
        if type(row["resolved_linkage"]) is not bool:
            raise ValueError("linkage status must be Boolean")
        if max(nda, type1) > cutoff or (event is not None and event <= cutoff):
            continue
        if not row["resolved_linkage"] or coverage != end:
            continue
        dated_records(row["provenance"]["outcome"], c9.S0)
        if any(day(record["record_date"]) > end for record in row["provenance"]["outcome"]):
            raise ValueError("outcome proof contains events beyond the training window")
        eligible[key] = (prompt, c9.resolve_training_label(cutoff, event, coverage))
    selected = c9.training_order(eligible)
    if {eligible[key][1] for key in selected} != {0, 1}:
        raise ValueError("selected C9 roster must contain both classes")
    return [{"drug_key": key, "t0": cutoff.isoformat(), "messages": eligible[key, cutoff][0],
             "label": eligible[key, cutoff][1]} for key, cutoff in selected]


def load_projection(path, expected, *, training):
    if not SHA256.fullmatch(expected):
        raise ValueError("an independently frozen projection SHA-256 is required")
    raw = checked_bytes(path, expected)
    envelope = strict_json(raw)
    spec = specification()
    if (envelope.keys() != {"schema", "s0_manifest_lf_sha256", "rows"}
            or envelope["schema"] != ("c9-development-v1" if training else "c9-track-a-v1")
            or envelope["s0_manifest_lf_sha256"] != spec["s0"]["manifest_lf_sha256"]
            or not isinstance(envelope["rows"], list) or not envelope["rows"]):
        raise ValueError("expected the independently admitted C9 S0 projection")
    return envelope["rows"]


def track_rows(rows):
    result = []
    seen = set()
    for row in rows:
        (drug, cutoff), prompt = validate_row(row, training=False)
        if drug in seen:
            raise ValueError("duplicate Track A key")
        seen.add(drug)
        result.append({"drug_key": drug, "t0": cutoff.isoformat(), "messages": prompt})
    if not result:
        raise ValueError("Track A roster is empty")
    return result


def tokenize_rows(rows, tokenizer, limit):
    tokens = []
    for row in rows:
        system, user = row["messages"]
        ids = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tokenize=True, add_generation_prompt=True, enable_thinking=False,
        )
        if not 0 < len(ids) <= limit:
            raise ValueError(f"pair failed prompt token limit for {row['drug_key']}")
        tokens.append(ids)
    return tokens


def roster_hashes(rows, tokens):
    return {
        "keys_sha256": digest(jsonl_bytes([row["drug_key"], row["t0"]] for row in rows)),
        "messages_sha256": digest(jsonl_bytes(row["messages"] for row in rows)),
        "prompt_token_ids_sha256": digest(jsonl_bytes(tokens)),
    }


def prediction_record(row, text):
    if not isinstance(text, str):
        raise ValueError("missing captured completion")
    parsed = parse_response(text)
    probability = parsed["p_entry"] if parsed["valid"] else c9.MALFORMED_PROBABILITY
    rank = parsed["p_entry"] if parsed["valid"] else c9.MALFORMED_RANK
    return {"drug_key": row["drug_key"], "t0": row["t0"], "horizon_months": c9.HORIZON_MONTHS,
            "completion": text, **parsed, "brier_probability": probability, "rank_score": rank}
