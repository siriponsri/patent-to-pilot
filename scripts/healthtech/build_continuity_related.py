"""Build the task-level continuity link table for family-aware splits (D1). Stdlib only.

Rule (DECLARED before the first run; written after a type/number-shape census of the two
related-document tables only, before any task was linked):

Inputs (PatentsView release 2026-04-10, ODP):
  g_us_rel_doc, pg_us_rel_doc  (related documents of grants / pre-grant publications)
  g_application                (patent_id -> application_id)
  pg_published_application     (pgpub_id  -> application_id)
  tasks.tsv                    (metadata column app_id only)

Nodes: US application numbers (8 digits after removing '/', ',' and spaces) as 'A:<num>'.
       A 'parent-grant-document' number is a US patent number and is mapped to its application
       through g_application; unmapped patent numbers become 'P:<num>'.
       A 'parent-pct-document' number becomes 'W:<normalised>' (a shared PCT parent joins siblings).
       Anything else that is not 8 digits becomes 'X:<raw>'.
Edges (primary rule): related_doc_type in {continuation, continuation-in-part, division,
       substitution, reissue, continuing-reissue} (US domestic continuity).
       Excluded: related-publication (the document's own publication), correction,
       us-reexamination-reissue-merger.
Sensitivity variant (reported, not used for the split): primary + us-provisional-application
       (a shared provisional joins applications).
Components: union-find over all nodes. For each task: group = component representative.
Output: related.tsv (app_id, related_app_id = component representative) for every task, for each
       variant; stats JSON with group-size distribution. No label column is read.

Usage: python3 -I build_continuity_related.py <patentsview_dir> <tasks.tsv> <out_dir>
"""
from __future__ import annotations

import collections
import csv
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
PRIMARY = {'continuation', 'continuation-in-part', 'division', 'substitution', 'reissue', 'continuing-reissue'}
PROVISIONAL = 'us-provisional-application'


def tsv(d: Path, name: str):
    z = zipfile.ZipFile(d / f'{name}.tsv.zip')
    return csv.DictReader(io.TextIOWrapper(z.open(f'{name}.tsv'), encoding='utf-8', newline=''), delimiter='\t')


def app_norm(s: str) -> str | None:
    t = re.sub(r'[\s/,]', '', s or '')
    return t if re.fullmatch(r'\d{8}', t) else None


class UF:
    def __init__(self):
        self.p: dict[str, str] = {}

    def find(self, x):
        p = self.p
        p.setdefault(x, x)
        r = x
        while p[r] != r:
            r = p[r]
        while p[x] != r:
            p[x], x = r, p[x]
        return r

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if rb < ra:
                ra, rb = rb, ra
            self.p[rb] = ra


def main(argv):
    pv, tasks_path, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    with open(tasks_path, encoding='utf-8', newline='') as f:
        tasks = [r['app_id'].strip() for r in csv.DictReader(f, delimiter='\t')]
    patent_app = {r['patent_id']: app_norm(r['application_id']) for r in tsv(pv, 'g_application')}
    pg_app = {r['pgpub_id']: app_norm(r['application_id']) for r in tsv(pv, 'pg_published_application')}

    def node(num: str, kind: str) -> str:
        if kind == 'parent-grant-document':
            a = patent_app.get(num.lstrip('0') if num.isdigit() else num) or patent_app.get(num)
            return f'A:{a}' if a else f'P:{num}'
        if kind == 'parent-pct-document':
            return 'W:' + re.sub(r'[^0-9A-Z]', '', num.upper())
        a = app_norm(num)
        return f'A:{a}' if a else f'X:{num}'

    ufs = {'primary': UF(), 'with_provisional': UF()}
    stats = collections.Counter()
    for table, idcol, idmap in (('g_us_rel_doc', 'patent_id', patent_app), ('pg_us_rel_doc', 'pgpub_id', pg_app)):
        for r in tsv(pv, table):
            typ = r['related_doc_type']
            if typ not in PRIMARY and typ != PROVISIONAL:
                continue
            src = idmap.get(r[idcol])
            if not src:
                stats[f'{table}:unmapped_source'] += 1
                continue
            a, b = f'A:{src}', node(r['related_doc_number'].strip(), r.get('related_doc_kind', ''))
            stats[f'{table}:{typ}:{b[0]}'] += 1
            ufs['with_provisional'].union(a, b)
            if typ in PRIMARY:
                ufs['primary'].union(a, b)
    result = {'rule': {'primary_types': sorted(PRIMARY), 'sensitivity_adds': PROVISIONAL},
              'edge_counts': dict(sorted(stats.items())), 'n_tasks': len(tasks), 'variants': {}}
    for v, uf in ufs.items():
        groups = {t: uf.find(f'A:{t}') for t in tasks}
        size = collections.Counter(groups.values())
        dist = collections.Counter(min(s, 10) for s in size.values())
        task_roots = set(groups.values())
        comp_nodes = collections.Counter(r for r in (uf.find(n) for n in list(uf.p)) if r in task_roots)
        result['variants'][v] = {
            'n_groups': len(size), 'tasks_in_multi_task_groups': sum(s for s in size.values() if s > 1),
            'max_tasks_per_group': max(size.values()), 'group_size_hist_cap10': dict(sorted(dist.items())),
            'tasks_with_any_link': sum(1 for t in tasks if comp_nodes.get(groups[t], 1) > 1)}
        with open(out / f'related-{v}.tsv', 'w', encoding='utf-8', newline='') as f:
            f.write('app_id\trelated_app_id\n')
            for t, g in groups.items():
                f.write(f'{t}\t{g}\n')
    result['seconds'] = round(time.time() - t0, 1)
    (out / 'continuity-stats.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'edge_counts'}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
