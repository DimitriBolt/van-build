# АРХИВ (2026-11-05): анализ места под батарею до утверждения этажерки; числа — по модели того дня
# (арка-эллипс, без подъёма кровати). Не обновляется — см. tools/drawings/*.py
"""Вариант 1 крупно: батарея между D-стойкой и аркой как можно ближе к борту + что промерить."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from shapely.geometry import Polygon as SPoly, box

BW, BL = 7.63, 10.07
ARCH_WALL, ARCH_IN, PROT = 5.5, 7.7, 10.6
DP_FACE, DP_Y = -1.9, 6.2
POST_IN = 0.3 + 0.8125                       # внутренняя грань стойки кровати от стены

def arch_x(y):                               # задняя грань арки на расстоянии y от стены
    return ARCH_WALL + (ARCH_IN - ARCH_WALL) * min(y, PROT) / PROT

def gap(y):                                  # D-стойка → арка на расстоянии y от стены
    return arch_x(y) - DP_FACE

# ближайшее к борту положение, где 7.63″ проходит
y_min = next(y / 100 for y in range(0, 1061) if gap(y / 100) >= BW)
print("gap at wall %.2f, need %.2f, closest y %.2f in" % (gap(0), BW, y_min))

arch = SPoly([(ARCH_WALL, 0), (14, 0), (14, PROT), (ARCH_IN, PROT)])
fig, ax = plt.subplots(figsize=(10.5, 8), dpi=150)
ax.add_patch(Rectangle((-5, -1.0), 19, 1.0, color="#bdbdbd"))
ax.text(10.5, -0.5, "борт (стена)", ha="center", va="center", fontsize=9)
ax.add_patch(Rectangle((-5, 0), DP_FACE + 5, DP_Y, fc="#d6d6d6", ec="#9e9e9e", hatch="///"))
ax.text(-3.4, 3.1, "D-стойка", ha="center", fontsize=9, color="#424242")
ax.add_patch(Rectangle((2.6, 0), 4.5, 0.6, color="#212121"))
ax.text(4.85, -0.5, "решётка вентиляции", ha="center", va="center", fontsize=7.5)
ax.add_patch(Rectangle((-1.625, 0.3), 1.625, 0.8125, color="#90a4ae"))
ax.text(-0.8, 0.0 - 0.0, "", fontsize=1)
ax.add_patch(Rectangle((-2.8, 0), 4.0, 5.0, fill=False, ls="--", ec="#b0bec5", lw=0.8))
ax.text(-0.9, 5.2, "пластина\n(батарея стоит на ней)", fontsize=7, color="#78909c", ha="center")
ax.add_patch(Polygon(list(arch.exterior.coords), color="#9e9e9e", alpha=0.9))
ax.text(10.5, 5, "колёсная\nарка", ha="center", va="center", fontsize=11, color="white")
# D-ring на D-стойке — возможное препятствие
ax.add_patch(Rectangle((DP_FACE, 3.8), 0.8, 2.0, fc="none", ec="#c62828", ls="--", lw=1.4))
ax.annotate("D-ring на D-стойке?\n(фото 5, 13: ~9–10″ от пола,\nвыступ ~¾″) — проверить",
            xy=(DP_FACE + 0.4, 5.8), xytext=(-4.8, 9.2), fontsize=8, color="#c62828",
            arrowprops=dict(arrowstyle="->", color="#c62828", lw=0.9))
# батарея в ближайшем положении
y0 = y_min
ax.add_patch(Rectangle((DP_FACE, y0), BW, BL, fc="#ff9800", alpha=0.18, ec="#e65100", lw=2))
ax.text(DP_FACE + BW / 2, y0 + BL / 2 + 0.8, "батарея 7.63 × 10.07″\n(узкой стороной вдоль борта)",
        ha="center", fontsize=9, color="#e65100", weight="bold")
ax.text(DP_FACE + BW / 2, y0 + BL / 2 - 0.9, "ближе всего к борту:\n%.1f″ (%.0f мм) от стены" % (y0, y0 * 25.4),
        ha="center", fontsize=9, color="#e65100")
# замеры A и B
for y, name, c in ((0.15, "B", "#6a1b9a"), (1.6, "A", "#1565c0")):
    ax.annotate("", xy=(DP_FACE, y), xytext=(arch_x(y), y),
                arrowprops=dict(arrowstyle="<->", color=c, lw=1.4))
ax.text(1.9, 1.85, "A: в 1½–2″ от стены — нужно ≥ 7¾″ (197 мм)", fontsize=8.5, color="#1565c0", ha="center")
ax.text(9.0, 0.25, "B: у самой стены ≈ %.1f″" % gap(0), fontsize=8.5, color="#6a1b9a")
ax.set_xlim(-5, 14)
ax.set_ylim(-1.0, 13)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань стойки кровати)")
ax.set_ylabel("от стены в салон, дюймы")
ax.grid(True, color="#eeeeee", lw=0.6)
ax.set_title("Вариант 1: батарея задом в D-стойку, как можно ближе к борту (вид сверху, по фото ±0.5″)",
             fontsize=10.5)
fig.tight_layout()
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "archive", "2026-11-05_battery_option1.png")
fig.savefig(out, facecolor="white")
print(out)
