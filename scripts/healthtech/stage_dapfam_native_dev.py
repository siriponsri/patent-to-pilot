"""OWNER ONLY: stage preserved-split DAPFAM dev inputs from pinned mixed sources.

Execute personally as curator, outside the development-agent role. Outputs contain
no protected queries/qrels. Runtime and dev-evaluator must be mounted separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.evaluation.dapfam_staging import stage_native_dev
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

PINS = {
    "corpus.parquet": "469fe8e04d8bd8775a1116eccf0983e570a03444bef9c6e14c97aabafb7526d6",
    "queries.parquet": "b5ad91a650349a0096911fadcb7bc35a0399eb12d1470fb2601d73af5fc2bcbe",
    "qrels_all.parquet": "e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74",
    "split.json": "dd76c019ee74c8d256e182ecfb329f9235638c1ecf9d2c7b1fa8073c4958e6dc",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--original-split", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--owner-curator", action="store_true", required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise InputBoundaryError("preserve existing attempt")
    import pyarrow as pa
    import pyarrow.parquet as pq
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    # Parse exactly the bytes hashed, not a second potentially changed file read.
    payload = {name: (args.original_split if name == "split.json" else args.data_dir / name).read_bytes()
               for name in PINS}
    hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in payload.items()}
    if hashes != PINS:
        raise InputBoundaryError("source identity mismatch")
    def rows(name, columns):
        return pq.read_table(pa.BufferReader(payload[name]), columns=columns, use_threads=False).to_pylist()
    receipt = stage_native_dev(
        rows("corpus.parquet", ["relevant_id", "title_en", "abstract_en", "claims_text"]),
        rows("queries.parquet", ["query_id", "title_en", "abstract_en"]),
        rows("qrels_all.parquet", ["query_id", "relevant_id", "relevance_score", "domain_rel"]),
        json.loads(payload["split.json"])["assignment"], args.output_root,
        source_hashes=hashes, expected_dev=474, expected_protected=773, expected_corpus=45336,
        expected_corpus_sha256="42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d")
    print(json.dumps(receipt))


if __name__ == "__main__":
    try:
        main()
    except (InputBoundaryError, OSError, KeyError, ValueError, TypeError):
        print("DAPFAM preparation failed. Preserve attempt; no completion accepted. Curator-only diagnosis required.", file=sys.stderr)
        raise SystemExit(1)
