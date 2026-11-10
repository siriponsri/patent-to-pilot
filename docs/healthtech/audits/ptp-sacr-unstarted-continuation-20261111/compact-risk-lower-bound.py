"""Read-only early bound on frozen bundle flags. No calls, cards or retrieval."""
from pathlib import Path
import sys,json,hashlib
job=Path('/home/chaw/patent-to-pilot-jobs/ptp-native-sacr-continuation-20261111-v1')
sys.path.insert(0,str(job/'runtime-code/src'))
from patent_to_pilot.research.sacr_native_fidelity import bind_sample
from patent_to_pilot.research.sacr_rejection_policy import assess_profile_attempt
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_views import compact_view,screen_view
old=job.parent/'ptp-native-sacr-fidelity-20261110-v1'
new=old/'out/continuation-a2966f862e87c13f1f1abca8b6b903e7a860f7bff57737759e3c9d8d06da5b91/attempt'
d=json.loads((job/'declaration.json').read_bytes())
entries=bind_sample((old/'inputs/queries-ta.jsonl').read_bytes(),(old/'inputs/sample.json').read_bytes(),query_sha256=d['query_sha256'],sample_sha256=d['sample_sha256'])
counts={'checked_completed':0,'rejected_profiles':0,'compact_unavailable':0,'compact_lexical_flagged':0,'compact_unflagged_only':0}
reasons={}
for i,(q,source,schema) in enumerate(entries):
 root=(old/'out/attempt' if i<46 else new)/'profiles'/f'{i:03d}'
 if not (root/'assessment.json').exists():continue
 a=json.loads((root/'assessment.json').read_bytes());raw=(root/'profile/generation.json').read_bytes()
 recomputed=assess_profile_attempt(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),source=source,query_id=q,input_kind='DAPFAM_TA',limits=GenerationLimits(),metrics=a['metrics'])
 assert recomputed==a
 counts['checked_completed']+=1
 if a['status']=='REJECTED_GENERATED_FAMILY':counts['rejected_profiles']+=1;continue
 assert a['status']=='STRUCTURAL_RESULT_FIDELITY_PENDING'
 profile=a['validation']['profile']
 c=compact_view(profile,source=source,query_id=q,input_kind='DAPFAM_TA')
 if c['text'] is None:counts['compact_unavailable']+=1;continue
 protected=[c['raw_text'] for b in profile['blocks'] for c in b['attached_conditions'] if c['relation_to_block']=='explicit']
 screen=screen_view(source,c['text'],protected_phrases=protected,maximum_characters=65536)
 if screen['status']!='LEXICAL_SCREEN_PASS':
  counts['compact_lexical_flagged']+=1
  for why in screen['rejection_reasons']+screen['review_flags']:reasons[why]=reasons.get(why,0)+1
 else:counts['compact_unflagged_only']+=1
flags=counts['rejected_profiles']+counts['compact_unavailable']+counts['compact_lexical_flagged']
print(json.dumps({'status':'EARLY_FROZEN_FLAG_LOWER_BOUND','counts':counts,'flagged_queries_lower_bound':flags,'reasons':reasons,'full_sample':100,'cap':20,'configuration_gate_impossible_without_policy_change':flags>20,'semantic_pass':False,'model_calls':0}))
