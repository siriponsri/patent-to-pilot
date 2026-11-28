"""Convert an IS2 Markdown draft into a kmitl-is-paper content module (paperkit contract).

Usage from a content module:
    from md2content import load
    globals().update(load("../IS2-DRAFT-TH.md", "th"))
"""
import re
from pathlib import Path

TEXT_W, COL_TW = 9360, 4320
LINK = re.compile(r"!?\[([^\]]*)\]\(([^)]*)\)")
EMPH = re.compile(r"(\*\*[^*]+\*\*|(?<![\\*])\*[^*]+\*)")


def _links(text, ref=False):
    def sub(m):
        label, url = m.group(1), m.group(2)
        if not url.startswith("http"):
            return "\x00"  # internal receipt link: dropped in print
        if ref:
            return label if label.lower().startswith("doi:") else "[Online]. Available: " + url
        return label
    t = LINK.sub(sub, text)
    t = re.sub(r"\s*(·\s*)?\x00(\s*·\s*\x00)*", "", t)
    return t.strip()


def _breaks(t):
    """Reference layout: zero-width break after the last "/" of a URL; keep "(C′ scoring)" together."""
    t = re.sub(r"(https?://\S*/)(?=[^/\s]+)", lambda m: m.group(1) + "​", t)
    return t.replace("(C′ scoring)", "(C′ scoring)")


def inline(text, ref=False):
    t = _links(text, ref)
    if ref:
        t = _breaks(t)
    out = []
    for part in EMPH.split(t):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append((part[2:-2], {"b": True}))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append((part[1:-1], {"i": True}))
        else:
            out.append(part)
    return [(s[0].replace("\\*", "*"), s[1]) if isinstance(s, tuple) else s.replace("\\*", "*") for s in out]


def plain(text):
    return "".join(s[0] if isinstance(s, tuple) else s for s in inline(text))


def _widths(rows, total):
    n = len(rows[0])
    head = [max(len(t) for t in plain(rows[0][i]).split()) for i in range(n)]
    cells = [max([len(plain(r[i])) for r in rows[1:]] or [0]) for i in range(n)]
    w = [min(max(5, head[i], cells[i]) + 2, 40) for i in range(n)]
    s = sum(w)
    tw = [int(total * x / s) for x in w]
    tw[-1] += total - sum(tw)
    return tw


def load(md_path, lang):
    here = Path(__file__).resolve().parent
    L = (here / md_path).read_text(encoding="utf-8").split("\n")
    nonblank = lambda i: next(j for j in range(i, len(L)) if L[j].strip())  # noqa: E731

    def after(head):
        i = L.index(head)
        return L[nonblank(i + 1)].strip()

    kw = lambda tag: next(x for x in L if x.startswith(tag))[len(tag):].strip()  # noqa: E731
    C = {
        "LANG": lang,
        "TITLE_TH": L[0][2:].strip(),
        "TITLE_EN": L[2][2:].strip(),
        "AUTH_TH": ["นายศิริพล ศรีเฮงไพบูลย์", " และ ผศ.ดร.ทัศนัย พลอยสุวรรณ"],
        "AUTH_EN": ["Siripon Srihangpiboon", " and Tuchsanai Ploysuwan"],
        "ABS_TH": plain(after("## บทคัดย่อ")),
        "ABS_EN": plain(after("## Abstract")),
        "KW_TH": kw("**คำสำคัญ**"),
        "KW_EN": kw("**Keywords**"),
        "EMAIL": "68076060@kmitl.ac.th",
        "ADVISOR_FOOT_TH": "ผู้ช่วยศาสตราจารย์ คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "AUTHOR_META": "Siripon Srihangpiboon; Tuchsanai Ploysuwan",
    }
    start = next(i for i, x in enumerate(L) if re.match(r"^## 1[ .]", x))
    body, i, in_refs = [], start, False
    while i < len(L):
        x = L[i].rstrip()
        s = x.strip()
        if not s:
            i += 1
            continue
        if s.startswith("## "):
            h = s[3:].strip()
            h = re.sub(r"^(\d+) ", r"\1. ", h)
            in_refs = h in ("References", "เอกสารอ้างอิง")
            # Keep the body and its floating tables on a separate page from the front matter.
            body.append(("h1", h, i == start))
        elif s.startswith("### "):
            body.append(("h2", s[4:].strip()))
        elif in_refs and s.startswith("["):
            body.append(("ref", inline(s, ref=True)))
        elif s.startswith("!["):
            f = LINK.match(s).group(2).split("/")[-1]
            j = nonblank(i + 1)
            cap = L[j].strip().strip("*")
            full = f.startswith(("fig1", "fig2_recall"))
            body.append(("fig", f, 6.5 if full else 3.0, cap, full))
            i = j
        elif s.startswith("*") and re.match(r"^\*(Table \d|ตารางที่ \d)", s):
            cap = s.strip("*")
            j = nonblank(i + 1)
            rows, aligns = [], None
            while j < len(L) and L[j].strip().startswith("|"):
                cells = [c.strip() for c in L[j].strip().strip("|").split("|")]
                if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    aligns = ["right" if c.endswith(":") else "left" for c in cells]
                else:
                    rows.append(cells)
                j += 1
            full = len(rows[0]) > 5
            widths = _widths(rows, TEXT_W if full else COL_TW)
            body.append(("tbl", cap, [[inline(c) for c in r] for r in rows], widths, full, None, aligns))
            i = j - 1
        elif s.startswith("- "):
            body.append(("p", inline(s[2:])))
        elif s.startswith("<!--"):
            pass
        else:
            body.append(("p", inline(s)))
        i += 1
    C["BODY"] = body
    return C
