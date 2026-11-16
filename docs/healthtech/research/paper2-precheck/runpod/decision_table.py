"""Full-encoding decision table from encode_pilot.py receipts.

For each receipt: measured full-run passages/s (wall, includes tokenization) -> hours and USD for the
open-population corpus at 23M and 33M passages (OA-SPLITS: 5.5-7.9M documents x ~4.2-4.3 passages/doc).
Price per GPU-hour is given per receipt label on the command line (0 for the owned dr-train V100).
Usage: python decision_table.py LABEL=PRICE=path/to/receipt.json [...]
Example: python decision_table.py "V100 fp16 (dr-train)=0=v100/fp16/receipt-fp16.json" "4090 fp16=0.34=out-4090/receipt-fp16.json"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CORPUS_PASSAGES = (23_000_000, 33_000_000)


def main(argv: list[str]) -> int:
    rows = []
    for spec in argv:
        label, price, path = spec.split("=", 2)
        receipt = json.loads(Path(path).read_text(encoding="utf-8"))
        rate = receipt["full_run"]["passages_per_second_wall"]
        row = {"label": label, "gpu": receipt["gpu"].get("torch_name"), "mode": receipt["mode"],
               "batch_size": receipt["batch_size"], "passages": receipt["full_run"]["passages"],
               "passages_per_second": round(rate, 1), "usd_per_hour": float(price)}
        for n in CORPUS_PASSAGES:
            hours = n / rate / 3600
            row[f"hours_{n // 1_000_000}M"] = round(hours, 1)
            row[f"usd_{n // 1_000_000}M"] = round(hours * float(price), 2)
        rows.append(row)
    header = ["label", "gpu", "mode", "batch_size", "passages_per_second", "usd_per_hour",
              "hours_23M", "usd_23M", "hours_33M", "usd_33M"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(row[h]) for h in header) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
