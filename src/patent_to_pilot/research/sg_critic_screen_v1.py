"""Frozen unit construction and honest automated screening, no accepted edges."""
import hashlib,json
from jsonschema.exceptions import ValidationError
from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import CONFIG
from .literal_critic_contract_v1 import messages,schema,interpret

VERSION='sg-source-and-pair-critic-v1'
SOURCE_CRITERIA={
 'roles_direction':'Each extracted action/operand and positive/negative direction must match the actual unit; inspect subject attachment.',
 'quantities_units':'Retained complete units must preserve quantities and units and their pairing; do not infer numerical equivalence.',
 'polarity_exceptions':'Negated capability or an exception must not be promoted to a positive function.',
 'condition_attachment':'Use full source to check whether selected unit preserves attached operating/material/conditional constraints; uncertainty escalates.',
 'essential_coverage':'Check essential directed functions and constraints claimed for the invention throughout the supplied source, distinguishing background examples. Empty output is supported only when no essential functional information is present. Omitted essential functions are unsupported even if outside the extractor cue/verb rules or beyond its record cap; name the missing source evidence. Unclear essentiality is uncertain. Extractor limitations explain omissions but never exempt them from this risk pool.',
 'abstraction_support':'Only declared casefold/whitespace/leading-article normalization is permitted; no invented synonyms or generalizations.',
 'context_preservation':'The source unit and retained trailing context must support the proposed function. Missing cross-unit context is uncertain, not automatically safe.'}
PAIR_CRITERIA={
 'roles_direction':'Do both displayed witnesses denote the same directed action/operand function, rather than merely sharing words?',
 'quantities_units':'Each witness must retain its own quantities/units. Never equate incompatible quantitative operating claims.',
 'polarity_exceptions':'Do not connect a positive capability to its negation or an exception as an equivalent function.',
 'condition_attachment':'Check compatibility of attached conditions for the proposed shared-function relation; unresolved compatibility is uncertain.',
 'essential_coverage':'Inspect both witnesses. A matching hash or alias is not semantic evidence. Only these fixed witnesses are being reviewed, not all records of their families.',
 'abstraction_support':'The proposed edge means shared directed function with both contexts retained, not device interchangeability. Do not broaden beyond source support.',
 'context_preservation':'Use the displayed complete source units; full source fields are not supplied for this stratum. If external context is needed, mark uncertain. Never assume missing context agrees.'}


def units(source_rows,source_sample,aliases):
    rows={row['id']:row for row in source_rows}
    if len(rows)!=len(source_rows) or set(rows)!=set(source_sample['records_by_family']) or len(rows)!=100:
        raise InputBoundaryError('fixed full-source sample mismatch')
    if len(aliases['sample'])!=100:raise InputBoundaryError('fixed alias sample count')
    output=[]
    for fid in sorted(rows):
        row=rows[fid]
        source='TITLE\n'+row['title']+'\nABSTRACT\n'+row['abstract']+'\nCLAIMS\n'+row['claims']
        records=source_sample['records_by_family'][fid]
        # Bind retained source field hashes and every retained unit to the joined source.
        for record in records:
            text=row[record['source_field']];span=record['source_span']
            if hashlib.sha256(text.encode()).hexdigest()!=record['source_sha256'] or text[span['start']:span['end']]!=span['text']:
                raise InputBoundaryError('full source and retained extraction disagree')
        output.append({'stable_id':fid,'unit_type':'source','source':source,
            'artifacts':{'extracted_records':json.dumps(records,ensure_ascii=False,sort_keys=True,separators=(',',':'))},
            'criteria':SOURCE_CRITERIA,'scope':{'extractor':CONFIG,'coverage':'full essential source coverage; extractor rules are limitations, not omission exemptions'},
            'record_count':len(records)})
    for pair in aliases['sample']:
        records=[aliases['witness_records'][rid] for rid in pair['relation_ids']]
        source='WITNESS_A\n'+records[0]['source_span']['text']+'\nWITNESS_B\n'+records[1]['source_span']['text']
        candidate={'claim':'shared directed function with both witnessed contexts retained; no device interchangeability assertion',
                   'pair':pair,'witness_records':records}
        output.append({'stable_id':pair['sampling_sha256'],'unit_type':'alias','source':source,
            'artifacts':{'candidate_pair':json.dumps(candidate,ensure_ascii=False,sort_keys=True,separators=(',',':'))},
            'criteria':PAIR_CRITERIA,'scope':{'representative_policy':aliases['representative_policy'],
                'full_family_source':'NOT_PROVIDED','acceptance':'witness pair only, never all relations of family/key'},'record_count':2})
    for i,unit in enumerate(output):unit['query_id']=f'sg-r5-{i:03}'
    return output


def request(unit):
    args={k:unit[k] for k in ['query_id','source','artifacts','criteria','scope']}
    return messages(**args),schema(unit['query_id'],unit['source'],unit['artifacts'])


def screen_record(record,unit):
    if record['status']!='EOS_COMPLETE':
        return {'status':'RISK','reason':record['status'],'semantic_pass':False}
    try:
        result=interpret(record['text'].encode(),query_id=unit['query_id'],source=unit['source'],artifacts=unit['artifacts'])
    except (ValueError,TypeError,KeyError,UnicodeError,ValidationError) as error:
        return {'status':'RISK','reason':'MALFORMED_OR_UNGROUNDED_CRITIC','exception_type':type(error).__name__,'semantic_pass':False}
    return {'status':'SCREENING_PASS' if result['status']=='CRITIC_UNFLAGGED_NOT_FIDELITY_PASS' else 'RISK',
            'reason':result['status'],'review':result,'semantic_pass':False}
