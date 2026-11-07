"""Чертёж бака для воды TORVA 33 gal у водительской арки — из сечений модели (docs/drawing_data.json).
Дюймы. Вид на борт: x — вдоль борта, 0 = задняя грань задней стойки кровати, + вперёд;
поперечный разрез: y — от стены в салон; z — от чистового пола."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, load, save

d = load()
r = dict(d["tank"])
r["boxes"] = d["boxes"]
W, R, T, BED, DP = d["WHEEL_ARCH"], d["BATTERY_RACK"], d["WATER_TANK"], d["BED"], d["DPILLAR"]
XDP = d["geo"]["x_dp"]                         # передняя грань короба D-стойки у края фанеры
FF = d["geo"]["floor_top"]
YW = d["geo"]["arch_ywall"]                    # стена у пола
X0 = d["boxes"]["BedPost_pY_rear"][0]          # задняя грань задней стойки кровати
mx = lambda X: (X - X0) / IN
mz = lambda Z: (Z - FF) / IN
my = lambda Y: (YW - Y) / IN                  # от стены
B = r["boxes"]
tb = r["tank_bb"]
SO = (YW - r["y_back"]) / IN
import re
_m = re.search(r"→ подставка (\d+) мм \(([\d.]+)″\): ([^\n]+)", d.get("summary", ""))
RISER_TXT = _m.group(3) if _m else "доски на ребро"
C_T, C_A, C_W, C_S, C_D = "#4a90c2", "#9e9e9e", "#a0703c", "#607d8b", "#78909c"

fig = plt.figure(figsize=(16, 15.5), dpi=130)
gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], width_ratios=[1.75, 1])
axe = fig.add_subplot(gs[0, :])
axp = fig.add_subplot(gs[1, 0])
axs = fig.add_subplot(gs[1, 1])


def poly(ax, wires, fx, fy, **kw):
    for w in wires:
        ax.add_patch(Polygon([(fx(p), fy(p)) for p in w], closed=True, **kw))


def box_xz(ax, b, **kw):
    ax.add_patch(Rectangle((mx(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, **kw))


def box_xy(ax, b, **kw):
    ax.add_patch(Rectangle((mx(b[0]), my(b[3])), (b[1] - b[0]) / IN, (b[3] - b[2]) / IN, **kw))


def box_yz(ax, b, **kw):
    ax.add_patch(Rectangle((my(b[3]), mz(b[4])), (b[3] - b[2]) / IN, (b[5] - b[4]) / IN, **kw))


def vdim(ax, x, z0, z1, txt, side=1, color="k", fs=8.5):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=7)
    ax.text(x + 0.25 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right",
            fontsize=fs, color=color, zorder=7)


def hdim(ax, z, x0, x1, txt, color="k", fs=8.5, dz=0.35):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=7)
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs, color=color, zorder=7)


lift = (tb[4] - FF)
top = tb[5] - FF
xr_in, xf_in = mx(tb[0]), mx(tb[1])
cl = r["closest"]

# ───────── ВИД НА ВОДИТЕЛЬСКИЙ БОРТ ИЗ САЛОНА ─────────
ax = axe
ax.add_patch(Rectangle((-14, -1.9), 64, 1.9, color="#e8d9b5", zorder=5))
ax.text(-13.6, -0.75, "пол (фанера)", fontsize=7.5, zorder=6)
poly(ax, r["elev_arch_wall"], lambda p: mx(p[0]), lambda p: mz(p[2]), fill=False, ec=C_A, ls="--", lw=1.0)
poly(ax, r["elev_arch"], lambda p: mx(p[0]), lambda p: mz(p[2]), fc="#cfcfcf", ec="#757575", lw=1.0)
ax.text(mx(1000), mz(300), "арка\n(сечение у задней\nграни бака)", ha="center", fontsize=8.5, color="#424242")
poly(ax, r["elev_tank"], lambda p: mx(p[0]), lambda p: mz(p[2]), fc=C_T, alpha=0.30, ec=C_T, lw=1.6)
ax.text(mx(1250), mz(560), "бак TORVA 33 gal (125 л)", ha="center", fontsize=10, color="#1f5f8b", weight="bold")
for w in r["elev_riser"]:
    ax.add_patch(Polygon([(mx(p[0]), mz(p[2])) for p in w], closed=True, fc=C_W, alpha=0.85, ec="#5d4037"))
ax.text(mx(1000), mz(FF + 60), "подставка: " + RISER_TXT.split(";")[0], ha="center", fontsize=8, color="white")
# стойки кровати у стены (за баком) — пунктир; P3/P4 (перед баком) — сплошные
for n in ("BedPost_pY_rear", "BedPost_pY_front"):
    box_xz(ax, B[n], fill=False, ec=C_S, ls="--", lw=1.1)
box_xz(ax, B["TankSpacer_RearBedPost"], fc="#212121", alpha=0.5)
for n, lab in (("TankPost_P3", "P3"), ("TankPost_P4", "P4")):
    box_xz(ax, B[n], fc=C_S, alpha=0.85, ec="#37474f")
    ax.text(mx((B[n][0] + B[n][1]) / 2), mz(B[n][5]) + 0.35, lab, ha="center", fontsize=9, weight="bold")
for n in ("BedCross_1", "BedCross_RackFront", "BedCross_2", "BedCross_Rack_fwd", "BedCross_3"):
    box_xz(ax, B[n], fc="#263238")
box_xz(ax, B["BedSideRail_pY"], fill=False, ec="#263238", ls=":", lw=1)
ax.text(mx(B["BedCross_2"][0]), mz(B["BedCross_2"][5]) + 0.3, "поперечины кровати", ha="center", fontsize=7.5)
# D-стойка в плоскости задней грани бака: короб у пола + грань стойки выше него (фото сверху 2026-11-06)
dd = YW - r["y_back"]
xdp = XDP - DP["box_slant"] * (dd - DP["photo_wall"]) / DP["box_depth"]          # грань короба
xbody = XDP - DP["body_slant"] * dd / DP["body_depth"]                             # грань стойки выше
ax.add_patch(Rectangle((mx(XDP - DP["box_len"]), 0), (xdp - (XDP - DP["box_len"])) / IN, DP["box_h"] / IN,
                       fc=C_D, alpha=0.55, ec="#455a64", hatch="//"))
ax.add_patch(Rectangle((mx(xbody) - 1.6, DP["box_h"] / IN), 1.6, 30 - DP["box_h"] / IN, color=C_D, alpha=0.55))
ax.text(mx(xbody) - 0.8, 17, "D-стойка (в %.1f″ от стены)" % SO, rotation=90, ha="center", va="center",
        fontsize=8, color="white")
ax.text(mx(XDP - DP["box_len"]) + 0.2, DP["box_h"] / IN + 0.3, "короб D-стойки\n~%.0f″ (оценка)" % (DP["box_h"] / IN),
        fontsize=7, color="#37474f")
ax.plot([mx(cl[0][0])], [mz(cl[0][2])], "o", ms=7, mfc="none", mec="#d32f2f", mew=1.6)
ax.annotate("самое узкое место:\n%.0f мм (плечо арки ↔ скат тоннеля)" % cl[2],
            xy=(mx(cl[0][0]), mz(cl[0][2])), xytext=(mx(cl[0][0]) - 9, mz(cl[0][2]) + 3.6),
            fontsize=8.5, color="#d32f2f", arrowprops=dict(arrowstyle="->", color="#d32f2f"))
vdim(ax, xf_in + 0.8, 0, lift / IN, "подъём %.1f″ (%.0f)" % (lift / IN, lift))
vdim(ax, xf_in + 0.8, lift / IN, top / IN, "бак 20″")
vdim(ax, xf_in + 4.2, top / IN, mz(B["BedCross_3"][4]), "%.1f″ (%.0f) до поперечин" % (
    (B["BedCross_3"][4] - tb[5]) / IN, B["BedCross_3"][4] - tb[5]), fs=8)
vdim(ax, mx(W["center_x"]) - 0.4, 0, W["height"] / IN, "арка %.0f″" % (W["height"] / IN), side=-1, color="#616161")
hdim(ax, -2.2, xr_in, xf_in, "48″ (1220)")
if tb[0] < xdp:
    ax.annotate("торец бака нависает над коробом\nна %.0f мм (дно выше короба)" % (xdp - tb[0]),
                xy=(xr_in, lift / IN + 0.3), xytext=(xr_in - 10.5, lift / IN + 4.5), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
else:
    hdim(ax, -3.6, mx(xdp), xr_in, "%.0f мм" % (tb[0] - xdp), fs=8, dz=-0.9)
ax.set_xlim(-14, 50)
ax.set_ylim(-4.8, 31)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы (0 = задняя грань задней стойки кровати; вперёд — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на водительский борт из салона (сечение в плоскости задней грани бака, в %.1f″ от стены; пунктир — арка у стены)" % SO,
             loc="left", fontsize=11)

# ───────── ВИД СВЕРХУ ─────────
ax = axp
ax.add_patch(Rectangle((-14, -1.2), 64, 1.2, color="#cfcfcf"))
ax.text(-13.5, -0.85, "стена (у пола)", fontsize=7.5)
poly(ax, r["plan_arch0"], lambda p: mx(p[0]), lambda p: my(p[1]), fill=False, ec=C_A, ls="--", lw=1.0)
poly(ax, r["plan_arch"], lambda p: mx(p[0]), lambda p: my(p[1]), fc="#cfcfcf", ec="#757575")
poly(ax, r["plan_tank"], lambda p: mx(p[0]), lambda p: my(p[1]), fc=C_T, alpha=0.28, ec=C_T, lw=1.5)
for w in d["corners"]["pY"]["dpillar"]:
    ax.add_patch(Polygon([(mx(x), my(y)) for x, y in w], closed=True, color=C_D, alpha=0.8))
ax.text(mx(XDP) - 0.3, my(YW - DP["photo_wall"] - DP["box_depth"]) + 1.4, "короб\nD-стойки", fontsize=8, ha="right")
for n in ("BedPost_pY_rear", "BedPost_pY_front"):
    box_xy(ax, B[n], fc=C_S, ec="#37474f")
box_xy(ax, B["TankSpacer_RearBedPost"], fc="#212121", alpha=0.6)
ax.text(mx(B["TankSpacer_RearBedPost"][1]) + 0.3, my(905), "проставка %.0f мм" % (
    B["TankSpacer_RearBedPost"][3] - B["TankSpacer_RearBedPost"][2]), fontsize=7.5)
for n, lab in (("TankPost_P3", "P3"), ("TankPost_P4", "P4")):
    box_xy(ax, B[n], fc=C_S, ec="#37474f")
    box_xy(ax, B[n.replace("Post_", "PostPlate_")], fill=False, ec="#90a4ae", ls="--", lw=0.8)
    ax.text(mx((B[n][0] + B[n][1]) / 2), my(B[n][2]) + 0.9, lab, ha="center", fontsize=9, weight="bold")
ax.text(mx(1000), my(700), "арка", ha="center", fontsize=9, color="#424242")
ax.text(mx(1250), my(600), "бак", ha="center", fontsize=10, color="#1f5f8b", weight="bold")
yb_in = my(r["y_back"])
ycab_in = my(tb[2])
vdim(ax, xf_in + 1.0, 0, yb_in, "%.1f″ (%.0f)" % (yb_in, YW - r["y_back"]), fs=8)
vdim(ax, xf_in + 1.0, yb_in, ycab_in, "12.5″")
vdim(ax, xf_in + 6.0, 0, ycab_in, "%.1f″ (%.0f) от стены" % (ycab_in, YW - tb[2]), fs=8)
vdim(ax, mx(1000) + 6.5, 0, W["protrusion"] / IN, "арка %.1f″" % (W["protrusion"] / IN), color="#616161", fs=8)
ax.set_xlim(-14, 56)
ax.set_ylim(22, -2.0)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы")
ax.set_ylabel("от стены в салон, дюймы")
ax.set_title("Вид сверху (на высоте %.0f″ над полом; пунктир — арка у пола)" % ((r["plan_z"] - FF) / IN),
             loc="left", fontsize=11)

# ───────── РАЗРЕЗ ПОПЕРЁК ПО ЦЕНТРУ КОЛЕСА ─────────
ax = axs
sec = r["sec"]["1000.0"]
ax.add_patch(Rectangle((-1.2, -1.0), 1.2, 30, color="#cfcfcf"))
ax.add_patch(Rectangle((0, -1.9), 24, 1.9, color="#e8d9b5", zorder=5))
poly(ax, sec["arch"], lambda p: my(p[1]), lambda p: mz(p[2]), fc="#cfcfcf", ec="#757575")
poly(ax, sec["tank"], lambda p: my(p[1]), lambda p: mz(p[2]), fc=C_T, alpha=0.30, ec=C_T, lw=1.6)
for w in sec["riser"]:
    ax.add_patch(Polygon([(my(p[1]), mz(p[2])) for p in w], closed=True, fc=C_W, alpha=0.85, ec="#5d4037"))
box_yz(ax, B["BedSideRail_pY"], fc="#263238")
XC = B["BedCross_2"]
ax.add_patch(Rectangle((my(XC[3]), mz(XC[4])), 24 - my(XC[3]), (XC[5] - XC[4]) / IN, fill=False, ec="#263238", ls=":"))
ax.text(12, mz(XC[5]) + 0.3, "поперечины кровати (над баком)", fontsize=7.5, ha="center")
box_yz(ax, B["TankPost_P4"], fill=False, ec=C_S, ls="--", lw=1.1)
ax.text(my(B["TankPost_P4"][2]) + 0.2, 20, "P3/P4\n(за разрезом)", fontsize=7.5)
box_yz(ax, B["BedPost_pY_rear"], fill=False, ec=C_S, ls="--", lw=1.0)
ax.text(my(B["BedPost_pY_rear"][2]) - 0.3, 33, "стойка\nкровати", fontsize=7, ha="right")
ax.text(5.5, mz(250), "арка", ha="center", fontsize=9, color="#424242")
ax.text(13, mz(560), "бак", ha="center", fontsize=10, color="#1f5f8b", weight="bold")
hdim(ax, mz(FF) - 1.9, 0, W["protrusion"] / IN, "%.1f″" % (W["protrusion"] / IN), color="#616161", fs=8, dz=-0.75)
hdim(ax, mz(150), yb_in, yb_in + 235 / IN, "тоннель 9.25″", fs=8)
vdim(ax, 22.5, lift / IN, (lift + 325) / IN, "тоннель\n12.8″", side=-1, fs=8)
ax.set_xlim(-1.5, 24)
ax.set_ylim(-3.2, 36)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от стены в салон, дюймы")
ax.set_ylabel("от пола, дюймы")
ax.set_title("Разрез поперёк по центру колеса\n(вид спереди назад, стена слева)", loc="left", fontsize=11)

fig.suptitle("Бак TORVA 33 gal у водительской арки — утверждено 2026-11-06: подставка %.1f″, в %.1f″ от стены, "
             "P3/P4 до поперечин кровати (кровать поднята на %.0f″)\n"
             "арка у пола и D-стойка — по фото сверху 2026-11-06 (±0.2″); ⚠ верх арки и высота короба D-стойки — оценка" % (
                 r["lift"] / IN, SO, BED.get("rail_raise", 0.0) / IN), fontsize=12.5)
fig.tight_layout()
save(fig, "water_tank_drawing.png")
