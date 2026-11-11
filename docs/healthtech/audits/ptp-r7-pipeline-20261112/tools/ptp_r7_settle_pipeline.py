from pathlib import Path
import json
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');A=R/'docs/healthtech/audits/ptp-r7-pipeline-20261112'
v=json.loads((A/'terminal-observation.json').read_bytes());r=v['receipt'];state=v['container_state']
assert state['ExitCode']==0 and state['Pid']==0 and not state['Running'] and not state['OOMKilled']
assert r['status']=='PASS_AUTHORED_FULL_CALIBRATION_PIPELINE' and r['authored_backend_invocations']==31
assert r['real_model_calls']==0 and r['gpu_seconds']==0 and all(row['pass'] for row in r['bundle_fixture_results'])
L=R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
d=json.loads(L.read_bytes());s=d['r6_phase0_cpu'];j=s['jobs']['r7-pipeline-fixture'];r7=d['r7_cpu']
assert j['status']=='STAGED' and s['remote_cpu_reserved_seconds']==r7['reserved_seconds']==1200
charge=r['cpu_seconds']+v['terminal']['controller_cpu_seconds']
assert 0<=charge<=1200
s['remote_cpu_charged_seconds']+=charge;s['remote_cpu_reserved_seconds']=0
r7['measured_seconds']+=charge;r7['reserved_seconds']=0
j.update(status='TERMINAL_PASS_AUTHORED',cpu_seconds=charge,model_calls=0,gpu_seconds=0)
# Explicit zero-GPU observation for the intervening Graph CPU admission, needed
# by the new append-only CPU journal synchronizer. No scientific result changes.
assert d['graph_compact_v2_input']['GPU_seconds']==0
s['jobs']['graph-compact-input']['gpu_seconds']=0
L.write_text(json.dumps(d,indent=2)+'\n')
summary={'status':r['status'],'real_model_calls':0,'gpu_seconds':0,'authored_backend_invocations':31,
 'actual_grammar_tokens_checked':r['actual_grammar_tokens_checked'],'whole_wall_seconds':v['terminal']['whole_wall_seconds'],
 'charged_cpu_seconds':charge,'worker_peak_rss_bytes':r['worker_peak_rss_bytes'],
 'bundle_fixture_results':r['bundle_fixture_results'],'mocked_boundaries':r['mocked_boundaries'],
 'actual_boundaries':r['actual_boundaries'],'tasks_sha256':r['tasks_sha256'],
 'semantic_result':'Expected all-supported authored calibration failure; not an observed model outcome',
 'qualification_limits':'R7 calibration compact path qualified; additional bundle cases exercise unchanged R6 bundle only. Authored CPU doubles do not prove GPU, native fidelity or scientific success.',
 'R7_CPU_total_seconds':r7['conservative_charged_seconds']+r7['measured_seconds']}
with (A/'pipeline-fixture-summary.json').open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary))
