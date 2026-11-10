import hashlib
import json

import numpy as np
import pytest

from patent_to_pilot.research import sacr_factorial


def legacy(families, owner, passages):
    rows = [(p, families[int(o)]) for p, o in zip(passages, owner, strict=True)]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


@pytest.mark.parametrize('families,owner,passages', [
    (['family'], [0], ['passage']),
    (['b', 'a'], [1, 0, 1], ['p3', 'p1', 'p2']),
    (['ไทย', '🧪'], [0, 1], ['ข้อความ', 'é']),
    (['a"b', 'c\\d'], [1, 0], ['line\nbreak', '\t\x00']),
    (['unused'], [], []),
])
def test_exact_legacy_json_bytes(families, owner, passages):
    owner = np.array(owner, dtype=np.int64)
    assert sacr_factorial.passage_order_digest(families, owner, passages) == legacy(families, owner, passages)


@pytest.mark.parametrize('count', [4096, 4097, 8192, 10000])
def test_large_order_does_not_hash_one_large_serialization(monkeypatch, count):
    families = ['family']
    owner = np.zeros(count, dtype=np.int64)
    passages = [f'p{i}' for i in range(len(owner))]
    expected = legacy(families, owner, passages)
    original = hashlib.sha256
    sizes = []
    class Tracked:
        def __init__(self, raw):
            sizes.append(len(raw))
            self.hash = original(raw)

        def update(self, raw):
            sizes.append(len(raw))
            self.hash.update(raw)

        def hexdigest(self):
            return self.hash.hexdigest()
    monkeypatch.setattr(sacr_factorial.hashlib, 'sha256', Tracked)
    assert sacr_factorial.passage_order_digest(families, owner, passages) == expected
    assert max(sizes) < 100000
    assert len(sizes) == 2 * ((count + 4095) // 4096) + 1


@pytest.mark.parametrize('owner', [[-1], [1], [0, 0]])
def test_invalid_ownership_still_refused(owner):
    with pytest.raises(ValueError):
        sacr_factorial.passage_order_digest(['family'], np.array(owner), ['p'])
