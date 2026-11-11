from pathlib import Path
import json,hashlib
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
v=json.loads((A/'terminal-verification.json').read_bytes());diag=json.loads((A/'calibration-diagnosis.json').read_bytes())
f=json.loads((A/'final-state-verification.json').read_bytes());l=json.loads((A/'final-ledger.json').read_bytes())
d=json.loads((A/'dispatch/declaration.json').read_bytes())
assert all(not row['schema_errors'] for row in diag['rows']) and len(diag['rows'])==24
assert v['reason_counts']=={'VALID_CRITIC':21,'INVALID_EVALUATOR':3}
assert f['generation']==5 and f['active'] is None and not f['approved_gpu_occupied']
assert all(x['pid']==0 for x in f['terminal_containers'])
assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in d['files_sha256'].items())
assert json.loads((R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json').read_bytes())==l
assert len(f['attempts'])==2 and all(x['failure_axis']=='EVALUATOR_CALIBRATION' for x in f['attempts'])
s=json.loads((A/'reconciled-scope.json').read_bytes())
assert all(x['status']=='SETTLED' for x in s['reservations'])
assert s['stage_costs']['calibration']['calls']==48
assert all(not calls for stage,calls in s['stage_attempts'].items() if stage!='calibration')
cpu=l['r6_phase0_cpu'];r7=l['r7_cpu']
assert all(cpu[k]==0 for k in ['local_cpu_reserved_seconds','remote_cpu_reserved_seconds','gpu_reserved_seconds'])
assert r7['reserved_seconds']==0
cpu_total=sum(cpu[k] for k in ['cpu_prior_upper_bound_seconds','local_cpu_conservative_charged_seconds','local_cpu_measured_seconds','remote_cpu_charged_seconds'])
assert cpu_total<=28800 and r7['measured_seconds']+r7['conservative_charged_seconds']<=3600
summary={'status':'PASS_TERMINAL_COMPLETION_EVIDENCE','scientific_outcome':'CLOSED_CALIBRATION_FAILED',
 'exact_qualified_source_unchanged':True,'all24_schema_valid':True,'contract_valid':21,'contract_invalid':3,
 'all_calls_reconciled':True,'original_R6_failure_retained':True,'active':None,'journal_generation':5,
 'all_scope_reservations_settled':True,'downstream_attempt_registry_empty':True,
 'CPU_global_charged_seconds':cpu_total,'CPU_global_remaining_seconds':28800-cpu_total,
 'R7_CPU_charged_seconds':r7['measured_seconds']+r7['conservative_charged_seconds'],
 'GPU_remaining_seconds':l['gpu_remaining_seconds'],'fidelity_remaining_seconds':l['fidelity_generation_remaining_seconds'],
 'known_model_calls_cumulative_lower_bound':l['model_calls'],
 'evidence_sha256':{n:hashlib.sha256((A/n).read_bytes()).hexdigest() for n in ['terminal-verification.json',
 'calibration-diagnosis.json','final-state-verification.json','final-ledger.json','reconciliation.json']}}
with (A/'completion-checks.json').open('x') as stream:json.dump(summary,stream,indent=2)
print(json.dumps(summary))
