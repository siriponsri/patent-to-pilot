"""Render B53 Stage 2 results (b53_stage2_eval.py output) as Markdown tables for IS2 section 4.2 (Thai labels).

Table 1 (B53.3, confirmatory): for each first stage F0-F4, Patent-aware - Generic and Claim-focused - Generic on the
common-exposed set C: delta, 95% CI, Holm p, wins/losses.
Table 2 (descriptive): mean strict OUT nDCG@100 over all OUT queries per first stage for Generic, Patent-aware,
Claim-focused, Scrambled, BGE plain-pair and no rerank.
Usage: python render_b53_stage2.py <stage2-results.json> <out.md>
"""
import json, sys

ARMS = ('F0', 'F1', 'F2', 'F3', 'F4')
NAMES = {'F0': 'F0 patembed-base', 'F1': 'F1 BM25', 'F2': 'F2 RRF(F1, F0)', 'F3': 'F3 Arctic-embed', 'F4': 'F4 RRF(F1, F3)'}
SYSTEMS = (('generic', 'Generic'), ('patent_aware', 'Patent-aware'), ('claim_focused', 'Claim-focused'),
           ('scrambled', 'Scrambled'), ('bge', 'BGE'), ('norerank', 'ไม่ rerank'))


def fmt(x, signed=True):
    if x is None:
        return '—'
    s = f'{x:+.3f}' if signed else f'{x:.3f}'
    return s.replace('-', '−')


def fp(p):
    return '< 0.001' if p < 0.001 else f'{p:.3f}'


def render(r):
    out = [f"ชุดคำค้นที่ทุกแขน exposed ร่วมกัน (C) = {r['C']} คำค้น จาก OUT ทั้งหมด {r['n_out']} คำค้น", '',
           '| ตัวค้นคืนขั้นแรก | Patent-aware − Generic [95% CI] | Holm p | Claim-focused − Generic [95% CI] | Holm p |',
           '|---|---|---|---|---|']
    P = r['B53_3_primary_on_C']
    for F in ARMS:
        cells = []
        for a in ('patent_aware', 'claim_focused'):
            e = P[f'{F}|{a}-generic']
            cells += [f"{fmt(e['delta_C'])} [{fmt(e['ci95'][0])}, {fmt(e['ci95'][1])}] ({e['wins']}/{e['losses']})", fp(e['holm_p'])]
        out.append(f'| {NAMES[F]} | ' + ' | '.join(cells) + ' |')
    out += ['', 'ตัวเลขในวงเล็บท้ายคือจำนวนคำค้นที่ดีขึ้น/แย่ลง', '',
            '| ตัวค้นคืนขั้นแรก | π@100 | ' + ' | '.join(n for _, n in SYSTEMS) + ' |', '|' + '---|' * (len(SYSTEMS) + 2)]
    M = r['mean_ndcg100']
    for F in ARMS:
        out.append(f"| {NAMES[F]} | {fmt(r['pi100'][F], False)} | " + ' | '.join(fmt(M.get(f'{F}|{s}'), False) for s, _ in SYSTEMS) + ' |')
    out += ['', 'ค่าในตารางที่สองคือ strict OUT nDCG@100 เฉลี่ยบนคำค้น OUT ทั้งหมด (คำค้นที่ไม่ exposed = 0) เป็นผลเชิงพรรณนา']
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    r = json.load(open(sys.argv[1], encoding='utf-8'))
    open(sys.argv[2], 'w', encoding='utf-8').write(render(r))
    print(open(sys.argv[2], encoding='utf-8').read())
