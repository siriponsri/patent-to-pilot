"""Scoped independent offline probes at db079827; no real model/provider execution."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode=True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
work=Path(__file__).resolve().parent
root=work/'snapshot'
sys.path[:0]=[str(root/'src'),str(root),str(root/'tests')]
network=[]
def deny(*a,**k):
    network.append(True)
    raise RuntimeError('offline audit: network forbidden')
socket.socket.connect=deny
socket.socket.connect_ex=deny
socket.create_connection=deny
socket.getaddrinfo=deny
from test_healthtech_repairs import _write_synthetic_abbott_cohort,_write_json
from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.engine import run_dossier,serialize_dossier,export_markdown

probe=work/'probe'
probe.mkdir(exist_ok=True)
cohort=_write_synthetic_abbott_cohort(probe)
rights=json.loads((root/'docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/rights-matrix.json').read_text())
for policy in rights['sources']:
    policy['intended_use']['product_display']='ALLOWED'
    policy['intended_use']['redistribution']='ALLOWED'
    policy['displayable_fields']=['trade_name'] if policy['source_id']=='openfda-pma-records' else []
rights_path=probe/'rights.json'
_write_json(rights_path,rights)
data=next(iter(build_abbott_case_inputs(cohort,rights_matrix_path=rights_path).values()))
dossier,_,_=run_dossier(data,run_id='independent-query-projection-probe',code_commit='db079827')
pma=next(s for s in dossier.sources if s.source.source_type=='regulatory_record')
projection={}
for purpose in ['product_display','redistribution']:
    external=serialize_dossier(dossier,purpose=purpose)
    projected_pma=next(s for s in external['sources'] if s['source']['source_id']==pma.source.source_id)
    projection[purpose]={
        'reviewed_fields':pma.rights.displayable_fields,
        'external_source_payload':projected_pma['payload'],
        'external_query_company_metadata':external['query']['company_metadata'],
        'company_source_id':external['query']['company_source_id'],
        'restricted_source_applicant_retained_in_query':external['query']['company_metadata'].get('applicant')==pma.payload['applicant'],
        'restricted_field_evidence_omitted':not any(e.get('structured_field')=='applicant' for e in external['evidence'])}
(work/'query-projection-probe.json').write_text(json.dumps(projection,indent=2),encoding='utf-8')

import pytest
os.chdir(root)
scope=['tests/test_healthtech_repairs.py','tests/test_healthtech_boundary_matrix.py',
       'tests/test_healthtech_round1_budget.py','tests/test_healthtech_b4_live.py']
code=pytest.main(['-q','-rs','-p','no:cacheprovider',*scope,'--basetemp',str(work/'pytest-temp'),
                  '--junitxml',str(work/'tests.xml')])
cases=ET.parse(work/'tests.xml').findall('.//testcase')
summary={'snapshot':'db0798276e3158b04131b4e910abc0a11511e94c','scope':scope,
    'total':len(cases),'failures':[c.attrib['name'] for c in cases if c.find('failure') is not None or c.find('error') is not None],
    'skips':[{'name':c.attrib['name'],'reason':c.find('skipped').attrib.get('message')} for c in cases if c.find('skipped') is not None],
    'pytest_exit_code':int(code),'network_attempts':len(network),'remote_provider_calls':0,'neural_model_calls':0,
    'query_projection_probe':projection}
summary['passed']=summary['total']-len(summary['failures'])-len(summary['skips'])
(work/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
sys.exit(code)
