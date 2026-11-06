# АРХИВ (2026-11-05): анализ места под батарею до утверждения этажерки; числа — по модели того дня
# (арка-эллипс, без подъёма кровати). Не обновляется — см. tools/drawings/*.py
"""Вид сверху: угол D-стойки — колёсная арка (пассажирский борт), батарея внутрь от стойки кровати.
Дюймы: x — вдоль борта (0 = передняя грань стойки кровати, + к арке), y — от стены в салон."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from shapely.geometry import Polygon as SPoly, box

BL, BW = 10.07, 7.63                       # Buknuwo 150Ah: 10.07 × 7.63 × 9.82″
ARCH_WALL, ARCH_IN, PROT = 5.5, 7.7, 10.6  # арка: край у стены / по внутр. грани / выступ
DP_FACE, DP_DEPTH_Y = -1.9, 6.2            # передняя грань D-стойки (x) и её выступ от борта (y)
DOOR = -6.8                                # порог / закрытая задняя дверь (x)
DECK_REAR = -1.625                         # задний край настила = задняя грань стойки кровати

arch = SPoly([(ARCH_WALL, 0), (16, 0), (16, PROT), (ARCH_IN, PROT)])
dpillar = box(DOOR - 1, 0, DP_FACE, DP_DEPTH_Y)

cases = [
    ("1) Как ты предлагаешь: батарея внутрь от стойки,\nзадом в D-стойку, узкой стороной вдоль борта",
     box(DP_FACE, 1.3, DP_FACE + BW, 1.3 + BL)),
    ("2) Ещё дальше в салон (за край D-стойки),\nдлинной стороной вдоль борта, ближе к двери",
     box(DOOR + 0.5, DP_DEPTH_Y + 0.3, DOOR + 0.5 + BL, DP_DEPTH_Y + 0.3 + BW)),
]

fig, axes = plt.subplots(1, 2, figsize=(14, 7.2), dpi=150)
for ax, (title, bat) in zip(axes, cases):
    ax.add_patch(Rectangle((-8.5, -1.2), 25, 1.2, color="#bdbdbd"))
    ax.text(12.5, -0.6, "борт (стена)", ha="center", va="center", fontsize=9, color="#333")
    # D-стойка и проём задней двери
    ax.add_patch(Polygon(list(dpillar.exterior.coords), fc="#d6d6d6", ec="#9e9e9e", hatch="///", lw=0.8))
    ax.text((DOOR + DP_FACE) / 2 - 0.5, 3.1, "D-стойка\n(~6″ от борта)", ha="center", va="center",
            fontsize=8, color="#424242")
    ax.add_patch(Rectangle((-8.5, DP_DEPTH_Y), DOOR + 8.5, 9, color="#e0e0e0"))
    ax.plot([DOOR, DOOR], [DP_DEPTH_Y, 16], color="#455a64", lw=3)
    ax.text(DOOR - 0.35, 12.8, "задняя дверь (закрыта)", rotation=90, ha="right", va="center",
            fontsize=8, color="#455a64")
    ax.plot([DECK_REAR, DECK_REAR], [0, 16], color="#8d6e63", lw=1, ls=":")
    ax.text(DECK_REAR + 0.15, 15.3, "задний край\nнастила", fontsize=7.5, color="#6d4c41", va="top")
    # решётка вентиляции и стойка кровати (бледно — по условию не мешает)
    ax.add_patch(Rectangle((2.6, 0), 4.5, 0.6, color="#212121"))
    ax.text(4.85, -0.6, "решётка вентиляции", ha="center", va="center", fontsize=7.5, color="#212121")
    ax.add_patch(Rectangle((-1.625, 0.3), 1.625, 0.8125, color="#90a4ae"))
    ax.add_patch(Rectangle((-2.8, 0), 4.0, 5.0, fill=False, ls="--", ec="#b0bec5", lw=0.8))
    # арка
    ax.add_patch(Polygon(list(arch.exterior.coords), color="#9e9e9e", alpha=0.9))
    ax.text(12, 5, "колёсная\nарка", ha="center", va="center", fontsize=10, color="white")
    # батарея
    x0, y0, x1, y1 = bat.bounds
    hit = bat.intersection(arch).area + bat.intersection(dpillar).area
    gap_arch = bat.distance(arch)
    col = "#2e7d32" if hit == 0 and gap_arch >= 0.5 else "#e65100"
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=col, alpha=0.15, ec=col, lw=2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.6, "батарея\n%.2f × %.2f″" % (x1 - x0, y1 - y0),
            ha="center", va="center", fontsize=9, color=col, weight="bold")
    if hit > 0:
        verdict = "заходит в арку/стойку"
    else:
        verdict = "до арки %.1f″ (%.0f мм)" % (gap_arch, gap_arch * 25.4)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 1.0, verdict, ha="center", fontsize=8.5, color=col)
    ax.set_title(title, fontsize=10.5)
    ax.set_xlim(-8.5, 16)
    ax.set_ylim(-1.2, 16)
    ax.set_aspect("equal")
    ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань стойки кровати)")
    ax.set_ylabel("от стены в салон, дюймы")
    ax.grid(True, color="#eeeeee", lw=0.6)
    print(title.split("\n")[0], "| overlap", round(hit, 2), "| gap to arch", round(gap_arch, 2))
fig.suptitle("Батарея между D-стойкой и аркой (пассажирский борт), вид сверху. По фото, ±0.5″", fontsize=11)
fig.tight_layout()
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "archive", "2026-11-05_battery_pocket_plan2.png")
fig.savefig(out, facecolor="white")
print(out)
