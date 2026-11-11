"""Fixed24 authored calibration, revised after independent shortcut review.

Ten faithful nonidentical positives, ten critical negatives, four uncertainties.
Caller must separately attest EOS, request/reservation/limits/cost binding.
"""
from copy import deepcopy
import hashlib,json
from jsonschema.exceptions import ValidationError
from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import extract_family_v2
from .r6_critic_tasks import criteria
from .reference_critic_v1 import prepare, interpret


def record(source, family='fixture'):
    rows=extract_family_v2({'id':family,'title':'','abstract':source,'claims':''})['records']
    if len(rows)!=1:raise InputBoundaryError('authored fixture must yield exactly one R2 record')
    return rows[0]


def serialize(records):
    return json.dumps({'proposed_claim':'positive capability of the claimed device','records':records},sort_keys=True,separators=(',',':'))


def fixtures():
    rows=[]
    def add(name,branch,source,candidate,kind,required,allowed,terms,control=None,candidate_terms=()):
        opaque=hashlib.sha256(('r6-calibration-v2|'+name).encode()).hexdigest()[:16]
        artifacts={'candidate':candidate}
        if control is not None:artifacts['control']=control
        spans=[]
        for term in terms:
            if source.count(term)!=1:raise InputBoundaryError('fixture target must occur exactly once')
            start=source.index(term);spans.append([start,start+len(term)])
        candidate_spans=[]
        for term in candidate_terms:
            if candidate.count(term)!=1:raise InputBoundaryError('candidate target must occur exactly once')
            start=candidate.index(term);candidate_spans.append([start,start+len(term)])
        rows.append({'case_id':opaque,'branch':branch,'source':source,'artifacts':artifacts,
            'expected':{'kind':kind,'required_flags':required,'allowed_flags':allowed,
                        'target_source_spans':spans,'target_candidate_spans':candidate_spans,'target_artifact':'candidate'}})
    def pair(name,branch,source,good,bad,required,allowed,terms,bad_source=None,control=None,candidate_terms=()):
        add(name+'-faithful',branch,source,good,'positive',[],[],[],control)
        add(name+'-critical',branch,bad_source or source,bad,'negative',required,allowed,terms,control,candidate_terms)
    background=('Administrative context: the document contains a cover page, revision date, drawing index and glossary. '
        'These administrative entries describe how the file is organized and make no technical capability claim. '
        'The index lists numbered sections so a reader can locate the description. The glossary defines formatting conventions. '
        'The cover identifies the document revision and the drawing list identifies sheet numbers. This paragraph is administrative background only. ')
    pair('s1','SACR','The pump operates at 5 kPa below 40 C.',
        'Below 40 C, the pump operates at 5 kPa.','Below 40 C, the pump operates at 50 kPa.',
        ['quantities_units'],['quantities_units','essential_coverage'],['5 kPa'],candidate_terms=['50 kPa'])
    source=background+'The valve opens above 5 kPa; the pump stops above 40 C.'
    good=background+'The pump stops above 40 C, and the valve opens above 5 kPa.'
    pair('s2','SACR',source,good,background+'The valve opens above 40 C; the pump stops above 5 kPa.',
        ['condition_attachment'],['condition_attachment','roles_direction','quantities_units','essential_coverage'],
        ['The valve opens above 5 kPa','the pump stops above 40 C'],control=good,
        candidate_terms=['The valve opens above 40 C','the pump stops above 5 kPa'])
    pair('s3','SACR','The filter must not release particles except during cleaning.',
        'Except during cleaning, the filter must not release particles.','The filter must not release particles.',
        ['polarity_exceptions'],['polarity_exceptions','condition_attachment','essential_coverage'],['except during cleaning'])
    source=background+'A prior filter uses a laser. The claimed invention uses a membrane to filter particles.'
    good='A laser belongs to the prior filter; the invention filters particles with a membrane.'
    pair('s4','SACR',source,good,'The claimed invention uses a laser to filter particles.',
        ['context_preservation','abstraction_support'],['context_preservation','abstraction_support','essential_coverage','roles_direction'],
        ['The claimed invention uses a membrane'],control=good)
    pos='The claimed device is configured to remove particles.';neg='The claimed device is NOT configured to remove particles.'
    pair('e1','SG_RECORD',pos,serialize([record(pos)]),serialize([record(neg)]),
        ['polarity_exceptions'],['polarity_exceptions','context_preservation','roles_direction'],['NOT configured'],bad_source=neg)
    source='The claimed pump is configured to move coolant when temperature is below 40 C.'
    original=record(source);broken=deepcopy(original);end=source.index(' when')
    broken['source_span']={'start':0,'end':end,'text':source[:end]}
    broken['trailing_context_span']={'start':end,'end':end,'text':''}
    pair('e2','SG_RECORD',source,serialize([original]),serialize([broken]),
        ['condition_attachment','essential_coverage'],['condition_attachment','essential_coverage'],['when temperature is below 40 C'])
    source='The claimed module is configured to convert heat into electricity.'
    original=record(source);broken=deepcopy(original);start=source.index('electricity')
    broken['operand_span']={'start':start,'end':start+11,'text':'electricity'}
    broken['alias_descriptor']='convert|electricity';broken['alias_key']=hashlib.sha256(b'convert|electricity').hexdigest()
    pair('e3','SG_RECORD',source,serialize([original]),serialize([broken]),
        ['roles_direction'],['roles_direction','abstraction_support'],['convert heat into electricity'])
    pos='The claimed device is configured to detect pressure.'
    neg='Only the prior device is configured to detect pressure. The claimed device measures temperature.'
    pair('e4','SG_RECORD',pos,serialize([record(pos)]),serialize([record(neg)]),
        ['context_preservation'],['context_preservation','roles_direction'],['Only the prior device'],bad_source=neg)
    def alias(a,b):
        return json.dumps({'proposed_claim':'shared positive technical action/operand with both contexts retained; no interchangeability',
            'witness_records':[record(a,'left'),record(b,'right')],'full_witness_contexts':[a,b]},sort_keys=True,separators=(',',':'))
    left='Device A is configured to filter particles when pressure is below 5 kPa.'
    right='Device B is configured to filter the particles when temperature is below 40 C.'
    bad=right.replace('is configured','is NOT configured')
    pair('a1','SG_ALIAS','WITNESS A\n'+left+'\nWITNESS B\n'+right,alias(left,right),alias(left,bad),
        ['polarity_exceptions'],['polarity_exceptions','roles_direction','context_preservation'],['NOT configured'],
        bad_source='WITNESS A\n'+left+'\nWITNESS B\n'+bad)
    left='Device A is configured to store charge. Here charge means electric charge.'
    right='Device B is configured to store charge. Here charge also means electric charge.'
    bad='Device B is configured to store charge. Here charge means a billing fee.'
    pair('a2','SG_ALIAS','WITNESS A\n'+left+'\nWITNESS B\n'+right,alias(left,right),alias(left,bad),
        ['abstraction_support'],['abstraction_support','context_preservation','roles_direction'],['billing fee'],
        bad_source='WITNESS A\n'+left+'\nWITNESS B\n'+bad)
    add('u1','SACR','Valve A responds to sensor B at a threshold. The source does not identify whether this threshold belongs to A or B.',
        'Valve A responds to sensor B at the threshold belonging to A.','uncertain',['condition_attachment'],
        ['condition_attachment','context_preservation','roles_direction'],['does not identify'])
    add('u2','SACR','The first unit feeds the second unit. It reduces pressure. The source does not identify the antecedent of It.',
        'The first unit feeds the second unit and reduces pressure.','uncertain',['roles_direction'],
        ['roles_direction','context_preservation'],['does not identify the antecedent'])
    source='The claimed device is configured to adjust pressure under Procedure X. Procedure X is not supplied.'
    add('u3','SG_RECORD',source,serialize([record(source)]),'uncertain',['condition_attachment','context_preservation'],
        ['condition_attachment','context_preservation'],['Procedure X is not supplied'])
    left='Device A is configured to control process under Figure A. Figure A is unavailable.'
    right='Device B is configured to control process under Figure B. Figure B is unavailable.'
    add('u4','SG_ALIAS','WITNESS A\n'+left+'\nWITNESS B\n'+right,alias(left,right),'uncertain',
        ['abstraction_support','context_preservation'],['abstraction_support','context_preservation'],['Figure A is unavailable','Figure B is unavailable'])
    return sorted(rows,key=lambda r:r['case_id'])


def request(case):
    return prepare(query_id=case['case_id'], source=case['source'], artifacts=case['artifacts'],
        criteria=criteria(case['branch']), scope={'branch':case['branch'],
        'purpose':'authored calibration; judge proposed candidate claims, not source-copy accuracy alone',
        'target_artifact':'candidate','missing_context_policy':'uncertain, not a forced true/false decision'})


def assess(results):
    gold={r['case_id']:r for r in fixtures()}
    if len(results)!=24 or len({r['case_id'] for r in results})!=24 or {r['case_id'] for r in results}!=set(gold):
        raise InputBoundaryError('all fixed24 calibration cases required, no substitutions')
    errors={'invalid_evaluator_cases':0,'positive_cases_flagged':0,'required_verdict_misses':0,
            'unrelated_dimension_flags':0,'irrelevant_evidence_cases':0}
    for row in results:
        if set(row)!={'case_id','critic_text'} or not isinstance(row['critic_text'],str):
            raise InputBoundaryError('raw critic text required; self-reported VALID is not evidence')
        case=gold[row['case_id']];expected=case['expected']
        try:parsed=interpret(row['critic_text'].encode(),request(case))
        except (InputBoundaryError,ValidationError,ValueError,TypeError,KeyError,UnicodeError):
            errors['invalid_evaluator_cases']+=1;continue
        dims=parsed['dimensions'];flagged={k for k,v in dims.items() if v!='supported'}
        if expected['kind']=='positive':
            errors['positive_cases_flagged']+=bool(flagged);continue
        required_status='unsupported' if expected['kind']=='negative' else 'uncertain'
        errors['required_verdict_misses']+=any(dims[k]!=required_status for k in expected['required_flags'])
        errors['unrelated_dimension_flags']+=bool(flagged-set(expected['allowed_flags'])) or (expected['kind']=='uncertain' and any(v=='unsupported' for v in dims.values()))
        relevant=True
        for dim in expected['required_flags']:
            selected=[u for f in parsed['findings'] if f['dimension']==dim and f['artifact']==expected['target_artifact'] for u in f['source_evidence']]
            covered={i for u in selected for i in range(u['start'],u['end'])}
            if any(not set(range(a,b))<=covered for a,b in expected['target_source_spans']):relevant=False
            selected_candidate=[u for f in parsed['findings'] if f['dimension']==dim and f['artifact']==expected['target_artifact'] for u in f['candidate_evidence']]
            candidate_covered={i for u in selected_candidate for i in range(u['start'],u['end'])}
            if any(not set(range(a,b))<=candidate_covered for a,b in expected['target_candidate_spans']):relevant=False
        errors['irrelevant_evidence_cases']+=not relevant
    return {'status':'AUTHORED_CALIBRATION_QUALIFIED' if not any(errors.values()) else 'CALIBRATION_FAILED',
            'cases':24,**errors,'execution_attestation':'REQUIRED_SEPARATELY',
            'native_fidelity_proven':False,'independent_expert_review':False}
