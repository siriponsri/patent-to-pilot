"""Declared CPU-only candidate gate. No model weights or benchmark inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


def run(tokenizer_path, payload_path, declaration_path, output):
    declaration = json.loads(declaration_path.read_bytes())
    payload_raw = payload_path.read_bytes()
    if hashlib.sha256(payload_raw).hexdigest() != declaration['payload_sha256']:
        raise ValueError('declared payload mismatch')
    for name, expected in declaration['tokenizer_files_sha256'].items():
        if hashlib.sha256((tokenizer_path / name).read_bytes()).hexdigest() != expected:
            raise ValueError('declared tokenizer identity mismatch')
    code_root = Path(__file__).resolve().parents[2]
    for relative, expected in declaration['code_files_sha256'].items():
        if hashlib.sha256((code_root / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('declared archived code mismatch')
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'reservation.json', {'status': 'RESERVED', 'pid': os.getpid(),
                                       'model_calls': 0, 'payload_sha256': declaration['payload_sha256']})
    started = time.monotonic()
    import torch
    from transformers import AutoTokenizer
    from jsonschema import Draft202012Validator
    from lmformatenforcer import CharacterLevelParserConfig
    from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
    from patent_to_pilot.research.sacr_alphabet import build_alphabet
    from patent_to_pilot.research.sacr_escape_callback import build_escape_callback
    from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard

    payload = json.loads(payload_raw)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True, trust_remote_code=False)
    data = build_token_enforcer_tokenizer_data(tokenizer)
    alphabet = build_alphabet(tokenizer, payload['source'])
    config = CharacterLevelParserConfig(alphabet=alphabet['alphabet'], max_consecutive_whitespaces=4096,
                                        force_json_field_order=False, max_json_array_length=4096)
    validator = Draft202012Validator(payload['schema'])
    results = []
    for index, case in enumerate(payload['cases']):
        prefix = tokenizer.encode('Synthetic full schema probe:\n', add_special_tokens=False)
        callback = build_escape_callback(data, payload['schema'], config,
                                         expected_source_sha256=declaration['lmfe_source_sha256'])
        guard = CompleteJsonEOSGuard(prefix_fn=callback, tokenizer=tokenizer, prompt_tokens=len(prefix),
                                     eos_token_ids=[151645, 151643], validate=validator.validate)
        valid = False
        try:
            validator.validate(json.loads(case['text']))
            valid = True
        except (ValueError, TypeError):
            pass
        except Exception as error:
            if type(error).__name__ != 'ValidationError':
                raise
        rejected, early, failure = None, [], None
        accepted = False
        tokens = tokenizer.encode(case['text'], add_special_tokens=False)
        try:
            for position, token in enumerate(tokens):
                allowed = guard(0, torch.tensor(prefix, dtype=torch.long))
                if tokenizer.eos_token_id in allowed:
                    early.append(position)
                if token not in allowed:
                    rejected = position
                    break
                prefix.append(token)
            allowed = guard(0, torch.tensor(prefix, dtype=torch.long))
            accepted = rejected is None and tokenizer.eos_token_id in allowed
        except Exception as error:
            failure = type(error).__name__
        row = {'case': case['name'], 'expected': case['expected'], 'independent_valid': valid,
               'accepted': accepted, 'rejected_token_position': rejected, 'early_eos': early,
               'exception_type': failure, 'config': callback.configuration_receipt,
               'pass': accepted == case['expected'] and valid == case['expected'] and not early and failure is None}
        write(output / f'case-{index:02d}.json', row)
        results.append(row)
        print(json.dumps({'case': case['name'], 'pass': row['pass']}), flush=True)
    result = {'format': 'sacr-escape-candidate-cpu-v1', 'model_calls': 0, 'weights_loaded': False,
              'cases': results, 'all_expected': all(row['pass'] for row in results),
              'wall_seconds': time.monotonic() - started, 'semantic_status': 'NOT_ESTABLISHED'}
    write(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('tokenizer', 'payload', 'declaration', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.tokenizer, args.payload, args.declaration, args.output)
