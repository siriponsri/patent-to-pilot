"""Bridge automatic pipeline to existing reserved local-model executor."""
import json
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sacr_generation import GenerationLimits
from .r6_dispatch_journal import document_hash


def adapt_reserved_executor(*, destination, executor, limits=GenerationLimits(), stages=('marking', 'review')):
    """executor(stage,path,messages,schema) persists original reservation/raw.

    The existing executor currently hardcodes GenerationLimits(); reject any
    other limits rather than pretend a different ceiling was enforced.
    """
    if limits != GenerationLimits():
        raise InputBoundaryError('existing executor requires original generation limits')
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    consumed = set()

    def invoke(stage, request):
        if stage not in stages or stage in consumed:  # Paper 1 FA/GR pass stages=('rewrite',)
            raise InputBoundaryError('unknown or repeated automatic call stage')
        consumed.add(stage)
        path = root / stage
        before = document_hash(request)
        metrics = executor(stage, path, request['messages'], request['schema'])
        if document_hash(request) != before:
            raise InputBoundaryError('reserved executor changed request')
        reservation = json.loads((path / 'reservation.json').read_bytes())
        # Original executor uses ensure_ascii=False, sorted keys, default spacing.
        import hashlib
        messages_hash = hashlib.sha256(json.dumps(request['messages'], ensure_ascii=False,
                                                   sort_keys=True).encode()).hexdigest()
        if (reservation.get('status') != 'RESERVED' or reservation.get('retry') is not False
                or reservation.get('limits') != limits.__dict__
                or reservation.get('messages_sha256') != messages_hash):
            raise InputBoundaryError('reserved model attempt differs from request')
        raw = (path / 'generation.json').read_bytes()
        diagnostics = path.with_name(path.name + '-diagnostics-private')
        if metrics.get('model_calls') == 1:
            dispatch = json.loads((diagnostics / 'backend-dispatch.json').read_bytes())
            returned = json.loads((diagnostics / 'backend-return.json').read_bytes())
            if (dispatch.get('status') != 'DISPATCH_INTENT' or dispatch.get('retry') is not False
                    or returned.get('status') != 'BACKEND_RETURNED_NOT_VALIDATED'):
                raise InputBoundaryError('backend completion diagnostics inconsistent')
        elif metrics.get('model_calls') != 0:
            raise InputBoundaryError('unexpected backend invocation count')
        return raw, metrics
    return invoke
