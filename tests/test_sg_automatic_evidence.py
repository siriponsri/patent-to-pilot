from copy import deepcopy
import pytest
from patent_to_pilot.research.sg_automatic_evidence import bind_screened_relations, bind_path_witnesses
from patent_to_pilot.research.sg_relations_v2 import extract_family_v2
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixture():
    family = {'id': 'family-a', 'title': '', 'abstract': 'A pump is configured to reduce pressure when activated.', 'claims': ''}
    records = extract_family_v2(family)['records']
    assert len(records) == 1
    screens = {r['relation_id']: {'record_sha256': document_hash(r), 'terminal': 'completed', 'screening': 'screened'} for r in records}
    return family, records, screens


def test_source_bound_membership_has_traceable_witness():
    family, records, screens = fixture()
    graph = bind_screened_relations([family], records, screens)
    path = [('key', records[0]['alias_key']), ('family', family['id'])]
    assert bind_path_witnesses(path, graph)[0]['relation_ids'] == [records[0]['relation_id']]
    assert graph['semantic_certified'] is False


def test_changed_quote_is_integrity_failure_even_when_screened():
    family, records, screens = fixture()
    records[0]['source_span']['text'] = 'different text'
    screens[records[0]['relation_id']]['record_sha256'] = document_hash(records[0])
    with pytest.raises(InputBoundaryError):
        bind_screened_relations([family], records, screens)


def test_uncertain_edge_abstains_without_disappearing_from_counts():
    family, records, screens = fixture()
    screens[records[0]['relation_id']]['screening'] = 'uncertain'
    graph = bind_screened_relations([family], records, screens)
    assert graph['postings'] == {} and graph['screening_counts'] == {'uncertain': 1}


def test_missing_screen_and_unknown_execution_cannot_pass():
    family, records, screens = fixture()
    with pytest.raises(InputBoundaryError):
        bind_screened_relations([family], records, {})
    screens[records[0]['relation_id']]['terminal'] = 'unknown'
    with pytest.raises(InputBoundaryError):
        bind_screened_relations([family], records, screens)


def test_altered_path_cannot_claim_other_family_evidence():
    family, records, screens = fixture()
    graph = bind_screened_relations([family], records, screens)
    with pytest.raises(InputBoundaryError):
        bind_path_witnesses([('key', records[0]['alias_key']), ('family', 'foreign')], graph)
