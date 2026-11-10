"""CPU-only inspection of existing corpus, vectors, model files and dev receipts.

No GPU model loading, query/label access, encoding or scoring. Refuses overwrite.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.research.mtm_runtime import decode_json  # noqa: E402
from patent_to_pilot.research.vector_identity import (  # noqa: E402
    observe_identity, sha256, verify_historical_receipts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("corpus", "vectors", "model-root", "encoding-receipt", "reuse-receipt", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    observed = observe_identity(args.corpus, args.vectors, args.model_root,
                                Path(__file__).with_name("run_dapfam_dense_pool.py"))
    provenance = verify_historical_receipts(observed, decode_json(args.encoding_receipt.read_bytes()),
                                           decode_json(args.reuse_receipt.read_bytes()))
    report = {"identity": observed, "provenance": provenance,
              "receipt_sha256": {"encoding": sha256(args.encoding_receipt), "reuse": sha256(args.reuse_receipt)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": provenance["status"], "families": observed["corpus"]["families"],
                      "passages": observed["corpus"]["passages"], "shape": observed["vectors"]["shape"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
