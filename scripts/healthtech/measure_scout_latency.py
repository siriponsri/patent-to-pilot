"""E4 of the frozen Solution Scout protocol: CPU live-search latency on the HUPD index (descriptive).

Each authored demo brief is searched ``--repeats`` times after one warm-up search; reports the median and max
encode and search milliseconds, plus the machine's platform and CPU count. Run with the CPU venv.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--briefs", type=Path, default=ROOT / "examples/healthtech/scout-demo-briefs.json")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import torch

    from patent_to_pilot.healthtech.scout_live import LiveIndex

    index = LiveIndex.load(args.data_dir, args.model_dir)
    briefs = json.loads(args.briefs.read_text(encoding="utf-8"))["briefs"]
    index.search(briefs[0]["text"])  # warm-up, not recorded
    encode, search = [], []
    for brief in briefs:
        for _ in range(args.repeats):
            _, e, s = index.search(brief["text"])
            encode.append(e)
            search.append(s)
    summary = lambda xs: {"median_ms": round(statistics.median(xs), 1), "max_ms": round(max(xs), 1), "n": len(xs)}
    result = {"format": "ptp-scout-latency-e4-v1", "families": len(index.rows), "passages": int(index.vectors.shape[0]),
              "encode": summary(encode), "search": summary(search), "torch": torch.__version__,
              "torch_threads": torch.get_num_threads(), "platform": platform.platform(), "cpu_count": os.cpu_count()}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
