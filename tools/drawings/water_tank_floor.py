"""ВАРИАНТЫ «T4100_floor» / «T4320_floor» (van_v0.WATER_VARIANT): бак на полу рядом с водительской аркой — T-4100
на поддоне или T-4320 прямо на полу (коврик); верх бака — вровень с полкой батарей. Рисуется для включённого
варианта → docs/water_tank_<бак>_drawing.png.
Дюймы. x — вдоль борта от передней грани короба D-стойки (вперёд — вправо); y — от стены у пола в салон;
z — от чистового пола. Все числа — из модели (docs/drawing_data.json)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import FuncFormatter

from _common import IN, load, arch_profile, save

d = load()
if "tfl" not in d:
    raise SystemExit("water_tank_floor.py: бак на полу не включён (WATER_VARIANT=%s) — чертёж не меняю" %
                     d.get("WATER_VARIANT"))
G, W, TF, DP, BED = d["geo"], d["WHEEL_ARCH"], d["TANK_FLOOR"], d["DPILLAR"], d["BED"]
S = TF["_summary"]
FF, XDP, YW = G["floor_top"], G["x_dp"], G["arch_ywall"]
B = d["boxes"]
SEC = d["tfl"]
TN = S["tank_name"]
PAL = S.get("base_mode") == "pallet"
tl_, tw_, th_ = (v / IN for v in TF["tank"])
fmt = lambda v: ("%.3f" % v).rstrip("0").rstrip(".")
DIMS = "%s × %s × %s″" % (fmt(tl_), fmt(tw_), fmt(th_))
GAL = TF["title"].split(",")[-1].strip()
YMAX = max(28.0, S["from_wall"][2] / IN + 1.0)          # план: до бруска бака со стороны прохода
SXR = max(35.0, S["from_wall"][2] / IN + 8.0)           # разрез: правый край
mx = lambda X: (X - XDP) / IN
yd = lambda Y: (YW - abs(Y)) / IN
mz = lambda Z: (Z - FF) / IN


def xr_(n):
    return mx(B[n][0]), mx(B[n][1])


def yr(n):
    a, c = yd(B[n][2]), yd(B[n][3])
    return min(a, c), max(a, c)


def zr(n):
    return mz(B[n][4]), mz(B[n][5])


def rect_xy(ax, n, **kw):
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


C_S, C_T, C_ARCH, C_PLY, C_DECK, C_STRAP, C_WOOD = ("#607d8b", "#4a90c2", "#9e9e9e", "#d7b98e", "#d7ccc8", "#e65100",
                                                    "#a0703c")
CROSS = [n for n in ("BedCross_1", "BedCross_2", "BedCross_3") if n in B]
POSTS_W = ("BedPost_pY_rear", "BedPost_pY_front")
FITS = sorted(k for k in B if k.startswith("TankFloor_Fitting_"))
STRAPS = sorted(k for k in B if k.startswith("TankFloor_Strap_"))
RUNNERS = sorted(k for k in B if k.startswith("TankFloor_Runner_"))
CLEATS = sorted(k for k in B if k.startswith("TankFloor_Cleat_"))
SPACERS = sorted(k for k in B if k.startswith("TankFloor_ArchSpacer_"))
DECK0, DECK1 = mx(B["BedDeck"][0]), mx(B["BedDeck"][1])
SHOWER = mx(B["Shower_Pan"][0]) if "Shower_Pan" in B else None          # задний край поддона душа
XL, XR = -8.5, mx(B["BedPost_pY_front"][1]) + 4.5
R_T = TF["tank_r"] / IN
FR = S.get("fittings_end") == "front"
ZBANK = mz(S["bank_top"]) if S.get("bank_top") else None

fig = plt.figure(figsize=(20, 16.5), dpi=130)
gs = fig.add_gridspec(2, 2, width_ratios=[XR - XL, SXR + 3.0], height_ratios=[YMAX + 4.5, 36.0 + FF / IN], wspace=0.06,
                      hspace=0.12)
axt = fig.add_subplot(gs[0, 0])
axe = fig.add_subplot(gs[1, 0])
axs = fig.add_subplot(gs[:, 1])


def fit_label(ax, f_, y):
    ax.text(mx(f_["x"]) + (0.9 if FR else -0.9), y, "%s″ %s" % (("%.1f" % f_["d"]).rstrip("0").rstrip("."), f_["what"]),
            ha="left" if FR else "right", va="center", fontsize=7, color="#212121", zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.5))


# ───────── ВИД СВЕРХУ (стена — сверху) ─────────
ax = axt
ax.add_patch(Rectangle((XL, 0), XR - XL, 1.2, color="#cfcfcf"))
ax.text(XL + 0.4, 0.6, "водительский борт", va="center", fontsize=9)
for w in d["corners"]["pY"]["dpillar"]:
    ax.add_patch(Polygon([(mx(x), -yd(y)) for x, y in w], fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
for w in d["corners"]["pY"]["arch"]:
    ax.add_patch(Polygon([(mx(x), -yd(y)) for x, y in w], color=C_ARCH, alpha=0.6))
ax.text(mx(W["center_x"]), -4.6, "колёсная арка (выступ %.1f″, верх %.2f″)" % (W["protrusion"] / IN, W["height"] / IN),
        ha="center", fontsize=8.5, color="#424242")
for n in RUNNERS:
    rect_xy(ax, n, fill=False, ec="#5d4037", ls="--", lw=0.9, zorder=2)
if PAL:
    rect_xy(ax, "TankFloor_BasePly", fc=C_PLY, alpha=0.45, ec="#a1887f", zorder=2)
for n in [k for k in B if k.startswith("TankFloor_Anchor_")]:
    rect_xy(ax, n, fc="#9e9e9e", ec="#424242", zorder=6)
for n in CLEATS:
    rect_xy(ax, n, fc=C_WOOD, ec="#5d4037", zorder=5)
for n in SPACERS:
    rect_xy(ax, n, color="#212121", zorder=5)
(x0, x1), (y0, y1) = xr_(TN), yr(TN)
ax.add_patch(FancyBboxPatch((x0, -y1), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=%.3f" % R_T,
                            fc=C_T, alpha=0.40, ec="#1f5f8b", lw=2, zorder=4))
ax.text((x0 + x1) / 2, -(y0 + y1) / 2, "бак %s, %s\n%s (выс. %s″)\nполный ≈%.0f кг" % (
    TN.split("_")[1].replace("T", "T-"), GAL, DIMS, fmt(th_), TF["full_kg"]),
        ha="center", va="center", fontsize=10, color="#0d47a1", weight="bold", zorder=6)
for n in STRAPS:
    rect_xy(ax, n, fc=C_STRAP, alpha=0.9, zorder=5)
ax.text(sum(xr_(STRAPS[0])) / 2, -yr(STRAPS[0])[1] - 0.9, "ремни 1″", ha="center", fontsize=7.5, color=C_STRAP)
for n in FITS:
    (fx0, fx1), (fy0, fy1) = xr_(n), yr(n)
    ax.add_patch(Rectangle((fx0, -fy1), fx1 - fx0, fy1 - fy0, fc="#fafafa", ec="#424242", lw=0.9, zorder=7))
for f_ in S["fittings"]:
    fit_label(ax, f_, -yd(f_["y"]))
rect_xy(ax, "Water_Pump12V", fc="#3f51b5", alpha=0.5, ec="#283593", zorder=3)
if "Toilet_Camco" in B:
    rect_xy(ax, "Toilet_Camco", fc="#bdbdbd", ec="#424242", lw=1.5, zorder=5)
    (ux0, ux1), (uy0, uy1) = xr_("Toilet_Camco"), yr("Toilet_Camco")
    ax.text((ux0 + ux1) / 2, -(uy0 + uy1) / 2, "туалет\nCamco\n16.25×14×17″", ha="center", va="center", fontsize=8.5,
            weight="bold", color="#212121", zorder=6)
    if SHOWER is not None:
        ax.annotate("", xy=(SHOWER - 0.3, -(uy0 + uy1) / 2), xytext=(ux1 + 0.2, -(uy0 + uy1) / 2),
                    arrowprops=dict(arrowstyle="->", lw=1.6, color="#2e7d32", ls="--"), zorder=7)
        ax.text((ux1 + SHOWER) / 2 + 0.8, -(uy0 + uy1) / 2 - 2.6, "позже — выезжает\nна платформе в душ", ha="center",
                fontsize=7.5, color="#2e7d32", zorder=7)
    hdim(ax, -uy0 + 1.6, ux1, DECK1, "%.1f″" % (S["toilet"]["in_deck"] / IN), fs=7.5)
(qx0, qx1), (qy0, qy1) = xr_("Water_Pump12V"), yr("Water_Pump12V")
ax.text(qx1 + 0.3, -(qy0 + qy1) / 2, "насос +\nфильтр", va="center", fontsize=7.5, color="#283593", zorder=7)
for n in POSTS_W:
    rect_xy(ax, n, color="#37474f", zorder=6)
for n, lab in (("BedPost_pY_rear", "P1"), ("BedPost_pY_front", "Pf")):
    ax.text(sum(xr_(n)) / 2, 2.0, lab, ha="center", fontsize=8.5, weight="bold", color="#263238")
for n in CROSS:
    cx0, cx1 = xr_(n)
    ax.add_patch(Rectangle((cx0, -YMAX - 1.0), cx1 - cx0, YMAX + 2.2, fill=False, ec="#263238", ls="-.", lw=0.9,
                           zorder=8))
    ax.text((cx0 + cx1) / 2, -YMAX - 1.6, n.replace("BedCross_", "#"), ha="center", fontsize=7.5, color="#263238")
for xx, lab, col in ((DECK0, "задний край\nщита", "#6d4c41"), (DECK1, "передний край\nщита кровати", "#6d4c41"),
                     (SHOWER, "поддон\nдуша", "#1565c0")):
    if xx is None:
        continue
    ax.plot([xx, xx], [-YMAX - 1.0, 1.2], color=col, ls="--", lw=1.1)
    ax.text(xx + 0.25, -YMAX + 0.2, lab.replace("\n", " "), fontsize=7.5, color=col, va="top", zorder=9)
hdim(ax, -(y0 + y1) / 2 - 5.2, x1, DECK1, "%.1f″" % (S["in_deck"] / IN), fs=8)
hdim(ax, -(y0 + y1) / 2 + 1.0, DECK0, x0, "%.1f″" % (S["behind"] / IN), fs=8)
xd_ = DECK1 + 3.0
for a_, b_, txt in ((0.0, y0, "%.1f″" % y0), (0.0, y1, "%.1f″" % y1)):
    ax.annotate("", xy=(xd_, -a_), xytext=(xd_, -b_), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#1f5f8b"))
    ax.text(xd_ + 0.25, -b_ + 0.5, txt + (" — грань бака к борту" if b_ == y0 else " — к проходу"), fontsize=7.5,
            color="#1f5f8b")
    xd_ += 3.4
ax.set_xlim(XL, XR)
ax.set_ylim(-YMAX - 2.2, 2.6)
ax.set_aspect("equal")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%g" % abs(v)))
ax.set_ylabel("от стены (у пола) в салон, дюймы")
ax.set_title("Вид сверху (щит и матрас не показаны%s)" % ("; пунктир — бруски поддона" if PAL else
             "; серые — анкеры ремней в полу"), fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА ВОДИТЕЛЬСКИЙ БОРТ ИЗНУТРИ (зад — слева; бак — перед аркой) ─────────
ax = axe
zs = -FF / IN
ax.add_patch(Rectangle((XL, zs), XR - XL, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((XL, -0.47), XR - XL, 0.47, color=C_PLY))
ax.add_patch(Rectangle((XL, zs), mx(XDP) - XL, DP["box_h"] / IN - zs, fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
ax.text(XL + 0.3, DP["box_h"] / IN + 0.4, "короб D-стойки", fontsize=7.5, color="#616161")
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
rect_xz(ax, "BedSideRail_pY", color=C_S, alpha=0.55)
rect_xz(ax, "BedDeck", color=C_DECK, ec="#8d6e63")
for n in CROSS:
    rect_xz(ax, n, color="#263238")
for n in POSTS_W:
    rect_xz(ax, n, color="#90a4ae", zorder=1)
for n in RUNNERS:
    rect_xz(ax, n, fc=C_WOOD, ec="#5d4037", zorder=3)
if PAL:
    rect_xz(ax, "TankFloor_BasePly", color=C_PLY, ec="#8d6e63", zorder=3)
(x0, x1), (z0, z1) = xr_(TN), zr(TN)
ax.add_patch(FancyBboxPatch((x0, z0), x1 - x0, z1 - z0, boxstyle="round,pad=0,rounding_size=%.3f" % R_T,
                            fc=C_T, alpha=0.6, ec="#1f5f8b", lw=1.5, zorder=4))
ax.text((x0 + x1) / 2, (z0 + z1) / 2 + 1.0, "бак %s, %s (≈%.0f кг)\nна полу перед аркой\n(арка — за ним)" % (
    TN.split("_")[1].replace("T", "T-"), GAL, TF["full_kg"]), ha="center", va="center", fontsize=10, color="#0d47a1", weight="bold", zorder=6)
for n in STRAPS:
    rect_xz(ax, n, fc=C_STRAP, alpha=0.85, zorder=5)
for n in CLEATS:
    rect_xz(ax, n, fc=C_WOOD, ec="#5d4037", zorder=5)
for n in FITS:
    rect_xz(ax, n, fc="#fafafa", ec="#424242", lw=0.9, zorder=7)
for f_ in S["fittings"]:
    fit_label(ax, f_, mz(f_["z"]))
rect_xz(ax, "Water_Pump12V", fc="#3f51b5", alpha=0.85, zorder=2)
for n, lab in (("BedPost_pY_rear", "P1"), ("BedPost_pY_front", "Pf")):
    ax.text(sum(xr_(n)) / 2, min(zr(n)[1], 35.0) + 0.3, lab, ha="center", fontsize=8.5, weight="bold")
if ZBANK is not None:
    ax.plot([XL, XR], [ZBANK, ZBANK], color="#e65100", ls="--", lw=1.0, zorder=8)
    ax.text(XR - 0.3, ZBANK + 0.4, "уровень полки батарей %.2f″" % ZBANK, ha="right", fontsize=8, color="#e65100")
if "Toilet_Camco" in B:                                  # справа от бака — туалет: размеры внутри бака
    vdim(ax, x1 - 3.0, z0, z1, "%s″" % fmt(th_), side=-1)
    vdim(ax, x1 - 1.2, 0, z1, "")
    ax.text(x1 - 1.5, z1 - 1.0, "верх %.2f″" % z1, ha="right", fontsize=8, zorder=9)
else:
    xm = mx(W["center_x"]) + 4.0
    if PAL:
        vdim(ax, xm, 0, z0, "поддон %.1f″" % z0)
    vdim(ax, xm, z0, z1, "%s″" % fmt(th_))
    vdim(ax, xm + 7.0, 0, z1, "верх бака %.2f″" % z1)
vdim(ax, x1 - 2.0, z1, zr("BedCross_2")[0], "%.1f″ до поперечин кровати" % (zr("BedCross_2")[0] - z1), fs=7.5,
     color="#1565c0", side=-1)
hdim(ax, z1 + 0.8, x0, x1, "%s″" % fmt(tl_), fs=8)
zq_ = z1 + 2.4 if "Toilet_Camco" in B else z0 + 3.0
hdim(ax, zq_, x1, DECK1, "", fs=7.5)
ax.text(DECK1 + 0.3, zq_ - 0.25, "%.1f″ от бака до края щита" % (S["in_deck"] / IN), fontsize=7.5, color="#6d4c41", zorder=9,
        bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
ax.plot([DECK1, DECK1], [0.0, zr("BedDeck")[1]], color="#6d4c41", ls="--", lw=1.0, zorder=8)
if "Toilet_Camco" in B:
    rect_xz(ax, "Toilet_Camco", fc="#bdbdbd", ec="#424242", lw=1.5, zorder=6)
    (ux0, ux1), (uz0, uz1) = xr_("Toilet_Camco"), zr("Toilet_Camco")
    ax.text((ux0 + ux1) / 2, (uz0 + uz1) / 2 + 2.0, "туалет\nCamco\n17″", ha="center", va="center", fontsize=8.5,
            weight="bold", zorder=7)
    hdim(ax, 9.0, ux1, DECK1, "", fs=7.5)
    ax.text(DECK1 + 0.3, 8.75, "%.1f″ от туалета" % (S["toilet"]["in_deck"] / IN), fontsize=7.5, color="#6d4c41",
            zorder=9, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
    if SHOWER is not None:
        ax.annotate("в душ (позже)", xy=(SHOWER - 0.2, 5.0), xytext=(ux1 + 0.6, 5.0), fontsize=7.5, color="#2e7d32",
                    va="center", arrowprops=dict(arrowstyle="->", lw=1.4, color="#2e7d32"), zorder=8)
        ax.plot([SHOWER, SHOWER], [zs, 33.0], color="#1565c0", ls="--", lw=1.0)
        ax.text(SHOWER + 0.2, 33.3, "поддон душа", fontsize=7.5, color="#1565c0")
ax.plot([DECK0, DECK0], [0, zr("BedDeck")[1]], color="#6d4c41", ls="--", lw=1.0, zorder=8)
hdim(ax, z0 + 8.0, DECK0, x0, "", fs=7.5)
ax.text(DECK0 - 0.3, z0 + 9.0, ("%.1f″ под\nштуцеры" if not FR else "%.2f″ до\nдвери") % (S["behind"] / IN),
        fontsize=7.5, color="#6d4c41", ha="right",
        zorder=9, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
ax.set_xlim(XL, XR)
ax.set_ylim(zs - 0.2, 36.0)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань короба D-стойки; вперёд — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на водительский борт изнутри", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── РАЗРЕЗ ПО РЕМНЮ (смотрим вперёд; борт — слева) ─────────
ax = axs
half = G["half"]
wall = [(yd(hw), mz(z)) for hw, z in half if z < FF + 1100.0]
ax.add_patch(Polygon([(-3.0, wall[0][1])] + wall + [(-3.0, wall[-1][1])], color="#cfcfcf"))
ax.add_patch(Rectangle((-3.0, zs), SXR + 3.0, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((-3.0, -0.47), SXR + 3.0, 0.47, color=C_PLY))
for w in SEC["arch"]:
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], color=C_ARCH, zorder=2))
for w in SEC.get("deck", []):
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc=C_DECK, ec="#8d6e63", zorder=2))
for w in SEC.get("mattress", []):
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc="#e3f2fd", ec="#90caf9", zorder=2))
rect_yz(ax, "BedSideRail_pY", color=C_S, zorder=3)
rect_yz(ax, "BedCross_2", fill=False, ec="#263238", ls="-.", lw=0.9, zorder=3)
if PAL:
    rect_yz(ax, RUNNERS[0], fill=False, ec="#5d4037", ls="--", lw=0.9, zorder=3)
    rect_yz(ax, "TankFloor_BasePly", color=C_PLY, ec="#8d6e63", zorder=4)
for n in [k for k in B if k.startswith("TankFloor_Anchor_1")]:
    rect_yz(ax, n, fc="#9e9e9e", ec="#424242", zorder=6)
rect_yz(ax, "TankFloor_Cleat_Aisle", fc=C_WOOD, ec="#5d4037", zorder=5)
rect_yz(ax, SPACERS[0], fill=False, ec="#212121", ls="--", lw=0.9, zorder=5)
for w in SEC["tank"]:
    ax.add_patch(Polygon([(yd(p[1]), mz(p[2])) for p in w], fc=C_T, alpha=0.6, ec="#1f5f8b", lw=1.5, zorder=5))
if "Toilet_Camco" in B:
    rect_yz(ax, "Toilet_Camco", fill=False, ec="#424242", ls="--", lw=1.2, zorder=6)
    ax.text(sum(yr("Toilet_Camco")) / 2, zr("Toilet_Camco")[1] - 1.2, "туалет (впереди)", ha="center", fontsize=7.5,
            color="#424242", zorder=7)
for w in SEC.get("strap", []):
    ax.plot([yd(p[1]) for p in w] + [yd(w[0][1])], [mz(p[2]) for p in w] + [mz(w[0][2])], color=C_STRAP, lw=1.6,
            zorder=6)
(y0, y1), (z0, z1) = yr(TN), zr(TN)
ax.text((y0 + y1) / 2, (z0 + z1) / 2, "бак\n%s × %s″" % (fmt(tw_), fmt(th_)), ha="center", va="center", fontsize=10, weight="bold",
        color="#0d47a1", zorder=7)
if ZBANK is not None:
    ax.plot([-3.0, SXR], [ZBANK, ZBANK], color="#e65100", ls="--", lw=1.0, zorder=8)
    ax.text(SXR - 0.4, ZBANK + 0.5, "полка батарей\n(другой борт) %.2f″" % ZBANK, ha="right", fontsize=7.5, color="#e65100")
hdim(ax, z1 + 1.3, 0.0, y0, "%.1f″" % y0, fs=8, color="#1f5f8b")
hdim(ax, z1 + 3.3, 0.0, y1, "%.1f″" % y1, fs=8, color="#1f5f8b")
if PAL:
    vdim(ax, y1 + 4.0, 0, z0, "поддон %.1f″" % z0, fs=7.5)
vdim(ax, y1 + 2.2, z0, z1, "%s″" % fmt(th_), fs=8)
vdim(ax, y1 + 5.6, z1, zr("BedCross_2")[0], "%.1f″" % (zr("BedCross_2")[0] - z1), fs=8, color="#1565c0")
ax.text(W["protrusion"] / IN / 2, 6.0, "арка", ha="center", color="white", fontsize=9, zorder=3)
ax.text(y0 - 0.2, z0 + 9.5, "проставка\nк арке", ha="right", fontsize=7, zorder=7)

ax.text(0.3, zr("BedSideRail_pY")[1] + 0.4, "рейка кровати", fontsize=7.5, color="#37474f")
ax.text(SXR - 0.4, zr("BedCross_2")[1] + 0.35, "поперечина кровати #2 (за разрезом)", ha="right", fontsize=7,
        color="#263238")
ax.set_xlim(-3.0, SXR)
ax.set_ylim(zs - 0.2, 40.0)
ax.set_aspect("equal")
ax.set_xlabel("от стены (у пола) в салон, дюймы")
ax.set_title("Разрез %s (X=%.1f″), вид вперёд" % ("по ремню" if SEC.get("strap") else "у проставки к арке",
             mx(SEC["x"])), fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

if PAL:
    spec = ("T-4100 (Class A Customs): 39 × 16 × 16.625″ (±0.25″) по карточке реселлера; стоит на 16″. Без давления — нужен «дыхательный» штуцер.\n"
            "Штуцеры — на %s (положение — как у T-3500, уточнить на баке). Поддон %.1f × %.1f″: %d бруска 2×4 плашмя + фанера 1/2″,\n"
            "бруски 2×2 по периметру (к борту — проставки к арке), болты M8 через бруски в пол; 2 ремня 1″ через поддон.\n"
            "Багажник между рейкой батарей и поддоном бака — %.1f″ (с T-3500 на полке было 47.9″ между рейками + ниша под полкой)." % (
                "заднем торце (залив — от задних дверей)" if not FR else "переднем торце",
                (S["base"][1] - S["base"][0]) / IN, (S["base"][3] - S["base"][2]) / IN, S["n_runner"], (S["trunk"] or 0) / IN))
    sub = "без этажерки: поддон на болтах в пол"
else:
    spec = ("%s (Class A Customs): %s (±0.25″) по картинке продавца; без давления — нужен «дыхательный» штуцер. Прямо на полу (полосы-прижимы\n"
            "под баком сняты) на резиновом коврике 1/8″; бруски 2×2 в пол спереди и со стороны прохода, у борта — проставка к арке и брусок за аркой;\n"
            "2 ремня 1″ поверх бака к 4 анкерам в железном полу (у борта — за аркой). Сзади — закрытая дверь в 1/4″. Штуцеры — на %s;\n"
            "залив сзади — доп. штуцер Uniseal 1.5″ сверху у заднего края (до поперечин кровати %.1f″). Багажник до бака — %.1f″; с фитингами до края щита %.1f″." % (
                TN.split("_")[1].replace("T", "T-"), DIMS, "переднем торце (к кабине)" if FR else "заднем торце",
                (zr("BedCross_2")[0] - z1), (S["trunk"] or 0) / IN, S["in_deck_fit"] / IN))
    sub = "прямо на пол (коврик), вплотную к задней двери" + (", перед ним — туалет" if "Toilet_Camco" in B else "")
fig.text(0.012, 0.010, spec, fontsize=9, va="bottom", bbox=dict(fc="#e3f2fd", ec="#90caf9", alpha=0.95))
fig.suptitle("Бак для воды %s (%s) на полу рядом с водительской аркой — вариант 2026-11-07\n"
             "%s; верх бака %.2f″ — вровень с полкой батарей (%+.0f мм); целиком под щитом (до края %.1f″)" % (
                 TN.split("_")[1].replace("T", "T-"), GAL, sub, mz(B[TN][5]), S["level"] or 0, S["in_deck"] / IN),
             fontsize=12)
fig.subplots_adjust(left=0.05, right=0.99, top=0.93, bottom=0.10)
save(fig, "water_tank_%s_drawing.png" % S["name"])
