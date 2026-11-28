"""Input, prompt and response checks shared by the L1e executor and scorer."""
from hashlib import sha256
import json

import l1dev_protocol as l1
from loe_bench import l1e_prompt, llm_arm


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
                    for row in rows)


def identity(row):
    return {key: row[key] for key in l1.FIELDS}


def digest_lines(rows):
    return sha256(jsonl(rows)).hexdigest()


def prompt_digests(rows):
    return {"system_utf8_sha256": sha256(l1e_prompt.SYSTEM.encode()).hexdigest(),
            "template_utf8_sha256": sha256(l1e_prompt.TEMPLATE.encode()).hexdigest(),
            "messages_jsonl_sha256": digest_lines(l1e_prompt.build_prompt(row) for row in rows)}


def verify_input(data, config):
    pin = config["development_input"]
    if sha256(data).hexdigest() != pin["sha256"]:
        raise ValueError("L1e forecast input SHA-256 mismatch")
    rows = [json.loads(line, object_pairs_hook=l1.unique_fields) for line in data.splitlines()]
    if any(not isinstance(row, dict) or row.keys() != l1e_prompt.FIELDS for row in rows):
        raise ValueError("forecast must match the frozen L1e allowlist")
    l1.validate_input(jsonl(identity(row) for row in rows), pin["l1_rows_sha256"])
    if len(rows) != pin["rows"] or any(config["prompt"][key] != value for key, value in prompt_digests(rows).items()):
        raise ValueError("forecast count or rendered prompt bytes differ from freeze")
    return rows


def read_outputs(path, summary, inputs, expected_input, *, l1_output=False):
    data = path.read_bytes()
    if (summary["input_sha256"] != expected_input or summary["output_sha256"] != sha256(data).hexdigest()
            or summary["n_planned"] != len(inputs)):
        raise ValueError("inference summary and frozen input/output hashes disagree")
    outputs = [json.loads(line, object_pairs_hook=l1.unique_fields) for line in data.splitlines()]
    if len(outputs) > len(inputs):
        raise ValueError("inference output has rows outside the frozen roster")
    parsed = []
    for forecast, output in zip(inputs, outputs):
        if any(output[key] != forecast[key] for key in l1.FIELDS):
            raise ValueError("inference output order or identity disagrees with the frozen roster")
        result = llm_arm.parse_response(output["raw_text"])
        if any(output[key] != value for key, value in result.items()):
            raise ValueError("remote and local parser results differ")
        parsed.append(result)
    gate_rows = min(len(parsed), l1.GATE_ROWS)
    first_valid = sum(row["valid"] for row in parsed[:gate_rows])
    valid = sum(row["valid"] for row in parsed)
    abstains = sum(row["action"] == llm_arm.ACTIONS[-1] for row in parsed)
    summary_gate = first_valid if gate_rows == l1.GATE_ROWS else 0
    if (summary["n_rows"], summary["first_200_valid"], summary["valid_json"], summary["abstains"]) != (
        len(parsed), summary_gate, valid, abstains
    ):
        raise ValueError("inference summary and re-parsed counts disagree")
    gate_pass = gate_rows == l1.GATE_ROWS and first_valid >= l1.MINIMUM_VALID
    complete = summary["status"] == "COMPLETE" and len(parsed) == len(inputs)
    if l1_output and not (gate_pass and complete):
        raise ValueError("L1 comparator requires its original gate and full verified roster")
    gate = {"status": "PASS" if gate_pass else "FAIL" if gate_rows == l1.GATE_ROWS else "NOT_RUN",
            "evaluated_rows": gate_rows, "schema_valid": first_valid, "rows_returned": len(parsed),
            "full_roster": complete, "run_status": summary["status"]}
    return parsed, gate


def native_risks(parsed):
    return [row["p_entry"] if row["valid"] else -1.0 for row in parsed]
