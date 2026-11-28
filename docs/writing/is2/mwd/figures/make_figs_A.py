"""IS2 Figures 1 and 2, direction A ("Nature clean"), chosen by the owner on 28 Nov 2026.

Designed by the main planner from the co-planner spec. Numbers: docs/loe-bench/receipts/SCORE.md (C′ recall, H1-H3),
SCORELLM.md (L1, L1e). Consistent arm mapping across paper and report:
B1 grey filled circle, M1 open diamond, M3 blue filled square (only blue), L1 open triangle, L1e open inverted triangle.
Owner rule: no label may leave one or two orphan words on a line.
Run: python make_figs_A.py -> fig1_capacity_{en,th}.{png,svg} and fig2_recall_{en,th}.{png,svg}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

OUT = Path(__file__).parent
INK, MID, BLUE, TINT = "#1F1F1F", "#6E6E6E", "#0072B2", "#DCECF5"
VAL = {"B1": (46.48, 50.64), "M1": (65.49, 67.82), "M3": (66.85, 67.33), "L1": (26.14, 26.58), "L1e": (12.36, 14.50)}
STYLE = {"B1": ("o", MID, MID), "M1": ("D", "white", "#303030"), "M3": ("s", BLUE, BLUE),
         "L1": ("^", "white", MID), "L1e": ("v", "white", MID)}
H = [("H1", 20.37, 14.37, 26.16, "filled"), ("H2", 1.36, -2.20, 3.01, "filled"), ("H3", 16.69, 9.98, 24.21, "open")]
T = {
    "en": dict(
        rec="Records available by cutoff", cap=r"Review capacity per cutoff:  $k=\lfloor N/5\rfloor$",
        dos="Dated dossier and checklist for the selected cases", cut="Review cutoff $t_0$",
        evt="First linked final US ORIG/AP within the window", m12="12-month window", m24="24-month window",
        only="Outcomes are used only to score the queues",
        arms={"B1": "B1  drug age", "M1": "M1  dated-evidence table", "M3": "M3  table + graph states",
              "L1": "L1  exploratory identity prompt", "L1e": "L1e  exploratory evidence prompt"},
        pa="Recall at fixed review capacity (historical C′)",
        t24="24 months  ·  368 event rows, 924 slots", t12="12 months  ·  202 event rows, 1,048 slots",
        pb="Paired recall differences · +10 pp practical threshold",
        hl={"H1": "H1  M3 − B1, 24 months", "H2": "H2  M3 − M1, 24 months", "H3": "H3  M3 − B1, 12 months"},
        note={"H1": "H1 PASS against zero", "H2": "H2 FAIL, sequence stops", "H3": "Descriptive estimate only"},
        xl="Paired recall difference (percentage points)"),
    "th": dict(
        rec="หลักฐานที่เผยแพร่ภายในวันตัดข้อมูล", cap=r"จำนวนช่องทบทวนต่อวันตัดข้อมูล  $k=\lfloor N/5\rfloor$",
        dos="แฟ้มหลักฐานและรายการตรวจสอบสำหรับรายการที่เลือก", cut="วันตัดข้อมูล $t_0$",
        evt="ORIG/AP แรกในสหรัฐฯ ที่เชื่อมกับตัวยาได้ภายในช่วงติดตาม", m12="ติดตาม 12 เดือน", m24="ติดตาม 24 เดือน",
        only="ผลที่เกิดขึ้นใช้ประเมินคิวเท่านั้น",
        arms={"B1": "B1  อายุยา", "M1": "M1  ตารางหลักฐานตามวันที่", "M3": "M3  ตารางร่วมกับสถานะกราฟ",
              "L1": "L1  สำรวจด้วยคำสั่งระบุตัวยา", "L1e": "L1e  สำรวจด้วยคำสั่งพร้อมหลักฐาน"},
        pa="การครอบคลุมเมื่อกำหนดจำนวนช่องทบทวน (ชุดย้อนหลัง C′)",
        t24="24 เดือน  ·  368 แถวเหตุการณ์, 924 ช่อง", t12="12 เดือน  ·  202 แถวเหตุการณ์, 1,048 ช่อง",
        pb="ผลต่างแบบจับคู่ · เกณฑ์ประโยชน์เชิงปฏิบัติ +10 จุดร้อยละ",
        hl={"H1": "H1  M3 − B1, 24 เดือน", "H2": "H2  M3 − M1, 24 เดือน", "H3": "H3  M3 − B1, 12 เดือน"},
        note={"H1": "H1 ผ่านเมื่อเทียบกับศูนย์", "H2": "H2 ไม่ผ่าน จึงหยุดทดสอบ", "H3": "รายงานผลเชิงพรรณนา"},
        xl="ผลต่างการครอบคลุมแบบจับคู่ (จุดร้อยละ)"),
}


def thai_math():
    name = plt.rcParams["font.family"][0]
    plt.rcParams.update({"mathtext.fontset": "custom", "mathtext.rm": name, "mathtext.it": name + ":italic"})


def fig1(lang):
    t = T[lang]
    fig = fs.figure(6.5, 1.65)
    ax = fig.add_axes([0.01, 0.03, 0.98, 0.94])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.axis("off")
    t0 = 43
    ax.plot([3, t0], [14.5, 14.5], color=INK, lw=0.8)
    ax.text(3, 16.0, t["rec"], fontsize=fs.pt(7.5), va="bottom")
    x0, w, gap = 3, 4.2, 0.9
    for i in range(5):
        ax.add_patch(Rectangle((x0 + i * (w + gap), 7.2), w, 3.6, facecolor=INK if i == 0 else "white",
                               edgecolor=MID if i else INK, lw=0.6))
    ax.text(3, 5.0, t["cap"], fontsize=fs.pt(7.5), va="center")
    ax.text(3, 2.2, t["dos"], fontsize=fs.pt(7), color=MID, va="center")
    ax.plot([t0, t0], [1, 19], color="#3A3A3A", lw=0.9)
    ax.text(t0 + 0.8, 18.6, t["cut"], fontsize=fs.pt(8), weight="bold", va="top")
    for y, end, lab in ((11.5, 70, t["m12"]), (7.0, 97, t["m24"])):
        ax.plot([t0, end], [y, y], color=INK, lw=0.8)
        ax.plot([end, end], [y - 0.9, y + 0.9], color=INK, lw=0.8)
        ax.text(end - 0.6, y - 1.1, lab, fontsize=fs.pt(7), ha="right", va="top", color=MID)
    ax.text(t0 + 1.2, 13.9 if lang == "th" else 14.6, t["evt"], fontsize=fs.pt(7.5), va="bottom")
    ax.text(t0 + 1.2, 2.8, t["only"], fontsize=fs.pt(7), color=MID, va="center")
    fs.check_fonts(fig)
    fs.save(fig, OUT / f"fig1_capacity_{lang}", formats=("png", "svg"))


def dots(ax, idx, title):
    rows = {"B1": 0, "M1": 1, "M3": 2, "L1": 3.5, "L1e": 4.5}
    for k, y in rows.items():
        v = VAL[k][idx]
        m, fc, ec = STYLE[k]
        if k == "M3":
            ax.axhspan(y - 0.42, y + 0.42, color=TINT, lw=0, zorder=0)
        ax.plot([0, v], [y, y], color="#E6E6E6", lw=0.6, zorder=1)
        ax.plot([v], [y], marker=m, ms=4.6, mfc=fc, mec=ec, mew=0.8, ls="none", zorder=3)
        ax.text(v + 2.5, y, f"{v:.2f}%", va="center", fontsize=fs.pt(7), color=BLUE if k == "M3" else INK,
                weight="bold" if k == "M3" else "normal")
    ax.set_xlim(0, 100)
    ax.set_ylim(5.1, -0.7)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.set_yticks([])
    fs.clean(ax, left=False)
    ax.set_title(title, fontsize=fs.pt(7.6), loc="left", pad=3)


def fig2(lang):
    t = T[lang]
    fig = fs.figure(6.5, 3.55)
    lab = fig.add_axes([0.0, 0.52, 0.225, 0.36])
    lab.set_ylim(5.1, -0.7)
    lab.set_xlim(0, 1)
    lab.axis("off")
    for k, y in {"B1": 0, "M1": 1, "M3": 2, "L1": 3.5, "L1e": 4.5}.items():
        lab.text(0.98, y, t["arms"][k], ha="right", va="center", fontsize=fs.pt(7),
                 weight="bold" if k == "M3" else "normal", color=BLUE if k == "M3" else INK)
    top = 0.36
    dots(fig.add_axes([0.24, 0.52, 0.34, top]), 0, t["t24"])
    dots(fig.add_axes([0.63, 0.52, 0.34, top]), 1, t["t12"])
    fig.text(0.01, 0.975, "a", fontsize=fs.pt(8.5), weight="bold", va="top")
    fig.text(0.04, 0.975, t["pa"], fontsize=fs.pt(8), va="top")
    b = fig.add_axes([0.24, 0.15, 0.34, 0.22] if lang == "th" else [0.24, 0.11, 0.34, 0.25])
    for i, (h, e, lo, hi, kind) in enumerate(H):
        b.plot([lo, hi], [i, i], color=INK, lw=1.3)
        b.plot([e], [i], marker="s" if kind == "filled" else "o", ms=4.8, mfc=INK if kind == "filled" else "white",
               mec=INK, mew=0.9)
        b.text(-5.6, i, t["hl"][h], ha="right", va="center", fontsize=fs.pt(7.2))
        b.text(31, i, f"{e:+.2f} [{lo:+.2f}, {hi:+.2f}]".replace("-", "−"), va="center", fontsize=fs.pt(7))
        b.text(49, i, t["note"][h], va="center", fontsize=fs.pt(7), weight="bold" if h == "H2" else "normal")
    b.axvline(0, color=INK, lw=0.8)
    b.axvline(10, color=MID, lw=0.6, ls=(0, (1, 1.6)))
    b.set_xlim(-5, 30)
    b.set_ylim(2.6, -0.6)
    b.set_yticks([])
    b.set_xticks([0, 10, 20, 30])
    b.set_xlabel(t["xl"], fontsize=fs.pt(7.2))
    fs.clean(b, left=False)
    fig.text(0.01, 0.44, "b", fontsize=fs.pt(8.5), weight="bold", va="top")
    fig.text(0.04, 0.44, t["pb"], fontsize=fs.pt(8), va="top")
    fs.check_fonts(fig)
    fs.save(fig, OUT / f"fig2_recall_{lang}", formats=("png", "svg"))


if __name__ == "__main__":
    for lang in ("en", "th"):
        fs.setup(lang)
        if lang == "th":
            thai_math()
        fig1(lang)
        fig2(lang)
    print("ok")
