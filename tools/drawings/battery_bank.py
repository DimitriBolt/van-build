"""Все 4 батареи по пассажирскому борту: задний блок (D-стойка ↔ арка, 2 одна над другой) + полка НАД аркой
(ещё 2, проект 2026-11-07). Вид сверху и вид на борт изнутри. Дюймы: x — вдоль борта от передней грани короба
D-стойки (вперёд — вправо), y — от стены в салон, z — от чистового пола. Все числа — из модели."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, load, box, arch_profile, save

d = load()
G, W, R, DP = d["geo"], d["WHEEL_ARCH"], d["BATTERY_RACK"], d["DPILLAR"]
FF, XDP, YW = G["floor_top"], G["x_dp"], G["yw_post"]
mx = lambda X: (X - XDP) / IN
mz = lambda Z: (Z - FF) / IN
B = d["boxes"]


def xr_(n):
    b = B[n]
    return mx(b[0]), mx(b[1])


def yr(n):                                   # от стены, деталь на −Y
    b = B[n]
    a, c = (YW + b[2]) / IN, (YW + b[3]) / IN
    return min(a, c), max(a, c)


def zr(n):
    b = B[n]
    return mz(b[4]), mz(b[5])


def rect_xy(ax, n, **kw):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **kw))


def rect_xz(ax, n, **kw):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, **kw))


C_S, C_BAT, C_ARCH, C_PLY, C_DECK = "#607d8b", "#ef6c00", "#9e9e9e", "#d7b98e", "#d7ccc8"
BATS_R = ("Battery_Lower", "Battery_Upper")
BATS_O = sorted(n for n in B if n.startswith("Battery_OverArch_"))
CROSS = [n for n in ("BedCross_1", "BedCross_RackFront", "BedCross_2", "BedCross_3") if n in B]
DOOR = mx(B["Opening_SlidingDoor"][0])
DECK0, DECK1 = mx(B["BedDeck"][0]), mx(B["BedDeck"][1])
XL, XR = -7, DOOR + 2.0

fig, (axt, axe) = plt.subplots(2, 1, figsize=(17, 15.8), dpi=140,
                               gridspec_kw=dict(height_ratios=[16.6 + 3.2, 40.2 + FF / IN]))

# ───────── ВИД СВЕРХУ ─────────
ax = axt
ax.add_patch(Rectangle((XL, -1.2), XR - XL, 1.2, color="#cfcfcf"))
ax.text(XL + 0.4, -0.6, "борт", va="center", fontsize=9)
for w in d["corners"]["nY"]["dpillar"]:
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
for w in d["corners"]["nY"]["arch"]:
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], color=C_ARCH, alpha=0.55))
ax.text(mx(W["center_x"]), 12.0, "колёсная арка (у пола) — под полкой", ha="center", fontsize=9, color="#616161")
for n in CROSS:
    x0, x1 = xr_(n)
    ax.add_patch(Rectangle((x0, -1.2), x1 - x0, 17.4, fill=False, ec="#263238", ls="-.", lw=1.0))
    ax.text((x0 + x1) / 2, 15.6, n.replace("BedCross_", "#").replace("#RackFront", "нов."), ha="center",
            fontsize=7.5, color="#263238")
ax.text(mx(B["BedCross_1"][0]) - 0.3, 14.3, "поперечины кровати:", ha="right", fontsize=7.5, color="#263238")
for xx, lab in ((DECK1, "передний край\nщита кровати"), (DOOR, "край проёма\nсдвижной двери")):
    ax.plot([xx, xx], [-1.2, 16.2], color="#8d6e63" if "щита" in lab else "#212121", ls="--", lw=1.2)
    ax.text(xx + 0.2, 12.6, lab, fontsize=8, color="#6d4c41" if "щита" in lab else "#212121")
for n in ("BedPostPlate_nY_rear", "BedPostPlate_nY_front", "RackPostPlate_P2", "RackPostPlate_P3", "RackPostPlate_P4",
          "RackPostPlate_P3f"):
    rect_xy(ax, n, fill=False, ec="#90a4ae", ls=":", lw=0.8)
for n in ("OverArchShelf",):
    rect_xy(ax, n, fc=C_PLY, alpha=0.35, ec="#a1887f")
for n in ("OverArchRail_Wall", "OverArchRail_Inner", "OverArchCross_Front"):
    rect_xy(ax, n, fc=C_S, alpha=0.75)
for n in BATS_R[:1] + tuple(BATS_O):
    rect_xy(ax, n, fc=C_BAT, alpha=0.35, ec=C_BAT, lw=2)
for n in ("BedPost_nY_rear", "BedPost_nY_rackP2", "RackPost_P3", "RackPost_P4", "BedPost_nY_front", "RackPost_P3f"):
    rect_xy(ax, n, color="#37474f")
for n, lab, dy in (("BedPost_nY_rear", "P1", -2.2), ("BedPost_nY_rackP2", "P2", -2.2),
                   ("BedPost_nY_front", "передняя стойка\nкровати", -2.6), ("RackPost_P3", "P3", 1.3),
                   ("RackPost_P4", "P4", 1.3), ("RackPost_P3f", "P3f (новая)", 1.3)):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.text((x0 + x1) / 2, (y1 + dy) if dy > 0 else dy, lab, ha="center", fontsize=8, color="#263238")
(x0, x1), (y0, y1) = xr_("Battery_Lower"), yr("Battery_Lower")
ax.text((x0 + x1) / 2, (y0 + y1) / 2, "задний блок:\n2 батареи\nодна над другой", ha="center", va="center",
        fontsize=8.5, color="#e65100", weight="bold")
for i, n in enumerate(BATS_O):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, "над аркой #%d" % (i + 1), ha="center", va="center", fontsize=8.5,
            color="#e65100", weight="bold")
xf0 = xr_(BATS_O[-1])[1] + 0.13
xfe = xr_("OverArchCross_Front")[0]
(y0, y1) = yr("OverArchShelf")
ax.text((xf0 + xfe) / 2, (y0 + y1) / 2, "свободно на полке\n%.1f″ — инвертор,\nзарядник, предохранители" % (xfe - xf0),
        ha="center", va="center", fontsize=8, color="#5d4037")
yl = yr("Battery_Lower")[1]
ax.annotate("", xy=(XL, yl), xytext=(DOOR, yl), arrowprops=dict(arrowstyle="-", lw=0.6, ls=":", color="#e65100"))
ax.text(mx(W["center_x"]) + 6.0, yl + 0.95, "все 4 батареи — в полосе %.1f″ от стены (у пола)" % (
    yl + (G["arch_ywall"] - YW) / IN), ha="center", fontsize=8, color="#e65100")
ax.set_xlim(XL, XR)
ax.set_ylim(-3.2, 16.6)
ax.set_aspect("equal")
ax.set_ylabel("от стены в салон, дюймы")
ax.set_title("Вид сверху (настил и матрас не показаны)", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА БОРТ ИЗНУТРИ ─────────
ax = axe
zs = -FF / IN
ax.add_patch(Rectangle((XL, zs), XR - XL, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((XL, -0.47), XR - XL, 0.47, color=C_PLY))
ax.add_patch(Rectangle((XL, zs), -XL - 0.0, DP["box_h"] / IN - zs, fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
ax.text(XL + 0.3, DP["box_h"] / IN + 0.4, "короб D-стойки", fontsize=7.5, color="#616161")
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
ax.text(mx(W["center_x"]), 6.5, "арка (верх %.0f″ — по Upfit, промерить)" % (W["height"] / IN), ha="center",
        color="white", fontsize=10)
ax.add_patch(Rectangle((DOOR, zs), 0.9, 40, color="#212121"))
ax.text(DOOR + 0.45, 20, "проём сдвижной двери", rotation=90, ha="center", va="center", color="white", fontsize=8)
# кровать
rect_xz(ax, "BedSideRail_nY", color=C_S, alpha=0.55)
rect_xz(ax, "BedDeck", color=C_DECK, ec="#8d6e63")
rect_xz(ax, "BedMattress", color="#e3f2fd", ec="#90caf9")
for n in CROSS:
    rect_xz(ax, n, color="#263238")
ax.text(DECK1 - 0.3, mz(B["BedMattress"][5]) + 0.4, "щит кровати (кончается в %.1f″ за передними стойками)" % (
    (B["BedPost_nY_front"][0] - B["BedDeck"][1]) / IN), ha="right", fontsize=8, color="#6d4c41")
ax.text(mx(B["BedSideRail_nY"][1]) + 0.2, mz(B["BedSideRail_nY"][4]) + 0.3, "продольная рейка\nкровати", fontsize=7.5)
# стойки
for n in ("BedPost_nY_rear", "BedPost_nY_rackP2", "BedPost_nY_front"):
    rect_xz(ax, n, color="#90a4ae", zorder=1)
for n in ("RackPost_P3", "RackPost_P4", "RackPost_P3f"):
    rect_xz(ax, n, fc="none", ec="#263238", lw=1.1, ls="--", zorder=4)
# задний блок
for n in BATS_R:
    rect_xz(ax, n, fc=C_BAT, ec="#bf360c", zorder=2)
for n in ("RackShelfRail_Front", "RackShelfRail_Rear"):
    rect_xz(ax, n, color=C_S, alpha=0.8, zorder=3)
rect_xz(ax, "RackShelfPlate", color=C_PLY, zorder=3)
# полка над аркой
for n in ("OverArchRail_Wall", "OverArchCross_Front"):
    rect_xz(ax, n, color=C_S, alpha=0.85, zorder=3)
rect_xz(ax, "OverArchShelf", color=C_PLY, zorder=3)
rect_xz(ax, "OverArchPad", color="#212121", zorder=4)
for n in BATS_O:
    rect_xz(ax, n, fc=C_BAT, ec="#bf360c", zorder=2)
for n in [k for k in B if k.startswith("OverArchStop_") or k.startswith("OverArchSpacer_")]:
    rect_xz(ax, n, color="#5d4037", zorder=5)


def vdim(x, z0, z1, txt, fs=8, color="black"):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color))
    ax.text(x + 0.25, (z0 + z1) / 2, txt, va="center", fontsize=fs, color=color)


def hdim(z, x0, x1, txt, fs=8, dz=0.35):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9))
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs)


zt_arch = W["height"] / IN
zs1 = zr("OverArchShelf")[1]
zb_top = zr(BATS_O[0])[1]
z_rail_b = zr("BedSideRail_nY")[0]
z_deck_b = zr("BedDeck")[0]
xo1 = xr_(BATS_O[-1])[1]
vdim(xo1 + 1.2, 0, zt_arch, "верх арки %.1f″" % zt_arch)
vdim(xo1 + 7.0, 0, zs1, "полка %.1f″" % zs1)
vdim(xo1 + 1.2, zs1, zb_top, "батарея → %.1f″" % zb_top)
vdim(xo1 + 1.2, zb_top, z_deck_b, "%.1f″ (%.0f) до настила" % (z_deck_b - zb_top, (z_deck_b - zb_top) * IN), fs=7.5,
     color="#1565c0")
ax.text(mx(B["OverArchRail_Wall"][0]) + 0.3, z_rail_b - 1.0,
        "⚠ до низа продольной рейки кровати — %.0f мм (у самого борта, полоса 0.8″)" % ((z_rail_b - zb_top) * IN),
        fontsize=7.5, color="#c62828")
bo = [xr_(n) for n in BATS_O]
hdim(zb_top + 3.0, bo[0][0], bo[0][1], "10.07″", fs=8)
hdim(zb_top + 3.0, bo[1][0], bo[1][1], "10.07″", fs=8)
hdim(zb_top + 3.0, bo[0][1], bo[1][0], "%.1f″" % (bo[1][0] - bo[0][1]), fs=7.5, dz=-0.9)
hdim(zr("OverArchRail_Wall")[0] - 1.1, *xr_("OverArchRail_Wall"),
     "рейки над аркой %.1f″ (%.0f), низ %.1f″ — на верх арки через резину" % (
         (B["OverArchRail_Wall"][1] - B["OverArchRail_Wall"][0]) / IN,
         B["OverArchRail_Wall"][1] - B["OverArchRail_Wall"][0], zr("OverArchRail_Wall")[0]), fs=7.5, dz=-0.9)
ax.text(mx(B["BedPost_nY_rackP2"][1]) + 0.2, 36.5, "P2", fontsize=8)
ax.text(mx(B["BedPost_nY_rear"][0]) - 0.2, 36.5, "P1", fontsize=8, ha="right")
ax.text(mx(B["RackPost_P3f"][0]) - 0.2, zr("RackPost_P3f")[1] + 0.4, "P3f (пунктир — со стороны салона)",
        fontsize=7.5, ha="right")
ax.set_xlim(XL, XR)
ax.set_ylim(zs - 0.2, 40)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань короба D-стойки; вперёд — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на пассажирский борт изнутри", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)
fig.suptitle("4 батареи Buknuwo 150Ah по пассажирскому борту: задний блок + полка НАД аркой (идея Dimitri, проект "
             "2026-11-07)\nвсе 4 батареи и арка — в одной полосе вдоль борта; ⚠ высота верха арки — оценка, от неё "
             "зависит зазор под кроватью", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.965))
save(fig, "battery_bank_drawing.png")
