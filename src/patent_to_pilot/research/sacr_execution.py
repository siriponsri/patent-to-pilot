"""Prospective execution declaration binding, not authorization or live preflight."""
from copy import deepcopy
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.mtm_queries import parse_dev_queries
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_run_reconcile import validate_plan

IDENTITIES = {'query_manifest', 'metadata_manifest', 'index_manifest', 'encoder_manifest',
              'generator_manifest', 'prompt_manifest', 'code_manifest', 'method_declaration',
              'fidelity_policy'}
LIMITS = {'input_tokens', 'output_tokens', 'context_tokens', 'response_bytes',
          'model_calls', 'wall_seconds', 'gpu_seconds', 'peak_memory_bytes', 'depth', 'views'}


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise InputBoundaryError('expected lowercase SHA256 digest')


def bind_execution(declaration, plan, *, expected_execution_sha256, expected_plan_sha256):
    """Return detached validated records; supplied digests must be trusted externally.

    Identity entries refer to complete manifests, not bare model names. Source
    hashes bind allowed text; null means missing, not an empty string. This checks
    declarations only: no files, labels, model, GPU or authorization are accessed.
    Limits are declared ceilings; an external controller must enforce them live.
    """
    validate_plan(plan, expected_manifest_sha256=expected_plan_sha256)
    exact_fields(declaration, {'format', 'split', 'run_id', 'plan_sha256', 'sources',
                               'identities', 'limits'})
    _sha(expected_execution_sha256)
    if (declaration['format'] != 'sacr-dev-execution-v1' or declaration['split'] != 'dev' or
            declaration['run_id'] != plan['run_id'] or
            declaration['plan_sha256'] != expected_plan_sha256 or
            digest(declaration) != expected_execution_sha256):
        raise InputBoundaryError('execution declaration differs from pinned plan or digest')
    exact_fields(declaration['identities'], IDENTITIES)
    for value in declaration['identities'].values():
        _sha(value)
    sources = declaration['sources']
    if type(sources) is not list or len(sources) != len(plan['query_ids']):
        raise InputBoundaryError('source cohort differs from planned cohort')
    for row, query in zip(sources, plan['query_ids'], strict=True):
        exact_fields(row, {'query_id', 'source_sha256'})
        if row['query_id'] != query:
            raise InputBoundaryError('source order differs from planned cohort')
        if row['source_sha256'] is not None:
            _sha(row['source_sha256'])
    limits = declaration['limits']
    exact_fields(limits, LIMITS)
    if any(type(v) is not int or v <= 0 for v in limits.values()):
        raise InputBoundaryError('limits require positive integer ceilings')
    GenerationLimits(**{k: limits[k] for k in ('input_tokens', 'output_tokens',
                                              'context_tokens', 'response_bytes')}).validate()
    ceilings = {'input_tokens': 8192, 'output_tokens': 4096, 'context_tokens': 40960,
                'response_bytes': 65536, 'views': 3, 'depth': 200,
                'model_calls': 3 * len(plan['query_ids'])}
    if any(limits[k] > maximum for k, maximum in ceilings.items()):
        raise InputBoundaryError('limits exceed the current SACR envelope')
    return deepcopy(declaration)


def bind_input_snapshots(declaration, plan, *, manifest_bytes, query_payload,
                         expected_execution_sha256, expected_plan_sha256):
    """Bind caller-provided permitted bytes; never discover/open protected paths.

    Returns immutable ordered (query ID, text-or-None) tuples from the same
    snapshots whose hashes were checked. Other manifest contents are opaque:
    their referenced files still require existing identity preflight. This is
    the MTM primary P lane only; it does not redefine DAPFAM query semantics.
    """
    bound = bind_execution(declaration, plan, expected_execution_sha256=expected_execution_sha256,
                           expected_plan_sha256=expected_plan_sha256)
    exact_fields(manifest_bytes, IDENTITIES)
    for key, raw in manifest_bytes.items():
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != bound['identities'][key]:
            raise InputBoundaryError('manifest byte snapshot differs from declared identity')
    if type(query_payload) is not bytes:
        raise InputBoundaryError('query payload requires immutable byte snapshot')
    queries = parse_dev_queries(manifest_bytes['query_manifest'], query_payload,
                                bound['identities']['query_manifest'], set(plan['query_ids']))
    if queries['view'] != 'P':
        raise InputBoundaryError('this binding requires the declared MTM primary P view')
    texts = {row['id']: row['text'] for row in queries['rows']}
    result = []
    for source in bound['sources']:
        text = texts.get(source['query_id'])
        observed = hashlib.sha256(text.encode('utf-8')).hexdigest() if text is not None else None
        if observed != source['source_sha256']:
            raise InputBoundaryError('source bytes or missing-input declaration changed')
        result.append((source['query_id'], text))
    return tuple(result)
