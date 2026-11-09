"""Чертёж: как стоят strut-профили — где спинка (овальные отверстия с шагом 2″) и где паз. Сечения модели.
Красная линия — спинка; открытая сторона «C» — паз. Дюймы (абсолютные координаты модели / 25.4)."""
import re

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from _common import IN, load, save

d = load()
if "strut" not in d:
    raise SystemExit("strut: нет данных — пропуск")
B, S, RULES = d["boxes"], d["strut"], d["STRUT_BACK"]
FF = d["geo"]["floor_top"]
AX = {"x": 0, "y": 1, "z": 2}
WORD = {"aisle": "в проход", "wall": "к борту", "+Y": "к водит. борту", "-Y": "к пасс. борту", "+X": "вперёд", "-X": "назад (к задним дверям)", "+Z": "вверх", "-Z": "вниз"}
COL = {"Battery_B": dict(fc="#ef6c00", alpha=0.35, ec="none"), "BankShelf": dict(fc="#d7b98e", alpha=0.7, ec="#8d6e63"),
       "BedDeck": dict(fc="#d7ccc8", alpha=0.7, ec="#8d6e63"), "BankRailBolt": dict(fc="#f9a825", ec="#795548")}


def rule(name):
    return next((b for p, b in RULES if re.match(p, name)), None)


def back_plane(name):
    """(ось, координата мм) плоскости спинки."""
    b, bb = rule(name), B[name]
    side = 1 if (bb[2] + bb[3]) > 0 else -1
    if b in ("aisle", "wall"):
        ax, sg = "y", (-side if b == "aisle" else side)
    else:
        ax, sg = b[1].lower(), (1 if b[0] == "+" else -1)
    i = AX[ax]
    return ax, (bb[2 * i + 1] if sg > 0 else bb[2 * i])


def panel(ax, key, h, v, lim, title, labels=()):
    hi, vi = AX[h], AX[v]
    conv = lambda p: (p[hi] / IN, (p[vi] - (FF if v == "z" else 0.0)) / IN)
    for n, wires in S[key].items():
        kw = next((c for k, c in COL.items() if n.startswith(k)), dict(fc="#b0bec5", ec="#37474f", lw=1.0))
        for w in wires:
            if len(w) > 2:
                ax.add_patch(Polygon([conv(p) for p in w], closed=True, zorder=3, **kw))
        if rule(n) and n in B:
            bax, bc = back_plane(n)
            bb = B[n]
            if bax in (h, v):                                   # спинка видна в этом сечении — красная линия
                other = v if bax == h else h
                oi = AX[other]
                a0, a1 = bb[2 * oi], bb[2 * oi + 1]
                lo, hi_ = (lim[2], lim[3]) if other == v else (lim[0], lim[1])
                off = FF if other == "z" else 0.0
                p0, p1 = max((a0 - off) / IN, lo), min((a1 - off) / IN, hi_)
                bcv = (bc - (FF if bax == "z" else 0.0)) / IN
                if bax == h:
                    ax.plot([bcv, bcv], [p0, p1], color="#d50000", lw=3, zorder=5, solid_capstyle="butt")
                else:
                    ax.plot([p0, p1], [bcv, bcv], color="#d50000", lw=3, zorder=5, solid_capstyle="butt")
    for txt, x, y, kw in labels:
        kw = dict(kw)
        kw.setdefault("fontsize", 8.5)
        ax.text(x, y, txt, zorder=6, bbox=dict(fc="white", ec="#9e9e9e", alpha=0.9, pad=2), **kw)
    ax.set_xlim(lim[0], lim[1])
    ax.set_ylim(lim[2], lim[3])
    ax.set_aspect("equal")
    ax.grid(True, color="#eeeeee", lw=0.6)
    names = {"x": "X вперёд от задней рамы", "y": "Y (+ водительский борт)", "z": "Z от пола"}
    ax.set_xlabel(names[h] + ", дюймы")
    ax.set_ylabel(names[v] + ", дюймы")
    ax.set_title(title, loc="left", fontsize=11)


def L(n):
    r = rule(n)
    return "%s\nспинка → %s" % (n, WORD.get(r, "?"))


fig, axs = plt.subplots(2, 3, figsize=(20, 14), dpi=110)
yzP = (-39.2, -28.6, 15.5, 33.5)
panel(axs[0, 0], "yz600", "y", "z", yzP, "Поперёк, X=23.6″ (взгляд вперёд): пассажирский борт — рейки",
      [(L("BedSideRail_nY"), -38.9, 30.5, {}), (L("BankRail_Wall"), -38.9, 15.9, {}),
       (L("BankRail_Inner"), -31.9, 15.9, {}), ("батарея B2\nна полке", -35.0, 24.0, dict(ha="center"))])
panel(axs[0, 1], "xy466", "x", "y", (13.0, 17.4, -39.0, -28.5),
      "План на Z=16.6″ над полом: стойки P1 и P3 и рейки этажерки (у рейки видны отверстия)",
      [(L("BedPost_nY_rear"), 13.1, -38.8, {}), (L("BankPost_P3"), 13.1, -30.2, {}),
       ("BankRail_Wall (разрез по спинке)", 15.7, -36.3, dict(fontsize=7.5)),
       ("BankRail_Inner\n(спинка к спинке с P3)", 15.7, -29.9, dict(fontsize=7.5))])
panel(axs[0, 2], "xy1000", "x", "y", (13.0, 16.5, 36.0, 38.6), "План на Z=37.6″: стойка кровати водительского борта",
      [(L("BedPost_pY_rear"), 14.9, 36.2, {})])
panel(axs[1, 0], "yz600", "y", "z", (35.5, 38.6, 29.6, 31.9), "Поперёк, X=23.6″: продольная рейка кровати водит. борта",
      [(L("BedSideRail_pY"), 35.6, 29.7, {})])
panel(axs[1, 1], "xz0", "x", "z", (14.8, 17.2, 29.8, 32.3), "Вдоль, Y=0: съёмная поперечина кровати #1 (на ребре)",
      [(L("BedCross_1"), 14.9, 29.9, {})])
panel(axs[1, 2], "xzm850", "x", "z", (13.6, 16.2, 9.0, 18.0), "Вдоль, Y=−33.5″: поперечина этажерки",
      [(L("BankCross_Rear"), 13.7, 16.2, {})] + ([(L("BankHolddown_B1"), 13.7, 9.3, {})] if "BankHolddown_B1" in B else []))
fig.suptitle("Strut 1-5/8 × 13/16″: где спинка и где паз (сечения модели, 2026-11-08)\n"
             "красная линия — СПИНКА (заводские овалы 9/16 × 1-1/8″ с шагом 2″), открытая сторона «C» — ПАЗ (губки)",
             fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.94))
save(fig, "strut_orientation_drawing.png")
