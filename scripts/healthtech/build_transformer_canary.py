"""Create a deterministic 64-row runtime-only Unicode encoder canary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.vector_artifacts import export_runtime_text


BASE_TEXTS = [
    "A catheter-based heart valve with a flexible sealing skirt.",
    "ลิ้นหัวใจเทียมสำหรับการรักษาผู้ป่วยโรคหัวใจ",
    "Combining e\u0301, emoji 🫀, and punctuation — for tokenizer coverage.",
    "A device with a tab\tseparator and an embedded\nline break.",
    "中文医学器械说明与ภาษาไทย mixed-language retrieval text.",
    "A very long edge-case row " + ("with repeated medical-device terminology " * 40),
    "Zero-width joiner 👩‍⚕️ and non-breaking\u00a0space.",
    "Claim-like wording: an apparatus comprising a pump, sensor, and valve.",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        {
            "item_id": f"canary-row-{index:03d}",
            "document_id": f"CANARY-{index:03d}",
            "text": BASE_TEXTS[index % len(BASE_TEXTS)] + f" Variant {index}.",
            "source_id": "authored-transformer-canary",
            "source_revision": "2026-10-31-v1",
        }
        for index in range(64)
    ]
    manifest = export_runtime_text(
        rows,
        args.output,
        dataset_id="ht-transformer-canary-20261031",
        source_revision="2026-10-31-v1",
        representation="unicode-edge-v1",
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
