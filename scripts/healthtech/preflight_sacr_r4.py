"""Approved CPU-only tokenizer/grammar qualification; never load model weights."""
from pathlib import Path
import hashlib,json,sys,time,resource
sys.path.insert(0,'/code/src')
def main():
    start=time.monotonic();out=Path('/out/receipt.json')
    receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration hash mismatch')
        d=json.loads(raw);source=d['source'];qid=d['query_id']
        identity=json.loads(Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes())
        for name in ['tokenizer.json','tokenizer_config.json','config.json']:
            if hashlib.sha256((Path('/models/qwen3-8b')/name).read_bytes()).hexdigest()!=identity['files'][name]['sha256']:
                raise RuntimeError('tokenizer/config source pin mismatch')
        from transformers import AutoTokenizer
        import lmformatenforcer
        from lmformatenforcer import JsonSchemaParser,CharacterLevelParserConfig
        for name,expected in d['lmfe_source_sha256'].items():
            if hashlib.sha256((Path(lmformatenforcer.__file__).parent/name).read_bytes()).hexdigest()!=expected:
                raise RuntimeError('grammar dependency source pin mismatch')
        from patent_to_pilot.research.sacr_evidence_prompt_v4 import contexts,proposal_schema,build_messages,validate_proposal
        from patent_to_pilot.research.sacr_token_profile import source_catalogue
        from patent_to_pilot.research.sacr_alphabet import build_alphabet
        from patent_to_pilot.research.sacr_evidence_review_v3 import review_payload
        from patent_to_pilot.research.sacr_prompts import build_messages as legacy_messages
        tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
        if type(tokenizer).__name__!='Qwen2TokenizerFast':raise RuntimeError('tokenizer identity mismatch')
        schema=proposal_schema(source,qid);catalogue=source_catalogue(source)
        alphabet=build_alphabet(tokenizer,source)
        config=CharacterLevelParserConfig(alphabet=alphabet['alphabet'],max_consecutive_whitespaces=4096,
                                         force_json_field_order=False,max_json_array_length=4096)
        checked=0
        for context in contexts(source):
            proposal={'version':'sacr-evidence-roles-v3','query_id':qid,'source_sha256':catalogue['source_sha256'],
             'blocks':[{'id':'b1','evidence':[{'field':'allowed_query',**context}],
                        'roles':{},'conditions':[],'abstraction':None}]}
            validate_proposal(proposal,source,qid)
            parser=JsonSchemaParser(schema,config=config)
            for char in json.dumps(proposal,ensure_ascii=False):
                if char not in parser.get_allowed_characters():raise RuntimeError('grammar rejected schema-valid fixture')
                parser=parser.add_character(char)
            if not parser.can_end():raise RuntimeError('grammar cannot end fixture')
            checked+=1
        messages={'profile':build_messages(source,qid),
                  'generic':legacy_messages(prompt_root=Path('/code/docs/healthtech/research/prompts'),kind='generic',
                    query_id=qid,input_kind='DAPFAM_TA',source=source)['messages'],
                  'critic_authored_minimal':review_payload(proposal,source=source,query_id=qid)['messages']}
        counts={}
        for name,value in messages.items():
            encoded=tokenizer.apply_chat_template(value,tokenize=True,add_generation_prompt=True,
                         return_tensors='pt',return_dict=True,enable_thinking=False)
            counts[name]=int(encoded['input_ids'].shape[1])
            if counts[name]>8192:raise RuntimeError('input token cap exceeded')
        receipt.update(status='PASS_CPU_PREFLIGHT_NOT_MODEL_OR_FIDELITY',grammar_fixture_count=checked,
            input_tokens=counts,critic_limit='Minimal authored critic only; real generated critic prompt still must pass runtime8192cap',
            tokenizer_class=type(tokenizer).__name__)
    except BaseException as error:
        receipt.update(status='FAILED_PREFLIGHT_NO_MODEL',exception_type=type(error).__name__,reason=str(error)[:250])
        raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with out.open('x') as f:json.dump(receipt,f,indent=2)
if __name__=='__main__':main()
