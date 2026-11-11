"""Pinned tokenizer + callback + EOS guard, authored cases only, no model."""
from pathlib import Path
import hashlib,json,resource,sys,time
sys.path.insert(0,'/code/src')


def main():
    start=time.monotonic();receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'cases':[],'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration mismatch')
        d=json.loads(raw)
        identity=json.loads(Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes())
        for name in ['tokenizer.json','tokenizer_config.json','config.json']:
            if hashlib.sha256((Path('/models/qwen3-8b')/name).read_bytes()).hexdigest()!=identity['files'][name]['sha256']:
                raise RuntimeError('tokenizer identity differs')
        import torch
        from transformers import AutoTokenizer
        from jsonschema import Draft202012Validator
        from lmformatenforcer import CharacterLevelParserConfig
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        from patent_to_pilot.research.sacr_alphabet import build_alphabet
        from patent_to_pilot.research.sacr_boundary_callback_v3 import build_boundary_callback
        from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
        from patent_to_pilot.research.sacr_grammar_qualification import fixture_matrix
        from patent_to_pilot.research.sacr_evidence_prompt_v5 import build_messages
        from patent_to_pilot.research.mtm_runtime import InputBoundaryError
        tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
        from copy import deepcopy
        from patent_to_pilot.research.literal_critic_contract_v1 import schema as critic_schema, messages as critic_messages
        from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
        source='A "valve" reduces pressure below 40 kPa.';qid='graph-critic-qualification'
        artifacts={'record':source}
        def build_messages(source,qid):return critic_messages(query_id=qid,source=source,artifacts=artifacts,criteria={},scope={'synthetic':True})
        schema=critic_schema(qid,source,artifacts)
        base={'query_id':qid,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
              'dimensions':{d:'supported' for d in DIMENSIONS},'findings':[]}
        risk=deepcopy(base);risk['dimensions']['roles_direction']='uncertain'
        risk['findings']=[{'dimension':'roles_direction','artifact':'record','source_quote':'"valve"',
                          'candidate_quote':'"valve"','reason':'Uncertain attachment.'}]
        bad=deepcopy(risk);bad['findings'][0]['literal_source_quote']=bad['findings'][0].pop('source_quote')
        bad_artifact=deepcopy(risk);bad_artifact['findings'][0]['artifact']='missing'
        matrix={'source':source,'query_id':qid,'cases':[{'name':name,'text':json.dumps(value,ensure_ascii=False),'expected':expected}
            for name,value,expected in [('supported',base,True),('uncertain-exact-quoted-finding',risk,True),
                                        ('prefixed-field-forbidden',bad,False),('unknown-artifact-forbidden',bad_artifact,False)]]}
        validator=Draft202012Validator(schema)
        prompt=tokenizer.apply_chat_template(build_messages(matrix['source'],matrix['query_id']),
            tokenize=True,add_generation_prompt=True,enable_thinking=False)
        if len(prompt)>8192:raise RuntimeError('prompt input cap')
        data=build_token_enforcer_tokenizer_data(tokenizer)
        receipt['diagnosed_token_10465']=data.tokenizer_tree.tokens_to_strs[10465]
        alphabet=build_alphabet(tokenizer,matrix['source'])
        settings=CharacterLevelParserConfig(alphabet=alphabet['alphabet'],max_consecutive_whitespaces=4096,
            force_json_field_order=False,max_json_array_length=4096)
        for case in matrix['cases']:
            case_start=time.monotonic()
            callback=build_boundary_callback(data,schema,settings,expected_source_sha256=d['lmfe_source_sha256'])
            guard=CompleteJsonEOSGuard(prefix_fn=callback,tokenizer=tokenizer,prompt_tokens=len(prompt),
                eos_token_ids=[151645,151643],validate=validator.validate)
            tokens=tokenizer.encode(case['text'],add_special_tokens=False);seq=list(prompt);accepted=True;reason='COMPLETE'
            for index,token in enumerate(tokens):
                try:allowed=guard(0,torch.tensor(seq,dtype=torch.long))
                except InputBoundaryError as error:
                    accepted=False;reason=str(error);break
                if token not in allowed:accepted=False;reason='TOKEN_NOT_ALLOWED';break
                seq.append(token)
            if accepted:
                try:accepted=bool(set(guard(0,torch.tensor(seq,dtype=torch.long))) & {151645,151643})
                except InputBoundaryError as error:accepted=False;reason=str(error)
            row={'case':case['name'],'expected':case['expected'],'accepted':accepted,
                 'matches':accepted==case['expected'],'tokens':len(tokens),'reason':reason,
                 'case_wall_seconds':time.monotonic()-case_start,
                 'boundary_token_count':callback.configuration_receipt['boundary_token_count'],
                 'boundary_trie_nodes':callback.configuration_receipt['boundary_trie_nodes'],
                 'boundary_build_seconds':callback.configuration_receipt['boundary_build_seconds']}
            receipt['cases'].append(row)
            with Path('/out/case-'+str(len(receipt['cases']))+'.json').open('x') as f:json.dump(row,f)
        receipt.update(status='PASS_TOKEN_CALLBACK_MATRIX' if all(r['matches'] for r in receipt['cases']) else 'FAIL_TOKEN_CALLBACK_MATRIX',
                       input_tokens=len(prompt),semantic_fidelity='NOT_ASSESSED')
    except BaseException as error:
        receipt.update(status='FAILED_PREFLIGHT_NO_MODEL',exception_type=type(error).__name__,reason=str(error)[:250])
        raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)

if __name__=='__main__':main()
