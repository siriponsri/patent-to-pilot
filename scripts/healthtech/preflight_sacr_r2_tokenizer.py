"""Offline CPU-only preflight; fixed dev cohort, no model loading or retrieval."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, '/code/src')
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_r2_preflight import preflight_token_profiles


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('CPU preflight timeout')))
    signal.alarm(180)
    output = Path('/out/attempt')
    output.mkdir(exist_ok=False)
    manifest = json.loads(Path('/code/manifest.json').read_bytes())
    for name, expected in manifest.items():
        p = (Path('/code') / name).resolve()
        if not p.is_relative_to(Path('/code')) or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise RuntimeError('code transport hash mismatch')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('HF_HUB_OFFLINE') != '1':
        raise RuntimeError('offline CPU environment required')
    from transformers import AutoTokenizer
    model = Path('/model')
    tokenizer_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in model.iterdir() if p.is_file() and p.suffix in ('.json', '.txt', '.jinja')}
    expected = {
        'tokenizer.json': 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4',
        'tokenizer_config.json': 'd5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101',
        'config.json': 'f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30',
    }
    if any(tokenizer_hashes.get(k) != v for k, v in expected.items()):
        raise RuntimeError('existing tokenizer identity changed')
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    result = preflight_token_profiles(
        query_bytes=Path('/inputs/queries-ta.jsonl').read_bytes(),
        sample_bytes=Path('/inputs/sample.json').read_bytes(),
        query_sha256='6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a',
        sample_sha256='cf0bce973696c6d71c06d2387a36bd024b0ddbdc2a36a2c77bc6ce17ba4bd767',
        prompt_root=Path('/code/docs/healthtech/research/prompts'), tokenizer=tokenizer,
        limits=GenerationLimits())
    with (output / 'private-result.json').open('x') as f:
        json.dump(result, f, indent=2)
    aggregate = {k: v for k, v in result.items() if k != 'records'}
    aggregate.update(tokenizer_class=type(tokenizer).__name__, tokenizer_files_sha256=tokenizer_hashes,
                     cpu_wall_seconds=time.monotonic()-started, gpu_seconds=0,
                     code_manifest_sha256=hashlib.sha256(Path('/code/manifest.json').read_bytes()).hexdigest())
    with (output / 'aggregate.json').open('x') as f:
        json.dump(aggregate, f, indent=2)
    print(json.dumps(aggregate))


if __name__ == '__main__':
    main()
