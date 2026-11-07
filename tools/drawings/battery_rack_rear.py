"""Чертёж заднего блока батарей (D-стойка ↔ арка, пассажирский борт): вид сверху + вид на борт.
Дюймы. x — вдоль борта (0 = передняя грань задней стойки кровати P1, + к арке); y — от стены в салон;
z — от чистового пола. Все числа — из модели (docs/drawing_data.json)."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, load, box, arch_profile, save

d = load()
G, W, R, B, DP = d["geo"], d["WHEEL_ARCH"], d["BATTERY_RACK"], d["BED"], d["DPILLAR"]
XDP = G["x_dp"]                                    # передняя грань короба D-стойки у края фанеры
FF = G["floor_top"]
P1b = box(d, "BedPost_nY_rear")
XREF = P1b[1]
mx = lambda X: (X - XREF) / IN
mz = lambda Z: (Z - FF) / IN
YW = G["yw_post"]                                  # стена на высоте болта стоек


def yr(b):                                         # (y0, y1) от стены для детали на −Y
    return (YW + b[2]) / IN, (YW + b[3]) / IN


def xr_(b):
    return mx(b[0]), mx(b[1])


def zr(b):
    return mz(b[4]), mz(b[5])


SW, SD = 41.3 / IN, 20.6 / IN
bat1, bat2 = box(d, "Battery_Lower"), box(d, "Battery_Upper")
X0, X1 = xr_(bat1)
BX = X1 - X0
YB0, YB1 = (YW - (-bat1[3])) / IN, (YW - (-bat1[2])) / IN
YB0, YB1 = min(YB0, YB1), max(YB0, YB1)
BY = YB1 - YB0
P1 = xr_(P1b)
P2 = xr_(box(d, "BedPost_nY_rackP2"))
YW0 = (YW - (-P1b[2])) / IN
YW0, YW1 = min(YW0, (YW - (-P1b[3])) / IN), max(YW0, (YW - (-P1b[3])) / IN)
Z_B1, Z_B2 = zr(bat1), zr(bat2)
Z_R = zr(box(d, "RackShelfRail_Rear"))
Z_S = zr(box(d, "RackShelfPlate"))
Z_BEDRAIL = zr(box(d, "BedSideRail_nY"))
Z_DECK = zr(box(d, "BedDeck"))
XC_REAR = xr_(box(d, "BedCross_1"))
XC_FRONT = xr_(box(d, "BedCross_RackFront"))
Z_TIE = zr(box(d, "BedCross_1"))
p3, p4 = box(d, "RackPost_P3"), box(d, "RackPost_P4")
LSTOP = box(d, "RackLowerFrontStop")
LSTOP_X, LSTOP_Z = xr_(LSTOP), zr(LSTOP)
Z_P34 = mz(p3[5])
Z_BOLT = mz(G["z_bolt"])
PROT = W["protrusion"] / IN
raise_in = B.get("rail_raise", 0.0) / IN

C_STRUT, C_BAT, C_ARCH, C_PLY = "#607d8b", "#ef6c00", "#9e9e9e", "#d7b98e"
fig, (axt, axe) = plt.subplots(2, 1, figsize=(11, 17.5), dpi=150, sharex=True,
                               gridspec_kw=dict(height_ratios=[17.8, 40.0]))

# ───────── ВИД СВЕРХУ ─────────
ax = axt
ax.add_patch(Rectangle((-10, -1.2), 28, 1.2, color="#cfcfcf"))
gx0, gx1 = mx(XDP + 4.4 * IN), mx(XDP + 10.1 * IN)                         # по фото сверху 2026-11-06
ax.add_patch(Rectangle((gx0, -0.75), gx1 - gx0, 0.75, color="#263238"))   # решётка утоплена в стену
ax.text((gx0 + gx1) / 2, -1.55, "решётка вентиляции (в борту)", ha="center", fontsize=8)
ax.text(15.5, -0.6, "борт", ha="center", va="center", fontsize=9)
for w in d["corners"]["nY"]["dpillar"]:            # сечение D-стойки модели у пола: короб
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
ax.text(mx(XDP) - 1.9, 2.4, "короб\nD-стойки", ha="center", fontsize=8.5)
for w in d["corners"]["nY"]["arch"]:               # сечение арки модели у пола (2″ над фанерой)
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], color=C_ARCH))
ax.text(14.5, 5, "колёсная арка\n(у пола)", ha="center", va="center", color="white", fontsize=10)
# свободно между батареей и аркой (у борта и у внутренней грани батарей)
arch_pts = [(x, (YW + y) / IN) for w in d["corners"]["nY"]["arch"] for x, y in w]
def arch_x_at(yy):
    c = [x for x, y in arch_pts if abs(y - yy) < 0.25]
    return mx(min(c)) if c else None
for xs, lab in ((P1, "P1\n(есть)"), (P2, "P2\n(новая)")):
    ax.add_patch(Rectangle((xs[0], YW0), SW, SD, color=C_STRUT))
    ax.text((xs[0] + xs[1]) / 2, -2.35, lab, ha="center", fontsize=8, color="#37474f")
for pn, plab in (("BedPostPlate_nY_rear", "TP35"), ("RackPostPlate_P2", "TP15")):   # пластины на полу
    pb = box(d, pn)
    py0 = min((YW + pb[2]) / IN, (YW + pb[3]) / IN)
    ax.add_patch(Rectangle((mx(pb[0]), py0), (pb[1] - pb[0]) / IN, (pb[3] - pb[2]) / IN,
                           fill=False, ec="#90a4ae", ls="--", lw=0.8))
    ax.text(mx((pb[0] + pb[1]) / 2), py0 + (pb[3] - pb[2]) / IN + 0.35, plab, ha="center", fontsize=6.5,
            color="#78909c")
ax.add_patch(Rectangle((X0, YB0), BX, BY, fc=C_BAT, alpha=0.25, ec=C_BAT, lw=2))
ax.text((X0 + X1) / 2, YB0 + 5.5, "2 батареи\n(одна над другой)\n7.63 × 10.07″", ha="center",
        fontsize=9, color="#e65100", weight="bold")
for x0 in (X0, X1 - SD):
    ax.add_patch(Rectangle((x0, YB0), SD, BY + SD, fill=False, ec=C_STRUT, ls=":", lw=1.4))
for xc in (XC_REAR, XC_FRONT):
    ax.add_patch(Rectangle((xc[0], YW1 + SD), SD, 15, fill=False, ec="#263238", ls="-.", lw=1.2))
ax.text(XC_FRONT[1] + 0.2, 14.3, "поперечины кровати → на всю ширину", fontsize=7.5, color="#263238")
ax.add_patch(Rectangle((LSTOP_X[0], YB0), LSTOP_X[1] - LSTOP_X[0], BY + SD, fc="#455a64", alpha=0.6))
ax.text(LSTOP_X[1] + 0.15, 3.3, "упор нижней\nбатареи", fontsize=7, color="#263238")
for b, lab in ((p3, "P3"), (p4, "P4")):
    x0 = mx(b[0])
    ax.add_patch(Rectangle((x0, YB1), SW, SD, color=C_STRUT))
    ax.add_patch(Rectangle((x0 + SW / 2 - 1.5, YB1), 3.0, 4.0, fill=False, ec="#90a4ae", ls="--", lw=0.8))
    ax.text(x0 + SW / 2, YB1 + 1.3, lab, ha="center", fontsize=8.5, color="#263238", weight="bold")
ax.annotate("", xy=(X0, 13.6), xytext=(X1, 13.6), arrowprops=dict(arrowstyle="<->", lw=1))
ax.text((X0 + X1) / 2, 13.9, "7.63″ (194)", ha="center", fontsize=8.5)
for yy in (YB0 + 0.15, min(YB1, PROT - 2.6)):
    xa = arch_x_at(yy)
    if xa is not None:
        ax.annotate("", xy=(X1, yy), xytext=(xa, yy), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#1565c0"))
        ax.text((X1 + xa) / 2, yy + 0.25, "%.1f″ (%.0f)" % (xa - X1, (xa - X1) * IN), ha="center", fontsize=7.5,
                color="#1565c0")
ax.text(X1 + 0.2, 9.6, "свободно до арки\n(кабели, предохранители)", fontsize=7, color="#1565c0")
ax.annotate("батареи — задом в короб\nD-стойки через резину %.0f мм" % R["dpillar_gap"],
            xy=(X0, YB0 + 0.6), xytext=(-9.7, 8.2), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
ax.annotate("", xy=(-7.0, YB0), xytext=(-7.0, YB1), arrowprops=dict(arrowstyle="<->", lw=1))
ax.text(-7.3, (YB0 + YB1) / 2, "10.07″", rotation=90, ha="right", va="center", fontsize=8.5)
ax.text(10.5, 12.3, "пунктир — пластины на полу\nточки — рейки полки (%.1f–%.1f″)\nштрих-пунктир — поперечины\n"
        "кровати = верхние стяжки" % (Z_R[0], Z_R[1]), fontsize=7.5, color="#546e7a")
ax.set_ylim(-2.8, 15)
ax.set_aspect("equal")
ax.set_ylabel("от стены в салон, дюймы")
ax.set_title("Вид сверху (арка и короб D-стойки — по фото сверху 2026-11-06)", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА БОРТ ИЗНУТРИ ─────────
ax = axe
zs = -FF / IN                                                              # железный пол
ax.add_patch(Rectangle((-10, zs), 28, -zs - 0.47, color="#f8bbd0"))      # XPS
ax.add_patch(Rectangle((-10, -0.47), 28, 0.47, color=C_PLY))              # фанера пола
ax.text(14.5, (zs - 0.47) / 2, "XPS 1″ + фанера ½″", fontsize=7.5, ha="center", va="center")
xbx = mx(XDP)                                                             # короб D-стойки у пола (выс. — оценка)
ax.add_patch(Rectangle((-10, zs), xbx + 10, DP["box_h"] / IN - zs, fc="#e0e0e0", ec="#9e9e9e", hatch="///", zorder=0))
ax.text(-7.6, DP["box_h"] / IN + 0.3, "короб D-стойки\n~%.0f″ (оценка)" % (DP["box_h"] / IN), fontsize=7, color="#616161")
d_bat = G["arch_ywall"] + bat1[2]                                         # грань батарей к борту, от стены
xbody = mx(XDP - DP["body_slant"] * d_bat / DP["body_depth"])
ax.add_patch(Rectangle((-10, DP["box_h"] / IN), xbody + 10, 38 - DP["box_h"] / IN, fc="#eeeeee", ec="#bdbdbd",
                       hatch="///", zorder=0))
ax.text(-7.6, 20, "D-стойка", ha="center", fontsize=9, color="#616161")
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
ax.text(16, 7, "арка\n(%.0f″)" % (W["height"] / IN), ha="center", color="white", fontsize=10)
for xs in (P1, P2):
    ax.add_patch(Rectangle((xs[0], 0.06), SW, 35.5, color="#90a4ae", zorder=1))
ax.text(-0.8, 35.9, "P1", ha="center", fontsize=8)
ax.text((P2[0] + P2[1]) / 2, 35.9, "P2 (новая, L=49.5″,\nдо рейки кровати)", ha="center", fontsize=8)
xb0 = mx(box(d, "BedSideRail_nY")[0])
ax.add_patch(Rectangle((xb0, Z_BEDRAIL[0]), 18 - xb0, SW, color=C_STRUT, alpha=0.5, zorder=1))
ax.text(10.5, Z_BEDRAIL[0] + 0.35, "продольная рейка кровати", fontsize=7.5, color="white")
xd0 = mx(box(d, "BedDeck")[0])
ax.add_patch(Rectangle((xd0, Z_DECK[0]), 18 - xd0, Z_DECK[1] - Z_DECK[0], color="#d7ccc8", zorder=1))
ax.text(10.5, Z_DECK[1] + 0.3, "настил кровати (поднят на %.0f″)" % raise_in if raise_in > 0 else "настил кровати",
        fontsize=7.5)
for xc, lab in ((XC_REAR, "задняя\nпоперечина"), (XC_FRONT, "новая\nпоперечина")):
    ax.add_patch(Rectangle((xc[0], Z_TIE[0]), SD, SW, color="#263238", zorder=6))
    ax.text(xc[0] + SD / 2, Z_TIE[0] - 1.3, lab, ha="center", fontsize=7, zorder=6)
for xb, lab in (((P1[0] + P1[1]) / 2, "M8 завод."), ((P2[0] + P2[1]) / 2, "M6 новая")):
    ax.plot(xb, Z_BOLT, "o", color="#2e7d32", ms=7, zorder=5)
    ax.text(xb, Z_BOLT + 1.1, lab, ha="center", fontsize=7, color="#2e7d32", zorder=5)
for z in (Z_B1, Z_B2):
    ax.add_patch(Rectangle((X0, z[0]), BX, z[1] - z[0], fc=C_BAT, ec="#bf360c", zorder=2))
ax.add_patch(Rectangle((X0, Z_R[0]), BX, SW, color=C_STRUT, alpha=0.6, zorder=2))
ax.add_patch(Rectangle((X0, Z_S[0]), BX, Z_S[1] - Z_S[0], color=C_PLY, zorder=3))
ax.add_patch(Rectangle((X1, Z_R[0]), 0.126, Z_B2[0] + 1.5 - Z_R[0], color="#263238", zorder=6))
ax.annotate("упор-уголок", xy=(X1 + 0.06, Z_B2[0] + 1.0), xytext=(X1 + 1.4, Z_B2[0] + 3.0), fontsize=7,
            arrowprops=dict(arrowstyle="-", lw=0.7))
ax.add_patch(Rectangle(((X0 + X1) / 2 - 1.18, Z_B1[1]), 2.36, Z_R[1] - Z_B1[1], color="#212121", zorder=1.5))
ax.add_patch(Rectangle((LSTOP_X[0], LSTOP_Z[0]), LSTOP_X[1] - LSTOP_X[0], LSTOP_Z[1] - LSTOP_Z[0], color="#263238",
                       zorder=6))
ax.annotate("упор нижней батареи\n(strut поперёк, к P2/P4)", xy=(LSTOP_X[1], (LSTOP_Z[0] + LSTOP_Z[1]) / 2),
            xytext=(7.4, 1.4), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.text((X0 + X1) / 2, Z_B1[1] - 0.9, "резиновый брусок", ha="center", fontsize=7, color="white", zorder=6)
for b in (p3, p4):
    ax.add_patch(Rectangle((mx(b[0]), 0.06), SW, Z_P34, fc="none", ec="#263238", lw=1.2, ls="--", zorder=4))
ax.text(mx(p4[1]) + 0.3, Z_TIE[0] - 4.2, "P3, P4 (со стороны\nсалона, пунктир),\nL=%.0f" % (p3[5] - p3[4]),
        fontsize=7.5, ha="left")


def hdim(z0, z1, x, txt):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9))
    ax.text(x + 0.25, (z0 + z1) / 2, txt, va="center", fontsize=8)


hdim(0, Z_B1[1], 6.6, "%.2f″ (%.0f) нижняя" % (Z_B1[1], Z_B1[1] * IN))
hdim(Z_B1[1], Z_R[0], 6.6, "%.1f″ клеммы" % (Z_R[0] - Z_B1[1]))
hdim(Z_R[0], Z_S[1], 6.6, "полка %.1f″" % (Z_S[1] - Z_R[0]))
hdim(Z_B2[0], Z_B2[1], 6.6, "верхняя → %.1f″ (%.0f)" % (Z_B2[1], Z_B2[1] * IN))
hdim(Z_B2[1], Z_TIE[0], 7.2, "%.1f″ (%.0f) клеммы" % (Z_TIE[0] - Z_B2[1], (Z_TIE[0] - Z_B2[1]) * IN))
ax.set_xlim(-10, 18)
ax.set_ylim(zs - 0.2, 38)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань задней стойки P1; назад к двери — влево)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на пассажирский борт изнутри (арка: светлая — у стены, тёмная — внутренняя грань)",
             fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)
fig.suptitle("Этажерка под 2 батареи Buknuwo 150Ah (между D-стойкой и аркой, пассажирский борт) — утверждено 2026-11-06\n"
             "strut SC14-10-EG; стяжки = поперечины кровати; угол D-стойка ↔ арка — фото сверху 2026-11-06 (±0.2″)",
             fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.975))
save(fig, "battery_rack_drawing.png")
