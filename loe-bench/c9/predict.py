"""Generate full label-free Track A predictions from a frozen roster."""

import argparse
from pathlib import Path
from time import monotonic

from peft import PeftModel
from transformers import set_seed

from .checkpoint import model_manifest
from .inputs import (SPEC_SHA256, file_digest, load_projection, prediction_record,
                     roster_hashes, schedule, specification, strict_json, tokenize_rows, track_rows,
                     write_json, write_jsonl)
from .roster import load_tokenizer
from .train import ARMS, adapter_files, decode, generate, load_base, runtime


def prepare_track(checkpoint, roster, roster_sha, spec):
    rows = track_rows(load_projection(roster, roster_sha, training=False))
    tokenizer = load_tokenizer(checkpoint)
    prompts = tokenize_rows(rows, tokenizer, spec["prompt"]["max_prompt_tokens"])
    return rows, tokenizer, prompts


def predict(checkpoint, roster, roster_sha, trained, arm, output, *, dry=False):
    spec = specification()
    device, versions = runtime(dry, spec)
    started = monotonic()
    model_info = model_manifest(checkpoint, dry=dry)
    training = trained / "training-roster.json"
    training_manifest = strict_json(training.read_bytes())
    adapter = trained / arm
    run = strict_json((adapter / "run.json").read_bytes())
    batches, _, repeats = schedule(spec, dry)
    if (run["status"] != "COMPLETE" or run["arm"] != arm or run["dry_run"] != dry
            or run["updates"] != batches * repeats or run["files"] != adapter_files(adapter)
            or run["training_roster_sha256"] != file_digest(training)
            or run["initial_sha256"] != file_digest(trained / "initial.safetensors")
            or training_manifest["spec_lf_sha256"] != SPEC_SHA256
            or training_manifest["checkpoint"] != model_info or training_manifest["runtime"] != versions
            or run["runtime"] != versions):
        raise ValueError("adapter or paired training manifest mismatch")
    rows, tokenizer, prompts = prepare_track(checkpoint, roster, roster_sha, spec)
    set_seed(spec["prediction"]["seed"])
    model = PeftModel.from_pretrained(load_base(checkpoint, device, spec), adapter,
                                      is_trainable=False, local_files_only=True)
    predictions = []
    size = spec["training"]["prompts_per_batch"]
    for start in range(0, len(prompts), size):
        completions = generate(model, tokenizer, prompts[start:start + size],
                               spec["prediction"], sample=False)
        for row, ids in zip(rows[start:start + size], completions, strict=True):
            predictions.append(prediction_record(row, decode(tokenizer, ids)))
    bad = sum(not row["valid"] for row in predictions)
    output.mkdir(parents=True)
    path = output / "predictions.jsonl"
    write_jsonl(path, predictions)
    result = {"status": "COMPLETE", "arm": arm, "dry_run": dry, "spec_lf_sha256": SPEC_SHA256,
              "runtime": versions,
              "track_a_roster_sha256": roster_sha, **roster_hashes(rows, prompts),
              "adapter_run_sha256": file_digest(adapter / "run.json"),
              "predictions_sha256": file_digest(path), "rows": len(predictions),
              "malformed": bad, "malformed_rate": bad / len(rows), "seconds": monotonic() - started}
    write_json(output / "prediction.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--track-a-roster", type=Path, required=True)
    parser.add_argument("--track-a-sha256", required=True)
    parser.add_argument("--trained", type=Path, required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predict(args.checkpoint, args.track_a_roster, args.track_a_sha256,
            args.trained, args.arm, args.output)


if __name__ == "__main__":
    main()
