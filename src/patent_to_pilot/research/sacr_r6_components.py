"""Prospective literal component projection; external fidelity gate required."""
import hashlib
from .sacr_components import digest
from .sacr_r6_candidate import validate_proposal,render_views,VERSION
from .sacr_views_v3 import _union
from .sacr_embedding import embedding_plan
from .mtm_runtime import InputBoundaryError


def compile_components(proposal,*,source,query_id,configuration_sha256):
    if (type(configuration_sha256) is not str or len(configuration_sha256)!=64
            or any(c not in '0123456789abcdef' for c in configuration_sha256)):
        raise InputBoundaryError('frozen component configuration identity required')
    compiled=validate_proposal(proposal,source,query_id)['compiled']
    uncertain=[c['id'] for b in compiled['blocks'] for c in b['conditions'] if c['attachment_proposal']!='explicit']
    status='ANCHOR_FALLBACK' if compiled['anchor_fallback_required'] else 'REVIEW_REQUIRED' if uncertain else 'COMPONENTS_PREPARED'
    rows=[];blocks=[]
    if status=='COMPONENTS_PREPARED':
        for block in compiled['blocks']:
            begin=len(rows)
            entries=[('relation',block['id'],block['literal_evidence'])]
            entries.extend(('condition',c['id'],c['literal_evidence']) for c in block['conditions'])
            for role,item_id,spans in entries:
                intervals=_union([(s['start'],s['end']) for s in spans])
                text='\n'.join(source[a:b] for a,b in intervals)
                rows.append({'row_id':digest([VERSION,query_id,configuration_sha256,block['id'],role,item_id]),
                    'block_id':block['id'],'item_id':item_id,'role':role,'text':text,
                    'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'original_spans':spans,'assembled_intervals':intervals})
            blocks.append({'block_id':block['id'],'start':begin,'end':len(rows)})
    if len(rows)>72:raise InputBoundaryError('R6 component ceiling')
    relation_texts=[r['text'] for r in rows if r['role']=='relation']
    body={'format':'sacr-r6-literal-component-plan-v1','status':status,'query_id':query_id,'input_kind':'DAPFAM_TA',
        'source_sha256':compiled['source_sha256'],'profile_sha256':digest(proposal),'configuration_sha256':configuration_sha256,
        'rows':rows,'blocks':blocks,'uncertain_conditions':uncertain,'fidelity_review':'REQUIRED',
        'semantic_status':'unknown','duplicate_relation_positions':len(relation_texts)-len(set(relation_texts))}
    return {**body,'plan_sha256':digest(body)}


def prepare_embedding(proposal,*,source,query_id,generic_views,configuration_sha256):
    components=compile_components(proposal,source=source,query_id=query_id,configuration_sha256=configuration_sha256)
    if components['status']!='COMPONENTS_PREPARED':raise InputBoundaryError('component review/abstention prevents embedding preparation')
    if type(generic_views) is not list or not 1<=len(generic_views)<=2:
        raise InputBoundaryError('one or two generic views required')
    views=render_views(proposal,source=source,query_id=query_id)
    prepared={'query_id':query_id,'components':components,'arms':{
        'generic':{'views':[source,*generic_views]},
        'selective':{'views':[source,views['compact'],views['selective']]}}}
    # Shared source anchor is one planned acquisition position, before exact-text dedup.
    planned=len(components['rows'])+len(generic_views)+3
    if planned>77:raise InputBoundaryError('R6 query encoding ceiling')
    plan=embedding_plan(prepared)
    return {'prepared':prepared,'embedding_plan':plan,'planned_positions':planned,
        'unique_text_rows':len(plan['rows']),'compact_equals_anchor':views['compact']==source,
        'semantic_pass':False,'dispatch_authorized':False}
