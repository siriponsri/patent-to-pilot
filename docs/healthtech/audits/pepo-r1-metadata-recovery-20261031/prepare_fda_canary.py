"""Prepare only the reviewed, hash-pinned FDA factual subset; never dispatch.

Inputs and output pack/messages belong in private storage. The small manifest
may be retained with the audit. This is a regulatory-fact canary, not a patent
association benchmark or an authorization to spend.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from patent_to_pilot.healthtech.generation_payload import build_generation_messages, build_rights_cleared_paired_payload, sha256_json

INPUT_SHA='2594295d4bbc82c7707365e4a0f372be5c0da6b88264a7c1bd76df5f22f0043a'
SOURCES={
 'openfda-pma-p100009-base':'613e6d9c72da134861ce895ce3dff548abb234376fe6b0b4ee35c4782bcb8c43',
 'openfda-pma-p240042-base':'99c35a6a724b554edd7c0c9d755f4f5a63fad4dd3c768e9d3cd22e58e26201b9',
 'openfda-pma-p230007-base':'1d50de03827b92fba33de7871d487a1b94104000d3f76bff6af21a26e44b5ad5',
}
FIELDS=['pma_number','trade_name','applicant']
BASIS='https://open.fda.gov/terms/'

def prepare(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA:
        raise ValueError('Input differs from reviewed source pack')
    original=json.loads(raw)
    assert sha256_json({k:v for k,v in original.items() if k!='pack_sha256'})==original['pack_sha256']
    pack=deepcopy(original)
    pack.pop('pack_sha256',None)
    pack['purpose']='FDA factual canary only; no device-patent comparison'
    pack['status']='PREPARED_OFFLINE_NOT_EXECUTED'
    pack['captured_at_utc']=datetime.now(timezone.utc).isoformat()
    pack['parent_pack_sha256']=original['pack_sha256']
    pack['evidence_policy']={'fields':FIELDS,'source_basis':BASIS,'excluded':'all patents, disclosures, generic/GMDN terms, raw text and evaluator material'}
    pack['prompt_contract']['system_instructions']=[
      'Extract only the supplied FDA structured facts. Data provided by the U.S. Food and Drug Administration (https://open.fda.gov).',
      'Keep exact record IDs and source locators. Do not infer clinical suitability, approval status, FTO, patent associations or investment value.',
      'Return JSON only. Omitted evidence is unresolved, never a negative finding.'
    ]
    for case in pack['cases']:
        source=next(s for s in case['sources'] if s['source_id'] in SOURCES)
        assert source['sha256']==SOURCES[source['source_id']]
        source.update(basis_url=BASIS,clause_locator='Data Rights and Usage; Attribution',displayable_fields=FIELDS)
        case['sources']=[source]
        case['evidence']=[e for e in case['evidence'] if e['source_id']==source['source_id'] and e['structured_field'] in FIELDS]
        assert len(case['evidence'])==3
        case['evidence_order']=[e['evidence_id'] for e in case['evidence']]
        case['candidates']=[]
        old_query=case['query']
        case['query']={k:old_query.get(k) for k in ('query_id','device_id_canonical','device_id_raw','jurisdiction','evidence_cutoff')}
        case['query'].update(selected_comparator_source_id=source['source_id'],brief='Summarize the reviewed FDA facts.',technical_description='',features_of_interest=[],user_questions=[])
        case['unresolved_items']=[]
        case['remote_transfer_review']={
          'purpose':'ht-o3-generation','provider':'openrouter','route':'deepinfra',
          'message_sha256':sha256_json(build_generation_messages(pack,case)),
          'basis_reference':'openFDA-CC0-structured-PMA-facts-20261031-no-GMDN-no-third-party-documents',
        }
    pack['pack_sha256']=sha256_json(pack)
    payload=build_rights_cleared_paired_payload(pack,provider='openrouter',model='qwen/qwen3-32b',route='deepinfra',max_output_tokens=512)
    return pack,payload

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--private-output',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    args=p.parse_args()
    if args.private_output.exists() or args.manifest.exists():
        raise SystemExit('Output already exists')
    pack,payload=prepare(args.input)
    args.private_output.mkdir(parents=True,exist_ok=False)
    for name,value in [('evidence-pack.json',pack),('exact-messages.json',payload['cases'])]:
        with (args.private_output/name).open('x',encoding='utf-8') as handle:json.dump(value,handle,indent=2,ensure_ascii=False)
    manifest={
      'status':'PASS_RIGHTS_PROJECTION_OFFLINE_ONLY','condition':'FDA_FACTUAL_CANARY_NOT_DEVICE_PATENT_STUDY',
      'input_file_sha256':INPUT_SHA,'prepared_pack_sha256':pack['pack_sha256'],
      'fields':FIELDS,'cases':len(pack['cases']),'evidence_rows':sum(len(c['evidence']) for c in pack['cases']),
      'basis_url':BASIS,'basis_checked_utc':'2026-10-31','source_rights':'CC0 public structured facts; no GMDN or third-party works',
      'manifest':payload['manifest'],'provider_calls':0,'gpu_jobs':0,
      'fresh_pricing_and_route':'NOT_CHECKED_NOT_DISPATCH_READY','paired_local_outputs':'NOT_RUN_NEW_FILTERED_PACK_REQUIRES_NEW_LOCAL_RUN',
    }
    with args.manifest.open('x',encoding='utf-8') as handle:json.dump(manifest,handle,indent=2,ensure_ascii=False)
    print(json.dumps({'status':manifest['status'],'cases':3,'evidence_rows':9,'pack_sha256':pack['pack_sha256']}))

if __name__=='__main__':main()
