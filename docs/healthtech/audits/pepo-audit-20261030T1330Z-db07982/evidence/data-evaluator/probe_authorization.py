"""Authored local-only approval-state probe; no real data or external actions."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode=True
repo=Path(r'C:\Users\User\Desktop\myProject\patent-to-pilot')
out=Path(__file__).resolve().parent/'authored-authorization-probe'
out.mkdir(exist_ok=False)
sys.path[:0]=[str(repo/'src'),str(repo)]
spec=importlib.util.spec_from_file_location('fixture',repo/'tests/test_healthtech_source_acquisition.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from patent_to_pilot.evaluation.healthtech.source_acquisition import source_snapshot_sha256,stage_authorized_semantic_source
from patent_to_pilot.evaluation.healthtech.source_authorization import validate_semantic_source_authorization
source=out/'authored-source';source.mkdir()
(source/'raw.jsonl').write_text('raw-data')
(source/'normalized.jsonl').write_text('norm')
manifest=mod._manifest(source_snapshot_sha256(source),expected_bytes=12)
manifest['status']='DRAFT_SOURCE_AUTHORIZATION'
validation=validate_semantic_source_authorization(manifest)
receipt=stage_authorized_semantic_source(source,out/'destination',manifest,
    authorization_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),receipt_path=out/'receipt.json')
result={'snapshot':'db0798276e3158b04131b4e910abc0a11511e94c','input_status':manifest['status'],
    'validation_status':validation['status'],'validation_authorization_status':validation['authorization_status'],
    'stage_status':receipt['status'],'completed_files':receipt['completed_files'],
    'staged_bytes':12,'real_sources_used':False,'provider_calls':0,'network_calls':0,'model_calls':0,
    'note':'Proves DRAFT is accepted by local staging helper; this is not authority to access any real source. CLI integration policy and caller authority must remain separate.'}
(out.parent/'authorization-probe-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
