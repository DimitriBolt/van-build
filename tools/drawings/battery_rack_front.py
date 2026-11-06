"""Чертёж переднего блока батарей (арка ↔ сдвижная дверь, пассажирский борт).
Дюймы. x — вдоль борта, 0 = задняя (к арке) грань передней стойки кровати P1, + к двери (вперёд);
y — от стены в салон; z — от чистового пола. Все числа — из модели (docs/drawing_data.json)."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, load, box, arch_profile, save

d = load()
G, W, B = d["geo"], d["WHEEL_ARCH"], d["BED"]
FF = G["floor_top"]
P1b = box(d, "BedPost_nY_front")
REF = P1b[0]
mx = lambda X: (X - REF) / IN
mz = lambda Z: (Z - FF) / IN
YW = G["yw_post"]
SW, SD = 41.3 / IN, 20.6 / IN


def xr_(b):
    return mx(b[0]), mx(b[1])


def zr(b):
    return mz(b[4]), mz(b[5])


def yr(b):                                   # от стены, деталь на −Y
    a, c = (YW + b[2]) / IN, (YW + b[3]) / IN
    return min(a, c), max(a, c)


bat1, bat2 = box(d, "Battery_Lower_fwd"), box(d, "Battery_Upper_fwd")
X0, X1 = xr_(bat1)
BX = X1 - X0
YB0, YB1 = yr(bat1)
BY = YB1 - YB0
P1 = xr_(P1b)
P2 = xr_(box(d, "BedPost_nY_rackP2_fwd"))
P3 = xr_(box(d, "RackPost_P3_fwd"))
P4 = xr_(box(d, "RackPost_P4_fwd"))
YW0, YW1 = yr(P1b)
DOOR = mx(box(d, "Opening_SlidingDoor")[0])
DECK_EDGE = mx(box(d, "BedDeck")[1])
Z_B1, Z_B2 = zr(bat1), zr(bat2)
Z_R = zr(box(d, "RackShelfRail_Rear_fwd"))
Z_S = zr(box(d, "RackShelfPlate_fwd"))
Z_BEDRAIL = zr(box(d, "BedSideRail_nY"))
Z_DECK = zr(box(d, "BedDeck"))
Z_BOLT = mz(G["z_bolt"])
XC_OLD = xr_(box(d, "BedCross_3"))
XC_NEW = xr_(box(d, "BedCross_Rack_fwd"))
LSTOP = box(d, "RackLowerFrontStop_fwd")
LSTOP_X, LSTOP_Z = xr_(LSTOP), zr(LSTOP)
PROT = W["protrusion"] / IN
p3b = box(d, "RackPost_P3_fwd")
raise_in = B.get("rail_raise", 0.0) / IN

C_STRUT, C_BAT, C_ARCH, C_PLY = "#607d8b", "#ef6c00", "#9e9e9e", "#d7b98e"
XL, XR = -12, 13
fig, (axt, axe) = plt.subplots(2, 1, figsize=(11, 17.5), dpi=150, sharex=True,
                               gridspec_kw=dict(height_ratios=[17.8, 40.0]))

# ───────── ВИД СВЕРХУ ─────────
ax = axt
ax.add_patch(Rectangle((XL, -1.2), XR - XL, 1.2, color="#cfcfcf"))
ax.text(-9, -0.6, "борт", ha="center", va="center", fontsize=9)
xw1 = mx(W["center_x"] + W["len_x_wall"] / 2.0)
xi1 = mx(W["center_x"] + W["len_x"] / 2.0)
ax.add_patch(Polygon([(XL, 0), (xw1, 0), (xi1, PROT), (XL, PROT)], color=C_ARCH))
ax.text(-9.5, 5, "колёсная\nарка (у пола)", ha="center", va="center", color="white", fontsize=10)
ax.add_patch(Rectangle((DOOR, -1.2), 1.2, 17, color="#212121"))
ax.text(DOOR + 0.6, 8, "край сдвижной двери (U-уплотнитель)", rotation=90, color="white",
        ha="center", va="center", fontsize=8)
ax.plot([DECK_EDGE, DECK_EDGE], [0, 16], color="#8d6e63", ls=":", lw=1)
ax.text(DECK_EDGE + 0.15, 15.4, "передний край\nнастила", fontsize=7.5, color="#6d4c41", va="top")
for xs, lab in ((P1, "P1 (передняя\nстойка, есть)"), (P2, "P2\n(новая)")):
    ax.add_patch(Rectangle((xs[0], YW0), SW, SD, color=C_STRUT))
    ax.text((xs[0] + xs[1]) / 2, -2.35, lab, ha="center", fontsize=8, color="#37474f")
ax.add_patch(Rectangle(((P1[0] + P1[1]) / 2 - 2.0, 0), 4.0, 5.0, fill=False, ec="#90a4ae", ls="--", lw=0.8))
ax.add_patch(Rectangle((P2[0], 0), 4.0, 5.0, fill=False, ec="#90a4ae", ls="--", lw=0.8))
ax.add_patch(Rectangle((X0, YB0), BX, BY, fc=C_BAT, alpha=0.25, ec=C_BAT, lw=2))
ax.text((X0 + X1) / 2, YB0 + 5.5, "2 батареи\n(одна над другой)\n7.63 × 10.07″", ha="center",
        fontsize=9, color="#e65100", weight="bold")
for x0 in (X0, X1 - SD):
    ax.add_patch(Rectangle((x0, YB0), SD, BY + SD, fill=False, ec=C_STRUT, ls=":", lw=1.4))
for xs, lab in ((P3, "P3"), (P4, "P4")):
    ax.add_patch(Rectangle((xs[0], YB1), SW, SD, color=C_STRUT))
    ax.add_patch(Rectangle(((xs[0] + xs[1]) / 2 - 1.5, YB1), 3.0, 4.0, fill=False, ec="#90a4ae", ls="--", lw=0.8))
    ax.text((xs[0] + xs[1]) / 2, YB1 + 1.3, lab, ha="center", fontsize=8.5, color="#263238", weight="bold")
for xc in (XC_OLD, XC_NEW):
    ax.add_patch(Rectangle((xc[0], YW1 + SD), xc[1] - xc[0], 15, fill=False, ec="#263238", ls="-.", lw=1.2))
ax.add_patch(Rectangle((LSTOP_X[0], YB0), LSTOP_X[1] - LSTOP_X[0], BY + SD, fc="#455a64", alpha=0.6))
ax.text(LSTOP_X[1] + 0.4, 3.0, "упор нижней\nбатареи", fontsize=7.5, color="#263238")
ax.annotate("", xy=(X0, 13.6), xytext=(X1, 13.6), arrowprops=dict(arrowstyle="<->", lw=1))
ax.text((X0 + X1) / 2, 13.9, "7.63″ — задом к арке", ha="center", fontsize=8.5)
gap = (DOOR - X1)
ax.annotate("", xy=(X1, 12.4), xytext=(DOOR, 12.4), arrowprops=dict(arrowstyle="<->", lw=1, color="#1565c0"))
ax.text((X1 + DOOR) / 2, 12.7, "%.1f″ (%.0f) до двери" % (gap, gap * IN), ha="center", fontsize=8.5, color="#1565c0")
ax.set_xlim(XL, XR)
ax.set_ylim(-2.8, 15)
ax.set_aspect("equal")
ax.set_ylabel("от стены в салон, дюймы")
ax.set_title("Вид сверху", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА БОРТ ИЗНУТРИ ─────────
ax = axe
zs = -FF / IN
ax.add_patch(Rectangle((XL, zs), XR - XL, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((XL, -0.47), XR - XL, 0.47, color=C_PLY))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
ax.text(-9.5, 7, "арка", ha="center", color="white", fontsize=10)
ax.add_patch(Rectangle((DOOR, zs), 1.2, 39, color="#212121"))
for xs in (P1, P2):
    ax.add_patch(Rectangle((xs[0], 0.06), SW, 35.5, color="#90a4ae", zorder=1))
ax.text((P1[0] + P1[1]) / 2 + 0.6, 35.9, "P1 (есть)", ha="center", fontsize=8)
ax.text((P2[0] + P2[1]) / 2 - 0.6, 35.9, "P2 (новая)", ha="center", fontsize=8)
for xb, lab in (((P1[0] + P1[1]) / 2, "M8 завод."), ((P2[0] + P2[1]) / 2, "M6 новая")):
    ax.plot(xb, Z_BOLT, "o", color="#2e7d32", ms=7, zorder=5)
    ax.text(xb, Z_BOLT + 1.1, lab, ha="center", fontsize=7, color="#2e7d32", zorder=5)
ax.add_patch(Rectangle((XL, Z_BEDRAIL[0]), DECK_EDGE - XL, SW, color=C_STRUT, alpha=0.5, zorder=1))
ax.add_patch(Rectangle((XL, Z_DECK[0]), DECK_EDGE - XL, Z_DECK[1] - Z_DECK[0], color="#d7ccc8", zorder=1))
ax.text(-11.5, Z_DECK[1] + 0.3, "настил кровати (поднят на %.0f″)" % raise_in if raise_in > 0 else "настил кровати",
        fontsize=7.5)
for z in (Z_B1, Z_B2):
    ax.add_patch(Rectangle((X0, z[0]), BX, z[1] - z[0], fc=C_BAT, ec="#bf360c", zorder=2))
ax.add_patch(Rectangle((X0, Z_R[0]), BX, SW, color=C_STRUT, alpha=0.6, zorder=2))
ax.add_patch(Rectangle((X0, Z_S[0]), BX, Z_S[1] - Z_S[0], color=C_PLY, zorder=3))
ax.add_patch(Rectangle((X1, Z_R[0]), 0.126, Z_B2[0] + 1.5 - Z_R[0], color="#263238", zorder=6))
ax.add_patch(Rectangle((LSTOP_X[0], LSTOP_Z[0]), LSTOP_X[1] - LSTOP_X[0], LSTOP_Z[1] - LSTOP_Z[0], color="#263238", zorder=6))
ax.text(X1 + 1.0, LSTOP_Z[0] + 0.3, "упор нижней", fontsize=7)
ax.text(X1 + 0.4, Z_B2[0] + 0.6, "упор верхней", fontsize=7)
ax.add_patch(Rectangle(((X0 + X1) / 2 - 1.18, Z_B1[1]), 2.36, Z_R[1] - Z_B1[1], color="#212121", zorder=1.5))
for xs in (P3, P4):
    ax.add_patch(Rectangle((xs[0], 0.06), SW, mz(p3b[5]), fc="none", ec="#263238", lw=1.2, ls="--", zorder=4))
for xc, lab in ((XC_OLD, "поперечина\n(есть)"), (XC_NEW, "новая\nпоперечина")):
    ax.add_patch(Rectangle((xc[0], Z_BEDRAIL[0]), xc[1] - xc[0], SW, color="#263238", zorder=6))
    ax.text((xc[0] + xc[1]) / 2, Z_BEDRAIL[0] - 1.3, lab, ha="center", fontsize=7, zorder=6)


def hdim(z0, z1, x, txt):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9))
    ax.text(x + 0.25, (z0 + z1) / 2, txt, va="center", fontsize=8)


hdim(0, Z_B1[1], 6.0, "%.2f″ нижняя" % Z_B1[1])
hdim(Z_B2[0], Z_B2[1], 6.0, "верхняя → %.1f″" % Z_B2[1])
hdim(Z_B2[1], Z_BEDRAIL[0], 6.0, "%.1f″ (%.0f) клеммы" % (Z_BEDRAIL[0] - Z_B2[1], (Z_BEDRAIL[0] - Z_B2[1]) * IN))
ax.text(P4[1] + 0.2, Z_BEDRAIL[0] - 4.6, "P3, P4\n(пунктир),\nL=%.0f" % (p3b[5] - p3b[4]), fontsize=7.5)
ax.set_xlim(XL, XR)
ax.set_ylim(zs - 0.2, 38)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = задняя грань передней стойки кровати; вперёд к двери — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на пассажирский борт изнутри (перед — справа)", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)
fig.suptitle("Передний блок: 2 батареи Buknuwo 150Ah между аркой и сдвижной дверью (пассажирский борт)\n"
             "схема как у заднего блока, зеркально; по фото 20 арка может быть на ~1″ дальше — тогда батареи вровень с настилом",
             fontsize=11)
fig.tight_layout()
save(fig, "battery_rack_front_drawing.png")
