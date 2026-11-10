"""Label-free prospective corpus sample; no extraction or retrieval scores."""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields, identifier

SALT = 'ptp-sg-corpus-stratified-v1-20261110'


def corpus_sample(metadata):
    """100 records:25 per rank-based raw-TAC character-length quartile.

    Ties on length use immutable IDs. Within each stratum hash ordering fixes
    membership. All sources remain eligible, including empty/partial texts.
    Small synthetic populations return all sources, never duplicate them.
    """
    records, seen = [], set()
    for row in metadata:
        exact_fields(row, {'id', 'source_chars'})
        identifier(row['id'])
        if row['id'] in seen or type(row['source_chars']) is not int or row['source_chars'] < 0:
            raise InputBoundaryError('invalid corpus sampling population')
        seen.add(row['id'])
        records.append(dict(row))
    if not records:
        raise InputBoundaryError('empty corpus sampling population')
    records.sort(key=lambda r: (r['source_chars'], r['id']))
    strata = [[] for _ in range(4)]
    for rank, row in enumerate(records):
        stratum = min(3, 4 * rank // len(records))
        strata[stratum].append({**row, 'stratum': stratum,
            'sampling_sha256': hashlib.sha256(f"{SALT}|{row['id']}".encode()).hexdigest()})
    sample = []
    for rows in strata:
        sample.extend(sorted(rows, key=lambda r: (r['sampling_sha256'], r['id']))[:25])
    return {'format': 'ptp-sg-corpus-sample-v1', 'salt': SALT, 'population': len(records),
            'stratum_sizes': [len(rows) for rows in strata], 'sample': sample,
            'uses_qrels': False, 'uses_retrieval_scores': False}
