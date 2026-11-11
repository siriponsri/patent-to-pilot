"""Read-only pinned character-parser qualification. No model/tokenizer imports.

Run existing remote Python -I -S -B, feed frozen fixture payload via stdin.
Output aggregate synthetic-only JSON. No writes to the remote filesystem.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import types


def main(payload):
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    signal.alarm(90)
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, available[:2])
    deps = Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages')
    package = deps / 'lmformatenforcer'
    for name, expected in payload['lmfe_source_sha256'].items():
        if hashlib.sha256((package / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('pinned parser source mismatch')
    sys.path.append(str(deps))
    # Avoid optional package initialization importing Torch, which is not tested here.
    namespace = types.ModuleType('lmformatenforcer'); namespace.__path__ = [str(package)]
    sys.modules['lmformatenforcer'] = namespace
    from lmformatenforcer.jsonschemaparser import JsonSchemaParser
    from lmformatenforcer.characterlevelparser import CharacterLevelParserConfig
    alphabet = ''.join(sorted(set(''.join(c['text'] for c in payload['cases'])) | set(chr(i) for i in range(32, 127))))
    config = CharacterLevelParserConfig(alphabet=alphabet, max_consecutive_whitespaces=4096,
                                       force_json_field_order=False, max_json_array_length=4096)
    def accepts(schema, text):
        parser = JsonSchemaParser(schema, config=config)
        for index, char in enumerate(text):
            if char not in parser.get_allowed_characters(): return False, index
            parser = parser.add_character(char)
        return bool(parser.can_end()), len(text)
    results = []
    for version, schema in payload['schemas'].items():
        for case in payload['cases']:
            accepted, position = accepts(schema, case['text'])
            results.append({'version': version, 'case': case['name'], 'accepted': accepted,
                'expected': case['expected'], 'matches_schema_expectation': accepted == case['expected'],
                'position': position, 'layer': case['layer']})
    numeric = []
    schema = {'type': 'integer', 'enum': [1, 10, 11]}
    for value in ['1', '10', '11', '12', '01', '-1', '1.0']:
        accepted, position = accepts(schema, value)
        numeric.append({'value': value, 'accepted': accepted, 'expected': value in ['1', '10', '11']})
    print(json.dumps({'status': 'CHARACTER_ONLY_OBSERVATION', 'results': results, 'numeric_enum': numeric,
        'wall_seconds': time.monotonic()-start, 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'model_calls': 0, 'gpu_seconds': 0, 'tokenizer_qualification': 'NOT_RUN',
        'bootstrap': 'PINNED_CHARACTER_MODULES_WITHOUT_OPTIONAL_PACKAGE_INIT', 'retry': False}))


if __name__ == '__main__':
    main(json.load(sys.stdin))
