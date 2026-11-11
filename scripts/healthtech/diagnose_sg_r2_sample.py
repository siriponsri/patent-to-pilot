"""Read-only diagnosis of the fixed exposed100-family sample; no new extraction config."""
import hashlib
import json
from pathlib import Path
import sys
import time
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from patent_to_pilot.research.sg_relations_v2 import BOUNDARY, CUE, ROLE, VERBS, CONFIG


def main():
    start = time.monotonic()
    private = ROOT.parent/'_private_artifacts/healthtech'
    sample_raw = (private/'ptp-sg-sample-20261110/sample.json').read_bytes()
    if hashlib.sha256(sample_raw).hexdigest() != 'f364014d3a8e429812ad0cc8328ae80b6e3e52e5af2f4ff9cbbcc976880591af':
        raise RuntimeError('sample changed')
    sample = json.loads(sample_raw)
    ids = {r['id'] for r in sample['sample']}
    if len(ids) != 100: raise RuntimeError('wrong sample')
    counts = Counter(); seen = set(); digest = hashlib.sha256()
    with (private/'ptp-dapfam-native-dev-20261110-v3/runtime-dev/corpus.jsonl').open('rb') as stream:
        for raw in stream:
            if time.monotonic()-start > 120: raise TimeoutError('diagnostic limit')
            digest.update(raw)
            row = json.loads(raw)
            if row['id'] not in ids: continue
            if row['id'] in seen: raise RuntimeError('duplicate sample family')
            seen.add(row['id'])
            for field in CONFIG['fields']:
                for unit in BOUNDARY.split(row[field]):
                    unit = unit.strip()
                    for cue in CUE.finditer(unit):
                        counts['cue_occurrences'] += 1
                        if len(unit) > CONFIG['maximum_unit_chars']:
                            counts['over_length'] += 1; continue
                        match = ROLE.fullmatch(unit[cue.end():])
                        if not match:
                            counts['role_pattern_no_match'] += 1
                        elif match['action'].casefold() not in VERBS:
                            counts['action_outside_fixed_vocabulary'] += 1
                        else:
                            counts['supported_action_before_operand_filter'] += 1
    if digest.hexdigest() != sample['corpus_sha256'] or seen != ids:
        raise RuntimeError('source identity mismatch')
    old = json.loads((ROOT/'docs/healthtech/audits/ptp-sg-feasibility-r2-20261111/aggregate.json').read_text())
    assert counts['cue_occurrences'] == old['counts']['cue_occurrences']
    assert counts['over_length'] == old['counts']['over_length']
    assert counts['role_pattern_no_match'] + counts['action_outside_fixed_vocabulary'] == old['counts']['unsupported_action']
    receipt = {'status':'RETAINED_SAMPLE_DIAGNOSIS_ONLY', 'counts':dict(counts),
        'sample_families':len(seen), 'sample_sha256':hashlib.sha256(sample_raw).hexdigest(),
        'corpus_sha256':digest.hexdigest(), 'elapsed_seconds':time.monotonic()-start,
        'model_calls':0,'gpu_seconds':0,'new_config_evaluated':False,
        'limitations':['No semantic acceptance inferred from recognized action',
                       'Vocabulary/parser diagnosis is not full-corpus link census',
                       'No unsupported raw action strings published']}
    out = ROOT/'docs/healthtech/audits/ptp-r3-diagnosis-20261111/sg-r2-rejection-breakdown.json'
    with out.open('x',encoding='utf-8') as f: json.dump(receipt,f,indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__': main()
