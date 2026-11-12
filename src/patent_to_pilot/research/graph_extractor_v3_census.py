"""Extractor v3: corpus postings + query census + frozen feasibility gate (GRAPH-EXTRACTOR-V3-20261112)."""
import json
from .sg_relations_v3 import extract_family_v3, VERSION
from .graph_query_census import census

GATE = {'G1_min_query_share_with_usable_key': 0.5, 'G2_min_pilot_queries_with_structure': 10, 'G3_min_shared_keys': 1000}


def v3_query_keys(qid, text):
    return {r['alias_key'] for r in extract_family_v3({'id': qid, 'title': '', 'abstract': text, 'claims': ''},
                                                     fields=('abstract',))['records']}


def build_postings(corpus_lines):
    postings, families, records = {}, 0, 0
    for line in corpus_lines:
        if not line.strip(): continue
        row = json.loads(line); families += 1
        for r in extract_family_v3({k: row[k] for k in ('id', 'title', 'abstract', 'claims')})['records']:
            records += 1
            postings.setdefault(r['alias_key'], {}).setdefault(row['id'], r['relation_id'])
    degrees = sorted((len(v) for v in postings.values()), reverse=True)
    return postings, {'families': families, 'records': records, 'keys': len(postings),
                      'shared_keys': sum(d >= 2 for d in degrees), 'hub_keys_over_100': sum(d > 100 for d in degrees),
                      'max_key_degree': degrees[0] if degrees else 0}


def evaluate(corpus_lines, queries):
    postings, corpus = build_postings(corpus_lines)
    result = census(queries, postings, query_keys=v3_query_keys)
    share = result['all']['with_structure'] / result['all']['queries']
    gates = {'G1': share >= GATE['G1_min_query_share_with_usable_key'],
             'G2': result['pilot']['with_structure'] >= GATE['G2_min_pilot_queries_with_structure'],
             'G3': corpus['shared_keys'] >= GATE['G3_min_shared_keys']}
    result.update(extractor=VERSION, corpus=corpus, query_share_with_usable_key=share, gate=GATE,
                  gate_results=gates, gate_status='PASS' if all(gates.values()) else 'FAIL')
    return result, postings
