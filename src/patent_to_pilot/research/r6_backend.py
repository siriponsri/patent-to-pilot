"""One grammar factory shared by CPU qualification and local GPU execution."""
import hashlib
import json
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sacr_native_fidelity import write_new


class R6Backend:
    def __init__(self,*,tokenizer,output_root,lmfe_source_sha256,model=None,max_consecutive_whitespaces=4096):
        # Default 4096 preserves closed R6/R7 behaviour; native v2 review ran away on whitespace,
        # so automatic-round workers declare a small cap explicitly.
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        self.tokenizer=tokenizer;self.model=model;self.output_root=Path(output_root)
        self.lmfe_source_sha256=lmfe_source_sha256
        if type(max_consecutive_whitespaces) is not int or not 8<=max_consecutive_whitespaces<=4096:raise ValueError('whitespace cap')
        self.max_consecutive_whitespaces=max_consecutive_whitespaces
        self.token_data=build_token_enforcer_tokenizer_data(tokenizer)

    def prompt_tokens(self,messages):
        tokens=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
        if type(tokens) is not list or any(type(t) is not int for t in tokens):
            raise InputBoundaryError('unexpected exact chat template token shape')
        return tokens

    def count_tokens(self,messages):return len(self.prompt_tokens(messages))

    def grammar(self,stage,schema,messages):
        from lmformatenforcer import CharacterLevelParserConfig
        from .sacr_alphabet import build_alphabet
        from .sacr_boundary_callback_v3 import build_boundary_callback
        if not stage or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in stage):
            raise InputBoundaryError('invalid stage receipt name')
        # Include ALL actual request text: source, role artifacts and generic views.
        text=json.dumps(messages,ensure_ascii=False,sort_keys=True)
        alphabet=build_alphabet(self.tokenizer,text)
        settings=CharacterLevelParserConfig(alphabet=alphabet['alphabet'],max_consecutive_whitespaces=getattr(self,'max_consecutive_whitespaces',4096),
            force_json_field_order=False,max_json_array_length=4096)
        callback=build_boundary_callback(self.token_data,schema,settings,expected_source_sha256=self.lmfe_source_sha256)
        if callback.configuration_receipt['requested']!=callback.configuration_receipt['effective_root']:
            raise InputBoundaryError('grammar effective configuration differs')
        write_new(self.output_root/(stage+'-grammar-private.json'),{
            **callback.configuration_receipt,'messages_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'schema_sha256':hashlib.sha256(json.dumps(schema,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
        return callback

    def eos_guard(self,callback,schema,prompt_tokens,validate=None):
        from jsonschema import Draft202012Validator
        from .sacr_grammar_guard import CompleteJsonEOSGuard
        validator=Draft202012Validator(schema).validate
        return CompleteJsonEOSGuard(prefix_fn=callback,tokenizer=self.tokenizer,prompt_tokens=prompt_tokens,
            eos_token_ids=[151645,151643],validate=validator if validate is None else validate(validator))

    def factory(self,stage,schema,diagnostics,messages):
        if self.model is None:raise InputBoundaryError('model execution unavailable in CPU qualification')
        model=self.model
        if schema is None:
            class Plain:
                def generate(self,**kwargs):return diagnostics.call_backend(model,**kwargs)
            return Plain()
        callback=self.grammar(stage,schema,messages)
        owner=self
        class Guarded:
            def generate(self,**kwargs):
                prompt=int(kwargs['input_ids'].shape[1])
                guard=owner.eos_guard(callback,schema,prompt,validate=diagnostics.validator)
                monitored=diagnostics.grammar(guard,prompt)
                return diagnostics.call_backend(model,**kwargs,prefix_allowed_tokens_fn=monitored)
        return Guarded()

    def qualify(self,stage,schema,messages,text):
        """Replay authored output tokens through the SAME callback and EOS guard."""
        import torch
        prompt=self.prompt_tokens(messages)
        if len(prompt)>8192:return {'accepted':False,'reason':'INPUT_LIMIT','input_tokens':len(prompt)}
        callback=self.grammar(stage,schema,messages)
        guard=self.eos_guard(callback,schema,len(prompt))
        tokens=self.tokenizer.encode(text,add_special_tokens=False);seq=list(prompt)
        reason='COMPLETE';accepted=True
        for token in tokens:
            try:allowed=guard(0,torch.tensor(seq,dtype=torch.long))
            except InputBoundaryError as error:
                if str(error)!='premature grammar termination refused':raise
                accepted=False;reason='SCHEMA_EOS_REJECTED';break
            if token not in allowed:accepted=False;reason='TOKEN_NOT_ALLOWED';break
            seq.append(token)
        if accepted:
            try:
                accepted=bool(set(guard(0,torch.tensor(seq,dtype=torch.long))) & {151645,151643})
                if not accepted:reason='EOS_NOT_ALLOWED'
            except InputBoundaryError as error:
                if str(error)!='premature grammar termination refused':raise
                accepted=False;reason='SCHEMA_EOS_REJECTED'
        return {'accepted':accepted,'reason':reason,'input_tokens':len(prompt),'output_tokens':len(tokens),
            'model_calls':0,'schema_eos_only':True}
