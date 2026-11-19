"""Fill the faculty IS short-paper template (AI4BA) from docs/writing/is2/IS2-SHORT-PAPER-DRAFT.md.

Keeps the template's own run formatting and its section breaks (single-column title block, two-column body) by copying
template paragraphs as format exemplars. Usage:
  python build_is2_shortpaper_docx.py <template.docx> <draft.md> <out.docx>
Markdown conventions used by the draft:
- '## N. title' = main heading;
- a line '**x.y title**' at line start (optionally followed by text) = sub-heading;
- '- ' = bullet; '|' rows = table;
- '[n] ...' under 'เอกสารอ้างอิง' = reference.
"""
import copy, re, sys
import docx
from docx.shared import Pt

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def has_sect(p):
    return p._p.pPr is not None and p._p.pPr.find(W + 'sectPr') is not None


def set_text(p, text, bold=None):
    for h in p._p.findall(W + 'hyperlink'):          # template e-mails are hyperlinks outside p.runs
        h.getparent().remove(h)
    runs = p.runs
    if not runs:
        p.add_run(text)
        return p
    runs[0].text = text
    if bold is not None:
        runs[0].bold = bold
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    return p


def clone_after(anchor_el, exemplar, text, bold=None):
    new = copy.deepcopy(exemplar._p)
    anchor_el.addnext(new)
    p = docx.text.paragraph.Paragraph(new, exemplar._parent)
    set_text(p, text, bold)
    return p


def parse(md):
    lines = md.splitlines()
    sec = {}
    cur = None
    for l in lines:
        m = re.match(r'^(#{2,3}) (.*)$', l)
        if m:
            cur = m.group(2).strip(); sec[cur] = []
            continue
        if cur is not None:
            sec[cur].append(l)
    return sec


def block_text(ls):
    return ' '.join(x.strip().lstrip('- ').strip() for x in ls if x.strip() and not x.startswith('**คำสำคัญ') and not x.startswith('**Keywords'))


def main(tpl, md_path, out):
    md = open(md_path, encoding='utf-8').read()
    sec = parse(md)
    d = docx.Document(tpl)
    P = d.paragraphs
    th_title = sec['ชื่อบทความ (TH)'][1].strip() if sec['ชื่อบทความ (TH)'][0] == '' else sec['ชื่อบทความ (TH)'][0].strip()
    th_lines = [x for x in sec['ชื่อบทความ (TH)'] if x.strip()]
    en_lines = [x for x in sec['Title (EN)'] if x.strip()]
    set_text(P[2], th_lines[0]); set_text(P[3], th_lines[1]); set_text(P[4], th_lines[2]); set_text(P[5], th_lines[3])
    abs_th = sec['บทคัดย่อ']; kw_th = [x for x in abs_th if x.startswith('**คำสำคัญ')][0].replace('**', '')
    set_text(P[8], block_text(abs_th)); set_text(P[10], kw_th)
    abs_en = sec['Abstract']; kw_en = [x for x in abs_en if x.startswith('**Keywords')][0].replace('**', '')
    foot = [x.strip() for x in abs_en if x.strip().startswith(('\\*', '1.', '2.'))]
    abs_en_body = [x for x in abs_en if not x.strip().startswith(('\\*', '1.', '2.', '---'))]
    set_text(P[22], '* Author’s Email: 68076060@kmitl.ac.th')
    set_text(P[23], '1 นักศึกษาปริญญาโท สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง')
    set_text(P[24], '2 [ตำแหน่ง] คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง')
    set_text(P[25], en_lines[0]); set_text(P[27], en_lines[1]); set_text(P[28], en_lines[2]); set_text(P[29], '')
    set_text(P[32], block_text(abs_en_body)); set_text(P[34], kw_en)
    set_text(P[52], '* Author’s Email: 68076060@kmitl.ac.th')
    set_text(P[53], '1. Postgraduate Student, Artificial Intelligence for Business Analytics Program, School of Information Technology, King Mongkut\'s Institute of Technology Ladkrabang')
    set_text(P[54], '2. [Position], School of Information Technology, King Mongkut\'s Institute of Technology Ladkrabang')
    head_ex, body_ex, sub_ex = copy.deepcopy(P[55]), copy.deepcopy(P[56]), copy.deepcopy(P[59])
    head_ex = docx.text.paragraph.Paragraph(head_ex._p, P[55]._parent)
    body_ex = docx.text.paragraph.Paragraph(body_ex._p, P[56]._parent)
    sub_ex = docx.text.paragraph.Paragraph(sub_ex._p, P[59]._parent)
    ack_head, ack_body, ref_head, ref_body = P[102], P[103], P[105], P[106]
    # remove the template body (55..100) except section-break paragraphs; remove appendix + manual links (107..110)
    anchor = P[54]._p
    for i in list(range(55, 101)) + list(range(107, 111)):
        if not has_sect(P[i]):
            P[i]._p.getparent().remove(P[i]._p)
    # body sections 1..5
    body_keys = [k for k in sec if re.match(r'^\d\. ', k)]
    el = anchor
    for k in body_keys:
        el = clone_after(el, head_ex, k)._p
        rows = []
        merged = []                      # join consecutive plain lines into one paragraph
        for l in sec[k]:
            s0 = l.strip()
            plain = s0 and not s0.startswith(('|', '- ', '**', '[')) and not l.startswith('  ')
            if plain and merged and merged[-1][1]:
                merged[-1] = (merged[-1][0] + ' ' + s0, True)
            else:
                merged.append((l, bool(plain)))
        for l in [m[0] for m in merged] + ['']:
            s = l.strip()
            if s.startswith('|'):
                rows.append([c.strip() for c in s.strip('|').split('|')]); continue
            if rows:
                rows = [r for r in rows if not set(''.join(r)) <= set('-: ')]
                t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = d.styles['Table Grid'] if 'Table Grid' in [s.name for s in d.styles] else t.style
                for i, r in enumerate(rows):
                    for j, c in enumerate(r):
                        cell = t.cell(i, j); cell.text = c
                        for pp in cell.paragraphs:
                            for rr in pp.runs:
                                rr.font.size = Pt(11); rr.font.name = 'TH SarabunPSK'; rr.bold = (i == 0)
                t.autofit = False
                widths = [1.25] + [(3.05 - 1.25) / (len(rows[0]) - 1)] * (len(rows[0]) - 1)
                for j, wd in enumerate(widths):
                    for cell in t.columns[j].cells:
                        cell.width = docx.shared.Inches(wd)
                for gc, wd in zip(t._tbl.tblGrid.findall(W + 'gridCol'), widths):   # grid widths drive the layout
                    gc.set(W + 'w', str(int(wd * 1440)))
                tblPr = t._tbl.tblPr
                tw = tblPr.find(W + 'tblW')
                if tw is None:
                    tw = docx.oxml.OxmlElement('w:tblW'); tblPr.append(tw)
                tw.set(W + 'w', str(int(3.05 * 1440))); tw.set(W + 'type', 'dxa')
                el.addnext(t._tbl); el = t._tbl; rows = []
            if not s or s.startswith('[PENDING') and False:
                continue
            m = re.match(r'^\*\*(\d\.\d[^*]*)\*\*\s*(.*)$', s)
            if m:
                el = clone_after(el, sub_ex, m.group(1).strip())._p
                if m.group(2):
                    el = clone_after(el, body_ex, m.group(2).strip())._p
                continue
            if s.startswith('**กิตติกรรมประกาศ'):
                set_text(ack_body, s.split('**', 2)[2].strip()); continue
            txt = s.replace('**', '')
            if s.startswith('- '):
                txt = '• ' + txt[2:]
            elif l.startswith('  ') and not s.startswith('|'):
                txt = '   ' + txt
            el = clone_after(el, body_ex, txt)._p
    set_text(ack_head, 'กิตติกรรมประกาศ'); set_text(ref_head, 'เอกสารอ้างอิง')
    refs = [x.strip() for x in sec['เอกสารอ้างอิง'] if x.strip().startswith('[')]
    set_text(ref_body, refs[0].replace('*', ''))
    el = ref_body._p
    for r in refs[1:]:
        el = clone_after(el, ref_body, r.replace('*', ''))._p
    d.save(out)
    print('saved', out, 'paragraphs', len(d.paragraphs), 'tables', len(d.tables))


if __name__ == '__main__':
    main(*sys.argv[1:])
