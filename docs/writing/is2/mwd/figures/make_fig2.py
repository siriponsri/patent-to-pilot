"""Figure 2: paired recall differences H1-H3, development vs sealed test (C′).

Sources: docs/loe-bench/receipts/FREEZE.md (development) and docs/loe-bench/receipts/SCORE.md (C′).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs
from matplotlib.transforms import blended_transform_factory as btf

ROWS = [  # step, contrast, months, (dev est, lo, hi, drugs), (C′ est, lo, hi, drugs), decision
    ("H1", "M3 − B1", 24, (9.80, 0.14, 19.65, 67), (20.37, 14.37, 26.16, 202), "pass"),
    ("H2", "M3 − M1", 24, (5.49, -2.00, 11.25, 67), (1.36, -2.20, 3.01, 202), "fail"),
    ("H3", "M3 − B1", 12, (13.00, 3.27, 23.17, 90), (16.69, 9.98, 24.21, 202), "desc"),
]
TXT = {
    "en": dict(month="mo", x="Recall difference (percentage points)", thr="+10 pp useful",
               dev="Development", test="Sealed test (C′)",
               dec={"pass": "confirmed", "fail": "not confirmed", "desc": "descriptive"}),
    "th": dict(month="เดือน", x="ผลต่าง recall (จุดร้อยละ)", thr="เกณฑ์ใช้ได้จริง +10",
               dev="ชุดพัฒนา", test="ชุดทดสอบปิดผนึก (C′)",
               dec={"pass": "ยืนยันแล้ว", "fail": "ไม่ยืนยัน", "desc": "เชิงพรรณนา"}),
}


def fmt(v):
    return f"{v:+.2f}".replace("-", "−")


def draw(lang: str, out: Path) -> None:
    fs.setup(lang)
    t = TXT[lang]
    fig = fs.figure(fs.COL_W, 2.7)
    ax = fig.add_axes([0.30, 0.27, 0.40, 0.62])
    tr = btf(fig.transFigure, ax.transData)
    ys = [2, 1, 0]
    off = 0.17
    for y, (h, c, mo, dev, test, dec) in zip(ys, ROWS):
        # development: grey open circle, upper
        ax.plot([dev[1], dev[2]], [y + off] * 2, color=fs.GREY, lw=1.1, solid_capstyle="butt")
        ax.plot([dev[0]], [y + off], marker="o", ms=3.6, mfc="white", mec=fs.GREY_D, mew=0.9, zorder=3)
        # sealed test: accent filled square, lower
        ax.plot([test[1], test[2]], [y - off] * 2, color=fs.ACCENT, lw=1.5, solid_capstyle="butt")
        ax.plot([test[0]], [y - off], marker="s", ms=3.8, color=fs.ACCENT, mec="white", mew=0.5, zorder=3)
        ax.text(0.02, y + 0.12, f"{h}  {c}", transform=tr, fontsize=fs.pt(6.6), va="center", ha="left")
        ax.text(0.02, y - 0.22, f"{mo} {t['month']}", transform=tr, fontsize=fs.pt(6), va="center",
                ha="left", color=fs.GREY_D)
        ax.text(0.995, y - off, f"{fmt(test[0])} {t['dec'][dec]}", transform=tr, fontsize=fs.pt(6),
                va="center", ha="right", color=fs.ACCENT if dec == "pass" else "black")
        ax.text(0.995, y + off, fmt(dev[0]), transform=tr, fontsize=fs.pt(6), va="center", ha="right",
                color=fs.GREY_D)
    ax.axvline(0, color=fs.GREY_D, lw=0.7, ls=(0, (3, 2)))
    ax.axvline(10, color=fs.GREY_D, lw=0.7, ls=(0, (1, 1.5)))
    ax.text(10, 2.62, t["thr"], fontsize=fs.pt(6), ha="center", va="bottom", color=fs.GREY_D)
    # legend below the axis
    ax.plot([], [], marker="o", ms=3.6, mfc="white", mec=fs.GREY_D, color=fs.GREY, lw=1.1, label=t["dev"])
    ax.plot([], [], marker="s", ms=3.8, color=fs.ACCENT, lw=1.5, label=t["test"])
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False,
               fontsize=fs.pt(6), handlelength=1.6, columnspacing=1.2)
    ax.set_ylim(-0.55, 2.6)
    ax.set_xlim(-5, 28)
    ax.set_xticks([0, 10, 20])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fs.clean(ax, left=False)
    ax.set_xlabel(t["x"], fontsize=fs.pt(6.2))
    fs.check_fonts(fig)
    fs.save(fig, out)


if __name__ == "__main__":
    here = Path(__file__).parent
    for lang in ("en", "th"):
        draw(lang, here / f"fig2_effects_{lang}")
