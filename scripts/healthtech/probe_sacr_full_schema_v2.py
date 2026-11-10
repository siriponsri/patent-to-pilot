"""Run full-schema authored fixtures through CPU token filtering; no model load."""
import hashlib
import importlib.metadata
import json


def run(tokenizer_path, payload):
    import torch
    from transformers import AutoTokenizer
    from lmformatenforcer import JsonSchemaParser, CharacterLevelParserConfig
    from jsonschema import Draft202012Validator
    from patent_to_pilot.research.sacr_alphabet import build_alphabet
    from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
    from lmformatenforcer.integrations.transformers import (
        build_token_enforcer_tokenizer_data,
        build_transformers_prefix_allowed_tokens_fn,
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    data = build_token_enforcer_tokenizer_data(tokenizer)
    alphabet = build_alphabet(tokenizer, payload["source"])
    config = CharacterLevelParserConfig(alphabet=alphabet["alphabet"], max_consecutive_whitespaces=4096,
                                        force_json_field_order=False, max_json_array_length=4096)
    validator = Draft202012Validator(payload["schema"])
    results = []
    for case in payload['cases']:
        base_fn = build_transformers_prefix_allowed_tokens_fn(data, JsonSchemaParser(payload['schema'], config=config))
        prefix = tokenizer.encode('Synthetic full schema probe:\n', add_special_tokens=False)
        fn = CompleteJsonEOSGuard(prefix_fn=base_fn, tokenizer=tokenizer, prompt_tokens=len(prefix),
                                  eos_token_ids=[151645, 151643], validate=validator.validate)
        tokens = tokenizer.encode(case['text'], add_special_tokens=False)
        rejected = None
        early_eos = []
        for index, token in enumerate(tokens):
            allowed = fn(0, torch.tensor(prefix, dtype=torch.long))
            if tokenizer.eos_token_id in allowed:
                early_eos.append(index)
            if token not in allowed:
                rejected = index
                break
            prefix.append(token)
        allowed = fn(0, torch.tensor(prefix, dtype=torch.long))
        accepted = rejected is None and tokenizer.eos_token_id in allowed
        results.append({'case': case['name'], 'accepted': accepted,
                        'expected': case['expected'], 'first_rejected_token': rejected,
                        'early_eos_indices': early_eos,
                        'end_allowed_eos': [i for i in [151645, 151643] if i in allowed],
                        'pass': accepted == case['expected'] and not early_eos})
    return {'format': 'sacr-full-schema-cpu-probe-v2', 'model_calls': 0,
            'model_weights_loaded': False, 'device': 'cpu',
            'alphabet': {k: v for k, v in alphabet.items() if k != 'alphabet'},
            'parser_config': {'max_consecutive_whitespaces':4096, 'force_json_field_order':False,
                              'max_json_array_length':4096},
            'lm_format_enforcer_version': importlib.metadata.version('lm-format-enforcer'),
            'payload_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            'cases': results, 'all_expected': all(r['pass'] for r in results),
            'semantic_status': 'NOT_ESTABLISHED'}
