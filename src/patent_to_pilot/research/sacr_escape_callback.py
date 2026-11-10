"""Candidate pinned LMFE adapter. NOT validated for tokenizer/model execution.

No import of LMFE, tokenizer or model occurs until explicitly called. The next
declared CPU gate must test this intervention; existing generation never uses it.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import importlib.metadata

from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SOURCE_FILES = ('tokenenforcer.py', 'tokenizerprefixtree.py', 'jsonschemaparser.py',
                'characterlevelparser.py', 'integrations/transformers.py')


def build_escape_callback(tokenizer_data, schema, config, *, expected_source_sha256):
    """Require externally pinned source identities; no installation or fallback.

    Keep the caller's independent complete-JSON EOS guard. This callback itself
    does not prove complete JSON, semantic fidelity or acceptable resource costs.
    """
    if type(expected_source_sha256) is not dict or set(expected_source_sha256) != set(SOURCE_FILES):
        raise InputBoundaryError('complete reviewed LMFE source pins required')
    distribution = importlib.metadata.distribution('lm-format-enforcer')
    if distribution.version != '0.11.3':
        raise InputBoundaryError('candidate adapter requires LMFE 0.11.3')
    for name in SOURCE_FILES:
        observed = hashlib.sha256(distribution.locate_file('lmformatenforcer/' + name).read_bytes()).hexdigest()
        if observed != expected_source_sha256[name]:
            raise InputBoundaryError('installed LMFE source differs from reviewed pin')

    from lmformatenforcer import JsonSchemaParser, CharacterLevelParserConfig
    from lmformatenforcer.tokenenforcer import TokenEnforcer

    if type(config) is not CharacterLevelParserConfig:
        raise InputBoundaryError('explicit parser configuration required')
    frozen_config = deepcopy(config)
    requested = asdict(frozen_config)
    parser = JsonSchemaParser(deepcopy(schema), config=frozen_config)

    class EscapeAwareEnforcer(TokenEnforcer):
        def _collect_allowed_tokens(self, current, node, allowed, shortcut_key):
            super()._collect_allowed_tokens(current, node, allowed, shortcut_key)
            # The base shortcut dynamically follows quotes only. Traverse the
            # backslash subtree with the same exact parser, never whole-vocabulary
            # no-shortcut traversal and never unconditional token admission.
            if (isinstance(shortcut_key, tuple) and shortcut_key[0] == 'json_freetext' and
                    '\\' in node.children and '\\' in current.get_allowed_characters()):
                next_parser = current.add_character('\\')
                super()._collect_allowed_tokens(next_parser, node.children['\\'], allowed, None)

    enforcer = EscapeAwareEnforcer(tokenizer_data, parser)
    overwritten = asdict(parser.config)
    # Constructor overwrites the root config, but no tokens have been consumed.
    # Restore before traversal; initial parser context was built from this config.
    parser.config = frozen_config
    if asdict(enforcer.root_parser.config) != requested:
        raise InputBoundaryError('effective root parser configuration differs')

    class Callback:
        token_enforcer = enforcer

        @property
        def configuration_receipt(self):
            def summary(values):
                result = deepcopy(values)
                alphabet = result.pop('alphabet')
                result['alphabet_sha256'] = hashlib.sha256(alphabet.encode()).hexdigest()
                result['alphabet_characters'] = len(alphabet)
                return result
            return {'format': 'sacr-escape-callback-candidate-v1',
                    'requested': summary(requested), 'constructor_overwrite': summary(overwritten),
                    'effective_root': summary(asdict(enforcer.root_parser.config)),
                    'source_sha256': deepcopy(expected_source_sha256),
                    'runtime_acceptance': 'NOT_ESTABLISHED'}

        def __call__(self, batch_id, sent):
            if batch_id != 0:
                raise InputBoundaryError('candidate grammar supports one sequence only')
            # Existing cached tokens and exact backslash traversal can overlap.
            return sorted(set(enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens))

    return Callback()
