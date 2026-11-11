"""CPU tokenizer preflight on the unchanged sealed cohort; never model loading."""
from .mtm_runtime import InputBoundaryError
from .sacr_native_fidelity import bind_sample, schema_digest
from .sacr_prompts import build_messages
from .sacr_schema import token_profile_schema


def preflight_token_profiles(*, query_bytes, sample_bytes, query_sha256, sample_sha256,
                             prompt_root, tokenizer, limits):
    limits.validate()
    # Validate the ORIGINAL sealed sample and its original schema hashes first.
    entries = bind_sample(query_bytes, sample_bytes, query_sha256=query_sha256,
                          sample_sha256=sample_sha256)
    records = []
    for q, source, _ in entries:
        prompt = build_messages(prompt_root=prompt_root, kind='profile_tokens',
                                query_id=q, input_kind='DAPFAM_TA', source=source)
        encoded = tokenizer.apply_chat_template(prompt['messages'], tokenize=True,
            add_generation_prompt=True, return_tensors='pt', return_dict=True,
            enable_thinking=False)
        shape = encoded['input_ids'].shape
        if len(shape) != 2 or shape[0] != 1 or shape[1] <= 0:
            raise InputBoundaryError('invalid tokenizer preflight shape')
        count = int(shape[1])
        schema = token_profile_schema(source=source, query_id=q, input_kind='DAPFAM_TA')
        records.append({'query_id': q, 'source_sha256': prompt['source_sha256'],
            'messages_sha256': prompt['messages_sha256'], 'prompt_sha256': prompt['prompt_sha256'],
            'schema_sha256': schema_digest(schema), 'input_tokens': count,
            'within_limit': count <= limits.input_tokens})
    exceeded = sum(not row['within_limit'] for row in records)
    return {'format': 'sacr-r2-profile-input-preflight-v1',
            'status': 'STOP_INPUT_LIMIT' if exceeded else 'PROFILE_INPUT_LIMIT_PASS_ONLY',
            'original_query_sha256': query_sha256, 'original_sample_sha256': sample_sha256,
            'sample_size': len(records), 'exceeded': exceeded,
            'maximum_input_tokens': max(r['input_tokens'] for r in records),
            'total_input_tokens': sum(r['input_tokens'] for r in records),
            'limits': limits.__dict__, 'records': records, 'model_calls': 0,
            'truncation': False, 'bundle_input_limits': 'NOT_ESTABLISHED',
            'generation_budget': 'NOT_ESTABLISHED', 'semantic_fidelity': 'NOT_ASSESSED'}
