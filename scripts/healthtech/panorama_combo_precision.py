"""Measure how often 'co-cited under 103 in the same office action' (the AM-7 E2 label) is a true claim-level combination.

Uses PANORAMA (LG AI Research, CC BY-NC-SA 4.0; 8,143 USPTO records), whose parsed_CTNF field lists, per claim and per
rejection reason, the section code and the ordered cited patents (first listed = primary reference).
For every action with >= 2 distinct 103 references, every unordered pair of its 103 references is checked:
  together = the two appear in at least one claim-level 103 reason;
  with_primary = one of them is the first-listed reference of a 103 reason that also lists the other.
No P1 data is read. Usage: python -I panorama_combo_precision.py <panorama.parquet> <out.json>
"""
import itertools, json, sys

import pyarrow.parquet as pq


def combos(parsed):
    sets = []
    for c in json.loads(parsed):
        for rs in c.get('reasons', []):
            if rs.get('sectionCode') == 103:
                pats = [x['patentNum'] for x in rs.get('citedPatents', [])]
                if pats:
                    sets.append(pats)
    return sets


def measure(rows):
    acts = pairs = together = prim = 0
    macro = []
    for r in rows:
        sets = combos(r['parsed_CTNF'])
        refs = sorted({x for s in sets for x in s})
        if len(refs) < 2:
            continue
        tog, pr = set(), set()
        for s in sets:
            tog.update(itertools.combinations(sorted(set(s)), 2))
            pr.update(tuple(sorted((s[0], b))) for b in s[1:] if b != s[0])
        allp = list(itertools.combinations(refs, 2))
        t = sum(1 for x in allp if x in tog)
        acts += 1; pairs += len(allp); together += t; prim += sum(1 for x in allp if x in pr); macro.append(t / len(allp))
    return {'actions': acts, 'pairs': pairs, 'pair_together_share': round(together / pairs, 4),
            'pair_with_primary_share': round(prim / pairs, 4), 'macro_together_share': round(sum(macro) / len(macro), 4)}


if __name__ == '__main__':
    rows = pq.read_table(sys.argv[1], columns=['filingDate', 'parsed_CTNF']).to_pylist()
    res = {'format': 'ptp-panorama-combo-precision-v1', 'records': len(rows),
           'all': measure(rows), 'filed_le_2014': measure([r for r in rows if r['filingDate'][:4] <= '2014'])}
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
    print(json.dumps(res, indent=1))
