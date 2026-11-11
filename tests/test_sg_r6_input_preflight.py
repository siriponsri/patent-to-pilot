import pytest
from test_sg_r6_manifest import fixture
from patent_to_pilot.research.sg_r6_manifest import build_manifest,preflight_graph
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('risks',[0,20,21])
def test_complete114_preflight_retains_denominator_and_stop_rule(risks):
    rows,s,a=fixture();manifest=build_manifest(rows,s,a);seen=[];saved=[]
    def count(messages):seen.append(1);return 8193 if len(seen)<=risks else 10
    result=preflight_graph(manifest,count_tokens=count,write_request=lambda i,p:saved.append(i),check_admission=lambda i:None)
    assert len(seen)==len(saved)==114 and result['risk_units']==risks
    assert result['source_coverage_units']==100 and result['source_abstentions']==86
    assert result['status']==('STOP_GRAPH_INPUT_RISK_CAP' if risks>20 else 'PASS_GRAPH_INPUT_ADMISSION_WITH_RISKS')
    assert result['model_calls']==0


def test_unexpected_builder_failure_is_not_input_risk(monkeypatch):
    import patent_to_pilot.research.sg_r6_manifest as module
    rows,s,a=fixture();manifest=build_manifest(rows,s,a)
    def bad(unit):raise InputBoundaryError('unexpected integrity bug')
    monkeypatch.setattr(module,'request',bad)
    with pytest.raises(InputBoundaryError):preflight_graph(manifest,count_tokens=lambda m:10,write_request=lambda i,p:None,check_admission=lambda i:None)
