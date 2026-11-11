from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.r6_attempt_registry import AttemptRegistry, initialize, completed_bundle


def parameters():
    return dict(namespace='owner-approved-R6', benchmark='DAPFAM', split='dev',
                configuration_sha256='a'*64, query_id='q1', source_sha256='b'*64,
                manifest_sha256='c'*64, execution_sha256='d'*64)


def registry(tmp_path):
    path = tmp_path/'attempts.sqlite'
    initialize(path, 'e'*64)
    return AttemptRegistry(path, 'e'*64)


def test_reopen_blocks_unknown_and_changed_source(tmp_path):
    first = registry(tmp_path)
    first.claim(**parameters())
    reopened = AttemptRegistry(first.path, 'e'*64)
    for values in (parameters(), dict(parameters(), source_sha256='f'*64),
                   dict(parameters(), execution_sha256='f'*64)):
        with pytest.raises(InputBoundaryError, match='replay forbidden'):
            reopened.claim(**values)


def test_completed_claim_still_cannot_replay_or_resettle(tmp_path):
    db = registry(tmp_path)
    claim = db.claim(**parameters())
    with pytest.raises(InputBoundaryError):
        db.settle(claim, {})
    db.begin_dispatch(claim)
    with pytest.raises(InputBoundaryError):
        db.begin_dispatch(claim)
    assert len(db.settle(claim, {'status': 'UNASSESSABLE'})) == 64
    db.verify_completed(claim, {'status': 'UNASSESSABLE'})
    with pytest.raises(InputBoundaryError):
        db.verify_completed(claim, {'status': 'changed'})
    with pytest.raises(InputBoundaryError):
        db.settle(claim, {'status': 'UNASSESSABLE'})
    with pytest.raises(InputBoundaryError):
        db.claim(**parameters())


def test_concurrent_claim_has_exactly_one_winner(tmp_path):
    db = registry(tmp_path)
    def try_claim(_):
        try:
            AttemptRegistry(db.path, 'e'*64).claim(**parameters())
            return True
        except InputBoundaryError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(try_claim, range(2))) == 1


def test_missing_identity_or_changed_binding_cannot_admit(tmp_path):
    with pytest.raises(FileNotFoundError):
        AttemptRegistry(tmp_path/'missing', 'e'*64)
    db = registry(tmp_path)
    with pytest.raises(InputBoundaryError):
        AttemptRegistry(db.path, 'f'*64)
    claim = db.claim(**parameters())
    with pytest.raises(InputBoundaryError):
        db.settle(dict(claim, binding='changed'), {})
    with pytest.raises(FileExistsError):
        initialize(db.path, 'e'*64)


def test_cached_bundle_byte_change_and_execution_substitution_fail(tmp_path):
    db = registry(tmp_path)
    out = tmp_path/'bundle';out.mkdir()
    result = {'query_id': 'q1', 'status': 'UNASSESSABLE', 'retry': False}
    execution = {'model_identity': 'authored'}
    source = 'b'*64
    (out/'input.json').write_text(json.dumps(dict(query_id='q1', source_sha256=source,
                                                execution=execution, retry=False)))
    (out/'result.json').write_text(json.dumps(result))
    args = dict(query_id='q1', source_sha256=source, execution=execution, result=result)
    binding = completed_bundle(out, **args)
    claim = db.claim(**parameters());db.begin_dispatch(claim);db.settle(claim, binding)
    db.verify_completed(claim, completed_bundle(out, **args))
    (out/'result.json').write_text(json.dumps(result, indent=2))
    with pytest.raises(InputBoundaryError):
        db.verify_completed(claim, completed_bundle(out, **args))
    with pytest.raises(InputBoundaryError):
        completed_bundle(out, **dict(args, execution={'model_identity': 'changed'}))


def test_unresolved_never_reused_and_deleted_registry_never_recreated(tmp_path):
    db = registry(tmp_path);claim = db.claim(**parameters())
    with pytest.raises(InputBoundaryError):
        db.verify_completed(claim, {})
    db.path.unlink()
    with pytest.raises(Exception):
        db.claim(**parameters())
    assert not db.path.exists()


def test_real_bundle_entry_rejects_new_destination_and_run_without_calls(tmp_path):
    from test_sacr_r6_bundle_runner import setup
    from patent_to_pilot.research.r6_attempt_registry import run_registered_bundle
    db = registry(tmp_path)
    args, calls, _ = setup(tmp_path)
    dispatch = dict(registry=db, namespace='R6', configuration_sha256='a'*64,
                    manifest_sha256='c'*64, bundle_arguments=args)
    receipt = run_registered_bundle(**dispatch)
    assert len(calls) == 3
    assert json.loads(receipt['claim']['binding'])['destination'] == str(args['destination'].resolve())
    db.verify_completed(receipt['claim'], receipt['binding'])
    args['destination'] = tmp_path/'different-output'
    args['execution'] = dict(args['execution'], run_id='different-run')
    with pytest.raises(InputBoundaryError, match='replay forbidden'):
        run_registered_bundle(**dispatch)
    assert len(calls) == 3 and not args['destination'].exists()


def test_real_bundle_unknown_backend_cannot_replay_elsewhere(tmp_path):
    from test_sacr_r6_bundle_runner import setup
    from patent_to_pilot.research.r6_attempt_registry import run_registered_bundle
    db = registry(tmp_path)
    args, calls, _ = setup(tmp_path, 'infra')
    dispatch = dict(registry=db, namespace='R6', configuration_sha256='a'*64,
                    manifest_sha256='c'*64, bundle_arguments=args)
    with pytest.raises(RuntimeError):
        run_registered_bundle(**dispatch)
    count = len(calls)
    args['destination'] = tmp_path/'different-output'
    with pytest.raises(InputBoundaryError, match='replay forbidden'):
        run_registered_bundle(**dispatch)
    assert len(calls) == count
