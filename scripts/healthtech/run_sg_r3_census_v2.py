"""Declared CPU-only census entrypoint; no model/query/evaluator access."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,'/code/src')
from patent_to_pilot.research.sg_census_runner import run_census


def main():
    raw=Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration mismatch')
    d=json.loads(raw)
    if d['run_id']!='ptp-sg-r3-census-20261111-v2' or d['expected_families']!=45336:
        raise RuntimeError('census scope mismatch')
    run_census('/input/corpus.jsonl','/out/attempt',expected_sha256=d['corpus_sha256'],
        expected_config_sha256=d['config_sha256'],expected_families=45336,
        max_seconds=1560,max_input_bytes=d['max_input_bytes'],max_line_bytes=8*1024**2)


if __name__=='__main__':main()
