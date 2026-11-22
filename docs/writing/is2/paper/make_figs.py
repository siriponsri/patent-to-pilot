# -*- coding: utf-8 -*-
"""IS2 short-paper figures (Thai and English labels), journal-minimal house style.

python make_figs.py            -> figs_th/ and figs_en/ (PNG 600 dpi + SVG + PDF)

Every number is read from ../results/b53-stage1-results.json and b53-stage2-results.json; nothing is typed by hand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r"C:/Users/User/.claude/skills/academic-figures/scripts")
import figstyle as fs  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

RES = HERE.parent / "results"
S1 = json.loads((RES / "b53-stage1-results.json").read_text(encoding="utf-8"))
S2 = json.loads((RES / "b53-stage2-results.json").read_text(encoding="utf-8"))
ARMS = ["F0", "F1", "F2", "F3", "F4"]
NAMES = {"F0": "F0 patembed-base", "F1": "F1 BM25", "F2": "F2 RRF(F1, F0)", "F3": "F3 Arctic-embed", "F4": "F4 RRF(F1, F3)"}
MINUS = "\u2212"


def sgn(x: float, d: int = 3) -> str:
    if x != 0 and abs(x) < 0.5 * 10 ** -d:  # e.g. -0.00015 would print as -0.000
        d += 1
    s = f"{x:+.{d}f}"
    return s.replace("-", MINUS)


T = {
    "en": {
        "boxes": [
            ("1  Queries", "DAPFAM\n905 OUT queries\nTAC text (title,\nabstract, claims)"),
            ("2  First stage", "F0 patembed-base\nF1 BM25\nF2 RRF(F1, F0)\nF3 Arctic-embed\nF4 RRF(F1, F3)"),
            ("3  Candidate pool", "top 100 per query\nStage 1 endpoint:\nexposure \u03c0@100\n(also @200, @1000)"),
            ("4  Reranker", "Qwen3-Reranker-0.6B\n4 instructions: Generic,\nPatent-aware, Claim-\nfocused, Scrambled"),
            ("5  Evaluation", "strict OUT nDCG@100\nStage 2 contrasts on\nC = 153 queries exposed\nunder all of F0\u2013F4"),
        ],
        "varied": "varied", "fixed": "held fixed",
        "stage1": "Stage 1 (n = 905)", "stage2": "Stage 2 (C = 153)",
        "k": "k = ", "xexp": "Exposure \u03c0@k (share of 905 OUT queries)",
        "forest_x": "Difference in strict OUT nDCG@100 vs Generic",
        "pa": "Patent-aware", "cf": "Claim-focused", "con": "Instruction \u2212 Generic",
        "hd": ["\u0394 [95% CI]", "W/L", "Holm p"], "first": "First stage",
    },
    "th": {
        "boxes": [
            ("1  คำค้น", "DAPFAM\nคำค้น OUT 905 รายการ\nข้อความ TAC (ชื่อเรื่อง\nบทคัดย่อ ข้อถือสิทธิ)"),
            ("2  ตัวค้นคืนขั้นแรก", "F0 patembed-base\nF1 BM25\nF2 RRF(F1, F0)\nF3 Arctic-embed\nF4 RRF(F1, F3)"),
            ("3  กลุ่มผู้สมัคร", "100 อันดับแรกต่อคำค้น\nตัวชี้วัดขั้นที่ 1:\nexposure \u03c0@100\n(และ @200, @1000)"),
            ("4  Reranker", "Qwen3-Reranker-0.6B\nคำสั่ง 4 แบบ: Generic,\nPatent-aware, Claim-\nfocused, Scrambled"),
            ("5  การประเมิน", "strict OUT nDCG@100\nขั้นที่ 2 เปรียบเทียบบน\nกลุ่ม C = 153 คำค้นที่\nF0\u2013F4 เปิดเผยทุกแบบ"),
        ],
        "varied": "ตัวแปรที่เปลี่ยน", "fixed": "ตรึงไว้",
        "stage1": "ขั้นที่ 1 (n = 905)", "stage2": "ขั้นที่ 2 (C = 153)",
        "k": "k = ", "xexp": "อัตราการเปิดเผย \u03c0@k (คำค้น OUT, n = 905)",
        "forest_x": "ผลต่าง strict OUT nDCG@100 เทียบ Generic",
        "pa": "Patent-aware", "cf": "Claim-focused", "con": "คำสั่ง − Generic",
        "hd": ["\u0394 [95% CI]", "ดีขึ้น/แย่ลง", "Holm p"], "first": "ตัวค้นคืนขั้นแรก",
    },
}


def fig_design(lang: str, out: Path) -> None:
    L = T[lang]
    fig = fs.figure(fs.FULL_W, 1.72)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 6.5)
    ax.set_ylim(0, 1.72)
    ax.axis("off")
    w, gap, x0, yb, h = 1.12, 0.20, 0.03, 0.50, 1.18
    for i, (head, body) in enumerate(L["boxes"]):
        x = x0 + i * (w + gap)
        varied = i == 1
        ax.add_patch(FancyBboxPatch((x, yb), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc="#E6F1F8" if varied else "white", ec=fs.ACCENT if varied else fs.GREY_D,
                                    lw=1.4 if varied else 0.7, ls="-" if varied else (0, (3, 1.5))))
        ax.text(x + 0.06, yb + h - 0.06, head, ha="left", va="top", weight="bold", fontsize=fs.pt(7.6),
                color=fs.ACCENT if varied else fs.INK)
        ax.text(x + 0.06, yb + h - 0.30, body, ha="left", va="top", fontsize=fs.pt(6.6), linespacing=1.05 if lang == "th" else 1.25)
        tag = L["varied"] if varied else (L["fixed"] if i >= 2 else "")
        if i == 2:
            tag = ""
        if tag:
            ax.text(x + w - 0.03, yb - 0.025, tag, ha="right", va="top", fontsize=fs.pt(6.2), style="italic",
                    color=fs.ACCENT if varied else fs.GREY_D)
        if i < 4:
            ax.annotate("", xy=(x + w + gap - 0.02, yb + h / 2), xytext=(x + w + 0.02, yb + h / 2),
                        arrowprops=dict(arrowstyle="-|>", lw=0.9, color=fs.INK, mutation_scale=7))
    # stage brackets
    def bracket(xa, xb, label):
        y = 0.24
        ax.plot([xa, xa, xb, xb], [y + 0.06, y, y, y + 0.06], color=fs.GREY_D, lw=0.7)
        ax.text((xa + xb) / 2, y - 0.05, label, ha="center", va="top", fontsize=fs.pt(6.8), color=fs.GREY_D)
    bracket(x0, x0 + 3 * w + 2 * gap, L["stage1"])
    bracket(x0 + 3 * (w + gap), x0 + 5 * w + 4 * gap, L["stage2"])
    fs.check_fonts(fig)
    fs.save(fig, out / "fig1_design")


def fig_exposure(lang: str, out: Path) -> None:
    L = T[lang]
    fig = fs.figure(fs.COL_W, 2.0 if lang == "th" else 2.2)
    ax = fig.add_axes([0.30, 0.22, 0.66, 0.70] if lang == "th" else [0.30, 0.21, 0.66, 0.70])
    ks = [("pi100", "o", fs.ACCENT, "100"), ("pi200", "s", fs.GREY_D, "200"), ("pi1000", "^", fs.INK, "1000")]
    for r, a in enumerate(ARMS):
        y = len(ARMS) - 1 - r
        v = [S1["arms"][a][k] for k, *_ in ks]
        ax.plot([v[0], v[2]], [y, y], color=fs.GREY_L, lw=1.6, zorder=1)
        for (k, m, c, _), val in zip(ks, v):
            filled = k == "pi100"
            ax.plot(val, y, m, ms=4.6, mfc=c if filled else "white", mec=c, mew=1.0, zorder=3)
            ax.text(val, y - (0.17 if lang == "th" else 0.30), f"{val:.3f}", ha="center", va="top", fontsize=fs.pt(6.1),
                    color=fs.ACCENT if filled else fs.GREY_D)
    # direct marker key above the top row (F0)
    top = len(ARMS) - 1
    for (k, m, c, lab) in ks:
        ax.text(S1["arms"]["F0"][k], top + 0.42, L["k"] + lab if k == "pi100" else lab, ha="center", va="bottom",
                fontsize=fs.pt(6.2), color=c, weight="bold" if k == "pi100" else "normal")
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([NAMES[a] for a in reversed(ARMS)])
    ax.set_ylim(-0.75, len(ARMS) - 0.2)
    ax.set_xlim(0.2, 0.8)
    ax.set_xticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ax.set_xlabel(L["xexp"])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fs.check_fonts(fig)
    fs.save(fig, out / "fig3_exposure")


def fig_forest(lang: str, out: Path) -> None:
    L = T[lang]
    P = S2["B53_3_primary_on_C"]
    fig = fs.figure(fs.FULL_W, 2.45)
    ax = fig.add_axes([0.335, 0.21, 0.30, 0.72] if lang == "th" else [0.335, 0.17, 0.30, 0.76])
    from matplotlib.transforms import blended_transform_factory
    trf = blended_transform_factory(fig.transFigure, ax.transData)
    rows = []
    for a in ARMS:
        for key, lab, m, c in (("patent_aware", L["pa"], "o", fs.ACCENT), ("claim_focused", L["cf"], "s", fs.GREY_D)):
            rows.append((a, lab, m, c, P[f"{a}|{key}-generic"]))
    n = len(rows)
    ys = []
    for i, (a, lab, m, c, r) in enumerate(rows):
        y = n - 1 - i - (i // 2) * 0.45
        ys.append(y)
        lo, hi = r["ci95"]
        ax.plot([lo, hi], [y, y], color=c, lw=1.2, solid_capstyle="butt")
        ax.plot(r["delta_C"], y, m, ms=4.4, color=c, mfc=c, mec=c)
        # right text columns (figure coordinates via blended transform)
        tr = ax.get_yaxis_transform()
        ax.text(1.03, y, f"{sgn(r['delta_C'])} [{sgn(lo)}, {sgn(hi)}]", transform=tr, ha="left", va="center",
                fontsize=fs.pt(6.4))
        ax.text(1.66, y, f"{r['wins']}/{r['losses']}", transform=tr, ha="center", va="center", fontsize=fs.pt(6.4))
        ax.text(1.93, y, f"{r['holm_p']:.3f}", transform=tr, ha="center", va="center", fontsize=fs.pt(6.4))
        ax.text(-0.03, y, lab, transform=tr, ha="right", va="center", fontsize=fs.pt(6.4), color=c)
        if i % 2 == 0:
            ax.text(0.008, y - 0.5, NAMES[a], transform=trf, ha="left", va="center", fontsize=fs.pt(6.8), weight="bold")
    top = max(ys) + 0.9
    tr = ax.get_yaxis_transform()
    for xpos, ha, t in ((1.03, "left", L["hd"][0]), (1.66, "center", L["hd"][1]), (1.93, "center", L["hd"][2]),
                        (-0.03, "right", L["con"])):
        ax.text(xpos, top, t, transform=tr, ha=ha, va="center", fontsize=fs.pt(6.6), weight="bold")
    ax.text(0.008, top, L["first"], transform=trf, ha="left", va="center", fontsize=fs.pt(6.6), weight="bold")
    fs.zero_line(ax)
    ax.set_ylim(min(ys) - 0.7, top + 0.5)
    ax.set_xlim(-0.010, 0.022)
    ax.set_xticks([-0.01, 0, 0.01, 0.02])
    ax.set_xticklabels([sgn(-0.01, 2), "0", sgn(0.01, 2), sgn(0.02, 2)])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(L["forest_x"])
    fs.check_fonts(fig)
    fs.save(fig, out / "fig2_forest")


if __name__ == "__main__":
    for lang in ("en", "th"):
        fs.setup(lang)
        if lang == "th":  # TH Sarabun New lacks Greek letters (pi, Delta): fall back to Arial for those glyphs
            fs.plt.rcParams["font.family"] = list(fs.plt.rcParams["font.family"]) + ["Arial"]
        out = HERE / f"figs_{lang}"
        fig_design(lang, out)
        fig_exposure(lang, out)
        fig_forest(lang, out)
        print("done", lang, out)
