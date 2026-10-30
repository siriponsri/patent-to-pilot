"""Offline application-budget scope counterexample; synthetic ledger costs only."""
import json
from pathlib import Path
import socket
import sys
sys.dont_write_bytecode=True
w=Path(__file__).resolve().parent
root=w/'snapshot'
sys.path[:0]=[str(root/'src'),str(root)]
def deny(*a,**k):raise RuntimeError('network forbidden')
socket.socket.connect=deny
socket.create_connection=deny
socket.getaddrinfo=deny
from patent_to_pilot.providers.round1 import Round1ProjectBudget,build_round1_policy
from patent_to_pilot.healthtech.b4_live import B4Pricing,B4ProviderSelector

common={'model_provider_map':{'audit-model':'audit-provider'},'pricing_snapshot_sha256':'a'*64,'pricing_snapshot_utc':'2026-10-30T00:00:00Z'}
rows=[]
for label in ['ledger-A','ledger-B']:
    b=Round1ProjectBudget(w/f'{label}.sqlite3',**common)
    for phase,amount in [('paired_pilot','5.40'),('robustness','1.20'),('canary','0.40')]:
        aid=f'{label}-{phase}'
        b.reserve(attempt_id=aid,phase=phase,model='audit-model',provider='audit-provider',payload_sha256='b'*64,
                  upper_bound_usd=amount,bound_verified=True,data_class='synthetic')
        b.settle(aid,amount)
    s=b.snapshot()
    rows.append({'ledger':label,'authorization_id':s['authorization_id'],'simulated_committed_nano_usd':s['committed_nano_usd'],
                 'breach':s['breach'],'dispatch_blocked':s['dispatch_blocked']})
    b.close()

b=Round1ProjectBudget(w/'pricing-probe.sqlite3',**common)
policy=build_round1_policy(**common)
pricing=B4Pricing(model='audit-model',upstream_provider='different-provider',snapshot_sha256='c'*64,
                  snapshot_utc='1900-01-01T00:00:00Z',prompt_usd_per_million='0.00000001',
                  completion_usd_per_million='0.00000001',max_price_prompt=999,max_price_completion=999)
factory_calls=[]
def transport_factory():
    factory_calls.append(True)
    raise AssertionError('no transport may be constructed by this probe')
selector=B4ProviderSelector(budget=b,policy=policy,pricing=pricing,run_id='audit',query_id='q',phase='canary',
    transport_factory=transport_factory,live_enabled=False,visible_sources=[],transfer_manifest=None)
out={'snapshot':'db0798276e3158b04131b4e910abc0a11511e94c','kind':'authored offline simulation; no actual costs',
     'separate_ledgers_same_authorization':rows,'aggregate_simulated_committed_usd':sum(x['simulated_committed_nano_usd'] for x in rows)/1e9,
     'single_authorization_total_usd':8,'canonical_path_enforcement':'not found in actual CLI/library',
     'pricing_selector_constructor_accepted_mismatched_snapshot_time_provider':True,
     'pricing_probe_scope':'constructor accepted; no complete/select/transport call executed',
     'policy_snapshot_hash':policy['pricing_snapshot_sha256'],'pricing_snapshot_hash':pricing.snapshot_sha256,
     'policy_provider':policy['models']['audit-model'],'pricing_provider':pricing.upstream_provider,
     'transport_factory_calls':len(factory_calls),'network_calls':0,'provider_calls':0,'paid_usd':0}
(w/'budget-scope-probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
b.close()
