"""CPU-only tokenizer/grammar probe; authored fixtures, no model or benchmark."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tokenizer', required=True)
    args = parser.parse_args()
    import torch
    from transformers import AutoTokenizer
    from lmformatenforcer import JsonSchemaParser
    from lmformatenforcer.integrations.transformers import (
        build_transformers_prefix_allowed_tokens_fn,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    schema = {
        'type': 'object', 'additionalProperties': False,
        'required': ['field', 'text'],
        'properties': {'field': {'type': 'string', 'enum': ['allowed_query']},
                       'text': {'type': 'string', 'minLength': 1}},
    }
    cases = [
        ('literal_quote', '{"field":"allowed_query","text":"low pressure"}', True),
        ('invented_quote', '{"field":"allowed_query","text":"invented mechanism"}', True),
        ('missing_comma', '{"field":"allowed_query" "text":"low pressure"}', False),
        ('wrong_field', '{"field":"hidden_label","text":"low pressure"}', False),
        ('extra_property', '{"field":"allowed_query","text":"low pressure","extra":1}', False),
    ]
    results = []
    for name, text, expected in cases:
        fn = build_transformers_prefix_allowed_tokens_fn(tokenizer, JsonSchemaParser(schema))
        prefix = tokenizer.encode('Synthetic CPU probe:\n', add_special_tokens=False)
        rejected = None
        for index, token in enumerate(tokenizer.encode(text, add_special_tokens=False)):
            if token not in fn(0, torch.tensor(prefix, dtype=torch.long)):
                rejected = index
                break
            prefix.append(token)
        allowed_end = fn(0, torch.tensor(prefix, dtype=torch.long))
        accepted = rejected is None and tokenizer.eos_token_id in allowed_end
        results.append({'case': name, 'accepted': accepted, 'expected': expected,
                        'first_rejected_token_index': rejected,
                        'pass': accepted == expected})
    source = inspect.getsource(build_transformers_prefix_allowed_tokens_fn).encode()
    print(json.dumps({
        'format': 'sacr-json-grammar-feasibility-v1',
        'scope': 'SMALL_QUOTE_SCHEMA_ONLY_NOT_FULL_PROFILE',
        'model_calls': 0, 'model_weights_loaded': False, 'device': 'cpu',
        'packages': {name: importlib.metadata.version(name) for name in
                     ['lm-format-enforcer', 'transformers', 'tokenizers', 'torch']},
        'factory_source_sha256': hashlib.sha256(source).hexdigest(),
        'schema': schema, 'cases': results,
        'all_expected': all(result['pass'] for result in results),
        'semantic_status': 'NOT_ESTABLISHED_INVENTED_QUOTE_ALLOWED',
    }, indent=2))


if __name__ == '__main__':
    main()
