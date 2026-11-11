"""Authored grammar cases; schema acceptance and contract validity are separate."""
from copy import deepcopy
import json
from . import sacr_r6_candidate as profile
from .sacr_token_profile import source_catalogue
from .r6_critic_calibration import fixtures,request
from .reference_critic_v1 import interpret


def matrix(kind):
    rows=[]
    def add(name,prepared,value,schema_ok,contract_ok,branch,source=None):
        rows.append({'name':name,'prepared':prepared,'text':json.dumps(value,ensure_ascii=False),
            'expected_schema':schema_ok,'expected_contract':contract_ok,'branch':branch,'source':source})
    if kind=='profile':
        source=' '.join(['The "pump" transfers water at 5 kPa.']*17)+' Thai ไทย and symbol 🚰.'
        cat=source_catalogue(source);n=len(cat['tokens']);qid='r6-profile-qualification'
        prepared={'messages':profile.build_messages(source,qid),'schema':profile.proposal_schema(source,qid),'query_id':qid}
        value={'version':'sacr-evidence-roles-v3','query_id':qid,'source_sha256':cat['source_sha256'],
            'blocks':[{'id':'b','evidence':[{'field':'allowed_query','start_token':0,'end_token':n}],
                'roles':{},'conditions':[],'abstraction':'A "pump" transfers water. ไทย 🚰 \\'}]}
        add('profile-complete-unicode',prepared,value,True,True,'profile',source)
        add('profile-alternate-field-order',prepared,dict(reversed(list(value.items()))),True,True,'profile',source)
        empty=deepcopy(value);empty['blocks']=[];add('profile-abstention',prepared,empty,True,True,'profile',source)
        partial=deepcopy(value);partial['blocks'][0]['evidence'][0]['start_token']=1
        add('profile-partial-context',prepared,partial,False,False,'profile',source)
        reversed_role=deepcopy(value);reversed_role['blocks'][0]['roles']={'action':[{'field':'allowed_query','start_token':2,'end_token':1}]}
        add('profile-reversed-role-contract',prepared,reversed_role,True,False,'profile',source)
        zero=deepcopy(reversed_role);zero['blocks'][0]['roles']['action'][0].update(start_token=2,end_token=2)
        add('profile-zero-width-role-contract',prepared,zero,True,False,'profile',source)
        duplicated=deepcopy(value);duplicated['blocks'].append(deepcopy(value['blocks'][0]))
        add('profile-duplicate-id-contract',prepared,duplicated,True,False,'profile',source)
        missing=deepcopy(value);del missing['source_sha256'];add('profile-missing-field',prepared,missing,False,False,'profile',source)
        extra=deepcopy(value);extra['unexpected']=True;add('profile-extra-field',prepared,extra,False,False,'profile',source)
        fractional=deepcopy(reversed_role);fractional['blocks'][0]['roles']['action'][0].update(start_token=0.5,end_token=1)
        add('profile-fractional-reference',prepared,fractional,False,False,'profile',source)
        outside=deepcopy(reversed_role);outside['blocks'][0]['roles']['action'][0].update(start_token=n,end_token=n+1)
        add('profile-outside-reference',prepared,outside,False,False,'profile',source)
        many=deepcopy(value);many['blocks']=[dict(deepcopy(value['blocks'][0]),id=f'b{i}') for i in range(9)]
        add('profile-block-bound',prepared,many,False,False,'profile',source)
        unit_size=len(source_catalogue('The "pump" transfers water at 5 kPa.')['tokens'])
        condition=deepcopy(value);condition['blocks'][0]['conditions']=[{'id':'c17','kind':'numeric','attachment':'explicit',
            'evidence':[{'field':'allowed_query','start_token':16*unit_size+5,'end_token':17*unit_size}],
            'attachment_evidence':[{'field':'allowed_query','start_token':16*unit_size,'end_token':17*unit_size}]}]
        add('profile-late-condition',prepared,condition,True,True,'profile',source)
    elif kind=='critic':
        for index,case in enumerate(fixtures()):
            prepared=request(case)
            value={'binding_sha256':prepared['binding_sha256'],
                'dimensions':{k:'supported' for k in prepared['schema']['properties']['dimensions']['properties']},'findings':[]}
            # Grammar fixture only, NEVER scored as the semantic calibration answer.
            add(f'critic-fixed-{index:02}',prepared,value,True,True,'critic')
        prepared=rows[0]['prepared'];base=json.loads(rows[0]['text'])
        add('critic-reordered',prepared,dict(reversed(list(base.items()))),True,True,'critic')
        wrong=deepcopy(base);wrong['binding_sha256']='0'*64
        add('critic-wrong-binding',prepared,wrong,False,False,'critic')
        flag=deepcopy(base);flag['dimensions']['roles_direction']='uncertain'
        branch=prepared['schema']['properties']['findings']['items']['anyOf'][0]['properties']
        flag['findings']=[{'dimension':'roles_direction','artifact':branch['artifact']['enum'][0],
            'source_units':[branch['source_units']['items']['enum'][0]],'candidate_units':[],
            'reason':'Authored uncertain role attachment.'}]
        add('critic-flag-reference',prepared,flag,True,True,'critic')
        unsupported=deepcopy(flag);unsupported['dimensions']['roles_direction']='unsupported'
        add('critic-unsupported-reference',prepared,unsupported,True,True,'critic')
        omitted=deepcopy(flag);omitted['findings']=[]
        add('critic-omitted-finding-contract',prepared,omitted,True,False,'critic')
        empty=deepcopy(flag);empty['findings'][0]['source_units']=[]
        add('critic-empty-evidence-contract',prepared,empty,True,False,'critic')
        unknown=deepcopy(flag);unknown['findings'][0]['candidate_units']=['foreign-artifact-unit']
        add('critic-foreign-reference',prepared,unknown,False,False,'critic')
        unrelated=deepcopy(flag);unrelated['dimensions']['roles_direction']='supported'
        add('critic-unflagged-finding-contract',prepared,unrelated,True,False,'critic')
        duplicate=deepcopy(flag);duplicate['findings'][0]['source_units']*=2
        add('critic-duplicate-reference',prepared,duplicate,False,False,'critic')
        too_many=deepcopy(flag);too_many['findings']*=22
        add('critic-findings-bound',prepared,too_many,False,False,'critic')
        from .reference_critic_v1 import prepare
        empty_request=prepare(query_id='empty-artifact',source='A pump moves water.',artifacts={'empty':'','other':'Water is moved.'},
            criteria=prepared['payload']['criteria'],scope={'authored':True})
        empty_base=deepcopy(base);empty_base['binding_sha256']=empty_request['binding_sha256']
        add('critic-empty-artifact-supported',empty_request,empty_base,True,True,'critic')
        bad_empty=deepcopy(empty_base);bad_empty['dimensions']['roles_direction']='uncertain'
        bad_empty['findings']=[{'dimension':'roles_direction','artifact':'empty','source_units':[empty_request['payload']['source_units'][0]['id']],
            'candidate_units':[empty_request['payload']['artifact_units']['empty'][0]['id']],'reason':'An empty artifact has no evidence.'}]
        add('critic-empty-artifact-bound',empty_request,bad_empty,False,False,'critic')
        cross=deepcopy(bad_empty);cross['findings'][0]['candidate_units']=[empty_request['payload']['artifact_units']['other'][0]['id']]
        add('critic-known-cross-artifact-reference',empty_request,cross,False,False,'critic')
    else:raise ValueError('unknown qualification group')
    truncated=deepcopy(rows[0]);truncated.update(name=kind+'-incomplete-json-eos',text=rows[0]['text'][:-1],
        expected_schema=False,expected_contract=False)
    rows.append(truncated)
    return rows


def validate_contract(case):
    value=json.loads(case['text'])
    if case['branch']=='profile':return profile.validate_proposal(value,case['source'],case['prepared']['query_id'])
    return interpret(case['text'].encode(),case['prepared'])
