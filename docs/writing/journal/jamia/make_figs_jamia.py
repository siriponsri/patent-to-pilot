"""JAMIA manuscript Figures 1 and 2 (house "direction A": clean, grayscale-safe, direct labels, one blue accent).

Figure 1: what was knowable at the review cutoff (timeline plus one synthetic cutoff from Supplement S1).
Figure 2: registered paired recall contrasts H1-H3 at 20% per-cutoff review capacity.

Numbers for Figure 2 come from loe-bench/data/SCORE_CPRIME_RESULTS.json (committed aggregate) and are asserted against
the values printed in the manuscript. Dates for Figure 1 come from docs/loe-bench/receipts/TRACKA-FREEZE.md and the
manuscript Methods; the synthetic cutoff values come from Supplement S1. Manuscript text stays outside Git; only this
script and its receipt are committed.

OUP artwork guidance: Arial text of at least 7 pt at print size, lines 0.25-1 pt, RGB, 600 dpi PNG plus vector PDF and
SVG (text converted to paths), files named fig1/fig2, captions in the manuscript not in the image.
Owner rule: no label line may leave a single orphan word.

Run from the repository root:
    py -3.12 docs/writing/journal/jamia/make_figs_jamia.py --out <manuscript>/figures
"""
import argparse
import json
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "loe-bench" / "data" / "SCORE_CPRIME_RESULTS.json"
INK, MID, BLUE, TINT, RULE = "#1F1F1F", "#5E5E5E", "#0072B2", "#DCECF5", "#BDBDBD"
FS = 7.0  # minimum OUP text size at print size, in points
W = 6.5   # full text width, inches

# Registered contrasts, in testing order, exactly as reported in Results (percentage points).
MANUSCRIPT_H = {"H1": (20.37, 14.37, 26.16), "H2": (1.36, -2.20, 3.01), "H3": (16.69, 9.98, 24.21)}
SOURCE = {"H1": ("24", "M3-B1"), "H2": ("24", "M3-M1"), "H3": ("12", "M3-B1")}


def setup():
    plt.rcParams.update({
        "font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": FS,
        "axes.linewidth": 0.6, "lines.linewidth": 0.9, "patch.linewidth": 0.6,
        "xtick.major.width": 0.6, "xtick.major.size": 2.5, "text.color": INK, "axes.edgecolor": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "xtick.labelsize": FS,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "svg.fonttype": "path",
        "axes.spines.top": False, "axes.spines.right": False,
    })


def load_contrasts():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))["horizons"]
    out = {}
    for h, (hz, key) in SOURCE.items():
        c = data[hz]["contrasts"][key]["recall"]
        est, lo, hi = (round(100 * v, 2) for v in (c["estimate"], *c["ci95"]))
        assert (est, lo, hi) == MANUSCRIPT_H[h], (h, est, lo, hi)
        assert c["undefined_draws"] == 0
        out[h] = (est, lo, hi)
    return out


def fmt(v, sign=False):
    s = f"{v:+.2f}" if sign else f"{v:.2f}"
    return s.replace("-", "−")


def audit(fig, name):
    """Fail on text under 7 pt, orphan single-word lines in multi-line labels, or overlapping text boxes."""
    fig.canvas.draw()
    texts = [t for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip() and t.get_visible()]
    for t in texts:
        assert t.get_fontsize() >= FS, (name, t.get_text(), t.get_fontsize())
        lines = t.get_text().split("\n")
        if len(lines) > 1:
            for ln in lines:
                assert len(ln.split()) >= 2, (name, "orphan word", ln)
    r = fig.canvas.get_renderer()
    boxes = [(t, t.get_window_extent(r).expanded(1.0, 1.0)) for t in texts]
    bad = [(a.get_text()[:25], b.get_text()[:25]) for (a, ba), (b, bb) in combinations(boxes, 2) if ba.overlaps(bb)]
    assert not bad, (name, "overlapping text", bad)
    fw, fh = fig.canvas.get_width_height()
    for t, bb in boxes:
        assert bb.x0 >= 0 and bb.y0 >= 0 and bb.x1 <= fw and bb.y1 <= fh, (name, "clipped", t.get_text()[:30])
    return r


def save(fig, out, stem):
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out / f"{stem}.{ext}", dpi=600 if ext == "png" else None)
    plt.close(fig)


def canvas(height):
    fig = plt.figure(figsize=(W, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(height, 0)  # y measured downward in inches
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, dashed=False, fc="white", ec=INK, lw=0.8):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, lw=lw, ls=(0, (3, 2)) if dashed else "-"))


def fig1(out):
    H = 6.5
    fig, ax = canvas(H)
    # ---- panel a: common date axis
    ax.text(0.05, 0.1, "a", fontsize=8.5, weight="bold", va="center")
    ax.text(0.22, 0.1, "Development, historical evaluation and prospective freeze (all cutoffs on 1 January)",
            fontsize=8, va="center")
    x0, per = 1.95, 0.22
    X = lambda yr: x0 + (yr - 2009.5) * per  # noqa: E731
    ax.plot([X(2009.5), X(2029.5)], [0.5, 0.5], color=INK, lw=0.6)
    for yr in (2010, 2015, 2020, 2025):
        ax.plot([X(yr), X(yr)], [0.5, 0.56], color=INK, lw=0.6)
        ax.text(X(yr), 0.36, str(yr), ha="center", va="center", fontsize=FS)
    ax.text(X(2029.5), 0.36, "Year", ha="right", va="center", fontsize=FS, color=MID)
    rows = {"fit": 0.82, "v12": 1.12, "v24": 1.40, "c12": 1.78, "c24": 2.12, "pro": 2.55}
    names = {
        "fit": "Model fit, both horizons", "v12": "Validation, 12-month horizon",
        "v24": "Validation, 24-month horizon", "c12": "Registered historical\nevaluation C′, 12 months",
        "c24": "Registered historical\nevaluation C′, 24 months", "pro": "Prospective Track A",
    }
    for k, y in rows.items():
        ax.text(1.75, y, names[k], ha="right", va="center", fontsize=FS, linespacing=1.15)
        ax.plot([X(2009.5), X(2029.5)], [y, y], color="#E4E4E4", lw=0.4, zorder=0)
    ax.plot([0.05, 6.45], [1.595, 1.595], color=RULE, lw=0.4)
    ax.plot([0.05, 6.45], [2.335, 2.335], color=RULE, lw=0.4)
    marks = (("fit", [2010], "s", INK, "2010 cutoff"), ("v12", range(2012, 2016), "o", "white", "2012–2015"),
             ("v24", [2013, 2014], "o", "white", "2013–2014"), ("c12", range(2017, 2026), "o", INK, "2017–2025"),
             ("c24", range(2017, 2025), "o", INK, "2017–2024"))
    for k, yrs, m, fc, lab in marks:
        yrs = list(yrs)
        ax.plot([X(y) for y in yrs], [rows[k]] * len(yrs), ls="none", marker=m, ms=3.6, mfc=fc, mec=INK, mew=0.8, zorder=3)
        ax.text(X(yrs[-1]) + 0.12, rows[k], lab, fontsize=FS, va="center", color=MID)
    # circled 2024 cutoff, enlarged in panel b
    ax.plot([X(2024)], [rows["c24"]], ls="none", marker="o", ms=8.5, mfc="none", mec=BLUE, mew=0.9, zorder=4)
    ax.text(X(2024) + 0.2, rows["c24"] + 0.17, "circled cutoff enlarged in b", fontsize=FS, va="center", ha="right",
            color=BLUE)
    # prospective row
    ys, y12, y24 = X(2026.9), X(2027.9), X(2028.9)
    yp = rows["pro"]
    ax.plot([ys, y24], [yp, yp], color=INK, lw=0.7, ls=(0, (2, 2)))
    ax.plot([ys], [yp], ls="none", marker="D", ms=4.3, mfc=INK, mec=INK, zorder=3)
    for xx in (y12, y24):
        ax.plot([xx], [yp], ls="none", marker="o", ms=3.8, mfc="white", mec=INK, mew=0.9, zorder=3)
    call = [
        (ys, "Reference date 27 Nov 2026", 2.85, "-"),
        (ys, "Forecast freeze 28 Nov 2026, 11:18:44 UTC", 3.03, "-"),
        (ys, "OSF update 4 submitted 28 Nov 2026, 11:30:06 UTC", 3.21, "-"),
        (y12, "12-month window ends 27 Nov 2027 (outcomes pending)", 3.39, "-"),
        (y24, "24-month window ends 27 Nov 2028 (outcomes pending)", 3.57, "-"),
    ]
    for xx, lab, yy, _ in call:
        ax.plot([xx, xx], [yp + 0.07, yy], color=MID, lw=0.5)
        ax.plot([xx - 0.07, xx], [yy, yy], color=MID, lw=0.5)
        ax.text(xx - 0.1, yy, lab, ha="right", va="center", fontsize=FS)
    # ---- panel b: one cutoff enlarged
    tb = 3.98
    ax.plot([0.05, 6.45], [tb - 0.13, tb - 0.13], color=RULE, lw=0.4)
    ax.text(0.05, tb + 0.05, "b", fontsize=8.5, weight="bold", va="center")
    ax.text(0.22, tb + 0.05,
            "One cutoff enlarged: synthetic ingredient MOI-A, t₀ = 1 January 2024 (Supplement S1)",
            fontsize=8, va="center")
    by, bh = tb + 0.3, 0.92
    spec = [
        (1.00, "1  Identity link", ["Alias and", "application link", "give ingredient", "set MOI-A"]),
        (1.50, "2  Source admission", ["OB-A, proof 15 Nov 2023:", "admitted, expiry 2027", "OB-B, proof 5 Jan 2024:",
                                       "excluded, late proof"]),
        (1.28, "3  Feature table", ["Challenge date missing,", "so state is UNKNOWN;", "graph state CONTESTED"]),
        (1.05, "4  Native risk", ["Five roster rows,", "scores 0.62, 0.62,", "0.31, 0.22, 0.08"]),
        (1.12, "5  Queue boundary", ["N = 5, k = 1 slot;", "two 0.62 scores tie,", "weights 0.5, 0.5"]),
    ]
    gap = (6.4 - sum(s[0] for s in spec)) / 4
    xs, x = [], 0.05
    for i, (w, head, body) in enumerate(spec):
        box(ax, x, by, w, bh, dashed=(i == 1 and False), fc=TINT if i == 4 else "white", ec=BLUE if i == 4 else INK)
        ax.text(x + 0.06, by + 0.14, head, fontsize=FS, weight="bold", va="center")
        ax.text(x + 0.06, by + 0.32, "\n".join(body), fontsize=FS, va="top", linespacing=1.3,
                color=INK)
        xs.append((x, w))
        if i < 4:
            ax.annotate("", xy=(x + w + gap, by + bh / 2), xytext=(x + w, by + bh / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, mutation_scale=6, shrinkA=0, shrinkB=0))
        x += w + gap
    # separation between ranking path and evaluator path
    sep = by + bh + 0.3
    ax.plot([0.05, 6.45], [sep, sep], color=MID, lw=0.6, ls=(0, (4, 3)))
    ax.text(0.05, sep - 0.1, "Ranking path: only records available by t₀", fontsize=FS, va="center", color=MID)
    ax.text(0.05, sep + 0.1, "Evaluation path: later events, used only to score the queue", fontsize=FS, va="center",
            color=MID)
    ey, eh = sep + 0.28, 0.62
    ex1w = xs[2][0] + xs[2][1] - 0.05
    box(ax, 0.05, ey, ex1w, eh, dashed=True)
    ax.text(0.11, ey + 0.1, "Later FDA evidence", fontsize=FS, weight="bold", va="center")
    ax.text(0.11, ey + 0.28, "First final original ANDA approval on 1 June 2025\n(synthetic), entered only into the evaluator",
            fontsize=FS, va="top", linespacing=1.3)
    ex2x = xs[3][0]
    ex2w = xs[4][0] + xs[4][1] - ex2x
    box(ax, ex2x, ey, ex2w, eh)
    ax.text(ex2x + 0.06, ey + 0.1, "Evaluator", fontsize=FS, weight="bold", va="center")
    ax.text(ex2x + 0.06, ey + 0.28, "Weight 0.5 on the event gives 0.5 hits;\nrecall 0.5, precision 0.5",
            fontsize=FS, va="top", linespacing=1.3)
    ax.annotate("", xy=(ex2x, ey + eh / 2), xytext=(0.05 + ex1w, ey + eh / 2),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, mutation_scale=6, shrinkA=0, shrinkB=0))
    qx = xs[4][0] + xs[4][1] / 2
    ax.annotate("", xy=(qx, ey), xytext=(qx, by + bh),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, mutation_scale=6, shrinkA=0, shrinkB=0))
    ax.text(qx + 0.08, sep + 0.0, "", fontsize=FS)
    audit(fig, "fig1")
    save(fig, out, "fig1")


def fig2(out, contrasts):
    Hh = 2.25
    fig = plt.figure(figsize=(W, Hh))
    px0, pw, py0, ph = 1.95, 2.55, 0.5, 1.3  # plot rectangle, inches (y from bottom)
    ax = fig.add_axes([px0 / W, py0 / Hh, pw / W, ph / Hh])
    ax.set_xlim(-5, 30)
    ax.set_ylim(2.55, -0.55)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks([0, 10, 20, 30])
    ax.set_xticklabels(["0", "10", "20", "30"])
    ax.set_xlabel("Paired recall difference at 20% review capacity (percentage points)", fontsize=FS, labelpad=3)
    ax.axvline(0, color=INK, lw=0.8, zorder=1)
    ax.axvline(10, color=MID, lw=0.8, ls=(0, (1, 1.6)), zorder=1)
    ax.set_xlabel(ax.get_xlabel(), loc="left")
    label = {"H1": ("H1  M3 versus B1", "24-month horizon"), "H2": ("H2  M3 versus M1", "24-month horizon"),
             "H3": ("H3  M3 versus B1", "12-month horizon")}
    status = {"H1": "Registered test passed", "H2": "Registered test failed;\nsequence stopped",
              "H3": "Descriptive, sequence\nstopped at H2"}
    fig.text(0.05 / W, 1 - 0.1 / Hh, "Registered paired recall contrasts in testing order", fontsize=8, va="center")
    fy = lambda t: 1 - t / Hh  # noqa: E731  (t measured down from the top, inches)
    ytop = Hh - py0 - ph      # top of the plot rectangle from the figure top, inches
    for i, h in enumerate(("H1", "H2", "H3")):
        est, lo, hi = contrasts[h]
        reg = h != "H3"
        ax.plot([lo, hi], [i, i], color=INK, lw=1.0, solid_capstyle="butt")
        ax.plot([lo, lo, lo], [i - 0.1, i + 0.1, i], color=INK, lw=1.0)
        ax.plot([hi, hi], [i - 0.1, i + 0.1], color=INK, lw=1.0)
        ax.plot([est], [i], marker="s" if reg else "o", ms=4.8, mfc=BLUE if reg else "white", mec=BLUE if reg else INK,
                mew=0.9, zorder=3)
        ytxt = ytop + (i + 0.55) / 3.1 * ph  # row centre from top, inches
        fig.text(1.8 / W, fy(ytxt), f"{label[h][0]}\n{label[h][1]}", ha="right", va="center", fontsize=FS,
                 linespacing=1.3, weight="bold" if h == "H2" else "normal")
        fig.text(4.65 / W, fy(ytxt), f"{fmt(est, True)} [{fmt(lo)}, {fmt(hi)}]\n{status[h]}", ha="left", va="center",
                 fontsize=FS, linespacing=1.3)
    ax.text(10.4, -0.45, "Practical-usefulness threshold, +10 points", fontsize=FS, va="center", color=MID)
    ax.text(-0.5, -0.45, "No difference", fontsize=FS, va="center", ha="right", color=INK)
    audit(fig, "fig2")
    save(fig, out, "fig2")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    setup()
    c = load_contrasts()
    fig1(args.out)
    fig2(args.out, c)
    print("ok", c)
