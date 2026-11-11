import copy,json
import pytest
from test_r6_critic_calibration import reports
from test_r6_reference_runner import setup
from patent_to_pilot.research.r6_critic_calibration import fixtures
from patent_to_pilot.research.r7_calibration_runner import frozen_tasks,run_calibration
from patent_to_pilot.research.r6_reference_runner import encoded,sha
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def arguments(tmp_path,fault=None):
    rows=reports();tasks=frozen_tasks();_,base,calls=setup('calibration')
    target=next(i for i,f in enumerate(fixtures()) if f['expected']['kind']=='negative'
                and len(f['expected']['allowed_flags'])<7)
    if fault in ('unrelated','missing_finding'):
        value=json.loads(rows[target]['critic_text'])
        if fault=='missing_finding':value['findings']=[]
        else:
            extra=sorted(set(value['dimensions'])-set(fixtures()[target]['expected']['allowed_flags']))[0]
            value['dimensions'][extra]='unsupported'
            finding=copy.deepcopy(value['findings'][0]);finding['dimension']=extra
            value['findings'].append(finding)
        rows[target]['critic_text']=json.dumps(value)
    def invoke(stage,path,messages,schema):
        index=int(stage.split('-')[-1]);prepared=tasks[index]['prepared']
        assert messages==prepared['messages'] and messages!=prepared['original']['messages']
        assert schema==prepared['original']['schema']
        metrics=base(stage,path,messages,schema)
        record=json.loads((path/'generation.json').read_bytes())
        # Author a fixture response before the runner consumes it; no real output.
        record.update(text=rows[index]['critic_text'],response_sha256=sha(rows[index]['critic_text'].encode()))
        if fault=='execution_rejected' and index==target:record['status']='NO_EOS'
        (path/'generation.json').write_text(json.dumps(record))
        if fault=='reservation' and index==0:
            reservation=json.loads((path/'reservation.json').read_bytes())
            reservation['messages_sha256']=prepared['original']['messages_sha256']
            (path/'reservation.json').write_text(json.dumps(reservation))
        return metrics
    return dict(destination=tmp_path/'out',tasks_sha256=sha(encoded(tasks)),run_id='authored-r7',
                invoke=invoke,count_tokens=lambda m:10,check_admission=lambda i:None),calls


def test_unchanged_gold_can_qualify_exact_compact_execution(tmp_path):
    args,calls=arguments(tmp_path);result=run_calibration(**args)
    assert len(calls)==24 and result['status']=='AUTHORED_CALIBRATION_QUALIFIED'
    assert result['assessment']['execution_rejected_cases']==0
    assert not result['native_fidelity_proven']


@pytest.mark.parametrize('fault',['unrelated','missing_finding','execution_rejected'])
def test_one_semantic_contract_or_execution_error_prevents_qualification(tmp_path,fault):
    args,calls=arguments(tmp_path,fault);result=run_calibration(**args)
    assert len(calls)==24 and result['status']=='CALIBRATION_FAILED'
    if fault=='unrelated':assert result['assessment']['unrelated_dimension_flags']==1
    else:assert result['assessment']['execution_rejected_cases']==1


def test_original_wire_reservation_is_not_compact_execution_evidence(tmp_path):
    args,calls=arguments(tmp_path,'reservation')
    with pytest.raises(InputBoundaryError,match='reservation mismatch'):run_calibration(**args)
    assert len(calls)==1 and not (tmp_path/'out/calibration-assessment.json').exists()


def test_frozen_task_change_never_dispatches(tmp_path):
    args,calls=arguments(tmp_path);args['tasks_sha256']='0'*64
    with pytest.raises(InputBoundaryError):run_calibration(**args)
    assert not calls and not (tmp_path/'out').exists()
