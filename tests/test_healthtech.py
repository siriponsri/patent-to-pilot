"""Hand-computable HealthTech integrity, budget and incomplete-judgment controls."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest
from pydantic import ValidationError

from patent_to_pilot.healthtech.contracts import (AcquisitionBudget, DeviceQuery, EvidenceItem,
    PatentCandidate, canonical_patent_id, content_hash)
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier
from patent_to_pilot.healthtech.provenance import check_evidence
from patent_to_pilot.healthtech.sources import field_evidence, normalize_510k_record, source_payload
from patent_to_pilot.evaluation.healthtech.retrieval import evaluate_known_links, shared_reference_groups

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def example():
    return json.loads((ROOT/'examples/healthtech/synthetic-device/input.json').read_text(encoding='utf-8'))


def evaluate(**kwargs):
    defaults=dict(expected_query_ids=['a','b'],references={'a':['US000001A1','US000002A1'],'b':['US000003A1']},
        predictions={'a':['US-000001-A1','US000001A1','US000002A1']},universe=['US000001A1','US000002A1','US000003A1'],k=2)
    return evaluate_known_links(**(defaults|kwargs))


def test_known_recall_deduplicates_before_cutoff_and_keeps_missing_failure():
    result=evaluate()
    assert result['macro_known_link_recall']==.5
    assert result['micro_known_link_recall']==pytest.approx(2/3)
    assert result['failed_query_ids']==['b']
    assert result['per_query'][0]['hits']==2


def test_unjudged_unknown_ids_consume_rank_but_never_become_negatives():
    result=evaluate(predictions={'a':['nonsense','US000001A1','US000002A1'],'b':[]},k=2)
    assert result['macro_known_link_recall']==.25
    assert result['per_query'][0]['unknown_ids_at_k']==['UNKNOWN:nonsense']
    assert 'precision' not in result and 'f1' not in result


def test_unjudged_query_not_a_negative_and_declared_failure_zeroes_partial_hits():
    result=evaluate(expected_query_ids=['a','b','c'],references={'a':['US000001A1'],'b':['US000003A1']},
        predictions={'a':['US000001A1'],'b':['US000003A1'],'c':[]},statuses={'a':'completed','b':'failed'})
    assert result['macro_known_link_recall']==.5
    assert result['excluded_unjudged_query_ids']==['c']
    assert result['per_query'][1]['hits']==0


@pytest.mark.parametrize('change',[
    {'expected_query_ids':['a','a']}, {'references':{'a':['US999999A1']}},
    {'predictions':{'leaked':[]}}, {'k':0}, {'k':True}, {'references':{}},
    {'universe':['US000001A1','US-000001-A1']},
])
def test_invalid_evaluation_contract_rejected(change):
    with pytest.raises(ValueError):evaluate(**change)


def test_normalization_preserves_kind_leading_zeros_and_jurisdiction():
    assert canonical_patent_id('us-000001-a1')=='US000001A1'
    assert canonical_patent_id('US000001B2')!='US000001A1'
    assert canonical_patent_id('EP000001A1')!='US000001A1'
    with pytest.raises(ValueError):canonical_patent_id('000001')


def test_shared_patent_and_family_groups_are_transitive():
    assert shared_reference_groups({'a':['US000001A1'],'b':['US000001A1','US000002A1'],
        'c':['US000003A1'],'d':['US000004A1']},families={'US000002A1':'F1','US000003A1':'F1'})==[['a','b','c'],['d']]


def test_end_to_end_is_offline_bounded_and_does_not_promote_candidates(example,monkeypatch):
    def denied(*a,**kw):pytest.fail('offline dossier tried network access')
    monkeypatch.setattr(socket,'create_connection',denied)
    monkeypatch.setattr(socket.socket,'connect',denied)
    data=DossierInput.model_validate(example)
    dossier,events,manifest=run_dossier(data,run_id='test',code_commit='test')
    assert len(dossier.candidates)==2
    assert all(c.association_status=='retrieved_candidate' for c in dossier.candidates)
    assert manifest.provider_calls==manifest.paid_cost_usd==0
    assert manifest.actual_search_calls==2
    assert manifest.actual_returned_candidates==2
    assert all(e.verification_status=='field_value_checked' for e in dossier.evidence)
    assert events[-1].stop_reason=='fixed_schedule_complete'
    assert 'SYNTHETIC' in export_markdown(dossier)
    assert dossier.model_validate_json(dossier.model_dump_json())==dossier


def test_zero_budget_dispatches_no_search(example):
    example['query']['acquisition_budget']['max_search_calls']=0
    dossier,events,manifest=run_dossier(DossierInput.model_validate(example),run_id='zero',code_commit='test')
    assert not dossier.candidates and manifest.actual_search_calls==0
    assert manifest.stop_reason=='budget_exhausted' and len(events)==1


def test_returned_candidate_cap_is_hard_even_across_repeated_queries(example):
    example['query']['acquisition_budget']['max_returned_candidates']=1
    _,events,manifest=run_dossier(DossierInput.model_validate(example),run_id='one',code_commit='test')
    assert manifest.actual_returned_candidates==1
    assert manifest.actual_search_calls==1
    assert events[-1].stop_reason=='budget_exhausted'


def test_search_failure_keeps_attempt_and_failure_status(example,monkeypatch):
    def fail(*a,**kw):raise RuntimeError('local fixture failure')
    monkeypatch.setattr('patent_to_pilot.healthtech.engine.FTSIndex.search',fail)
    _,events,manifest=run_dossier(DossierInput.model_validate(example),run_id='failed',code_commit='test')
    assert manifest.actual_search_calls==2
    assert manifest.failed_query_ids==[example['query']['query_id']]
    assert manifest.stop_reason=='run_failure'
    assert sum(bool(e.errors) for e in events)==2


@pytest.mark.parametrize('mode',['extra_gold','bad_hash','future_source','private','fake_public','evaluator_source','duplicate_patent'])
def test_runtime_rejects_leakage_and_false_source_claims(example,mode):
    if mode=='extra_gold':example['gold_links']=['US000001A1']
    if mode=='bad_hash':example['sources'][0]['payload']['device_name']='tampered'
    if mode=='future_source':example['query']['evidence_cutoff']='2000-01-01'
    if mode=='private':example['query']['brief']['data_class']='private'
    if mode=='fake_public':example['query']['brief']['data_class']='public'
    if mode=='evaluator_source':example['sources'][0]['source']['source_type']='benchmark_gold'
    if mode=='duplicate_patent':example['patents'].append(deepcopy(example['patents'][0]))
    with pytest.raises(ValidationError):DossierInput.model_validate(example)


def test_literal_span_and_field_checks_reject_semantic_promotion_and_type_coercion(example):
    data=DossierInput.model_validate(example);source=data.sources[0];item=data.evidence[0]
    with pytest.raises(ValueError):check_evidence(item.model_copy(update={'structured_value':False}),source)
    text=source_payload('text','abc def',uri='urn:synthetic:text',revision='v1',source_date=date(2026,10,27),
        jurisdiction='US',source_type='synthetic_record',license_note='authored fixture',synthetic=True)
    span=EvidenceItem(evidence_id='span',source_id='text',source_version='v1',payload_hash=text.source.sha256,
        locator='chars:4:7',quoted_span='def',evidence_kind='source_fact',statement='literal text',support_basis='exact text only',
        jurisdiction='US',source_date=text.source_date,extraction_method='literal_span')
    assert check_evidence(span,text).verification_status=='exact_span_checked'
    with pytest.raises(ValueError):check_evidence(span.model_copy(update={'locator':'chars:0:3'}),text)
    with pytest.raises(ValidationError):EvidenceItem.model_validate(span.model_dump()|{'evidence_kind':'system_inference','verification_status':'exact_span_checked'})


def test_fda_normalizer_preserves_codes_without_asserting_approval():
    source=normalize_510k_record({'k_number':'K000001','device_name':'SYNTHETIC','decision_code':'SESE',
        'openfda':{'gmdn_name':'restricted enrichment'},'labeler_duns_number':'restricted'},
        source_id='fda',snapshot_revision='fixture-v1',retrieved_date=date(2026,10,27),synthetic=True)
    assert source.payload['decision_code']=='SESE' and 'approval' not in source.payload
    assert 'openfda' not in source.payload and 'labeler_duns_number' not in source.payload
    assert source.source.uri.startswith('urn:synthetic:')
    assert check_evidence(field_evidence(source,'device_name','name'),source).verification_status=='field_value_checked'
    with pytest.raises(ValueError):normalize_510k_record({'k_number':1,'device_name':'x'},source_id='fda',snapshot_revision='v1',retrieved_date=date.today())


def test_disclosure_status_requires_independent_source_evidence(example):
    data=DossierInput.model_validate(example)
    dossier,_,_=run_dossier(data,run_id='test',code_commit='test')
    candidate=dossier.candidates[0]
    with pytest.raises(ValidationError):PatentCandidate.model_validate(candidate.model_dump()|{'association_status':'disclosed_link'})
    forged=candidate.model_copy(update={'association_status':'disclosed_link','disclosure_evidence_id':dossier.evidence[0].evidence_id})
    with pytest.raises(ValidationError):type(dossier).model_validate(dossier.model_dump()|{'candidates':[forged.model_dump()]})


def test_export_escapes_literal_markup_and_does_not_overwrite_existing_directory(example,tmp_path):
    example['query']['device_id_raw']='<script>alert(1)</script>|x'
    dossier,_,_=run_dossier(DossierInput.model_validate(example),run_id='test',code_commit='test')
    assert '<script>' not in export_markdown(dossier)
    script=ROOT/'scripts/healthtech/run_dossier.py'
    result=subprocess.run([sys.executable,'-B',str(script),str(ROOT/'examples/healthtech/synthetic-device/input.json'),str(tmp_path)],capture_output=True,text=True)
    assert result.returncode==2 and 'output already exists' in result.stderr
