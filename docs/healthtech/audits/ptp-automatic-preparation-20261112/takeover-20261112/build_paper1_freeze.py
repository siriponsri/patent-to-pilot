"""Build the Paper 1 freeze manifest from COMMITTED blobs (protocol section 11). Writes once; refuses overwrite."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import A, R, blob, git, sha

OUT = A/'paper1-freeze/freeze-manifest.json'
assert not OUT.exists(), 'freeze manifest already written'
files = ['docs/healthtech/research/plans/PAPER1-ACQUISITION-PROTOCOL-DRAFT-20261113.md',
         'src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/paper1_analysis.py',
         'tests/test_paper1_frozen_arms.py', 'src/patent_to_pilot/evaluation/dapfam_native.py',
         'src/patent_to_pilot/research/native_dense_ranking.py', 'scripts/healthtech/run_dapfam_native_baseline.py',
         'src/patent_to_pilot/research/patent_structure_marking.py', 'src/patent_to_pilot/research/km_automatic_review.py',
         'src/patent_to_pilot/research/sacr_automatic_runner.py', 'src/patent_to_pilot/research/r6_backend.py',
         'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md']
sys.path.insert(0, str(R/'src'))
from patent_to_pilot.research import paper1_rewrite_arms as arms, paper1_analysis as pa
v5 = json.loads((A/'native-sacr-pilot20-v5/declaration.json').read_bytes())
ret = json.loads((A/'sacr-pilot-retrieval/declaration.json').read_bytes())
fa, gr = arms.prepare('FA', arms.EXAMPLE_SOURCE, 'freeze-probe'), arms.prepare('GR', arms.EXAMPLE_SOURCE, 'freeze-probe')
manifest = {
    'status': 'PAPER1_PROTOCOL_FROZEN',
    'date': '2026-11-13',
    'owner_approval': {'answer': 'Freeze ได้เลย', 'record': 'owner-paper1-freeze-approval.json'},
    'frozen_commit': git('rev-parse', 'HEAD').decode().strip(),
    'files_sha256': {f: sha(blob(f)) for f in files},
    'arms': {
        'B0': {'rankings_sha256': ret['b0_rankings_sha256'], 'status': 'measured dev'},
        'SACR': {'configuration': 'native v5 (marking v5 + review v3)', 'native_v5_configuration_sha256': v5['configuration_sha256'],
                 'km_sha256': v5['km_sha256'], 'input_token_cap': v5['input_token_cap'],
                 'max_consecutive_whitespaces': v5['max_consecutive_whitespaces'], 'force_json_field_order': True, 'max_calls_per_query': 2},
        'FA': {'version': arms.FA_VERSION, 'system_prompt_sha256': sha(arms.FA_SYSTEM.encode()), 'probe_request_sha256': fa['request_sha256'],
               'field_max_chars': arms.FA_FIELD_MAX, 'fields': list(arms.FA_FIELDS), 'calls_per_query': 1},
        'GR': {'version': arms.GR_VERSION, 'system_prompt_sha256': sha(arms.GR_SYSTEM.encode()), 'probe_request_sha256': gr['request_sha256'],
               'max_chars': arms.GR_MAX, 'calls_per_query': 1},
        'fusion': {'method': 'RRF', 'k': pa.RRF_K, 'depth': pa.DEPTH, 'ties': 'better B0 rank (absent last), then family id',
                   'systems': ['F-SACR', 'F-GR', 'F-FA']}},
    'generation_runtime': {k: v5[k] for k in ('model_sha256', 'tokenizer_sha256', 'decoder_sha256', 'lmfe_source_sha256',
                                              'input_token_cap', 'max_consecutive_whitespaces', 'force_json_field_order')},
    'retrieval_runtime': {'encoder': 'PatEmbed-large (MeanPoolEncoder, batch 32, tf32 off)',
                          'query_prefix': 'encode query for different document retrieval: ',
                          'passage_vectors_sha256': '9a385bcfd0aab6c4c19f2a8715824922d42d328c53f0da58857b0106ed4f0137',
                          'aggregation': 'rank_maxp full-universe tie sort', 'depth': 200, 'corpus_reencoding': False},
    'dev_inputs': {'queries_sha256': '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a',
                   'qrels_dev_sha256': 'ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473',
                   'corpus_sha256': '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d',
                   'queries': 474, 'out_eligible': 349},
    'test_inputs': {'queries': 773, 'out_eligible': 556, 'status': 'SEALED; hashes pinned only at the separately authorized test stage'},
    'analysis': {'primary': 'OUT Recall@200 macro over eligible queries; missing output = 0',
                 'gatekeeping': [list(s) for s in pa.GATEKEEPING], 'alpha_two_sided': pa.ALPHA,
                 'equivalence_margin': pa.EQUIVALENCE_MARGIN, 'noninferiority_margin_IN_ALL': pa.NONINFERIORITY_MARGIN,
                 'ci': 'percentile cluster bootstrap over query-positive-target components', 'bootstrap_resamples': pa.BOOTSTRAP_RESAMPLES,
                 'randomization_resamples': pa.RANDOMIZATION_RESAMPLES, 'seed': pa.SEED,
                 'sensitivity': 'query-level bootstrap + sign-flip test if largest component > 50% of queries',
                 'secondary_descriptive': ['Recall@100', 'nDCG@10', 'nDCG@100', 'ALL/IN/OUT', 'exposure@200', 'exposure strata',
                                           'rescue/displacement', 'wins/losses/ties', 'first-positive rank bins', 'unjudged share top-10',
                                           'FA/GR lexical descriptives', 'failures', 'costs']},
    'failure_rules': {'unusable_output': 'original-query fallback; query kept in denominator', 'backend_unknown_state': 'HOLD; never retried automatically',
                      'input_over_cap': 'fallback (INPUT_LIMIT)', 'revision': 'at most one prompt/schema revision, only for an engineering failure on authored synthetic text',
                      'outcome_driven_retry': False},
    'stages': ['S1 CPU grammar qualification (FA/GR)', 'S2 synthetic GPU smoke (<=2 calls, <=1800 s per arm)',
               'S3 technical pilot on pilot-20 (throughput/failures only; not evaluated separately)',
               'S4 full-dev generation: SACR 6x79 batches (<=10800 s each), FA and GR batches from measured throughput',
               'S5 dev retrieval, fusion, evaluation', 'S6 owner checkpoint: proceed or stop only; plan cannot change',
               'S7 test stage amendment (journal stage "test", predecessor full_dev) and explicit go', 'S8 test generation, retrieval, single evaluation'],
    'graph': 'feasibility/negative section only; no Graph retrieval or GPU in Paper 1',
    'no_human_audit': True, 'no_llm_judge': True,
    'disclosures': ['B0 dev measured', 'SACR pilot-20 dev evaluated before drafting (0 OUT rescues)', 'R1-R7 history',
                    'Graph G2 FAIL and post-hoc owner override', 'new arms never run on DAPFAM at freeze', 'test split unopened'],
}
OUT.parent.mkdir(exist_ok=True)
with OUT.open('x', encoding='utf-8') as f: json.dump(manifest, f, indent=2, ensure_ascii=False); f.write('\n')
print(json.dumps({'frozen_commit': manifest['frozen_commit'], 'manifest_sha256': sha(OUT.read_bytes())}))
