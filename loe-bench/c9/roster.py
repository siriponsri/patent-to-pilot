"""Freeze the C9 training roster and check prompt lengths on CPU."""

import argparse
from pathlib import Path

from .checkpoint import model_manifest
from .inputs import (SPEC_SHA256, load_projection, roster_hashes, select_training,
                     specification, tokenize_rows, write_json)


def load_tokenizer(checkpoint):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False, padding_side="left",
    )
    tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.eos_token_id is None or not tokenizer.chat_template:
        raise ValueError("checkpoint lacks the pinned chat template or assistant EOS")
    return tokenizer


def prepare(checkpoint, projection, sha, spec, *, dry):
    rows = select_training(load_projection(projection, sha, training=True))
    if dry:
        rows = rows[:16]
        if len({(r["drug_key"], r["t0"]) for r in rows}) != 16:
            raise ValueError("CPU dry run requires 16 distinct synthetic prompts")
    tokenizer = load_tokenizer(checkpoint)
    prompts = tokenize_rows(rows, tokenizer, spec["prompt"]["max_prompt_tokens"])
    manifest = {
        "spec_lf_sha256": SPEC_SHA256,
        "training_projection_sha256": sha,
        "s0_manifest_lf_sha256": spec["s0"]["manifest_lf_sha256"],
        "prompt_contract_lf_sha256": spec["prompt"]["contract_lf_sha256"],
        "renderer_lf_sha256": spec["prompt"]["renderer_lf_sha256"],
        "parser_lf_sha256": spec["prompt"]["parser_source_lf_sha256"],
        "slots": len(rows), "max_prompt_tokens": max(map(len, prompts)),
        **roster_hashes(rows, prompts),
    }
    return rows, tokenizer, prompts, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    model = model_manifest(args.checkpoint, dry=False)
    _, _, _, manifest = prepare(args.checkpoint, args.projection, args.projection_sha256,
                                specification(), dry=False)
    write_json(args.out, manifest | {"checkpoint": model})


if __name__ == "__main__":
    main()
