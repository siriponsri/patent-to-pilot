"""Bounded signature accounting; candidates are not fidelity-approved edges.

No corpus reader or dispatch entrypoint: full corpus use needs separate approval.
Pair incidence counts can repeat a family pair across distinct keys.
"""
from collections import Counter, defaultdict
from .mtm_runtime import InputBoundaryError, identifier


class SignatureCensus:
    def __init__(self, *, max_families=45336, max_records=362688, hub_threshold=100):
        for value in (max_families, max_records, hub_threshold):
            if type(value) is not int or value < 1:
                raise InputBoundaryError('invalid census bound')
        self.max_families, self.max_records = max_families, max_records
        self.hub_threshold = hub_threshold
        self.families, self.relations = set(), set()
        self.postings = defaultdict(set)
        self.key_records = Counter()
        self.records = 0

    def add_family(self, family_id, records):
        identifier(family_id)
        if family_id in self.families:
            raise InputBoundaryError('duplicate census family')
        if type(records) is not list:
            raise InputBoundaryError('census records must be bounded list')
        if len(self.families) >= self.max_families or self.records + len(records) > self.max_records:
            raise InputBoundaryError('census resource cap exceeded')
        pending = []
        for record in records:
            if type(record) is not dict or not {'family_id', 'alias_key', 'relation_id'} <= set(record):
                raise InputBoundaryError('invalid census record')
            key, rid = record['alias_key'], record['relation_id']
            identifier(key); identifier(rid)
            if record['family_id'] != family_id or rid in self.relations or any(rid == r for _, r in pending):
                raise InputBoundaryError('census identity mismatch or duplicate relation')
            pending.append((key, rid))
        # Validate the complete family before mutating any state.
        self.families.add(family_id)
        for key, rid in pending:
            self.postings[key].add(family_id)
            self.key_records[key] += 1
            self.relations.add(rid)
        self.records += len(records)

    def summary(self):
        frequencies = Counter(len(v) for v in self.postings.values())
        return {'status': 'SIGNATURE_COUNTS_ONLY_NOT_FIDELITY',
                'families_seen': len(self.families), 'records': self.records,
                'keys': len(self.postings), 'family_frequency_histogram': dict(sorted(frequencies.items())),
                'cross_family_pair_key_incidences': sum(n * (n - 1) // 2 * count for n, count in frequencies.items()),
                'unique_family_pairs': 'NOT_COMPUTED_MAY_REPEAT_ACROSS_KEYS',
                'hub_keys': sum(count for n, count in frequencies.items() if n > self.hub_threshold),
                'hub_threshold_strictly_greater_than': self.hub_threshold,
                'max_families_per_key': max(frequencies, default=0),
                'max_records_per_key': max(self.key_records.values(), default=0),
                'accepted_edges': 0, 'model_calls': 0}


def posting_join(postings, seed_families):
    """One shared-key expansion, excluding seeds. Independent control for graph.

    Identical incidence data and one hop imply identical candidate sets. This
    does not implement a new scorer or establish relation compatibility.
    """
    seeds = set(seed_families)
    return set().union(*(set(families) for families in postings.values()
                         if seeds.intersection(families))) - seeds


def bipartite_one_hop(postings, seed_families):
    """Explicit family -> key -> family traversal for equivalence fixtures."""
    seeds = set(seed_families)
    reverse = defaultdict(set)
    for key, families in postings.items():
        for family in families:
            reverse[family].add(key)
    visited_keys = set()
    for seed in seeds:
        visited_keys.update(reverse[seed])
    candidates = set()
    for key in visited_keys:
        candidates.update(postings[key])
    return candidates - seeds
