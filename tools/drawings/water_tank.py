"""Бак для воды T-3500 (Class A Customs, 35 gal) на полке над водительской аркой — проект 2026-11-07.
Этажерка как у батарей на другом борту, но без рейки у борта: полка лежит на ровном верху арки через резину.
Дюймы. x — вдоль борта от передней грани короба D-стойки (вперёд — вправо); y — от стены у пола в салон;
z — от чистового пола. Все числа — из модели (docs/drawing_data.json). Прежний вариант (TORVA 33 gal) —
tools/drawings/archive/2026-11-07_water_tank_torva.py."""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import FuncFormatter

from _common import IN, load, arch_profile, save

d = load()
G, W, TR, DP, BED = d["geo"], d["WHEEL_ARCH"], d["TANK_RACK"], d["DPILLAR"], d["BED"]
S = TR["_summary"]
FF, XDP, YW = G["floor_top"], G["x_dp"], G["arch_ywall"]
B = d["boxes"]
SEC = d["trk"]
mx = lambda X: (X - XDP) / IN
yd = lambda Y: (YW - abs(Y)) / IN            # от стены у пола
mz = lambda Z: (Z - FF) / IN


def xr_(n):
    return mx(B[n][0]), mx(B[n][1])


def yr(n):
    a, c = yd(B[n][2]), yd(B[n][3])
    return min(a, c), max(a, c)


def zr(n):
    return mz(B[n][4]), mz(B[n][5])


def rect_xy(ax, n, **kw):                    # план: стена сверху (y = −от стены)
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.add_patch(Rectangle((x0, -y1), x1 - x0, y1 - y0, **kw))


def rect_xz(ax, n, **kw):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, **kw))


def rect_yz(ax, n, **kw):
    (y0, y1), (z0, z1) = yr(n), zr(n)
    ax.add_patch(Rectangle((y0, z0), y1 - y0, z1 - z0, **kw))


def vdim(ax, x, z0, z1, txt, fs=8, color="black", side=1):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=9)
    ax.text(x + 0.25 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right", fontsize=fs,
            color=color, zorder=9)


def hdim(ax, z, x0, x1, txt, fs=8, dz=0.35, color="black"):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=9)
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs, color=color, zorder=9)


C_S, C_T, C_ARCH, C_PLY, C_DECK, C_STRAP = "#607d8b", "#4a90c2", "#9e9e9e", "#d7b98e", "#d7ccc8", "#e65100"
CROSS = [n for n in ("BedCross_1", "BedCross_2", "BedCross_3") if n in B]
POSTS_W = ("BedPost_pY_rear", "BedPost_pY_front")
POSTS_I = ("TankPost_P3", "TankPost_P3f")
FITS = sorted(k for k in B if k.startswith("TankFitting_"))
STRAPS = sorted(k for k in B if k.startswith("TankStrap_"))
PADS = sorted(k for k in B if k.startswith("TankArchPad_"))
DECK1 = mx(B["BedDeck"][1])
SHOWER = mx(B["Shower_WallRear"][0]) if "Shower_WallRear" in B else None
XL, XR = -7.0, mx(B["BedPost_pY_front"][1]) + 4.5
tl, tw, th = (v / IN for v in TR["tank"])
R_T = TR["tank_r"] / IN

fig = plt.figure(figsize=(20, 15.5), dpi=130)
gs = fig.add_gridspec(2, 2, width_ratios=[XR - XL, 30.5], height_ratios=[25.5, 36.0 + FF / IN], wspace=0.06,
                      hspace=0.12)
axt = fig.add_subplot(gs[0, 0])
axe = fig.add_subplot(gs[1, 0])
axs = fig.add_subplot(gs[:, 1])

# ───────── ВИД СВЕРХУ (стена — сверху, как на плане фургона) ─────────
ax = axt
ax.add_patch(Rectangle((XL, 0), XR - XL, 1.2, color="#cfcfcf"))
ax.text(XL + 0.4, 0.6, "водительский борт", va="center", fontsize=9)
for w in d["corners"]["pY"]["dpillar"]:
    ax.add_patch(Polygon([(mx(x), -yd(y)) for x, y in w], fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
for w in d["corners"]["pY"]["arch"]:
    ax.add_patch(Polygon([(mx(x), -yd(y)) for x, y in w], color=C_ARCH, alpha=0.5))
ax.text(mx(W["center_x"]) - 2.0, -7.6, "колёсная арка (у пола) — под полкой и баком", ha="center", fontsize=8.5,
        color="#424242", zorder=6)
rect_xy(ax, "TankShelf", fc=C_PLY, alpha=0.35, ec="#a1887f")
for n in ("TankRail_Inner", "TankCross_Rear", "TankCross_Front"):
    rect_xy(ax, n, fc=C_S, alpha=0.85, zorder=3)
for n in PADS:
    rect_xy(ax, n, fill=False, ec="#212121", ls="--", lw=0.9, zorder=3)
for n in [k for k in B if k.startswith("TankPostPlate_")] + ["BedPostPlate_pY_rear", "BedPostPlate_pY_front"]:
    rect_xy(ax, n, fill=False, ec="#90a4ae", ls=":", lw=0.8)
rect_xy(ax, "Water_Pump12V", fc="#3f51b5", alpha=0.15, ec="#3f51b5", ls="--", lw=1.2, zorder=2)
(x0, x1), (y0, y1) = xr_("Water_Pump12V"), yr("Water_Pump12V")
ax.text((x0 + x1) / 2 - 0.4, -y1 + 0.5, "насос + фильтр\n(на полу,\nпод полкой)", ha="center", fontsize=7,
        color="#283593", zorder=7)
(x0, x1), (y0, y1) = xr_("WaterTank_T3500"), yr("WaterTank_T3500")
ax.add_patch(FancyBboxPatch((x0, -y1), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=%.3f" % R_T,
                            fc=C_T, alpha=0.35, ec="#1f5f8b", lw=2, zorder=4))
ax.text((x0 + x1) / 2 + 2.0, -14.0, "бак T-3500, 35 gal\n38.5 × 17.25 × 12″\nполный ≈%.0f кг" % TR["full_kg"],
        ha="center", va="center", fontsize=10, color="#0d47a1", weight="bold", zorder=6)
for n in STRAPS:
    rect_xy(ax, n, fc=C_STRAP, alpha=0.9, zorder=5)
(sx0, sx1) = xr_(STRAPS[0])
ax.text((sx0 + sx1) / 2, -yr(STRAPS[0])[1] - 0.9, "ремни 1″", ha="center", fontsize=7.5, color=C_STRAP)
for n in ("TankStop_Rear", "TankStop_Front"):
    rect_xy(ax, n, color="#263238", zorder=6)
for n in FITS:
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.add_patch(Rectangle((x0, -y1), x1 - x0, y1 - y0, fc="#fafafa", ec="#424242", lw=0.9, zorder=7))
for f_ in S["fittings"]:
    ax.text(mx(f_["x"]) - 0.9, -yd(f_["y"]), "%s″ %s" % (("%.1f" % f_["d"]).rstrip("0").rstrip("."), f_["what"]),
            ha="right", va="center", fontsize=7, color="#212121", zorder=8)
for n in POSTS_W + POSTS_I:
    rect_xy(ax, n, color="#37474f", zorder=6)
for n, lab in (("BedPost_pY_rear", "P1"), ("BedPost_pY_front", "Pf")):
    (x0, x1) = xr_(n)
    ax.text((x0 + x1) / 2, 2.0, lab, ha="center", fontsize=8.5, weight="bold", color="#263238")
for n, lab in (("TankPost_P3", "P3"), ("TankPost_P3f", "P3f")):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.text((x0 + x1) / 2, -y1 - 0.75, lab, ha="center", fontsize=8.5, weight="bold", color="#263238")
for n in CROSS:
    x0, x1 = xr_(n)
    ax.add_patch(Rectangle((x0, -23.0), x1 - x0, 24.2, fill=False, ec="#263238", ls="-.", lw=0.9, zorder=8))
    ax.text((x0 + x1) / 2, -22.6, n.replace("BedCross_", "#"), ha="center", fontsize=7.5, color="#263238")
ax.text(mx(B["BedCross_1"][0]) - 0.3, -22.6, "поперечины кровати:", ha="right", fontsize=7.5, color="#263238")
for xx, lab, col in ((DECK1, "передний край\nщита кровати", "#6d4c41"), (SHOWER, "задняя стенка\nдуша", "#1565c0")):
    if xx is None:
        continue
    ax.plot([xx, xx], [-23.0, 1.2], color=col, ls="--", lw=1.1)
    ax.text(xx + 0.25, -21.0, lab, fontsize=7.5, color=col)
(x0, x1), (y0, y1) = xr_("WaterTank_T3500"), yr("WaterTank_T3500")
ax.annotate("", xy=(x1 + 3.6, -y0), xytext=(x1 + 3.6, -y1), arrowprops=dict(arrowstyle="<->", lw=0.9))
ax.text(x1 + 3.85, -(y0 + y1) / 2, "17.25″", va="center", fontsize=8)
ax.annotate("", xy=(x1 + 1.8, 0), xytext=(x1 + 1.8, -y0), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#616161"))
ax.text(x1 + 2.0, -y0 / 2 + 0.25, "%.1f″" % y0, fontsize=7.5, color="#616161")
ax.plot([XL, XR], [-y1, -y1], color="#1f5f8b", ls=":", lw=0.8)
ax.text(24.0, -y1 - 2.3, "грань бака к проходу — %.1f″ от стены у пола (арка — %.1f″)" % (y1, W["protrusion"] / IN),
        fontsize=8, color="#1f5f8b")
ax.set_xlim(XL, XR)
ax.set_ylim(-23.5, 2.6)
ax.set_aspect("equal")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%g" % abs(v)))
ax.set_ylabel("от стены (у пола) в салон, дюймы")
ax.set_title("Вид сверху (щит и матрас не показаны; пунктир — под полкой)", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА ВОДИТЕЛЬСКИЙ БОРТ ИЗНУТРИ (зад — слева) ─────────
ax = axe
zs = -FF / IN
ax.add_patch(Rectangle((XL, zs), XR - XL, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((XL, -0.47), XR - XL, 0.47, color=C_PLY))
ax.add_patch(Rectangle((XL, zs), -XL, DP["box_h"] / IN - zs, fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
ax.text(XL + 0.3, DP["box_h"] / IN + 0.4, "короб D-стойки", fontsize=7.5, color="#616161")
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
ax.text(mx(W["center_x"]), 6.0, "арка: верх %.2f″ над фанерой" % (W["height"] / IN), ha="center", color="white",
        fontsize=10)
rect_xz(ax, "BedSideRail_pY", color=C_S, alpha=0.55)
rect_xz(ax, "BedDeck", color=C_DECK, ec="#8d6e63")
for n in CROSS:
    rect_xz(ax, n, color="#263238")
ax.text(mx(B["BedDeck"][0]) + 0.3, zr("BedDeck")[1] + 0.35, "щит кровати (как сейчас в модели: +%.0f″)" % (
    BED["rail_raise"] / IN), fontsize=8, color="#6d4c41")
for n in POSTS_W:
    rect_xz(ax, n, color="#90a4ae", zorder=1)
for n in POSTS_I:
    rect_xz(ax, n, fc="none", ec="#263238", lw=1.1, ls="--", zorder=4)
rect_xz(ax, "Water_Pump12V", fc="#3f51b5", alpha=0.8, zorder=2)
ax.text(mx(B["Water_Pump12V"][0]) + 0.1, zr("Water_Pump12V")[1] + 0.4, "насос", fontsize=7.5, color="#283593")
for n in ("TankCross_Rear", "TankCross_Front", "TankRail_Inner"):
    rect_xz(ax, n, color=C_S, alpha=0.95 if n != "TankRail_Inner" else 0.55, zorder=3)
rect_xz(ax, "TankShelf", color=C_PLY, zorder=3)
for n in PADS:
    rect_xz(ax, n, color="#212121", zorder=4)
(x0, x1), (z0, z1) = xr_("WaterTank_T3500"), zr("WaterTank_T3500")
ax.add_patch(FancyBboxPatch((x0, z0), x1 - x0, z1 - z0, boxstyle="round,pad=0,rounding_size=%.3f" % R_T,
                            fc=C_T, alpha=0.55, ec="#1f5f8b", lw=1.5, zorder=4))
ax.text((x0 + x1) / 2, (z0 + z1) / 2, "бак T-3500, 35 gal (≈%.0f кг)" % TR["full_kg"], ha="center", va="center",
        fontsize=10.5, color="#0d47a1", weight="bold", zorder=6)
for n in STRAPS:
    (x0_, x1_) = xr_(n)
    ax.add_patch(Rectangle((x0_, zr(n)[0]), x1_ - x0_, zr(n)[1] - zr(n)[0], fc=C_STRAP, alpha=0.85, zorder=5))
for n in ("TankStop_Rear", "TankStop_Front"):
    rect_xz(ax, n, color="#263238", zorder=6)
for n in FITS:
    rect_xz(ax, n, fc="#fafafa", ec="#424242", lw=0.9, zorder=7)
for f_ in S["fittings"]:
    ax.text(mx(f_["x"]) - 0.85, mz(f_["z"]), "%s″ %s" % (("%.1f" % f_["d"]).rstrip("0").rstrip("."), f_["what"]),
            ha="right", va="center", fontsize=7, zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.5))
for n, lab in (("BedPost_pY_rear", "P1"), ("BedPost_pY_front", "Pf")):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.text((x0 + x1) / 2, min(z1, 35.0) + 0.3, lab, ha="center", fontsize=8.5, weight="bold")
zt_arch = W["height"] / IN
zsh1 = zr("TankShelf")[1]
zt_top = zr("WaterTank_T3500")[1]
zc_b = zr("BedCross_2")[0]
xm = mx(W["center_x"]) - 2.0
vdim(ax, xm - 4.0, 0, zt_arch, "верх арки %.2f″" % zt_arch)
vdim(ax, xm + 4.0, 0, zsh1, "полка %.1f″" % zsh1)
vdim(ax, mx(S["x"][1]) - 4.0, zsh1, zt_top, "12″")
vdim(ax, mx(S["x"][1]) - 1.5, zt_top, zc_b, "", color="#1565c0")
ax.text(mx(S["x"][1]) - 1.9, zt_top - 1.0, "верх бака %.1f″; до поперечин кровати %.1f″ (%.0f мм)" % (
    zt_top, zc_b - zt_top, (zc_b - zt_top) * IN), fontsize=7.5, color="#1565c0", ha="right", zorder=9)
hdim(ax, zt_top + 0.9, mx(S["x"][0]), mx(S["x"][1]), "38.5″", fs=8)
hdim(ax, zr("TankRail_Inner")[0] - 1.0, *xr_("TankRail_Inner"),
     "рейка со стороны прохода %.1f″ (%.0f) на P3 и P3f; поперечины — у стоек кровати P1 и Pf; полка — фанера 3/4″ "
     "на них и на верху арки через резину %.0f мм" % (S["rail"] / IN, S["rail"], TR["pad"]), fs=7.5, dz=-0.95)
ax.annotate("упор на передней\nпоперечине", xy=(mx(B["TankStop_Front"][0]), zr("TankStop_Front")[1]),
            xytext=(mx(B["TankStop_Front"][0]) + 1.0, 21.5), fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.text(mx(B["TankPost_P3f"][1]) + 0.3, 6.5, "P3, P3f —\nпунктир (со\nстороны\nпрохода)", fontsize=7.5)
ax.set_xlim(XL, XR)
ax.set_ylim(zs - 0.2, 36.0)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань короба D-стойки; вперёд — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на водительский борт изнутри", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── РАЗРЕЗ ПО РЕМНЮ (смотрим вперёд, на кабину; борт — слева) ─────────
ax = axs
half = G["half"]
wall = [(yd(hw), mz(z)) for hw, z in half if z < FF + 1100.0]
ax.add_patch(Polygon([(-3.0, wall[0][1])] + wall + [(-3.0, wall[-1][1])], color="#cfcfcf"))
ax.add_patch(Rectangle((-3.0, zs), 30.0, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((-3.0, -0.47), 30.0, 0.47, color=C_PLY))
key_arch = [k for k in SEC if k.startswith("WheelArch_")][0]
for w in SEC[key_arch]:
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], color=C_ARCH, zorder=2))
for w in SEC.get("BedDeck", []):
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc=C_DECK, ec="#8d6e63", zorder=2))
for w in SEC.get("BedMattress", []):
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc="#e3f2fd", ec="#90caf9", zorder=2))
rect_yz(ax, "BedSideRail_pY", color=C_S, zorder=3)
rect_yz(ax, "BedCross_2", fill=False, ec="#263238", ls="-.", lw=0.9, zorder=3)
rect_yz(ax, "BedPost_pY_front", fill=False, ec="#90a4ae", ls="--", lw=0.9, zorder=1)
rect_yz(ax, "TankPost_P3f", fill=False, ec="#263238", ls="--", lw=1.0, zorder=3)
rect_yz(ax, "TankCross_Front", fill=False, ec=C_S, ls="--", lw=1.0, zorder=3)
rect_yz(ax, "TankRail_Inner", color=C_S, zorder=4)
rect_yz(ax, "TankShelf", color=C_PLY, ec="#8d6e63", zorder=4)
rect_yz(ax, PADS[0], fill=False, ec="#212121", ls="--", lw=0.9, zorder=4)
for w in SEC["WaterTank_T3500"]:
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc=C_T, alpha=0.6, ec="#1f5f8b", lw=1.5, zorder=5))
for w in SEC["TankStrap_1"]:
    ax.plot([yd(p[1]) for p in w] + [yd(w[0][1])], [mz(p[2]) for p in w] + [mz(w[0][2])], color=C_STRAP, lw=1.6,
            zorder=6)
(y0, y1), (z0, z1) = yr("WaterTank_T3500"), zr("WaterTank_T3500")
ax.text((y0 + y1) / 2, (z0 + z1) / 2 + 1.5, "бак\n17.25 × 12″", ha="center", va="center", fontsize=10, weight="bold",
        color="#0d47a1", zorder=7)
ax.text(y0 + 0.4, z0 + 0.9, "ремень вокруг бака и полки", fontsize=7, color=C_STRAP, zorder=7)
vdim(ax, y1 + 2.0, zsh1, z1, "12″", fs=8)
vdim(ax, y1 + 2.0, z1, zc_b, "%.1f″" % (zc_b - z1), fs=8, color="#1565c0")
vdim(ax, y1 + 5.2, 0, zsh1, "полка\n%.1f″" % zsh1, fs=8)
vdim(ax, (yd(B["TankRail_Inner"][2]) + W["protrusion"] / IN) / 2.0 - 1.5, 0, zr("TankShelf")[0], "", fs=8,
     color="#6d4c41")
ax.text(W["protrusion"] / IN + 0.4, 2.0, "под полкой —\nниша %.1f″\n(между аркой\nи рейкой)" % zr("TankShelf")[0],
        fontsize=7.5, color="#6d4c41")
hdim(ax, z1 + 1.2, y0, y1, "17.25″", fs=8)
ax.text(yr("TankRail_Inner")[0] - 0.3, zr("TankRail_Inner")[0] - 1.2, "рейка\n(на P3/P3f)", ha="right", fontsize=7.5)
ax.text(yd(B[PADS[0]][3]) + 0.2, zr(PADS[0])[0] - 1.3, "резина на\nверху арки", fontsize=7.5)
ax.text(0.3, zr("BedSideRail_pY")[1] + 0.4, "рейка кровати", fontsize=7.5, color="#37474f")
ax.text(26.8, zr("BedCross_2")[1] + 0.35, "поперечина кровати #2 (за разрезом)", ha="right", fontsize=7,
        color="#263238")
ax.text(0.5, -1.4, "стена", fontsize=7.5, color="#616161")
ax.set_xlim(-3.0, 27.5)
ax.set_ylim(zs - 0.2, 40.0)
ax.set_aspect("equal")
ax.set_xlabel("от стены (у пола) в салон, дюймы")
ax.set_title("Разрез по ремню (X=%.1f″), вид вперёд" % mx(SEC["x"]), fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

spec = ("T-3500 (Class A Customs; Amazon «T3500-TO»): 38.5 × 17.25 × 12″ (±0.25″), стенка 7/32″, без давления —\n"
        "нужен «дыхательный» штуцер. Штуцеры на заднем торце (к задним дверям): 1.5″ — залив и слив, 0.5″ — вентиль и к насосу.\n"
        "Полка — фанера 3/4″ %.1f × %.1f″;  рейка %.1f″, поперечины 2 × %.1f″, стойки P3/P3f 2 × %.1f″ (strut).\n"
        "Рейка в салон: %.0f%% веса бака → σ ≈ %.0f МПа (при толчке 3g — %.0f) при текучести %.0f; прогиб ≈ %.1f мм." % (
            S["shelf"][0] / IN, S["shelf"][1] / IN, S["rail"] / IN, S["cross"] / IN, S["post"] / IN, 100 * S["share"],
            S["sigma"], S["sigma3"], TR["yield_MPa"], S["defl"]))
fig.text(0.012, 0.012, spec, fontsize=9, va="bottom", family="DejaVu Sans",
         bbox=dict(fc="#e3f2fd", ec="#90caf9", alpha=0.95))
fig.suptitle("Бак для воды T-3500 (35 gal) на полке над водительской аркой, проект 2026-11-07\n"
             "как этажерка батарей, но без рейки у борта: полка лежит на верху арки через резину — бак (12″) влезает "
             "под кровать без её подъёма", fontsize=12)
fig.subplots_adjust(left=0.05, right=0.99, top=0.93, bottom=0.10)
save(fig, "water_tank_drawing.png")
