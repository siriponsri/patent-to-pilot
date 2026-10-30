"""Validate this authored UX documentation pack; no UI/server/provider execution.

Run from the repository root:
  rtk proxy python -B docs/healthtech/ux/validate_docs.py --repo-root .
Optionally use --receipt PATH to write a fresh documentation receipt.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    pack = Path(__file__).resolve().parent
    logical = repo / 'docs' / 'healthtech' / 'ux'
    sys.path.insert(0, str(repo / 'src'))
    from jsonschema import Draft202012Validator, FormatChecker, ValidationError as JSONSchemaValidationError
    from patent_to_pilot.healthtech.contracts import DossierVersion, content_hash
    from patent_to_pilot.healthtech.engine import DossierInput
    from patent_to_pilot.healthtech.provenance import check_evidence

    checks = []
    def check(name, fn):
        try:
            detail = fn()
            checks.append({'check': name, 'status': 'PASS', 'detail': detail})
        except Exception as exc:
            checks.append({'check': name, 'status': 'FAIL', 'detail': str(exc)})

    md_files = sorted(pack.glob('*.md'))
    texts = {p.name: p.read_text(encoding='utf-8') for p in md_files}
    id_pattern = re.compile(r'\b(?:J|US|SCR|CMP|ST|CAP|FX)-\d{2}\b')
    definitions = {}
    sources = {'J':'01_PERSONAS_JOURNEYS.md', 'US':'02_STORY_BACKLOG.md',
        'SCR':'03_SCREENS_DESIGN.md','CMP':'03_SCREENS_DESIGN.md',
        'ST':'04_INTEGRATION_STATES.md','CAP':'04_INTEGRATION_STATES.md','FX':'04_INTEGRATION_STATES.md'}
    expected_counts={'J':9,'US':28,'SCR':11,'CMP':14,'ST':15,'CAP':10,'FX':15}
    for prefix, file in sources.items():
        for line in texts[file].splitlines():
            pat = (rf'^### ({prefix}-\d{{2}})\b' if prefix in {'J','US','SCR'}
                   else rf'^\| ({prefix}-\d{{2}}) \|')
            match = re.match(pat, line)
            if match:
                identity=match.group(1)
                if identity in definitions:
                    raise ValueError(f'duplicate definition: {identity}')
                definitions[identity]=file

    bundle = json.loads((pack/'fixtures/ui-fixtures.json').read_text(encoding='utf-8'))
    schema = json.loads((pack/'fixtures/ui-fixtures.schema.json').read_text(encoding='utf-8'))
    def links():
        count=0
        for name, text in texts.items():
            for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)', text):
                target=target.strip().strip('<>')
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):
                    continue
                filepart, _, fragment=unquote(target).partition('#')
                rel=(logical/filepart).resolve()
                candidate=pack/rel.relative_to(logical) if rel.is_relative_to(logical) else rel
                if not candidate.exists():
                    # Receipt is a generated deliverable during the first validation.
                    if candidate.name=='verification.json' and args.receipt and args.receipt.resolve()==candidate.resolve():
                        pass
                    else:
                        raise AssertionError(f'{name}: missing local link {target}')
                if fragment:
                    raise AssertionError(f'{name}: anchor check not implemented; use whole-file link: {target}')
                count+=1
        return {'local_links':count, 'network_link_checks':'NOT_RUN (local-only scope)'}
    check('local_markdown_links', links)

    def ids():
        for prefix, count in expected_counts.items():
            actual={x for x in definitions if x.startswith(prefix+'-')}
            expected={f'{prefix}-{i:02}' for i in range(1,count+1)}
            assert actual==expected,(prefix,actual^expected)
        for name,text in {**texts,'ui-fixtures.json':json.dumps(bundle,ensure_ascii=False)}.items():
            for identity in id_pattern.findall(text):
                assert identity in definitions,(name,identity)
        assert {r['id'] for r in bundle['scenarios']}=={f'FX-{i:02}' for i in range(1,16)}
        return expected_counts
    check('cross_document_ids_and_fixture_references',ids)

    def stories():
        chunks=re.split(r'^### (US-\d{2})[^\n]*\n',texts['02_STORY_BACKLOG.md'],flags=re.M)
        graph={}
        for i in range(1,len(chunks),2):
            identity,body=chunks[i:i+2]
            assert all(x in body for x in ['**Priority:**','**Depends:**','HT-G3/HT-G7','HT-W','**Given**','**when**','**then**']),identity
            deps=re.search(r'\*\*Depends:\*\* (.*?)\. \*\*Map:',body)
            assert deps,identity
            graph[identity]=re.findall(r'US-\d{2}',deps.group(1))
        def visit(node, chain):
            assert node not in chain,('cycle',chain,node)
            for child in graph[node]:
                assert child in graph,child
                visit(child,chain+[node])
        for identity in graph: visit(identity,[])
        assert len(graph)==28
        return {'stories':len(graph),'dependencies':'acyclic','acceptance':'Given/When/Then and HT mapping present'}
    check('story_mapping_and_dependencies',stories)

    def fixture_schema():
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(bundle)
        return {'envelope':'ux-fixtures-v1','scenarios':len(bundle['scenarios'])}
    check('fixture_envelope_json_schema',fixture_schema)

    domain_schema=json.loads((repo/'schemas/healthtech/DossierVersion.schema.json').read_text(encoding='utf-8'))
    def domain_validate(raw):
        Draft202012Validator(domain_schema,format_checker=FormatChecker()).validate(raw)
        d=DossierVersion.model_validate(raw)
        assert d.query.brief.data_class!='private','private data not accepted'
        by_id={s.source.source_id:s for s in d.sources}
        for s in d.sources:
            assert s.source_date<=d.query.evidence_cutoff,'source newer than cutoff'
            if d.query.brief.data_class=='public':
                assert not s.synthetic,'synthetic cannot become public'
        for e in d.evidence:
            checked=check_evidence(e,by_id[e.source_id])
            assert checked.verification_status==e.verification_status,'imported check badge not reproducible'
        by_eid={e.evidence_id:e for e in d.evidence}
        for c in d.candidates:
            assert c.source_revision==by_id[c.source_id].source.version_label,'candidate revision mismatch'
            if c.association_status=='disclosed_link':
                e=by_eid[c.disclosure_evidence_id]
                assert e.source_id!=c.source_id,'disclosure is not independent of candidate document'
                assert by_id[e.source_id].source.source_type=='independent_disclosure','independent disclosure source required'
        return d

    def positives():
        details=[]
        for key in ['synthetic_dossier','empty_corpus_dossier']:
            d=domain_validate(bundle[key])
            assert d.query.brief.data_class=='synthetic'
            assert all(s.synthetic and s.source.uri.startswith('urn:synthetic:') for s in d.sources)
            details.append({'payload':key,'sources':len(d.sources),'evidence':len(d.evidence),'candidates':len(d.candidates)})
        u=next(e for e in bundle['synthetic_dossier']['evidence'] if e['evidence_id']=='ux-e-unicode')
        assert u['quoted_span']=='🙂' and u['locator']=='chars:1:2'
        return details
    check('embedded_dossiers_schema_pydantic_source_integrity',positives)

    def negatives():
        mutations={
            'payload_hash_mismatch':lambda d:d['sources'][0].update(payload={'device_name':'changed'}),
            'locator_mismatch':lambda d:d['evidence'][2].update(locator='chars:0:1'),
            'source_revision_mismatch':lambda d:d['evidence'][0].update(source_version='wrong-revision'),
            'dangling_evidence_source':lambda d:d['evidence'][0].update(source_id='missing'),
            'missing_disclosure':lambda d:d['candidates'][1].update(disclosure_evidence_id=None),
            'raw_canonical_mismatch':lambda d:d['candidates'][0].update(patent_id_canonical='US99000001B2'),
            'synthetic_presented_as_public':lambda d:d['query']['brief'].update(data_class='public'),
            'source_after_cutoff':lambda d:d['query'].update(evidence_cutoff='2026-10-26'),
            'candidate_revision_mismatch':lambda d:d['candidates'][0].update(source_revision='wrong'),
            'unsourced_family':lambda d:d['candidates'][0].update(family_id='invented-family'),
        }
        rejected=[]
        for name,mutate in mutations.items():
            raw=deepcopy(bundle['synthetic_dossier']);mutate(raw)
            try:domain_validate(raw)
            except (ValueError,AssertionError,KeyError,JSONSchemaValidationError) as exc:
                # JSON Schema errors and Pydantic errors are expected failures here.
                rejected.append({'case':name,'rejected_by':type(exc).__name__})
            else:raise AssertionError('accepted invalid mutation: '+name)
        input_raw=json.loads((repo/'examples/healthtech/synthetic-device/input.json').read_text(encoding='utf-8'))
        DossierInput.model_validate(input_raw)
        input_raw['gold_labels']={'forbidden':'evaluator data'}
        try:DossierInput.model_validate(input_raw)
        except ValueError:rejected.append({'case':'runtime_gold_extra_field','rejected_by':'closed_DossierInput'})
        else:raise AssertionError('runtime accepted evaluator extra field')
        return rejected
    check('hand_computable_negative_imports',negatives)

    def public_scope():
        rows=[]
        for kid in ['K190167','K163345','K121849']:
            inp=repo/f'results/healthtech/public-510k-20261027-r1/inputs/{kid}.json'
            out=repo/f'results/healthtech/public-dossiers-20261027-r3/{kid}/dossier.json'
            if not inp.exists() or not out.exists():
                rows.append({'device_id':kid,'status':'NOT_AVAILABLE_IN_THIS_CHECKOUT'})
                continue
            raw_in=json.loads(inp.read_text(encoding='utf-8'));raw_out=json.loads(out.read_text(encoding='utf-8'))
            assert raw_in['patents']==[] and raw_out['candidates']==[],kid
            assert len(raw_out['evidence'])==7,kid
            rows.append({'device_id':kid,'patent_input_count':0,'candidate_count':0,'evidence_count':7,
                'input_sha256':sha(inp),'dossier_sha256':sha(out),'scope':'public_source_engineering_only'})
        return rows
    check('read_only_current_public_empty_pool_observation',public_scope)

    def contrast():
        palette={}
        for line in texts['03_SCREENS_DESIGN.md'].splitlines():
            if re.match(r'^\| (canvas|surface|text|mutedText|primary|onPrimary|focusRing) \|',line):
                cells=[x.strip().strip('`') for x in line.split('|')[1:-1]]
                palette[cells[0]]=cells[1:]
        def luminance(h):
            rgb=[int(h[j:j+2],16)/255 for j in (1,3,5)]
            linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in rgb]
            return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))
        def ratio(a,b):
            x,y=sorted([luminance(a),luminance(b)])
            return (y+.05)/(x+.05)
        results=[]
        for i,theme in enumerate(['formal-light','formal-dark','kmitl-inspired','ict-inspired']):
            for fg,bg,min_ratio in [('text','canvas',4.5),('text','surface',4.5),('mutedText','canvas',4.5),
                    ('mutedText','surface',4.5),('onPrimary','primary',4.5),('focusRing','canvas',3),('focusRing','surface',3)]:
                actual=ratio(palette[fg][i],palette[bg][i])
                assert actual>=min_ratio,(theme,fg,bg,actual)
                results.append({'theme':theme,'pair':fg+'/'+bg,'ratio':round(actual,2),'minimum':min_ratio})
        return {'token_pairs':results,'scope':'proposed colors only; rendered UI/semantic states NOT_RUN'}
    check('proposed_theme_token_contrast',contrast)

    source_paths=['AGENTS.md','GOAL.md','PLAN.md','README.md','docs/healthtech/progress.json','memory/next-actions.md',
        'src/patent_to_pilot/product/contracts.py','src/patent_to_pilot/healthtech/contracts.py',
        'src/patent_to_pilot/healthtech/engine.py','src/patent_to_pilot/healthtech/history.py',
        'src/patent_to_pilot/healthtech/provenance.py','src/patent_to_pilot/healthtech/sources.py',
        'src/patent_to_pilot/healthtech/api.py','schemas/healthtech/DossierVersion.schema.json',
        'scripts/healthtech/run_dossier.py','scripts/healthtech/manage_dossier_history.py',
        'scripts/healthtech/view_dossier_source.py','scripts/healthtech/run_api_dry_run.py']
    fingerprints=[{'path':p,'sha256':sha(repo/p)} for p in source_paths]
    audit=Path(r'C:\Users\User\Documents\Codex\2026-10-27\task-3\pepo-luna-readonly-audit-r1\AUDIT_TH.md')
    audit_ref={'path':str(audit),'sha256':sha(audit) if audit.exists() else None,
        'status':'supplied_read_only_audit_not_repeated','reported_verdict':'CHANGES_REQUIRED','reported_clean_tests':269}
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=repo,check=True,capture_output=True,text=True).stdout.strip()
    result={'package':'HT-W13-UX-DOCUMENTATION','status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',
        'verified_at_utc':datetime.now(timezone.utc).isoformat(),'base_commit_observed':head,
        'command_argv':sys.argv,'checks':checks,'source_fingerprints':fingerprints,'supplied_audit':audit_ref,
        'authored_files':[{'path':str(p.relative_to(pack)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)}
            for p in sorted(pack.rglob('*')) if p.is_file() and p.name!='verification.json' and not p.name.endswith('.pyc')],
        'not_run':['UI implementation','screenshots','frontend browser/build tests','live APIs/providers',
            'scientific benchmarks','new user/commercial study','deployment','backend fixes','commit/push'],
        'source_directory_changes':'none by validator; only optional receipt path is written'}
    if args.receipt:
        args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[x for x in checks if x['status']=='FAIL'],
        'counts':expected_counts,'receipt':str(args.receipt) if args.receipt else None},ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
