# АРХИВ (2026-11-05): анализ места под батарею до утверждения этажерки; числа — по модели того дня
# (арка-эллипс, без подъёма кровати). Не обновляется — см. tools/drawings/*.py
"""Вид сверху: карман между задней стойкой кровати и колёсной аркой (пассажирский борт).
Координаты в дюймах: x — вдоль стены (0 = грань задней стойки, + к арке), y — от стены в салон."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from shapely.geometry import Polygon as SPoly, box

BAT_L, BAT_W = 10.07, 7.63          # Buknuwo 12.8V 150Ah: 10.07 × 7.63 × 9.82″
ARCH_WALL, ARCH_IN, PROT = 5.5, 7.7, 10.6   # край арки у стены / по внутр. грани; выступ

arch = SPoly([(ARCH_WALL, 0), (14.5, 0), (14.5, PROT), (ARCH_IN, PROT)])
post = box(-1.625, 0.3, 0.0, 0.3 + 0.8125)

fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), dpi=150)
for ax, (bx, by, title) in zip(axes, (
        (BAT_L, BAT_W, "Батарея длинной стороной вдоль стены"),
        (BAT_W, BAT_L, "Батарея повёрнута: узкой стороной вдоль стены"))):
    # стена и угол D-стойки
    ax.add_patch(Rectangle((-4.5, -1.2), 19.0, 1.2, color="#bdbdbd"))
    ax.add_patch(Rectangle((-4.5, 0), 2.6, 12.5, color="#d6d6d6", hatch="///", ec="#9e9e9e", lw=0))
    ax.text(-3.2, 9.5, "угол /\nD-стойка", ha="center", va="center", fontsize=9, color="#555")
    ax.text(11.5, -0.6, "борт (стена)", ha="center", va="center", fontsize=9, color="#333")
    # вентиляционная решётка кузова на стене
    ax.add_patch(Rectangle((2.6, 0), 4.5, 0.6, color="#212121"))
    ax.text(4.85, -0.6, "решётка вентиляции (4.7–10.6″ от пола)", ha="center", va="center",
            fontsize=7.5, color="#212121")
    # стойка кровати и её пластина
    ax.add_patch(Rectangle((-2.8, 0), 4.0, 5.0, fill=False, ls="--", ec="#9e9e9e", lw=0.9))
    ax.add_patch(Rectangle((-1.625, 0.3), 1.625, 0.8125, color="#607d8b"))
    ax.text(-0.8, 5.4, "задняя стойка\n+ пластина", ha="center", fontsize=8, color="#455a64")
    # арка
    ax.add_patch(Polygon(list(arch.exterior.coords), color="#9e9e9e", alpha=0.85))
    ax.text(11.5, 5, "колёсная\nарка", ha="center", va="center", fontsize=10, color="white")
    # зазоры
    ax.annotate("", xy=(0, PROT + 0.4), xytext=(ARCH_IN, PROT + 0.4),
                arrowprops=dict(arrowstyle="<->", color="#1565c0", lw=1.2))
    ax.text(ARCH_IN / 2, PROT + 0.75, "7.7″ (196 мм) у внутренней грани арки", ha="center",
            fontsize=8, color="#1565c0")
    ax.annotate("", xy=(0, 1.6), xytext=(ARCH_WALL, 1.6),
                arrowprops=dict(arrowstyle="<->", color="#1565c0", lw=1.2))
    ax.text(ARCH_WALL / 2, 1.85, "~5.5″ у стены", ha="center", fontsize=8, color="#1565c0")
    # батарея и пересечение
    bat = box(0, 0.6, bx, 0.6 + by)
    ax.add_patch(Rectangle((0, 0.6), bx, by, fill=False, ec="#e65100", lw=2))
    inter = bat.intersection(arch)
    if not inter.is_empty:
        ax.add_patch(Polygon(list(inter.exterior.coords), color="#d32f2f", alpha=0.55))
    ax.text(bx / 2, 0.6 + by / 2 + (1.6 if by > 9 else 0.9),
            "батарея %.2f × %.2f″" % (bx, by), ha="center", fontsize=9, color="#e65100",
            weight="bold")
    ax.text(bx / 2, 0.6 + by / 2 - 0.4,
            "заходит в арку\nна %.1f″²" % inter.area if not inter.is_empty else "", ha="center",
            fontsize=8, color="#b71c1c")
    ax.set_title(title, fontsize=11)
    ax.set_xlim(-4.5, 14.5)
    ax.set_ylim(-1.2, 12.8)
    ax.set_aspect("equal")
    ax.set_xlabel("вдоль борта, дюймы (0 = грань задней стойки)")
    ax.set_ylabel("от стены в салон, дюймы")
    ax.grid(True, color="#eeeeee", lw=0.6)
fig.suptitle("Карман между задней стойкой кровати и аркой (пассажирский борт), вид сверху. "
             "Размеры — по фото 2, ±0.5″", fontsize=11)
fig.tight_layout()
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "archive", "2026-11-05_battery_pocket_plan.png")
fig.savefig(out, facecolor="white")
print(out)
