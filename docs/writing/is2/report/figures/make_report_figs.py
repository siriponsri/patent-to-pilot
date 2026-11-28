"""Figures for the comprehensive Thai IS2 report (REPORT-TH.md). Designed by the main planner.

Every number below is copied from the receipt named next to it and was checked in the co-planner number audit
(28 Nov 2026). Run: python make_report_figs.py  (writes rfigNN.{png,svg,pdf} next to this file)
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/academic-figures/scripts"))
import figstyle as fs  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
from matplotlib.patches import Rectangle, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).parent
W = 6.0          # A4 report text width used for full-width figures (inches)
FREEZE_STATUS = "pending"   # set to "frozen" after TRACKA-FREEZE lands, then rerun


def fmt(v, d=2, sign=True):
    s = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
    return s.replace("-", "−")


# ---------------------------------------------------------------- Figure 1: research timeline
def fig01():
    fig = fs.figure(W, 3.0)
    ax = fig.add_axes([0.25, 0.20, 0.72, 0.77])
    rows = [  # label, start, end, phase colour index, sources: INDEX-PLAN, OWNER-DECISIONS, loe-bench HANDOFF
        ("กรอบวิจัยเดิม (G02, ต.ค.)", date(2026, 10, 24), date(2026, 10, 25), 0),
        ("ตรวจ DAPFAM และ IS1", date(2026, 11, 5), date(2026, 11, 16), 0),
        ("นำเสนอ Paper 53", date(2026, 11, 20), date(2026, 11, 21), 0),
        ("BridgeRet, AM-7, B53", date(2026, 11, 19), date(2026, 11, 23), 1),
        ("G03 และ P2", date(2026, 11, 21), date(2026, 11, 26), 1),
        ("Workbench ชุด S", date(2026, 11, 25), date(2026, 11, 26), 2),
        ("RA Pharma D30–D39", date(2026, 11, 26), date(2026, 11, 28), 2),
        ("LOE-Bench (D40)", date(2026, 11, 27), date(2026, 11, 28), 3),
        ("D41, OSF และ C′", date(2026, 11, 28), date(2026, 11, 29), 3),
    ]
    cols = [fs.GREY, fs.ACCENT_2, fs.GREY_D, fs.ACCENT]
    phase = ["ระยะ 1 จัดอันดับสิทธิบัตร", "ระยะ 2 ปรับขั้นค้นคืน", "ระยะ 3 Workbench และบริบทไทย", "ระยะ 4 Market Window Dossier"]
    n = len(rows)
    for i, (lab, s, e, p) in enumerate(rows):
        y = n - 1 - i
        ax.barh(y, (e - s).days, left=mdates.date2num(s), height=0.56, color=cols[p], edgecolor="none")
        ax.text(-0.02, y, lab, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=fs.pt(7.2))
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_yticks([])
    ticks = [date(2026, 10, 25), date(2026, 11, 1), date(2026, 11, 8), date(2026, 11, 15), date(2026, 11, 22), date(2026, 11, 29)]
    ax.set_xticks([mdates.date2num(d) for d in ticks])
    ax.set_xticklabels([f"{d.day} {'ต.ค.' if d.month == 10 else 'พ.ย.'}" for d in ticks], fontsize=fs.pt(7))
    ax.set_xlim(mdates.date2num(date(2026, 10, 22)), mdates.date2num(date(2026, 11, 30)))
    fs.clean(ax, left=False)
    for k, (c, t) in enumerate(zip(cols, phase)):
        fig.patches.append(Rectangle((0.02 + 0.245 * k, 0.03), 0.014, 0.035, transform=fig.transFigure,
                                     color=c, lw=0))
        fig.text(0.04 + 0.245 * k, 0.025, t, fontsize=fs.pt(6.6), va="bottom", color=fs.INK)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig01")


# ---------------------------------------------------------------- Figure 2: DAPFAM exposure (Paper 53)
def fig02():
    fig = fs.figure(W, 2.5)
    ax = fig.add_axes([0.02, 0.06, 0.56, 0.90])
    cols_n, n, hit = 36, 692, 257          # docs/evidence-scope/00-organization.md (original-source correction)
    for i in range(n):
        r, c = divmod(i, cols_n)
        ax.add_patch(Rectangle((c, -r), 0.82, 0.82, color=fs.ACCENT if i < hit else fs.GREY_L, lw=0))
    ax.set_xlim(-0.3, cols_n)
    ax.set_ylim(-(n // cols_n) - 1, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    t = fig.add_axes([0.61, 0.06, 0.37, 0.90])
    t.axis("off")
    t.text(0, 0.92, "692 คำค้นที่มีคำตอบข้ามสาขา (OUT)", fontsize=fs.pt(8), weight="bold", va="top")
    t.text(0, 0.74, "257", fontsize=fs.pt(16), color=fs.ACCENT, weight="bold", va="top")
    t.text(0.30, 0.715, "มีเป้าหมายที่ทราบอย่างน้อยหนึ่งฉบับ\nใน 100 อันดับแรก", fontsize=fs.pt(7.2), va="top")
    t.text(0, 0.47, "435", fontsize=fs.pt(16), color=fs.GREY_D, weight="bold", va="top")
    t.text(0.30, 0.445, "ไม่มีเป้าหมายในรายการ\nการจัดอันดับใหม่จึงช่วยไม่ได้", fontsize=fs.pt(7.2), va="top")
    t.text(0, 0.17, "strict OUT nDCG@100: Generic 0.0626\nPatent-aware 0.0634 (ต่าง +0.0008)", fontsize=fs.pt(6.8),
           va="top", color=fs.GREY_D)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig02")


# ---------------------------------------------------------------- Figure 4: BridgeRet fine-tune grid
def fig04():
    fig = fs.figure(W * 0.62, 2.4)
    ax = fig.add_axes([0.13, 0.20, 0.84, 0.72])
    # docs/healthtech/research/paper1-bridgeret/ft-grid30k/sstar-grid30k.md (OUT Recall@200)
    arms = [("Qwen3\nไม่ฝึกเพิ่ม", 0.2741, 0.2961, fs.GREY), ("Qwen3 หลังฝึก\n(สูตรที่เลือก)", 0.2472, 0.2826, fs.CONTRAST),
            ("PatEmbed\nไม่ฝึกเพิ่ม", 0.3282, 0.3494, fs.ACCENT)]
    for i, (lab, dev, val, c) in enumerate(arms):
        ax.bar(i - 0.19, dev, 0.36, color=c, alpha=0.55, edgecolor="none")
        ax.bar(i + 0.19, val, 0.36, color=c, edgecolor="none")
        ax.text(i - 0.19, dev + 0.006, f"{dev:.4f}", ha="center", fontsize=fs.pt(6.4))
        ax.text(i + 0.19, val + 0.006, f"{val:.4f}", ha="center", fontsize=fs.pt(6.4))
    ax.set_xticks(range(3))
    ax.set_xticklabels([a[0] for a in arms], fontsize=fs.pt(7))
    ax.set_ylim(0, 0.40)
    ax.set_ylabel("OUT Recall@200", fontsize=fs.pt(7))
    ax.text(0.01, 0.97, "แท่งจาง = DEV, แท่งเข้ม = VAL", transform=ax.transAxes, fontsize=fs.pt(6.6), va="top",
            color=fs.GREY_D)
    fs.clean(ax)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig04")


# ---------------------------------------------------------------- Figure 5: P2 structural acquisition
def fig05():
    fig = fs.figure(W * 0.62, 2.1)
    ax = fig.add_axes([0.30, 0.36, 0.62, 0.56])
    # docs/tracking/owner-note-22112026/receipts/P2-T04_results.md
    ax.barh(1, 11, color=fs.ACCENT, height=0.5)
    ax.barh(0, -58, color=fs.CONTRAST, height=0.5)
    ax.text(12, 1, "+11 เข้ามาใหม่", va="center", fontsize=fs.pt(7))
    ax.text(-59, 0, "58 หลุดออก", va="center", ha="right", fontsize=fs.pt(7))
    ax.axvline(0, color=fs.GREY_D, lw=0.7)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["หลุดจาก 200 อันดับ", "เข้าสู่ 200 อันดับ"], fontsize=fs.pt(7))
    ax.set_xlim(-80, 48)
    ax.set_xlabel("จำนวนเป้าหมายที่ทราบ (DEV 2,000 คำขอ)", fontsize=fs.pt(7))
    fs.clean(ax, left=False)
    fig.text(0.02, 0.03, "Recall@200: ข้อความสมบูรณ์ 0.44998 เทียบกับค้นตามความสัมพันธ์ 0.44372\n"
             "ต่าง −0.00626 [−0.00902, −0.00369]", fontsize=fs.pt(6.4), color=fs.GREY_D)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig05")


# ---------------------------------------------------------------- Figure 6: controlled evidence reading
def fig06():
    fig = fs.figure(W, 2.3)
    ax = fig.add_axes([0.36, 0.08, 0.50, 0.86])
    rows = [  # label, k, n, group  (S3 RESULTS, Option A RESULTS, EIGHT-IDEA-RESULTS, b1e PLANNER-REVIEW)
        ("S3 ภาษาไทย: ควบคุมความครอบคลุม", 6, 27, 0),
        ("S3 ภาษาไทย: ตัวควบคุมขอบเขต", 3, 27, 0),
        ("Option A: วิธีเดิม", 22, 22, 1),
        ("Option A: สถาปัตยกรรมใหม่", 22, 22, 1),
        ("FDA รอบแรก: คู่ฉบับตรงกรณี", 0, 3, 2),
        ("D37: ฉลากต้นฉบับครบ", 24, 24, 3),
        ("D37: คู่ฉบับที่ใช้ได้", 22, 24, 3),
    ]
    n = len(rows)
    for i, (lab, k, m, g) in enumerate(rows):
        y = n - 1 - i - (0.4 * g)
        ax.barh(y, 1, color=fs.GREY_L, height=0.55)
        ax.barh(y, k / m, color=fs.ACCENT if g != 0 else fs.ACCENT_2, height=0.55)
        ax.text(-0.02, y, lab, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=fs.pt(7))
        ax.text(1.02, y, f"{k}/{m}", va="center", fontsize=fs.pt(7))
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    fs.clean(ax, left=False, bottom=False)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig06")


# ---------------------------------------------------------------- Figure 9: exploratory C3 and C4
def fig09():
    fig = fs.figure(W, 2.2)
    a = fig.add_axes([0.13, 0.24, 0.33, 0.62])
    # C3: docs/loe-bench/receipts/C3b.md (DEV 2013) and SCORE.md (C′ 2017–2023), M3 − B1 recall, pp
    c3 = [("DEV 2013", 25.60, 6.25, 45.00), ("C′ 2017–2023", 30.11, 20.16, 36.86)]
    for y, (lab, e, lo, hi) in zip([1, 0], c3):
        a.plot([lo, hi], [y, y], color=fs.ACCENT, lw=1.4)
        a.plot([e], [y], "s", color=fs.ACCENT, ms=4)
        a.text(hi + 1.5, y, fmt(e), va="center", fontsize=fs.pt(6.8))
    a.axvline(0, color=fs.GREY_D, lw=0.7, ls=(0, (3, 2)))
    a.set_yticks([0, 1])
    a.set_yticklabels([c[0] for c in reversed(c3)], fontsize=fs.pt(7))
    a.set_xlim(-5, 60)
    a.set_ylim(-0.6, 1.6)
    a.set_xlabel("M3 − B1 (จุดร้อยละ)", fontsize=fs.pt(7))
    a.set_title("ก) ผู้ยื่นอนุมัติ ≥ 3 รายใน 36 เดือน", fontsize=fs.pt(7.4), loc="left")
    fs.clean(a)
    b = fig.add_axes([0.64, 0.24, 0.33, 0.62])
    # C4: docs/loe-bench/receipts/C4b.md, queue-linked subset (4 cutoffs, 160 pairs), Q4 USD per prescription
    c4 = [("ต่อแนวโน้ม", -172.13, -292.12, -66.37), ("ปรับตามคิว B1", 372.05, 193.27, 587.26),
          ("ปรับตามคิว M3", 381.24, 203.61, 606.77)]
    for y, (lab, e, lo, hi) in zip([2, 1, 0], c4):
        col = fs.ACCENT if e < 0 else fs.CONTRAST
        b.plot([lo, hi], [y, y], color=col, lw=1.4)
        b.plot([e], [y], "o", color=col, ms=4)
    b.axvline(0, color=fs.GREY_D, lw=0.7, ls=(0, (3, 2)))
    b.set_yticks([0, 1, 2])
    b.set_yticklabels([c[0] for c in reversed(c4)], fontsize=fs.pt(7))
    b.set_xlabel("ผลต่าง MAE เทียบค่าล่าสุด (USD ต่อใบสั่งยา)", fontsize=fs.pt(7))
    b.set_title("ข) ยอดเบิกจ่าย Medicaid ไตรมาสสุดท้าย", fontsize=fs.pt(7.4), loc="left")
    b.set_ylim(-0.6, 2.6)
    fs.clean(b)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig09")


# ---------------------------------------------------------------- Figure 10: Track A status
def fig10():
    fig = fs.figure(W, 2.8)
    ax = fig.add_axes([0.05, 0.42, 0.90, 0.55])
    pts = [(date(2026, 11, 27), "t0\n27 พ.ย. 2026"), (date(2027, 1, 31), "ตรึงก่อน\n31 ม.ค. 2027"),
           (date(2027, 11, 27), "ครบ 12 เดือน\n27 พ.ย. 2027"), (date(2028, 11, 27), "ครบ 24 เดือน\n27 พ.ย. 2028")]
    x0 = mdates.date2num(pts[0][0])
    ax.plot([x0, mdates.date2num(pts[-1][0])], [0, 0], color=fs.GREY, lw=1.2)
    for i, (d, lab) in enumerate(pts):
        x = mdates.date2num(d)
        done = i == 0 or (i == 1 and FREEZE_STATUS == "frozen")
        ax.plot([x], [0], "o", ms=6, color=fs.ACCENT if done else "white", mec=fs.ACCENT, mew=1.2)
        below = i == 1
        ax.text(x, -0.35 if below else 0.35, lab, ha="center", va="top" if below else "bottom", fontsize=fs.pt(7))
    ax.set_ylim(-1.3, 1.4)
    ax.axis("off")
    t = fig.add_axes([0.03, 0.02, 0.94, 0.36])
    t.axis("off")
    st = [("แกน B1, M1, M3, B3", "คำพยากรณ์ 651 ต่อกรอบเวลา คิว 130 ช่อง", "พร้อม"),
          ("P1-RSF-OPEN, P2-COX-OPEN", "ผ่านเกณฑ์ทางเทคนิค คำพยากรณ์ 651 ต่อกรอบเวลา", "พร้อม"),
          ("C9 SFT และ GRPO", "ฝึกครบวิธีละ 64 ครั้ง คำพยากรณ์รอ GPU L4", "รอ"),
          ("L1 และ L1e", "คำพยากรณ์รอ GPU L4", "รอ")]
    if FREEZE_STATUS == "frozen":
        st = [(a, b, "ตรึงแล้ว") for a, b, _ in st]
    for i, (a, b_, s) in enumerate(st):
        y = 0.88 - i * 0.26
        t.text(0.0, y, a, fontsize=fs.pt(7), weight="bold", va="center")
        t.text(0.30, y, b_, fontsize=fs.pt(7), va="center")
        t.text(0.93, y, s, fontsize=fs.pt(7), va="center", color=fs.ACCENT if s != "รอ" else fs.CONTRAST)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig10")


# ---------------------------------------------------------------- Figure 12: evidence gate (Thai/ASEAN hand-off)
def fig12():
    fig = fs.figure(W, 1.9)
    ax = fig.add_axes([0.36, 0.10, 0.52, 0.82])
    rows = [("ข้อความที่ย้อนถึงแหล่งได้ (32 แฟ้ม)", 1789, 1789, fs.ACCENT),     # UIBUILD
            ("…ที่มีค่าแฮชของเนื้อหา", 1757, 1789, fs.ACCENT_2),                # UIBUILD
            ("ข้อจำกัดสิทธิบัตรที่มีเอกสารรองรับ", 3, 5, fs.ACCENT),            # EVP C6
            ("เบาะแสตระกูลจากสิทธิบัตรหลักสหรัฐฯ", 17, 17, fs.ACCENT),          # EVP C7
            ("สถานะสิทธิบัตรไทยที่ยืนยันได้", 0, 6, fs.CONTRAST)]               # EVP C7
    n = len(rows)
    for i, (lab, k, m, c) in enumerate(rows):
        y = n - 1 - i
        ax.barh(y, 1, color=fs.GREY_L, height=0.55)
        ax.barh(y, k / m, color=c, height=0.55)
        ax.text(-0.02, y, lab, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=fs.pt(7))
        ax.text(1.02, y, f"{k:,}/{m:,}", va="center", fontsize=fs.pt(7))
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    fs.clean(ax, left=False, bottom=False)
    fs.check_fonts(fig)
    fs.save(fig, OUT / "rfig12")


if __name__ == "__main__":
    fs.setup("th")
    for f in (fig01, fig02, fig04, fig05, fig06, fig09, fig10, fig12):
        f()
    print("ok")
