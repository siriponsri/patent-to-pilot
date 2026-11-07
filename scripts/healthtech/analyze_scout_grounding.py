"""E3 of the frozen Solution Scout protocol: quote-by-reference (v1) vs free quotes (v0).

G1 fully grounded: every quote is found literally in the candidate text (server check_quote).
G2 support proxy: a local NLI cross-encoder; premise = matched quotes joined, hypothesis = what_it_does;
supported when P(entailment) >= 0.5. A parse failure counts as 0 on both. NLI is a proxy, not expert judgement.
Protocol: docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.scout_frozen import grounding_decision  # noqa: E402
from patent_to_pilot.healthtech.scout import check_quote  # noqa: E402


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _key(row: dict) -> tuple[str, str, str]:
    return row.get("sample", "hupd-demo"), row["brief_id"], row["family_id"]


class Nli:
    def __init__(self, model_dir: Path):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).eval()
        labels = {v.lower(): int(k) for k, v in self.model.config.id2label.items()}
        self.entail = labels["entailment"]

    def entailment(self, premise: str, hypothesis: str) -> float:
        with self.torch.inference_mode():
            batch = self.tokenizer([premise], [hypothesis], truncation=True, max_length=512, return_tensors="pt")
            return float(self.model(**batch).logits.softmax(-1)[0, self.entail])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True, help="candidate files with source_text")
    parser.add_argument("--v0", type=Path, nargs="+", required=True)
    parser.add_argument("--v1", type=Path, nargs="+", required=True)
    parser.add_argument("--nli-model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit("output exists: the frozen analysis runs once; write an amendment instead of overwriting")
    sources = {_key(r): r["source_text"] for path in args.inputs for r in _rows(path)}
    v0 = {_key(r): r for path in args.v0 for r in _rows(path)}
    v1 = {_key(r): r for path in args.v1 for r in _rows(path)}
    keys = sorted(sources)
    missing = [k for k in keys if k not in v0 or k not in v1]
    if missing:
        raise SystemExit(f"{len(missing)} candidate pairs lack a v0 or v1 output")
    nli = Nli(args.nli_model_dir)
    rows, details = [], {"v0": {"parse_failures": 0, "quotes": 0, "matched": 0, "prompt_tokens": 0, "output_tokens": 0, "latency": 0.0},
                         "v1": {"parse_failures": 0, "quotes": 0, "matched": 0, "invalid_references": 0, "prompt_tokens": 0,
                                "output_tokens": 0, "latency": 0.0}}
    for key in keys:
        row = {"key": "|".join(key), "cluster": f"{key[0]}|{key[1]}"}
        for name, outputs in (("v0", v0), ("v1", v1)):
            out, stats = outputs[key], details[name]
            stats["prompt_tokens"] += out["prompt_tokens"]
            stats["output_tokens"] += out["output_tokens"]
            stats["latency"] += out["latency_seconds"]
            parsed = out["parsed"]
            if parsed is None:
                stats["parse_failures"] += 1
                row[f"{name}_g1"] = row[f"{name}_g2"] = 0
                continue
            checks = [check_quote(q, sources[key]) for q in parsed["quotes"]]
            matched = [c.quote for c in checks if c.status == "matched"]
            stats["quotes"] += len(checks)
            stats["matched"] += len(matched)
            if name == "v1":
                stats["invalid_references"] += parsed.get("invalid_references", 0)
            row[f"{name}_g1"] = int(len(matched) == len(checks))
            row[f"{name}_g2"] = int(bool(matched) and nli.entailment(" ".join(matched), parsed["what_it_does"]) >= 0.5)
        rows.append(row)
    for stats in details.values():
        stats["latency_mean_seconds"] = round(stats.pop("latency") / len(keys), 3)
    by_sample = {}
    for sample in sorted({k[0] for k in keys}):
        subset = [r for r in rows if r["key"].startswith(sample + "|")]
        by_sample[sample] = {g: {v: sum(r[f"{v}_{g}"] for r in subset) / len(subset) for v in ("v0", "v1")}
                             for g in ("g1", "g2")} | {"pairs": len(subset)}
    nli_config = json.loads((args.nli_model_dir / "config.json").read_text(encoding="utf-8"))
    result = {"format": "ptp-scout-grounding-e3-v1", "nli_model": str(args.nli_model_dir.name),
              "nli_config_sha256": hashlib.sha256((args.nli_model_dir / "config.json").read_bytes()).hexdigest(),
              "nli_labels": nli_config.get("id2label"), "threshold": 0.5,
              "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [*args.inputs, *args.v0, *args.v1]},
              "details": details, "by_sample": by_sample, **grounding_decision(rows)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("decision", "pairs", "clusters", "g1", "g2")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
