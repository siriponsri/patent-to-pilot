"""Figure 2: paired recall differences H1-H3 on development data (source: docs/loe-bench/receipts/FREEZE.md)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs

ROWS = [  # label parts, drugs, estimate, lo, hi  (FREEZE development report)
    ("H1", "M3 − B1", 24, 67, 9.80, 0.14, 19.65),
    ("H2", "M3 − M1", 24, 67, 5.49, -2.00, 11.25),
    ("H3", "M3 − B1", 12, 90, 13.00, 3.27, 23.17),
]
TXT = {
    "en": dict(month="mo", drugs="drugs", x="Recall difference (percentage points)", thr="+10 pp useful"),
    "th": dict(month="เดือน", drugs="ตัวยา", x="ผลต่าง recall (จุดร้อยละ)", thr="เกณฑ์ใช้ได้จริง +10"),
}

def draw(lang: str, out: Path) -> None:
    fs.setup(lang)
    t = TXT[lang]
    fig = fs.figure(fs.COL_W, 1.95)
    ax = fig.add_axes([0.42, 0.25, 0.33, 0.62])
    from matplotlib.transforms import blended_transform_factory as btf
    tr = btf(fig.transFigure, ax.transData)
    ys = [2, 1, 0]
    for y, (h, c, mo, n, est, lo, hi) in zip(ys, ROWS):
        ax.plot([lo, hi], [y, y], color=fs.ACCENT, lw=1.4, solid_capstyle="butt")
        ax.plot([est], [y], marker="o", ms=4.2, color=fs.ACCENT, mec="white", mew=0.6, zorder=3)
        ax.text(0.02, y + 0.13, f"{h}  {c}, {mo} {t['month']}", transform=tr,
                fontsize=fs.pt(6.6), va="center", ha="left", color="black")
        ax.text(0.02, y - 0.22, f"{n} {t['drugs']}", transform=tr,
                fontsize=fs.pt(6), va="center", ha="left", color=fs.GREY_D)
        ax.text(0.995, y, f"{est:+.2f}\n[{lo:+.2f}, {hi:+.2f}]".replace("-", "\u2212"), transform=tr,
                fontsize=fs.pt(6), va="center", ha="right", color="black", linespacing=1.05)
    ax.axvline(0, color=fs.GREY_D, lw=0.7, ls=(0, (3, 2)))
    ax.axvline(10, color=fs.GREY_D, lw=0.7, ls=(0, (1, 1.5)))
    ax.text(10, 2.55, t["thr"], fontsize=fs.pt(6), ha="center", va="bottom", color=fs.GREY_D)
    ax.set_ylim(-0.5, 2.5)
    ax.set_xlim(-5, 25)
    ax.set_xticks([0, 10, 20])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fs.clean(ax, left=False)
    ax.set_xlabel(t["x"], fontsize=fs.pt(6.5))
    fs.check_fonts(fig)
    fs.save(fig, out)

if __name__ == "__main__":
    here = Path(__file__).parent
    for lang in ("en", "th"):
        draw(lang, here / f"fig2_effects_{lang}")
