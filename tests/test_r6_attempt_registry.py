from concurrent.futures import ThreadPoolExecutor

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.r6_attempt_registry import AttemptRegistry, initialize


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
