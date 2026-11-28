"""Mock-ups of three figure directions (A Nature clean, B Lancet-inspired, C modern ML) for owner choice.

Designed by the main planner from the co-planner spec (28 Nov 2026). Numbers: SCORE.md, SCORELLM.md.
Run: python make_mocks.py -> mock_{A,B,C}_fig{1,2}.png and a comparison sheet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs  # noqa: E402
from matplotlib.patches import Rectangle, FancyArrowPatch  # noqa: E402

OUT = Path(__file__).parent
INK, MID, BLUE, TINT, BG = "#1F1F1F", "#6E6E6E", "#0072B2", "#DCECF5", "#F4F5F6"
ARMS = [  # name, label, marker, face, edge, r24, r12
    ("B1", "B1  drug age", "o", MID, MID, 46.48, 50.64),
    ("M1", "M1  dated-evidence table", "D", "white", "#303030", 65.49, 67.82),
    ("M3", "M3  table + graph states", "s", BLUE, BLUE, 66.85, 67.33),
    ("L1", "L1  identity prompt (7B)", "^", "white", MID, 26.14, 26.58),
    ("L1e", "L1e  evidence prompt (7B)", "v", "white", MID, 12.36, 14.50),
]
H = [("H1", "M3 − B1, 24 mo", 20.37, 14.37, 26.16, "H1 met the criterion", "filled"),
     ("H2", "M3 − M1, 24 mo", 1.36, -2.20, 3.01, "Testing stopped at H2", "filled"),
     ("H3", "M3 − B1, 12 mo", 16.69, 9.98, 24.21, "Descriptive estimate only", "open")]


def arrow(ax, p, q, color=INK, lw=0.8):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, lw=lw, color=color, shrinkA=0, shrinkB=0))


def fig1(style):
    fig = fs.figure(6.5, 1.65)
    ax = fig.add_axes([0.01, 0.03, 0.98, 0.94])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.axis("off")
    t0 = 43
    if style == "B":
        ax.add_patch(Rectangle((t0, 0.5), 56, 19, color=BG, lw=0))
    # left: evidence line ending at t0
    ax.plot([3, t0], [14.5, 14.5], color=INK, lw=0.8)
    ax.text(3, 16.0, "Records available by cutoff", fontsize=fs.pt(7.5), va="bottom")
    # unit strip: five equal cells, first filled
    x0, w, gap = 3, 4.2, 0.9
    for i in range(5):
        ax.add_patch(Rectangle((x0 + i * (w + gap), 7.2), w, 3.6, facecolor=INK if i == 0 else "white",
                               edgecolor=MID if i else INK, lw=0.6))
    ax.text(3, 5.0, r"Review capacity per cutoff:  $k=\lfloor N/5\rfloor$", fontsize=fs.pt(7.5), va="center")
    ax.text(3, 2.2, "Dated dossier and checklist for the selected cases", fontsize=fs.pt(7), color=MID, va="center")
    if style == "C":
        ax.text(29, 9.0, "ranked by\nB1, M1 or M3", fontsize=fs.pt(6.6), color=MID, va="center", linespacing=1.1)
    # t0 line
    ax.plot([t0, t0], [1, 19], color="#3A3A3A", lw=0.9)
    ax.text(t0 + 0.8, 18.6, "Review cutoff $t_0$", fontsize=fs.pt(8), weight="bold", va="top")
    # right: follow-up windows
    for y, end, lab in ((11.5, 70, "12 months"), (7.0, 97, "24 months")):
        ax.plot([t0, end], [y, y], color=INK, lw=0.8)
        ax.plot([end, end], [y - 0.9, y + 0.9], color=INK, lw=0.8)
        ax.text(end - 0.6, y + 1.1, lab, fontsize=fs.pt(7), ha="right", va="bottom", color=MID)
    ax.text(t0 + 1.2, 14.6, "First final US generic approval observed in the window", fontsize=fs.pt(7.5),
            va="bottom")
    ax.text(t0 + 1.2, 2.8, "Outcomes are used only to score the queues", fontsize=fs.pt(7), color=MID, va="center")
    fs.check_fonts(fig)
    fs.save(fig, OUT / f"mock_{style}_fig1", formats=("png",))


def dot_panel(ax, key, title, style):
    rows = [0, 1, 2, 3.5, 4.5]
    for (name, lab, m, fc, ec, r24, r12), y in zip(ARMS, rows):
        v = r24 if key == 24 else r12
        if name == "M3" and style != "C":
            ax.axhspan(y - 0.42, y + 0.42, color=TINT, lw=0, zorder=0)
        ax.plot([0, v], [y, y], color="#E6E6E6", lw=0.6, zorder=1)
        ax.plot([v], [y], marker=m, ms=4.6, mfc=fc, mec=ec, mew=0.8, ls="none", zorder=3)
        ax.text(v + 2.5, y, f"{v:.2f}%", va="center", fontsize=fs.pt(7), color=BLUE if name == "M3" else INK,
                weight="bold" if name == "M3" else "normal")
    ax.set_xlim(0, 100)
    ax.set_ylim(5.1, -0.7)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.set_yticks([])
    fs.clean(ax, left=False)
    ax.set_title(title, fontsize=fs.pt(8), loc="left", pad=3)


def forest(ax, style):
    for i, (h, lab, e, lo, hi, note, kind) in enumerate(H):
        y = i
        ax.plot([lo, hi], [y, y], color=INK, lw=1.3)
        ax.plot([e], [y], marker="s" if kind == "filled" else "o", ms=4.8, mfc=INK if kind == "filled" else "white",
                mec=INK, mew=0.9)
        ax.text(-5.6, y, f"{h}  {lab}" if style != "C" else f"{h}  {lab.replace('M3 − B1', 'M3 vs drug age').replace('M3 − M1', 'M3 vs table')}",
                ha="right", va="center", fontsize=fs.pt(7.2))
        ax.text(31, y, f"{e:+.2f} [{lo:.2f}, {hi:.2f}]".replace("-", "−"), va="center", fontsize=fs.pt(7))
        ax.text(48, y, note, va="center", fontsize=fs.pt(7), weight="bold" if h == "H2" else "normal",
                color=BLUE if h == "H2" and style == "B" else INK)
    ax.axvline(0, color=INK, lw=0.8)
    ax.axvline(10, color=MID, lw=0.6, ls=(0, (1, 1.6)))
    ax.set_xlim(-5, 30)
    ax.set_ylim(2.6, -0.6)
    ax.set_yticks([])
    ax.set_xticks([0, 10, 20, 30])
    ax.set_xlabel("Paired recall difference (percentage points)", fontsize=fs.pt(7.2))
    fs.clean(ax, left=False)


def fig2(style):
    fig = fs.figure(6.5, 3.55)
    # labels column shared by the two dot panels
    lab_ax = fig.add_axes([0.0, 0.50, 0.22, 0.40])
    lab_ax.set_ylim(5.1, -0.7)
    lab_ax.set_xlim(0, 1)
    lab_ax.axis("off")
    for (name, lab, *_), y in zip(ARMS, [0, 1, 2, 3.5, 4.5]):
        lab_ax.text(0.98, y, lab, ha="right", va="center", fontsize=fs.pt(7),
                    weight="bold" if name == "M3" else "normal", color=BLUE if name == "M3" else INK)
    a1 = fig.add_axes([0.24, 0.50, 0.34, 0.40])
    a2 = fig.add_axes([0.63, 0.50, 0.34, 0.40])
    dot_panel(a1, 24, "24 months  ·  368 event cases, 924 slots", style)
    dot_panel(a2, 12, "12 months  ·  202 event cases, 1,048 slots", style)
    fig.text(0.01, 0.975, "a", fontsize=fs.pt(8.5), weight="bold", va="top")
    fig.text(0.04, 0.975, "Recall at fixed review capacity (sealed test C′)", fontsize=fs.pt(8), va="top")
    b = fig.add_axes([0.24, 0.10, 0.34, 0.25])
    forest(b, style)
    fig.text(0.01, 0.42, "b", fontsize=fs.pt(8.5), weight="bold", va="top")
    fig.text(0.04, 0.42, "Paired differences, preregistered sequence H1 → H2 → H3", fontsize=fs.pt(8), va="top")
    if style == "B":
        fig.add_artist(__import__("matplotlib").lines.Line2D([0.02, 0.98], [0.455, 0.455], color="#D0D0D0", lw=0.6))
    fs.check_fonts(fig)
    fs.save(fig, OUT / f"mock_{style}_fig2", formats=("png",))


if __name__ == "__main__":
    fs.setup("en")
    for s in "ABC":
        fig1(s)
        fig2(s)
    print("ok")
