"""Задние углы у пола (D-стойка ↔ арка) по 4 фото сверху с рулеткой, 2026-11-06, — точки с фото и модель.
Оба борта в одной ориентации: по горизонтали — от края фанеры у борта в салон, по вертикали — вперёд от
передней грани короба D-стойки (у края фанеры). Дюймы, по полу.
Точки с фото — docs/rear_corners_points.json (tools/photo_corners_2026-11-06.py), модель — docs/drawing_data.json."""
import json
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, DOCS, load, box, save

d = load()
G, W, DP, BED = d["geo"], d["WHEEL_ARCH"], d["DPILLAR"], d["BED"]
PH = json.load(open(os.path.join(DOCS, "rear_corners_points.json"), encoding="utf-8"))
XDP, YW = G["x_dp"], G["arch_ywall"]
PW = DP["photo_wall"]


def to_ph(x, y):
    """Модель (X, Y) → (от края фанеры в салон, вперёд от короба), дюймы."""
    return (YW - abs(y) - PW) / IN, (x - XDP) / IN


def a_lin(dd):
    return (W["len_x_wall"] - (W["len_x_wall"] - W["len_x"]) * dd / W["protrusion"]) / 2.0


def gap_model(yi):
    dd = PW + yi * IN
    xa = W["center_x"] - a_lin(dd)
    xb = XDP - DP["box_slant"] * (min(dd, PW + DP["box_depth"]) - PW) / DP["box_depth"]
    return (xa - xb) / IN, (xb - XDP) / IN, (xa - XDP) / IN


C_A, C_D, C_S = "#bdbdbd", "#d6d6d6", "#607d8b"
MK = {"p1": ("o", "#d32f2f"), "p2": ("s", "#1565c0"), "p3": ("o", "#d32f2f"), "p4": ("s", "#1565c0")}
fig, axs = plt.subplots(1, 2, figsize=(16.5, 11.5), dpi=140)
for ax, tag, side, photos, what in ((axs[0], "nY", "Пассажирский борт (правый)", ("p1", "p2"), "batt"),
                                    (axs[1], "pY", "Водительский борт (левый)", ("p3", "p4"), "tank")):
    # стена, модельные короб D-стойки и арка (сечения у пола)
    ax.add_patch(Rectangle((-1.6, -7), 1.6, 25, color="#e0e0e0", zorder=0))
    ax.plot([-PW / IN] * 2, [-7, 18], color="#9e9e9e", lw=0.8, ls=":")
    ax.text(-0.8, 15.3, "борт", rotation=90, ha="center", fontsize=9, color="#616161")
    for w in d["corners"][tag]["dpillar"]:
        ax.add_patch(Polygon([to_ph(x, y) for x, y in w], fc=C_D, ec="#9e9e9e", hatch="///", zorder=1))
    for w in d["corners"][tag]["arch"]:
        ax.add_patch(Polygon([to_ph(x, y) for x, y in w], fc=C_A, ec="#757575", alpha=0.9, zorder=1))
    ax.text(4.2, 15.5, "колёсная арка", ha="center", fontsize=11, color="#424242")
    ax.text(2.6, -3.3, "короб D-стойки", ha="center", fontsize=10, color="#424242")
    ax.text(2.6, -6.4, "уплотнитель задней двери ~5.6″ за гранью короба", ha="center", fontsize=7.5,
            color="#757575")
    # стойка кровати и пластина TP35 (модель), бат./бак (модель, пунктир)
    pb, pp = box(d, "BedPost_%s_rear" % tag), box(d, "BedPostPlate_%s_rear" % tag)
    for b, kw in ((pp, dict(fill=False, ec="#78909c", ls="--", lw=1.0)), (pb, dict(fc=C_S, ec="#37474f"))):
        (y0, x0), (y1, x1) = to_ph(b[0], b[3] if tag == "pY" else b[2]), to_ph(b[1], b[2] if tag == "pY" else b[3])
        ax.add_patch(Rectangle((min(y0, y1), x0), abs(y1 - y0), x1 - x0, zorder=3, **kw))
    if what == "batt":
        bb = box(d, "Battery_Lower")
        (y0, x0), (y1, x1) = to_ph(bb[0], bb[2]), to_ph(bb[1], bb[3])
        ax.add_patch(Rectangle((min(y0, y1), x0), abs(y1 - y0), x1 - x0, fc="#ef6c00", alpha=0.12, ec="#ef6c00",
                               lw=1.8, ls="--", zorder=2))
        ax.text((y0 + y1) / 2 + 0.6, (x0 + x1) / 2 + 1.0, "батареи\n7.63 × 10.07″", ha="center", fontsize=9,
                color="#e65100", weight="bold")
    else:
        tb = box(d, "WaterTank_TORVA33")
        rb = [box(d, n) for n in d["boxes"] if n.startswith("TankRiser_Sleeper_Foot")]
        for b in rb:
            (y0, x0), (y1, x1) = to_ph(b[0], b[3]), to_ph(b[1], b[2])
            ax.add_patch(Rectangle((min(y0, y1), x0), abs(y1 - y0), x1 - x0, fc="#a0703c", alpha=0.35, ec="#5d4037",
                                   zorder=2))
        (y0, x0), (y1, x1) = to_ph(tb[0], tb[3]), to_ph(tb[0] + 235.0, tb[2])
        ax.add_patch(Rectangle((min(y0, y1), x0), abs(y1 - y0), x1 - x0, fill=False, ec="#1f5f8b", lw=1.8, ls="--",
                               zorder=2))
        ax.text(min(y0, y1) + 6.9, x0 + 6.6, "«нога» бака\n(низ, 9.25″)\nи доски подставки", ha="center",
                fontsize=8.5, color="#1f5f8b")
    # точки с фото
    for k in photos:
        p = PH[k]
        m, c = MK[k]
        for key, lw in (("arch", 1.4), ("dpillar", 1.4), ("dp_inboard", 1.0)):
            pts = p[key]
            if pts:
                ax.plot([q[1] for q in pts], [q[0] for q in pts], marker=m, ms=4.5, color=c, lw=lw, alpha=0.85,
                        zorder=5, label="фото %s" % k[1] if key == "arch" else None)
        pl = p["plate"]
        ax.add_patch(Polygon([(q[1], q[0]) for q in pl], fill=False, ec=c, lw=0.9, ls=":", zorder=5))
        ax.plot([0.0], [p["post_center_X"]], marker="+", ms=11, mew=1.8, color=c, zorder=6)
    # размеры зазора короб ↔ арка (модель) + по фото
    for yi, key in ((0.0, "gap_wall"), (1.1, "gap_1_1"), (2.4, "gap_2_4"), (5.0, "gap_5")):
        g, xb, xa = gap_model(yi)
        xx = max(yi, 0.15)
        ax.annotate("", xy=(xx, xb), xytext=(xx, xa), arrowprops=dict(arrowstyle="<->", lw=1.0, color="#2e7d32"),
                    zorder=7)
        ax.text(xx + 0.1, xb + 0.35, "%.1f″" % g, fontsize=8.5, color="#2e7d32", rotation=90, va="bottom",
                ha="left", zorder=7, weight="bold")
    # таблица: зазор по фото и в модели
    rows = ["зазор короб ↔ арка по полу, дюймы", "от борта   модель   " + "   ".join("фото %s" % k[1] for k in photos)]
    for yi, key in ((0.0, "gap_wall"), (1.1, "gap_1_1"), (2.4, "gap_2_4"), (5.0, "gap_5")):
        rows.append("%5.1f″      %5.2f    " % (yi, gap_model(yi)[0]) + "    ".join("%5.2f" % PH[k][key] for k in photos))
    ax.text(6.5, -2.6, "\n".join(rows), fontsize=8.3, family="DejaVu Sans Mono", va="top", color="#1b5e20",
            bbox=dict(fc="white", ec="#a5d6a7", alpha=0.95), zorder=8)
    # выступ арки
    prot = (W["protrusion"] - PW) / IN
    ax.annotate("", xy=(0, 16.6), xytext=(prot, 16.6), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#424242"))
    ax.text(prot / 2, 16.85, "выступ арки %.2f″ (фото %s)" % (prot, " / ".join("%.2f" % PH[k]["protrusion"]
                                                                              for k in photos)),
            ha="center", fontsize=8.5, color="#424242")
    dep = DP["box_depth"] / IN
    ax.annotate("", xy=(0, -1.9), xytext=(dep, -1.9), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#424242"))
    ax.text(dep / 2, -1.65, "короб %.1f″ (фото %s)" % (dep, " / ".join("%.2f" % PH[k]["dp_depth"] for k in photos)),
            ha="center", fontsize=8, color="#424242")
    post_ph = " / ".join("%.2f" % PH[k]["post_center_X"] for k in photos)
    xc = (box(d, "BedPost_%s_rear" % tag)[0] + box(d, "BedPost_%s_rear" % tag)[1]) / 2.0
    ax.annotate("стойка кровати + пластина TP35:\nцентр %.2f″ от короба\n(фото %s;\nв модели — среднее бортов)" % (
        (xc - XDP) / IN, post_ph), xy=(0.95, (xc - XDP) / IN), xytext=(8.9, 9.0), fontsize=7.8, color="#37474f",
        zorder=8, bbox=dict(fc="white", ec="none", alpha=0.85), arrowprops=dict(arrowstyle="->", lw=0.8, color="#37474f"))
    ax.set_xlim(-1.6, 14.5)
    ax.set_ylim(-7, 18)
    ax.set_aspect("equal")
    ax.grid(True, color="#eeeeee", lw=0.6)
    ax.set_xlabel("от края фанеры у борта в салон, дюймы  (пунктир у борта — стена по скану, −0.63″)")
    ax.set_ylabel("вперёд от передней грани короба D-стойки, дюймы")
    ax.set_title(side, loc="left", fontsize=12)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9,
              title="линии с маркерами — с фото;\nзалито — модель; + — центр стойки", title_fontsize=7.5)

fig.suptitle("Задние углы у пола: D-стойка ↔ колёсная арка — по 4 фото сверху с рулеткой (2026-11-06), точность ±0.2″\n"
             "зазор короб D-стойки ↔ арка: у борта 10.6″ (пасс. 10.60, вод. 10.54); к центру растёт — арка уходит вперёд "
             "0.3″/1″, короб назад 0.2″/1″", fontsize=12.5)
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "rear_corners_drawing.png")
