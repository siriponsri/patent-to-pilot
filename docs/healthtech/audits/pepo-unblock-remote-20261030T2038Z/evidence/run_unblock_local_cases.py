"""Bounded real local ONNX exercise; no network/provider or remote execution."""
from pathlib import Path
import hashlib
import json
import os
import socket
import sys
import time

REPAIR=Path(r'C:\Users\User\Desktop\myProject\_worktrees\patent-to-pilot-pepo-unblock-20261030')
MAIN=Path(r'C:\Users\User\Desktop\myProject\patent-to-pilot')
OUTPUT=Path(r'C:\Users\User\AppData\Local\Temp\pepo-unblock-local-patents-20261030T2038Z')
sys.dont_write_bytecode=True
sys.path[:0]=[str(REPAIR/'src'),str(REPAIR)]
network=[]
def deny(*args,**kwargs):
    network.append('attempt')
    raise RuntimeError('local run: network forbidden')
socket.create_connection=deny
socket.getaddrinfo=deny
socket.socket.connect=deny
socket.socket.connect_ex=deny
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=Path(os.fsdecode(args[0])).resolve()
        if any(part in path.parts for part in ('.ssh','.aws')) or path.name.startswith('.env') and path.name!='.env.example':
            raise RuntimeError('local run: credential/config reading forbidden')
sys.addaudithook(audit)

import numpy as np
import onnxruntime as ort
from unittest.mock import patch
from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs, promote_disclosed_links
from patent_to_pilot.healthtech.engine import run_dossier, serialize_dossier, export_markdown
from patent_to_pilot.healthtech.history import save_version, append_user_edits, select_version, source_view
from patent_to_pilot.healthtech.rights import RightsBoundaryError
from patent_to_pilot.evaluation.healthtech.local_retrieval import DenseEncoder
from patent_to_pilot.evaluation.healthtech.vector_artifacts import export_runtime_text, encode_vector_shards, load_vector_bundle, PrecomputedVectorRetriever, sha256_file
from scripts.healthtech.encode_vector_shards import build_model_binding

assert not OUTPUT.exists(), 'Use a fresh output; do not overwrite a prior run'
OUTPUT.mkdir()
start=time.monotonic()
cohort=MAIN/'results/healthtech/ht-public-cohort-20261029-frozen-r2-typed'
cases=build_abbott_case_inputs(cohort)
assert len(cases)==3
patents=next(iter(cases.values())).patents
assert len(patents)==41
runtime=OUTPUT/'patents.jsonl'
export=export_runtime_text(
    [{'item_id':p.patent_id,'document_id':p.patent_id,'text':p.source.payload,'source_id':p.source.source.source_id,'source_revision':p.source.source.version_label} for p in patents],
    runtime, dataset_id='abbott-patent-publications', source_revision=sha256_file(cohort/'manifest.json'), representation='existing-normalized-patent-text-v1',
)
model=MAIN/'data/raw/healthtech/models/sentence-transformers-all-MiniLM-L6-v2/onnx/model_quint8_avx2.onnx'
tokenizer=model.parent.parent/'tokenizer.json'
binding=build_model_binding(model,tokenizer,model_id='sentence-transformers/all-MiniLM-L6-v2',revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
assert binding['model_artifact']['sha256']=='b941bf19f1f1283680f449fa6a7336bb5600bdcd5f84d10ddc5cd72218a0fd21'
assert binding['tokenizer_artifact']['sha256']=='be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037'
options=ort.SessionOptions()
options.intra_op_num_threads=1
options.inter_op_num_threads=1
session=ort.InferenceSession
def single_thread(*args,**kwargs):
    kwargs['sess_options']=options
    return session(*args,**kwargs)
with patch.object(ort,'InferenceSession',single_thread):
    base=DenseEncoder(model_path=str(model),tokenizer_path=str(tokenizer),max_length=256)

class CountingEncoder:
    calls=0
    rows=0
    tokens=0
    def encode(self,texts):
        self.calls+=1
        self.rows+=len(texts)
        values,tokens=base.encode(texts)
        self.tokens+=tokens
        return values,tokens

encoder=CountingEncoder()
bundle_dir=OUTPUT/'vectors'
config={'representation':'mean_pool_l2_normalized','max_length':256,'dtype':'<f4','norm_policy':'l2','batch_size':4,'shard_size':20,'backend':'onnx_cpu_quantized_avx2','intra_op_threads':1}
try:
    encode_vector_shards(runtime,bundle_dir,encoder,model=binding,config=config,batch_size=4,shard_size=20,stop_after_shards=1)
except RuntimeError as exc:
    assert 'injected interruption' in str(exc)
first_calls=encoder.calls
manifest=encode_vector_shards(runtime,bundle_dir,encoder,model=binding,config=config,batch_size=4,shard_size=20)
document_calls=encoder.calls
assert encoder.rows==41, 'Resume must not re-encode completed rows'
bundle=load_vector_bundle(bundle_dir)
assert len(bundle.document_ids)==41 and bundle.dimension==384
prior=load_vector_bundle(Path(r'C:\Users\User\AppData\Local\Temp\ptp-runtime-canary-luna-20261030-2\bundle'))
assert len(prior.document_ids)==64

class CountingSearch(PrecomputedVectorRetriever):
    calls=0
    def search(self,*args,**kwargs):
        self.calls+=1
        return super().search(*args,**kwargs)

summary=[]
for query_id,data in sorted(cases.items()):
    provider=CountingSearch(bundle,query_encoder=encoder)
    dossier,events,run_manifest=run_dossier(data,run_id='pepo-local-'+query_id,code_commit='a0ec9ce+pepo-repair-working-diff',vector_search=provider)
    dossier=promote_disclosed_links(dossier,data)
    dense=sum('dense_cosine' in p.scores for p in dossier.candidates)
    assert provider.calls>0 and dense>0
    assert not any('vector_' in error for event in events for error in event.errors)
    out=OUTPUT/query_id
    out.mkdir()
    history=out/'history'
    save_version(history,dossier)
    append_user_edits(history,{'review-note':'Local vector integration check; remote job remains pending allocation.'},expected_parent_version=1)
    selected=select_version(history,2)
    viewed=source_view(selected,data.query.selected_comparator_source_id,purpose='local_research')
    assert viewed['payload']
    (out/'dossier-v2.json').write_text(json.dumps(serialize_dossier(selected),ensure_ascii=False,indent=2),encoding='utf-8')
    for language in ('en','th'):
        (out/f'dossier-v2.{language}.md').write_text(export_markdown(selected,language=language),encoding='utf-8')
    blocked=False
    try:
        serialize_dossier(selected,purpose='product_display')
    except RightsBoundaryError:
        blocked=True
    assert blocked, 'Local-only source rights must remain enforced'
    summary.append({'query_id':query_id,'patent_inputs':len(data.patents),'candidates':len(dossier.candidates),'dense_scored_candidates':dense,'dense_search_calls':provider.calls,'history_versions':[1,2],'selected_export_version':selected.version,'languages':['json','en','th'],'source_view':'PASS','external_projection':'BLOCKED_EXPECTED_LOCAL_ONLY','errors':[]})
result={
    'status':'PASS_REAL_LOCAL_PATENT_VECTORS_THREE_DOSSIERS_REMOTE_NOT_RUN',
    'execution_location':'Windows local CPU only; not dr-train/returned vectors',
    'base_revision':'a0ec9ceaf381ebbce6e6c340a8b420189eb8474c','output_local_storage':str(OUTPUT),
    'input_rows':41,'runtime_input_sha256':export['sha256'],'qrels_or_gold_exported':False,
    'model':binding,'config':config,'vector_manifest_sha256':sha256_file(bundle_dir/'manifest.json'),
    'vector_rows':len(bundle.document_ids),'dimension':384,'shards':len(manifest['shards']),
    'resume':{'first_shard_calls':first_calls,'completed_document_calls':document_calls,'encoded_document_rows_total':41,'no_completed_row_reencoding':True},
    'prior_luna_real_canary_import_rows':len(prior.document_ids),
    'cases':summary,'actual_local_neural_calls':encoder.calls,'actual_local_encoded_rows_including_queries':encoder.rows,'tokens':encoder.tokens,
    'elapsed_seconds':time.monotonic()-start,'network_attempts':len(network),'provider_calls':0,'api_cost_usd':0,
    'remote_connections':0,'remote_encoding':'NOT_RUN_ALLOCATION_UNRESOLVED','remote_transfer':'NOT_RUN',
    'limits':['Small Abbott local development corpus; no final quality/scientific/generalization claim','Not remote-produced or transferred vectors','Derived text/vectors/dossiers kept in permitted private local storage, not public audit artifacts'],
}
(Path(__file__).resolve().parent/'unblock-local-cases-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
