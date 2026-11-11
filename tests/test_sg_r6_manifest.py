import hashlib
import json
from copy import deepcopy
import pytest
from patent_to_pilot.research.sg_r6_manifest import fixed_union, build_manifest, request
from patent_to_pilot.research.sg_r6_source_attachment import attach_fixed282_sources
from patent_to_pilot.research.sg_relations_v2 import extract_family_v2
from patent_to_pilot.research.sg_materialization_v1 import SALT
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixture():
    source_ids=[f's{i:03}' for i in range(100)]
    alias_ids=['s000']+[f'a{i:03}' for i in range(1,183)]
    rows={fid:{'id':fid,'title':'Authored fixture','abstract':'A pump is configured to transfer water at 5 bar.','claims':''}
        for fid in set(source_ids+alias_ids)}
    records={fid:extract_family_v2(row)['records'] for fid,row in rows.items()}
    sample={'records_by_family':{fid:records[fid] if i<14 else [] for i,fid in enumerate(source_ids)},'no_substitution':True}
    pairs=[(alias_ids[2*i],alias_ids[2*i+1]) for i in range(83)]
    pairs += [(alias_ids[0],alias_ids[i]) for i in range(166,183)]
    values=[]; witnesses={}
    for left,right in pairs:
        members=sorted([left,right]); rr=[records[fid][0] for fid in members]; key=rr[0]['alias_key']
        canonical=json.dumps([key,*members],ensure_ascii=False,separators=(',',':'))
        values.append({'families':members,'alias_key':key,'relation_ids':[r['relation_id'] for r in rr],
            'sampling_sha256':hashlib.sha256((SALT+canonical).encode()).hexdigest()})
        witnesses.update({r['relation_id']:r for r in rr})
    aliases={'sample':sorted(values,key=lambda p:p['sampling_sha256']),'witness_records':witnesses,
        'salt':SALT,'uses_queries_qrels_retrieval_scores':False}
    return list(rows.values()),sample,aliases


def test_full_union_and_abstentions_are_not_fidelity_passes():
    rows,sample,aliases=fixture(); manifest=build_manifest(rows,sample,aliases)
    assert len(fixed_union(sample,aliases))==282
    assert len(manifest['units'])==114 and len(manifest['coverage'])==100
    assert sum(r['status']=='ABSTENTION' for r in manifest['coverage'])==86
    assert not any(r['semantic_pass'] for r in manifest['coverage'])
    assert manifest['accepted_edges']==0
    alias=manifest['units'][14]
    assert alias['source'].count('TITLE\nAuthored fixture')==2
    prepared=request(alias)
    assert ''.join(u['text'] for u in prepared['payload']['source_units'])==alias['source']


@pytest.mark.parametrize('fault',['missing','duplicate','swapped','changed_context','extra_field','count','alias_duplicate'])
def test_integrity_rejects_changed_fixed_inputs(fault):
    rows,sample,aliases=fixture()
    if fault=='missing':rows.pop()
    if fault=='duplicate':rows.append(deepcopy(rows[0]))
    if fault=='swapped':rows[0]['id']='other'
    if fault=='changed_context':
        next(r for r in rows if r['id']=='s000')['abstract']+=' Altered context.'
    if fault=='extra_field':rows[0]['qrels']='forbidden'
    if fault=='count':sample['records_by_family']['s014']=deepcopy(sample['records_by_family']['s000'])
    if fault=='alias_duplicate':aliases['sample'][1]=deepcopy(aliases['sample'][0])
    with pytest.raises((InputBoundaryError,KeyError)):build_manifest(rows,sample,aliases)


def test_join_exact282_private_output_no_extraction_or_replay(tmp_path):
    rows,sample,aliases=fixture(); raw=b''.join(json.dumps(r).encode()+b'\n' for r in rows)
    corpus=tmp_path/'corpus'; corpus.write_bytes(raw)
    args={'expected_sha256':hashlib.sha256(raw).hexdigest(),'fixed_ids':fixed_union(sample,aliases)}
    receipt=attach_fixed282_sources(corpus,tmp_path/'out',**args)
    assert receipt['source_units']==282 and receipt['extraction']=='NOT_RUN'
    with pytest.raises(FileExistsError):attach_fixed282_sources(corpus,tmp_path/'out',**args)
    args['fixed_ids']=args['fixed_ids'][:-1]
    with pytest.raises(InputBoundaryError):attach_fixed282_sources(corpus,tmp_path/'wrong',**args)
    assert not (tmp_path/'wrong'/'sources-private.jsonl').exists()
