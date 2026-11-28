"""Run the frozen decoders on a new, label-free SCORELLM input freeze."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import time

import l1e_protocol as protocol
import runpod_l1dev
import runpod_l1e

from loe_bench import l1e_prompt, llm_arm


ARMS = {
    "L1": ("L1DEV", "L1_FROZEN_CONFIG.json", llm_arm.build_prompt, runpod_l1dev.run),
    "L1e": ("L1E", "L1E_FROZEN_CONFIG.json", l1e_prompt.build_prompt, runpod_l1e.run),
}


def check_inputs(data, manifest, arm):
    pin = manifest["arms"][arm]
    if sha256(data).hexdigest() != pin["input_sha256"]:
        raise ValueError(f"{arm} input bytes differ from the freeze")
    rows = [json.loads(line, object_pairs_hook=protocol.l1.unique_fields) for line in data.splitlines()]
    renderer = ARMS[arm][2]
    fields = protocol.l1.FIELDS if arm == "L1" else l1e_prompt.FIELDS
    for row in rows:
        if not isinstance(row, dict) or row.keys() != fields:
            raise ValueError(f"{arm} input has unexpected fields")
        entity = row["entity"]
        if not isinstance(entity, str) or not entity.strip() or not entity.isprintable():
            raise ValueError(f"{arm} input ingredient name is invalid")
        if type(row["horizon_months"]) is not int:
            raise ValueError(f"{arm} input horizon is invalid")
    identities = [(row["horizon_months"], row["t0"], row["entity"]) for row in rows]
    days = [identity[:2] for identity in identities]
    expected = {(int(h), day): count for h, counts in manifest["cutoffs"].items() for day, count in counts.items()}
    if (len(rows) != manifest["rows"] or len(rows) < protocol.l1.GATE_ROWS
            or len(set(identities)) != len(rows) or days != sorted(days) or Counter(days) != expected):
        raise ValueError(f"{arm} input does not cover the ordered common roster")
    if protocol.digest_lines(map(renderer, rows)) != pin["messages_sha256"]:
        raise ValueError(f"{arm} rendered messages differ from the freeze")
    return rows


def load_arms(work, config_dir):
    manifest = json.loads((work / "manifest.json").read_bytes())
    arms = {}
    for arm, (stem, config_file, _, runner) in ARMS.items():
        raw = (config_dir / config_file).read_bytes().replace(b"\r\n", b"\n")
        if sha256(raw).hexdigest() != manifest["config_lf_sha256"][config_file]:
            raise ValueError(f"{arm} configuration differs from the freeze")
        config = json.loads(raw)
        rows = check_inputs((work / f"{stem}_inputs.jsonl").read_bytes(), manifest, arm)
        arms[arm] = (rows, config, runner)
    if arms["L1"][0] != [protocol.identity(row) for row in arms["L1e"][0]]:
        raise ValueError("the arms do not share the full ordered roster")
    return arms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--deadline", type=int, required=True)
    args = parser.parse_args()
    arms = load_arms(args.work, args.work)
    for _, config, _ in arms.values():
        for name, digest in config["harness_lf_sha256"].items():
            data = (args.work / name).read_bytes().replace(b"\r\n", b"\n")
            if sha256(data).hexdigest() != digest:
                raise ValueError(f"harness digest mismatch: {name}")
    runpod_l1dev.verify_model(args.model, arms["L1"][1]["model"]["files"])
    manifest = json.loads((args.work / "manifest.json").read_bytes())
    for arm, (rows, config, runner) in arms.items():
        if time.time() >= args.deadline:
            raise ValueError(f"deadline reached before starting {arm}")
        plan = {**config, "development_input": {"sha256": manifest["arms"][arm]["input_sha256"]}}
        print(f"Starting {arm}", flush=True)
        runner(rows, args.model, args.work, plan, args.deadline)


if __name__ == "__main__":
    main()
