"""IS2 Figure 1 (academic schematic): ranking at the cutoff and scoring on the later window.

Designed by the main planner per docs/writing/is2/mwd/STYLE-GUIDE.md (Rougier et al. 2014; Schneeweiss et al. 2019
design-diagram convention). Full width 6.5 x 1.95 in, thin lines, no fills or glyphs, 7-7.5 pt (EN) / TH x1.4.
Run: python make_fig1_timeline.py -> fig1_timeline_{en,th}.{png,svg,pdf}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch  # noqa: E402

HERE = Path(__file__).parent
TXT = {
    "en": dict(A=["Records public", "by $t_0$"], B=["$N$ eligible cases", "scored by", "B1, M1, M3"],
               C=["Review set", r"$k=\lfloor N/5\rfloor$"], D=["Dated dossier", "and checklist"],
               F=["Recall at", "fixed capacity"], t0="$t_0$ (cutoff)", t1="$t_0+h$",
               win=r"First final ANDA approvals observed in $(t_0,\,t_0+h]$" + "\n" + r"with $h$ = 12 or 24 months",
               hand="hand-off", sel="selected cases", obs="observed events"),
    "th": dict(A=["ข้อมูลที่เผยแพร่", "ภายใน $t_0$"], B=["$N$ รายการที่เข้าเกณฑ์", "จัดลำดับด้วย", "B1, M1, M3"],
               C=["รายการที่ทบทวน", r"$k=\lfloor N/5\rfloor$"], D=["แฟ้มหลักฐาน", "และรายการตรวจ"],
               F=["การครอบคลุม", "(recall)"], t0="$t_0$ (วันตัดข้อมูล)", t1="$t_0+h$",
               win=r"การอนุมัติขั้นสุดท้ายครั้งแรกของคำขอ ANDA ในช่วง $(t_0,\,t_0+h]$" + "\n" + r"โดย $h$ เท่ากับ 12 หรือ 24 เดือน",
               hand="ส่งต่อ", sel="รายการที่เลือก", obs="เหตุการณ์ที่พบ"),
}


def box(ax, x0, x1, y0, y1, lines, accent=False):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.7 if not accent else 1.0,
                           ec=fs.ACCENT if accent else fs.INK))
    n = len(lines)
    step = (y1 - y0) / (n + 1)
    for i, ln in enumerate(lines):
        ax.text((x0 + x1) / 2, y1 - step * (i + 1), ln, ha="center", va="center", fontsize=fs.pt(7),
                weight="bold" if i == 0 else "normal")


def arrow(ax, p, q, style="-|>", ls="-", color=None):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=6, lw=0.7, ls=ls,
                                 color=color or fs.INK, shrinkA=0, shrinkB=0))


def draw(lang):
    fs.setup(lang)
    if lang == "th":   # math in the Thai font so t0 and floor(N/5) match the Thai text size
        import matplotlib.pyplot as plt
        name = plt.rcParams["font.family"][0]
        plt.rcParams.update({"mathtext.fontset": "custom", "mathtext.rm": name, "mathtext.it": name + ":italic",
                             "mathtext.bf": name + ":bold"})
    t = TXT[lang]
    fig = fs.figure(fs.FULL_W, 1.95)
    ax = fig.add_axes([0.005, 0.02, 0.99, 0.96])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")
    yb0, yb1 = 19, 29
    box(ax, 1, 16, yb0, yb1, t["A"])
    box(ax, 19.5, 34.5, yb0, yb1, t["B"])
    box(ax, 38, 52, yb0, yb1, t["C"], accent=True)
    box(ax, 57, 71, yb0, yb1, t["D"])
    box(ax, 82, 98, yb0, yb1, t["F"])
    ym = (yb0 + yb1) / 2
    arrow(ax, (16, ym), (19.5, ym))
    arrow(ax, (34.5, ym), (38, ym))
    arrow(ax, (52, ym), (57, ym))
    # selected cases routed below the boxes to the recall box
    ax.plot([45, 45, 88], [yb0, 16.5, 16.5], color=fs.ACCENT, lw=0.7)
    arrow(ax, (88, 16.5), (88, yb0), color=fs.ACCENT)
    ax.text(64, 16.9, t["sel"], ha="center", va="bottom", fontsize=fs.pt(6.2), color=fs.ACCENT)
    # timeline
    ya = 6.5
    arrow(ax, (1, ya), (99, ya), style="-|>")
    for x, lab in ((52, t["t0"]), (96, t["t1"])):
        ax.plot([x, x], [ya - 1, ya + 1], color=fs.INK, lw=0.7)
        ax.text(x, ya - 1.6, lab, ha="center", va="top", fontsize=fs.pt(6.8))
    ax.plot([52, 52], [ya + 1, yb0], color=fs.GREY, lw=0.6, ls=(0, (3, 2)))
    # outcome window
    ax.plot([52.6, 52.6, 95.4, 95.4], [ya + 2.6, ya + 3.4, ya + 3.4, ya + 2.6], color=fs.CONTRAST, lw=0.8)
    ax.text(53.5, ya + 4.0, t["win"], ha="left", va="bottom", fontsize=fs.pt(6.4), color=fs.CONTRAST, linespacing=1.15)
    arrow(ax, (95.4, ya + 3.4), (95.4, yb0), color=fs.CONTRAST)
    ax.text(94.6, 11.2, t["obs"], ha="right", va="center", fontsize=fs.pt(6.2), color=fs.CONTRAST)
    fs.check_fonts(fig)
    fs.save(fig, HERE / f"fig1_timeline_{lang}", formats=("png", "svg"))


if __name__ == "__main__":
    for lang in ("en", "th"):
        draw(lang)
    print("ok")
