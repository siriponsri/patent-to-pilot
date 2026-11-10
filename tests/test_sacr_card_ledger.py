import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_card_ledger import CardLedger


def cards(benchmark='DAPFAM'):
    return [{'benchmark': benchmark, 'configuration_digest': 'a' * 64,
             'query_id': str(i), 'category': 'escalation' if i < 20 else 'sentinel'} for i in range(30)]


def test_reload_preserves_cumulative_60_and_rejects_duplicate(tmp_path):
    path = tmp_path / 'ledger.jsonl'
    first = CardLedger.create(path)
    first.reserve(cards(), expected_head=first.snapshot()['head_sha256'])
    second = CardLedger(path)
    final = second.reserve(cards('MTM'), expected_head=second.snapshot()['head_sha256'])
    assert final['issued_total'] == 60 and first.snapshot() == final
    before = path.read_bytes()
    with pytest.raises(InputBoundaryError):
        second.reserve(cards(), expected_head=final['head_sha256'])
    assert path.read_bytes() == before


def test_stale_writer_cannot_overwrite_new_reservation(tmp_path):
    ledger = CardLedger.create(tmp_path / 'cards')
    old = ledger.snapshot()['head_sha256']
    ledger.reserve(cards()[:1], expected_head=old)
    with pytest.raises(InputBoundaryError, match='stale'):
        ledger.reserve(cards()[1:2], expected_head=old)
    assert ledger.snapshot()['issued_total'] == 1


def test_missing_truncated_and_changed_ledgers_never_reset(tmp_path):
    path = tmp_path / 'cards'
    with pytest.raises(FileNotFoundError):
        CardLedger(path)
    ledger = CardLedger.create(path)
    ledger.reserve(cards()[:1], expected_head=ledger.snapshot()['head_sha256'])
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        CardLedger.create(path)
    for bad in [original[:-1], original.replace(b'"query_id":"0"', b'"query_id":"x"'), b'']:
        path.write_bytes(bad)
        with pytest.raises(InputBoundaryError):
            CardLedger(path)


def test_over_budget_batch_is_not_partially_issued(tmp_path):
    path = tmp_path / 'cards'
    ledger = CardLedger.create(path)
    before = path.read_bytes()
    extra = {**cards()[0], 'query_id': 'extra'}
    with pytest.raises(InputBoundaryError, match='BUDGET'):
        ledger.reserve(cards() + [extra], expected_head=ledger.snapshot()['head_sha256'])
    assert path.read_bytes() == before


def test_owner_amendment_appends_without_reset_and_reserves_two_distinct_pools(tmp_path):
    path = tmp_path / 'cards'
    ledger = CardLedger.create(path)
    original = path.read_bytes()
    ledger.adopt_paper1_allocation(expected_head=ledger.snapshot()['head_sha256'])
    assert path.read_bytes().startswith(original)
    assert ledger.snapshot()['events'] == 1
    for pool in ('SACR', 'SG'):
        ledger.reserve([{**c, 'review_pool': pool} for c in cards()],
                       expected_head=ledger.snapshot()['head_sha256'])
    assert CardLedger(path).snapshot()['issued_total'] == 60
    assert ledger.snapshot()['by_pool']['SG']['sentinel'] == 10
    with pytest.raises(InputBoundaryError):
        ledger.reserve([{**cards('MTM')[0], 'review_pool': 'SG'}], expected_head=ledger.snapshot()['head_sha256'])


def test_amendment_cannot_refund_existing_cards_or_repeat(tmp_path):
    ledger = CardLedger.create(tmp_path / 'cards')
    ledger.reserve(cards()[:1], expected_head=ledger.snapshot()['head_sha256'])
    with pytest.raises(InputBoundaryError):
        ledger.adopt_paper1_allocation(expected_head=ledger.snapshot()['head_sha256'])
    other = CardLedger.create(tmp_path / 'other')
    other.adopt_paper1_allocation(expected_head=other.snapshot()['head_sha256'])
    with pytest.raises(InputBoundaryError):
        other.adopt_paper1_allocation(expected_head=other.snapshot()['head_sha256'])
