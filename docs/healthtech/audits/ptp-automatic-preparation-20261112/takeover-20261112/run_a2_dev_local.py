"""A2 dev design, run ONCE locally (CPU). Inputs hash-verified: S5 dev rankings (copied from the settled S5 retrieval job),
dev qrels/queries/corpus from the v3 dev staging. Dev only; test untouched. Public aggregates -> paper1-a2/dev-design.json."""
import hashlib, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import R, A
from patent_to_pilot.research.paper1_a2 import a2_systems, a2_dev_design
P = R.parent/'_private_artifacts/healthtech'; D = P/'ptp-paper1-a2-dev-20261115-v1'; S = P/'ptp-dapfam-native-dev-20261110-v3'
out = A/'paper1-a2/dev-design.json'; assert not out.exists() and not (D/'private-per-query.json').exists()
pins = json.loads((A/'paper1-s5-retrieval/terminal-observation.json').read_bytes())['completion']['files_sha256']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for f in ('reference', 'shuffle', 'FA-panel', 'GR-panel', 'SACR-panel'):
    assert sha(D/(f + '-top200-private.jsonl')) == pins[f + '-top200-private.jsonl'], f
assert sha(S/'dev-evaluation/qrels-dev.jsonl') == 'ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473'
assert sha(S/'runtime-dev/queries-ta.jsonl') == '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a'
t0 = time.process_time()
load = lambda p: [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
table = lambda f: {r['query_id']: r['families'] for r in load(D/(f + '-top200-private.jsonl'))}
corpus = []
with open(S/'runtime-dev/corpus.jsonl', encoding='utf-8') as fh:
    for line in fh:
        if line.strip(): corpus.append({'relevant_id': json.loads(line)['id'], 'title_en': '', 'abstract_en': '', 'claims_text': ''})
queries = [{'query_id': r['id'], 'title_en': '', 'abstract_en': ''} for r in load(S/'runtime-dev/queries-ta.jsonl')]
ref = table('reference')
systems = a2_systems(ref, {'FA': table('FA-panel'), 'GR': table('GR-panel'), 'SACR': table('SACR-panel'), 'shuffle': table('shuffle')})
public, private = a2_dev_design(corpus, queries, load(S/'dev-evaluation/qrels-dev.jsonl'), systems)
s5 = json.loads((A/'PAPER1-S5-SUMMARY.json').read_bytes())['recall200']
assert all(abs(public[p]['metrics']['B0']['Recall@200'] - s5[p]['B0']) < 1e-9 for p in ('ALL', 'IN', 'OUT')), 'B0 does not reproduce S5'
(D/'private-per-query.json').write_text(json.dumps(private) + '\n')
res = {'status': 'PAPER1_A2_DEV_DESIGN_DESCRIPTIVE', 'predeclaration_sha256': sha(A/'paper1-a2/A2-PREDECLARATION.md'),
       'inputs_verified': True, 'b0_reproduces_s5': True, 'protected_test_access': False, 'significance_claim': False,
       'process_cpu_seconds': time.process_time() - t0, 'results': public}
out.write_text(json.dumps(res, indent=2) + '\n'); print(json.dumps(public['selection']))
