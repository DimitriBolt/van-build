"""Чертёж: душ (поддон-сектор 32″, задняя стенка — только сверху, на ней газовый нагреватель) + кухня в 2 секции
(мойка | шкафчик + холодильник, торец к душу вогнутый по шторке) + локер пропана под кроватью.
Дюймы. Вид на борт и план: x — вдоль борта, 0 = передний край настила кровати, + к кабине;
план: y — от стены в салон; разрезы: y — от стены, z — от чистового пола. Данные — из модели."""
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

from _common import IN, load, save

d = load()
B, G, K = d["boxes"], d["geo"], d["SHOWER_KITCHEN"]
GL = d["galley"]
FF = G["floor_top"]
half = G["half"]
X0 = max(B["BedDeck"][1], B["BedSideRail_pY"][1])    # перед рамы кровати (щит кончается раньше — 2026-11-07)
mx = lambda X: (X - X0) / IN
mz = lambda Z: (Z - FF) / IN


def wall_y(z):                                        # полуширина борта (обшивка) на высоте z
    pts = sorted(half, key=lambda p: p[1])
    if z <= pts[0][1]:
        return pts[0][0]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0) if z1 > z0 else y0
    return pts[-1][0]


YW900 = wall_y(900.0)
my = lambda Y: (YW900 - Y) / IN                       # от стены (на высоте столешницы), план


def bx(name):
    return B[name]


def has(name):
    return name in B


def r_xz(ax, name, **kw):
    if not has(name):
        return
    b = bx(name)
    ax.add_patch(Rectangle((mx(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, **kw))


def r_xy(ax, name, **kw):
    if not has(name):
        return
    b = bx(name)
    ax.add_patch(Rectangle((mx(b[0]), my(b[3])), (b[1] - b[0]) / IN, (b[3] - b[2]) / IN, **kw))


def vdim(ax, x, z0, z1, txt, side=1, fs=8.5, color="k"):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=8)
    ax.text(x + 0.3 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right", fontsize=fs,
            color=color, zorder=8)


def hdim(ax, z, x0, x1, txt, fs=8.5, dz=0.5, color="k"):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=8)
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs, color=color, zorder=8)


C_WALL, C_PAN, C_CAB, C_TOP, C_FR, C_ST = "#e3e6ea", "#ffffff", "#d9a066", "#9c6b3c", "#3f6b8c", "#9aa4ad"
C_GAS, C_LOCK, C_ALARM = "#f9a825", "#f3d98b", "#e53935"
SEAT = mx(3190.0)
sx0, sx1 = bx("Shower_WallRear")[0], bx("Shower_Pan")[1]
PB = bx("Shower_Pan")
XP0, YPB, RP = PB[0], PB[3], PB[1] - PB[0]                   # угол сектора (у задней стенки и борта), радиус
RC = RP - K.get("curtain_in", 50.0)                          # шторка = вогнутый торец кухни
TOILET = has("Toilet_Camco")
GAS = has("Shower_GasHeater")
PROP = has("Propane_Locker")
kx0, kx1 = bx("Kitchen_Countertop")[0], bx("Kitchen_Carcass")[1]
z_pan = bx("Shower_Pan")[5]
z_ceil = bx("Shower_Ceiling")[4]
z_ct = bx("Kitchen_Countertop")[5]
z_up = bx("Kitchen_UpperCabinet")[4]
crown = half[-1][1]
gas_pts = GL.get("gas_pts") or []
x_div = bx("Kitchen_DoorSink")[1] if has("Kitchen_DoorSink") else None

fig = plt.figure(figsize=(19, 30), dpi=110)
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 0.95])
axe = fig.add_subplot(gs[0, 0])
axp = fig.add_subplot(gs[0, 1])
axs = fig.add_subplot(gs[1, 0])
axk = fig.add_subplot(gs[1, 1])
axl = fig.add_subplot(gs[2, 0])
axf = fig.add_subplot(gs[2, 1])

# ───────── ВИД НА ВОДИТЕЛЬСКИЙ БОРТ ИЗ ПРОХОДА ─────────
ax = axe
XL0 = -24
ax.add_patch(Rectangle((XL0, -1.8), 92, 1.8, color="#e8d9b5", zorder=1))
ax.text(XL0 + 0.4, -1.2, "пол (фанера)", fontsize=8, zorder=2)
ax.plot([XL0, 66], [mz(crown)] * 2, color="#757575", lw=1.2)
ax.text(XL0 + 0.4, mz(crown) + 0.4, "крыша (железо, по центру)", fontsize=8, color="#616161")
ax.add_patch(Rectangle((SEAT, -1.8), 4, mz(crown) + 1.8, fc="#eeeeee", ec="#bdbdbd", hatch="//"))
ax.text(SEAT + 2, 40, "кабина: спинка\nводителя", ha="center", fontsize=8.5, rotation=90, va="center")
# кровать (край)
r_xz(ax, "BedDeck", fc="#d7ccc8", ec="#8d6e63")
r_xz(ax, "BedMattress", fc="#9fb4e0", alpha=0.45, ec="#5c6bc0")
r_xz(ax, "BedSideRail_pY", fc="#90a4ae")
r_xz(ax, "BedPost_pY_front", fc="#90a4ae", ec="#607d8b")
for n in sorted(B):
    if n.startswith("BedCross_"):
        r_xz(ax, n, fc="#90a4ae", ec="#607d8b")
ax.text(-12, mz(bx("BedMattress")[5]) + 0.6, "кровать (край)", ha="center", fontsize=9)
TANK = next((n for n in sorted(B) if n.startswith("WaterTank_")), None)
if TANK:
    r_xz(ax, TANK, fc="#4a90c2", alpha=0.25, ec="#4a90c2")
    ax.text(XL0 + 0.4, mz(bx(TANK)[5]) + 0.6, "← бак %s" % TANK.split("_")[1].replace("T", "T-"), fontsize=7.5,
            color="#1f5f8b")
r_xz(ax, "Water_Pump12V", fc="#3949ab", alpha=0.7)
if TOILET:
    r_xz(ax, "Toilet_Camco", fc="#bdbdbd", ec="#424242", lw=1.2)
    ax.text(mx(bx("Toilet_Camco")[0]) + 2.1, 8.5, "туалет (за локером)", ha="center", va="center", fontsize=7.5,
            rotation=90, zorder=7)
    ax.annotate("", xy=(mx(XP0) + 4.0, 6.0), xytext=(mx(bx("Toilet_Camco")[1]) + 0.3, 6.0),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#2e7d32"))
if PROP:                                                     # локер — ближе к зрителю, чем туалет
    r_xz(ax, "Propane_Locker", fc=C_LOCK, alpha=0.55, ec="#bf8f00", lw=1.3, zorder=4)
    cb = bx("Propane_Cylinder")
    ax.add_patch(Rectangle((mx(cb[0]), mz(cb[4])), (cb[1] - cb[0]) / IN, (cb[5] - cb[4]) / IN, fill=False,
                           ec="#757575", ls="--", lw=1.1, zorder=5))
    ax.text(mx((cb[0] + cb[1]) / 2), mz((cb[4] + cb[5]) / 2), "локер\nпропана\n30 lb", ha="center", va="center",
            fontsize=8, zorder=6)
    r_xz(ax, "Safety_LPCO", fc=C_ALARM, zorder=6)
    lb = bx("Propane_Locker")
    zc = min(bx(n)[4] for n in B if n.startswith("BedCross_"))
    vdim(ax, mx(lb[0]) + 2.0, mz(lb[5]), mz(zc), "", fs=7)
    ax.text(mx(lb[0]) + 2.3, (mz(lb[5]) + mz(zc)) / 2, "%.1f″" % ((zc - lb[5]) / IN), fontsize=7, va="center")
if gas_pts:
    ax.plot([mx(p[0]) for p in gas_pts], [mz(p[2]) for p in gas_pts], color=C_GAS, lw=2.2, zorder=7)
    ax.text(mx(gas_pts[2][0]) - 0.3, mz(gas_pts[2][2]) + 0.5, "газ", fontsize=8, color="#e65100", ha="right", zorder=7)
r_xz(ax, "Safety_CO_Bed", fc=C_ALARM, zorder=6)
if has("Safety_CO_Bed"):
    ax.text(mx(bx("Safety_CO_Bed")[0]) - 0.3, mz(bx("Safety_CO_Bed")[5]) + 0.4, "датчик CO", ha="right", fontsize=7.5,
            color=C_ALARM)
# душ
for n in ("Shower_WallRear", "Shower_DripLedge"):
    r_xz(ax, n, fc=C_WALL, ec="#78909c")
r_xz(ax, "Shower_CurtainLower", fc="#4fc3f7", alpha=0.35, ec="#0277bd", ls="--")
r_xz(ax, "Shower_WallBack", fc="#f5f7f9", ec="none", zorder=0)
r_xz(ax, "Shower_Ceiling", fc=C_WALL, ec="#78909c")
r_xz(ax, "Shower_Pan", fc=C_PAN, ec="#455a64", lw=1.2)
r_xz(ax, "Shower_CurtainRod", fc=C_ST)
r_xz(ax, "Shower_Head", fc=C_ST, ec="#455a64")
r_xz(ax, "Shower_ExhaustFan", fc="#263238")
if GAS:
    r_xz(ax, "Shower_Flue", fc="#b0bec5", ec="#546e7a", zorder=3)
    r_xz(ax, "Shower_FlueCap", fc="#424242", zorder=3)
    r_xz(ax, "Shower_FlueThimble", fc="#424242", zorder=3)
    r_xz(ax, "Shower_GasHeater", fc="#fafafa", ec="#c62828", lw=1.5, zorder=4)
    hb = bx("Shower_GasHeater")
    ax.text(mx((hb[0] + hb[1]) / 2), mz((hb[4] + hb[5]) / 2), "газовый нагреватель Camplux", fontsize=8,
            color="#c62828", rotation=90, ha="center", va="center", zorder=5)
    vdim(ax, mx(hb[1]) + 0.6, 0, mz(hb[4]), "%.1f″" % mz(hb[4]), fs=7.5, color="#c62828")
    vdim(ax, mx(hb[1]) + 0.6, mz(hb[4]), mz(hb[5]), "17.3″", fs=7.5, color="#c62828")
    fb = bx("Shower_Flue")
    ax.text(mx(fb[1]) + 0.4, mz(bx("Shower_FlueCap")[4]) - 0.3, "дымоход ⌀3″ — вертикально через крышу", fontsize=7.5,
            color="#546e7a")
ax.text(mx((XP0 + sx1) / 2) + 2, mz(1100), "ДУШ\nподдон-сектор 32″\n(шторка снята)", ha="center", fontsize=11,
        weight="bold", color="#37474f")
ax.text(mx(bx("Shower_Head")[1]) + 0.3, mz(bx("Shower_Head")[5]), "лейка", fontsize=8)
ax.text(mx(bx("Shower_ExhaustFan")[1]) + 0.3, mz(bx("Shower_ExhaustFan")[4]) - 1.2, "вытяжка 12V", fontsize=8)
# кухня
r_xz(ax, "Kitchen_Plinth", fc="#5d4037")
r_xz(ax, "Kitchen_Carcass", fc=C_CAB, ec="#8d6e63", alpha=0.35)
r_xz(ax, "Kitchen_Fridge", fc=C_FR, ec="#263238")
r_xz(ax, "Kitchen_FridgeSlide", fc=C_ST)
fr = bx("Kitchen_Fridge")
ax.text(mx((fr[0] + fr[1]) / 2), mz((fr[4] + fr[5]) / 2), "%s\n23 qt на салазках" % K.get("fridge_title", "холодильник")
        .replace(" 23 qt", ""), ha="center", va="center", fontsize=8, color="white")
r_xz(ax, "Kitchen_DoorSink", fill=False, ec="#8d6e63", ls="--")
r_xz(ax, "Kitchen_DoorUpper", fill=False, ec="#8d6e63", ls="--")
if x_div:
    ax.plot([mx(x_div)] * 2, [mz(bx("Kitchen_Plinth")[5]), mz(z_ct)], color="#5d4037", lw=1.6)
    ds = bx("Kitchen_DoorSink")
    ax.text(mx((ds[0] + ds[1]) / 2) + 2.0, mz(ds[4]) + 6, "секция 1:\nмойка\n(под ней —\nчашки, чай,\nсифон)",
            ha="center", fontsize=8)
    du = bx("Kitchen_DoorUpper")
    ax.text(mx((du[0] + du[1]) / 2), mz((du[4] + du[5]) / 2), "секция 2:\nшкафчик", ha="center", va="center", fontsize=8)
sk = bx("Kitchen_Sink")
ax.add_patch(Rectangle((mx(sk[0]), mz(sk[4])), (sk[1] - sk[0]) / IN, (sk[5] - sk[4]) / IN, fill=False, ec="#546e7a",
                       ls=":", lw=1.2))
r_xz(ax, "Kitchen_Countertop", fc=C_TOP)
r_xz(ax, "Kitchen_Faucet", fc=C_ST)
r_xz(ax, "Kitchen_Kettle", fc="#cfd8dc", ec="#607d8b")
r_xz(ax, "Kitchen_Outlet", fc="#ffffff", ec="#424242")
r_xz(ax, "Kitchen_UpperCabinet", fc=C_CAB, ec="#8d6e63")
ax.text(mx((bx("Kitchen_UpperCabinet")[0] + kx1) / 2), mz(bx("Kitchen_UpperCabinet")[4]) + 5, "верхний шкафчик",
        ha="center", fontsize=9)
ax.text(mx((sk[0] + sk[1]) / 2), mz(sk[4]) - 1.3, "мойка 12×12″", ha="center", fontsize=7.5)
ax.text(mx((bx("Kitchen_Kettle")[0] + bx("Kitchen_Kettle")[1]) / 2), mz(bx("Kitchen_Kettle")[5]) + 0.5, "чайник",
        ha="center", fontsize=8)
# сдвижная дверь напротив
slx = (bx("Opening_SlidingDoor")[0], bx("Opening_SlidingDoor")[1])
ax.plot([mx(slx[0]), mx(slx[1])], [-3.0, -3.0], color="#2e7d32", lw=4, solid_capstyle="butt")
ax.text(mx(slx[0]), -4.3, "сдвижная дверь — на противоположном борту", fontsize=8, color="#2e7d32")
# размеры
hdim(ax, mz(1990), mx(sx0), mx(sx1), "душ %.1f″" % ((sx1 - sx0) / IN))
hdim(ax, mz(PB[5]) + 1.2, mx(sx0), mx(XP0), "%.1f″" % ((XP0 - sx0) / IN), fs=7.5)
hdim(ax, mz(2060), mx(kx0), mx(kx1), "кухня %.1f″ (по передней кромке)" % ((kx1 - kx0) / IN))
hdim(ax, mz(2130), 0, SEAT, "от кровати до спинки водителя %.1f″" % SEAT)
vdim(ax, mx(XP0) + 9.0, mz(z_pan), mz(z_ceil), "%.1f″\nот поддона\nдо потолка" % ((z_ceil - z_pan) / IN))
vdim(ax, mx(kx1) + 0.6, 0, mz(z_ct), "36″", fs=8.5)
vdim(ax, mx(kx1) + 0.6, mz(z_ct), mz(z_up), "%.1f″" % ((z_up - z_ct) / IN), fs=8.5)
ax.set_xlim(XL0, 66)
ax.set_ylim(-5.5, 88)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы (0 = передний край настила кровати; к кабине — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на водительский борт из прохода (шторки и дверцы сняты)", loc="left", fontsize=12)

# ───────── ПЛАН ─────────
ax = axp
ax.add_patch(Rectangle((XL0, -1.5), 92, 1.5, color="#cfcfcf"))
ax.text(XL0 + 0.5, -1.0, "водительская стена", fontsize=8)
yop = my(-wall_y(900.0))                                   # противоположная стена
ax.add_patch(Rectangle((XL0, yop), 92, 1.5, color="#cfcfcf"))
ax.add_patch(Rectangle((mx(slx[0]), yop), mx(slx[1]) - mx(slx[0]), 1.5, color="#2e7d32"))
ax.text(mx((slx[0] + slx[1]) / 2), yop + 2.6, "сдвижная дверь (пассажирский борт)", ha="center", fontsize=8.5,
        color="#2e7d32")
ax.add_patch(Rectangle((SEAT, -1.5), 4, yop + 3, fc="#eeeeee", ec="#bdbdbd", hatch="//"))
ax.text(SEAT + 2, yop / 2, "сиденья", rotation=90, ha="center", va="center", fontsize=8.5)
r_xy(ax, "BedDeck", fc="#d7ccc8", ec="#8d6e63", alpha=0.35)
ax.text(-12, yop - 6, "кровать (щит над всем этим)", ha="center", fontsize=9)
r_xy(ax, "BedPost_pY_front", fc="#607d8b")
arc = lambda r, n=60: [(mx(XP0 + r * math.cos(t)), my(YPB - r * math.sin(t))) for t in [math.pi / 2 * i / n for i in range(n + 1)]]
ax.add_patch(Polygon([(mx(XP0), my(YPB))] + arc(RP), fc=C_PAN, ec="#455a64", lw=1.2, zorder=2))
ax.add_patch(Polygon([(mx(XP0), my(YPB))] + arc(RP - 64.0), fill=False, ec="#90a4ae", lw=0.8, ls=":", zorder=2))
dr = bx("Shower_Drain")
ax.add_patch(Circle((mx((dr[0] + dr[1]) / 2), my((dr[2] + dr[3]) / 2)), (dr[1] - dr[0]) / 2 / IN, fc="#90a4ae",
                    ec="#455a64", zorder=3))
r_xy(ax, "Shower_WallRear", fc="#b0bec5", zorder=3)
r_xy(ax, "Shower_DripLedge", fc="#eceff1", ec="#78909c", hatch="//", zorder=3)
ac = arc(RC)
ax.plot([mx(bx("Shower_WallRear")[1])] + [p[0] for p in ac], [ac[0][1]] + [p[1] for p in ac], color="#0288d1", lw=2.0,
        zorder=6)
r_xy(ax, "Shower_CurtainLower", fc="#4fc3f7", zorder=4)
ax.text(mx(XP0 + RP * 0.45), my(YPB - RP * 0.52), "ДУШ\nсектор 32″", ha="center", fontsize=10, weight="bold",
        color="#37474f", zorder=5)
ax.text(mx(XP0 + RC * 0.30) - 2.5, my(YPB - RC * 0.95) + 2.2, "вход\n%.1f″" % (
    math.hypot(mx(XP0 + math.sqrt(max((RC + 0.5) ** 2 - (YPB - bx("Kitchen_Countertop")[2]) ** 2, 0.0))) -
               mx(bx("Shower_WallRear")[1]), my(YPB - RC) - my(bx("Kitchen_Countertop")[2]))),
        fontsize=8.5, color="#0277bd", zorder=6, ha="center")
if TOILET:
    r_xy(ax, "Toilet_Camco", fc="#bdbdbd", ec="#424242", zorder=3)
    tb = bx("Toilet_Camco")
    ax.text(mx((tb[0] + tb[1]) / 2), my((tb[2] + tb[3]) / 2), "туалет", ha="center", va="center", fontsize=8, zorder=5)
    ax.annotate("", xy=(mx(XP0) + 6.0, my((tb[2] + tb[3]) / 2)), xytext=(mx(tb[1]) + 0.3, my((tb[2] + tb[3]) / 2)),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#2e7d32"), zorder=6)
r_xy(ax, "Water_Pump12V", fc="#3949ab", alpha=0.7, zorder=3)
if has("Water_Pump12V"):
    pb_ = bx("Water_Pump12V")
    ax.text(mx((pb_[0] + pb_[1]) / 2), my((pb_[2] + pb_[3]) / 2), "насос", fontsize=6.5, ha="center", va="center",
            rotation=90, color="white", zorder=6)
if PROP:
    r_xy(ax, "Propane_Locker", fc=C_LOCK, ec="#bf8f00", lw=1.3, zorder=3)
    r_xy(ax, "Propane_LockerDoor", fc="#ffb74d", ec="#e65100", zorder=4)
    cb = bx("Propane_Cylinder")
    ax.add_patch(Circle((mx((cb[0] + cb[1]) / 2), my((cb[2] + cb[3]) / 2)), (cb[1] - cb[0]) / 2 / IN, fill=False,
                        ec="#616161", lw=1.2, zorder=5))
    ax.text(mx((cb[0] + cb[1]) / 2), my((cb[2] + cb[3]) / 2), "пропан\n30 lb", ha="center", va="center", fontsize=8,
            zorder=6)
    vb = bx("Propane_Vent")
    ax.add_patch(Circle((mx((vb[0] + vb[1]) / 2), my((vb[2] + vb[3]) / 2)), 0.6, fc="#212121", zorder=6))
    lb = bx("Propane_Locker")
    ax.text(mx(lb[0]) + 0.3, my(lb[2]) + 1.3, "дверца → к проходу", fontsize=7, color="#e65100", zorder=6)
    r_xy(ax, "Safety_LPCO", fc=C_ALARM, zorder=6)
    vdim(ax, mx(lb[0]) - 1.0, 0, my(lb[3]), "%.1f″" % my(lb[3]), side=-1, fs=7.5)
if gas_pts:
    ax.plot([mx(p[0]) for p in gas_pts], [my(p[1]) for p in gas_pts], color=C_GAS, lw=2.2, zorder=7)
if GAS:
    r_xy(ax, "Shower_GasHeater", fc="#fafafa", ec="#c62828", lw=1.5, zorder=5)
    fb = bx("Shower_Flue")
    ax.add_patch(Circle((mx((fb[0] + fb[1]) / 2), my((fb[2] + fb[3]) / 2)), (fb[1] - fb[0]) / 2 / IN, fc="#b0bec5",
                        ec="#546e7a", zorder=6))
    hb = bx("Shower_GasHeater")
    ax.text(mx(hb[0]) + 0.2, my(hb[2]) + 0.6, "нагреватель\n+ дымоход", fontsize=7.5, color="#c62828", va="top",
            zorder=6)
# кухня: столешница (вогнутая кромка) — сечение модели
for w in GL["plan"].get("Kitchen_Countertop", []):
    ax.add_patch(Polygon([(mx(p[0]), my(p[1])) for p in w], closed=True, fc=C_TOP, alpha=0.85, ec="#6d4c41", zorder=3))
for w in GL["plan"].get("Kitchen_UpperCabinet", []):
    ax.add_patch(Polygon([(mx(p[0]), my(p[1])) for p in w], closed=True, fill=False, ec="#6d4c41", ls="-.", zorder=4))
r_xy(ax, "Kitchen_Sink", fc="#cfd8dc", ec="#546e7a", zorder=4)
ke = bx("Kitchen_Kettle")
ax.add_patch(Circle((mx((ke[0] + ke[1]) / 2), my((ke[2] + ke[3]) / 2)), (ke[1] - ke[0]) / 2 / IN, fc="#eceff1",
                    ec="#607d8b", zorder=4))
ax.add_patch(Rectangle((mx(fr[0]), my(fr[3])), (fr[1] - fr[0]) / IN, (fr[3] - fr[2]) / IN, fill=False, ec=C_FR,
                       ls="--", lw=1.4, zorder=4))
slide = K["fridge_slide"]
ax.add_patch(Rectangle((mx(fr[0]), my(fr[3] - slide)), (fr[1] - fr[0]) / IN, (fr[3] - fr[2]) / IN, fill=False,
                       ec=C_FR, ls=":", lw=1.4, zorder=4))
ax.text(mx((fr[0] + fr[1]) / 2), my(fr[2] - slide) - 1.2, "холодильник выдвинут\n(открыть крышку)",
        ha="center", fontsize=8, color=C_FR)
if x_div:
    ax.plot([mx(x_div)] * 2, [0, my(bx("Kitchen_Carcass")[2])], color="#5d4037", lw=1.4, ls="--", zorder=5)
    ax.text(mx(x_div) - 0.4, my(bx("Kitchen_Carcass")[2]) - 1.4, "1: мойка", ha="right", fontsize=8, zorder=6)
    ax.text(mx(x_div) + 0.4, my(bx("Kitchen_Carcass")[2]) - 1.4, "2: шкафчик + холодильник", ha="left", fontsize=8,
            zorder=6)
ax.text(mx(kx1) + 0.3, my(bx("Kitchen_UpperCabinet")[2]) + 0.3, "← верхний\n   шкафчик", fontsize=7.5, color="#6d4c41",
        va="top")
if TANK:
    r_xy(ax, TANK, fc="#4a90c2", alpha=0.25)
    ax.text(XL0 + 0.3, my((bx(TANK)[2] + bx(TANK)[3]) / 2) + 3.0, "← бак", fontsize=8, color="#1f5f8b", ha="left")
a_sh = my(PB[2])
a_k = my(bx("Kitchen_Countertop")[2])
vdim(ax, mx(XP0) + 1.0, a_sh, yop, "проход %.1f″" % ((yop - a_sh)), fs=8.5)
vdim(ax, mx(kx1) - 2, a_k, yop, "%.1f″" % (yop - a_k), fs=8.5)
vdim(ax, mx(kx1) - 2, 0, a_k, "%.1f″" % a_k, fs=8.5)
ax.set_xlim(XL0, 66)
ax.set_ylim(yop + 3.5, -2.5)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы")
ax.set_ylabel("от водительской стены, дюймы")
ax.set_title("План: столешница на 36″ (вогнутая кромка по шторке), под щитом — туалет и локер пропана", loc="left",
             fontsize=12)


# ───────── РАЗРЕЗЫ ПОПЕРЁК ─────────
wy = half[0][0]
ys_ = lambda Y: (wy - abs(Y)) / IN                           # от стены (у пола)


def profile(ax):
    ys = [((half[0][0] - y) / IN, mz(z)) for y, z in half]
    ax.plot([p[0] for p in ys], [p[1] for p in ys], color="#616161", lw=2)
    ax.add_patch(Rectangle((-2, -1.8), 50, 1.8, color="#e8d9b5"))


def secpoly(ax, wires, **kw):
    for w in wires:
        if len(w) > 2:
            ax.add_patch(Polygon([((wy - p[1]) / IN, mz(p[2])) for p in w], closed=True, **kw))


def r_yz(ax, name, **kw):
    if not has(name):
        return
    b = bx(name)
    ax.add_patch(Rectangle((ys_(b[3]), mz(b[4])), (b[3] - b[2]) / IN, (b[5] - b[4]) / IN, **kw))


def finish(ax, title):
    ax.set_xlim(-2, 44)
    ax.set_ylim(-3, 84)
    ax.set_aspect("equal")
    ax.grid(True, color="#f2f2f2", lw=0.6)
    ax.set_xlabel("от стены в салон, дюймы")
    ax.set_ylabel("от пола, дюймы")
    ax.set_title(title, loc="left", fontsize=11)


S = GL["shower"]
ax = axs
profile(ax)
secpoly(ax, S.get("Shower_DripLedge", []), fc=C_WALL, ec="#78909c", alpha=0.6)
secpoly(ax, S["Shower_WallBack"], fc="#b0bec5", ec="#78909c")
secpoly(ax, S["Shower_Ceiling"], fc="#b0bec5", ec="#78909c")
secpoly(ax, S["Shower_Pan"], fc=C_PAN, ec="#455a64", lw=1.3)
secpoly(ax, S["Shower_Curtain"], fc="#4fc3f7", ec="#0277bd")
secpoly(ax, S.get("Shower_Drain", []), fc="#455a64")
secpoly(ax, S["Shower_CurtainRod"], fc=C_ST)
secpoly(ax, S["Shower_ExhaustFan"], fc="#263238")
if GAS:                                                       # за спиной (у задней стенки) — проекция
    r_yz(ax, "Shower_GasHeater", fill=False, ec="#c62828", ls="--", lw=1.3)
    r_yz(ax, "Shower_Flue", fill=False, ec="#546e7a", ls="--", lw=1.1)
    hb = bx("Shower_GasHeater")
    ax.text(ys_(hb[3]) + 0.3, mz(hb[5]) + 0.6, "нагреватель на задней\nстенке (за спиной)", fontsize=7.5,
            color="#c62828")
zp = mz(z_pan)
hx = 22.0
H = float(int((z_ceil - z_pan) / IN))                      # человек ростом «впритык» к потолку
ax.add_patch(Circle((hx, zp + H - 4.3), 4.3, fc="none", ec="#d84315", lw=1.4))
ax.plot([hx, hx], [zp + H - 8.6, zp + 0.47 * H], color="#d84315", lw=1.4)
ax.plot([hx - 4, hx, hx + 4], [zp, zp + 0.47 * H, zp], color="#d84315", lw=1.4)
ax.plot([hx - 6, hx, hx + 6], [zp + 0.64 * H, zp + 0.81 * H, zp + 0.64 * H], color="#d84315", lw=1.4)
ax.text(hx + 5.0, zp + H - 12, "рост %.0f″\n(%.0f см)\nстоит прямо" % (H, H * 2.54), fontsize=8, color="#d84315")
vdim(ax, 33.5, mz(z_pan), mz(z_ceil), "%.1f″" % ((z_ceil - z_pan) / IN), side=1)
hdim(ax, mz(z_pan) + 2.2, ys_(bx("Shower_Pan")[3]), ys_(bx("Shower_Pan")[2]), "поддон 32″ (по задней стенке)", fs=8)
ax.text(1.5, mz(crown) - 6, "борт заваливается\nк крыше", fontsize=7.5, color="#616161")
finish(ax, "Разрез по душу через слив (взгляд к кабине, стена слева); поддон утоплен в пол")


def kitchen_sec(ax, secd, title, fridge_out=False):
    profile(ax)
    for n, kw in (("Kitchen_Plinth", dict(fc="#5d4037")), ("Kitchen_Carcass", dict(fc=C_CAB, ec="#8d6e63")),
                  ("Kitchen_FridgeSlide", dict(fc=C_ST)), ("Kitchen_Fridge", dict(fc=C_FR, ec="#263238")),
                  ("Kitchen_DoorSink", dict(fc="#e0b27a", ec="#8d6e63")), ("Kitchen_DoorUpper", dict(fc="#e0b27a", ec="#8d6e63")),
                  ("Kitchen_Countertop", dict(fc=C_TOP)), ("Kitchen_Sink", dict(fc="#cfd8dc", ec="#546e7a")),
                  ("Kitchen_Faucet", dict(fc=C_ST)), ("Kitchen_Kettle", dict(fc="#eceff1", ec="#607d8b")),
                  ("Kitchen_UpperCabinet", dict(fc=C_CAB, ec="#8d6e63"))):
        secpoly(ax, secd.get(n, []), **kw)
    if fridge_out:
        ax.add_patch(Rectangle(((wy - fr[2] + slide) / IN - (fr[3] - fr[2]) / IN, mz(fr[4])), (fr[3] - fr[2]) / IN,
                               (fr[5] - fr[4]) / IN, fill=False, ec=C_FR, ls=":", lw=1.4))
        ax.text((wy - fr[2] + slide) / IN - (fr[3] - fr[2]) / IN / 2, mz(fr[5]) + 0.6, "выдвинут —\nкрышка открывается",
                ha="center", fontsize=8, color=C_FR)
    vdim(ax, 40.0, 0, mz(z_ct), "36″")
    vdim(ax, 40.0, mz(z_ct), mz(z_up), "%.1f″" % ((z_up - z_ct) / IN))
    hdim(ax, mz(z_ct) + 1.4, 0, ys_(bx("Kitchen_Countertop")[2]), "%.1f″" % ys_(bx("Kitchen_Countertop")[2]), fs=8)
    finish(ax, title)


kitchen_sec(axk, GL["kitchen"], "Разрез по кухне, секция 1 — через мойку")
if "fridge" in GL:
    kitchen_sec(axf, GL["fridge"], "Разрез по кухне, секция 2 — шкафчик над холодильником %s" % K.get("fridge_title", ""),
                fridge_out=True)

# — под кроватью по локеру пропана (взгляд к кабине): впереди, за плоскостью — задняя стенка душа и нагреватель —
ax = axl
profile(ax)
if "locker" in GL:
    L = GL["locker"]
    for n in sorted(L):
        if n.startswith("BedCross"):
            secpoly(ax, L[n], fc="#90a4ae", ec="#607d8b")
    for n, kw in (("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")), ("BedMattress", dict(fc="#9fb4e0", alpha=0.5, ec="#5c6bc0")),
                  ("BedSideRail_pY", dict(fc="#90a4ae")), ("BankShelf", dict(fc="#d7b98e", ec="#8d6e63")),
                  ("BankRail_Inner", dict(fc="#90a4ae")), ("Toilet_Camco", dict(fc="#bdbdbd", ec="#424242")),
                  ("Propane_Locker", dict(fc=C_LOCK, ec="#bf8f00")), ("Propane_LockerDoor", dict(fc="#ffb74d", ec="#e65100")),
                  ("Propane_Cylinder", dict(fc="#fafafa", ec="#616161", lw=1.2)), ("Propane_Strap", dict(fc="#424242")),
                  ("Propane_Vent", dict(fc="#212121")), ("Propane_Regulator", dict(fc="#b0bec5", ec="#546e7a"))):
        secpoly(ax, L.get(n, []), **kw)
    # дальше, за плоскостью (к кабине): задняя стенка душа, нагреватель, дымоход, поддон — проекция пунктиром
    for n, ec in (("Shower_WallRear", "#78909c"), ("Shower_DripLedge", "#78909c"), ("Shower_GasHeater", "#c62828"),
                  ("Shower_Flue", "#546e7a"), ("Shower_Pan", "#455a64"), ("Shower_CurtainLower", "#0277bd")):
        r_yz(ax, n, fill=False, ec=ec, ls="--", lw=1.1)
    if gas_pts:
        ax.plot([ys_(p[1]) for p in gas_pts], [mz(p[2]) for p in gas_pts], color=C_GAS, lw=2.2, zorder=7)
    lb, cb = bx("Propane_Locker"), bx("Propane_Cylinder")
    ax.text(ys_((cb[2] + cb[3]) / 2), mz((cb[4] + cb[5]) / 2), "баллон\n30 lb", ha="center", va="center", fontsize=8.5)
    ax.text(ys_(lb[2]) + 0.4, mz(lb[4]) + 18, "← дверца\n(к проходу)", fontsize=7.5, color="#e65100")
    tb = bx("Toilet_Camco")
    ax.text(ys_((tb[2] + tb[3]) / 2), mz(tb[5]) - 4, "туалет", ha="center", fontsize=8.5)
    vb = bx("Propane_Vent")
    ax.annotate("вент ⌀1″ через пол\nнаружу (проверить\nснизу: бензобак,\nтрубки, выхлоп)",
                xy=(ys_((vb[2] + vb[3]) / 2), -1.0), xytext=(40.3, 2.5), fontsize=7.5, va="center",
                arrowprops=dict(arrowstyle="->", lw=0.8))
    hb = bx("Shower_GasHeater")
    ax.text(ys_(hb[3]) + 0.3, mz(hb[5]) + 0.5, "нагреватель (впереди,\nна задней стенке душа)", fontsize=7.5,
            color="#c62828")
    ax.text(ys_(gas_pts[2][1]) + 0.4, mz(gas_pts[2][2]) + 0.6, "газ (шланг LP 3/8″)", fontsize=7.5, color="#e65100")
    zc = min(bx(n)[4] for n in B if n.startswith("BedCross_"))
    vdim(ax, ys_(lb[2]) + 1.0, 0, mz(lb[5]), "%.1f″" % mz(lb[5]), fs=8)
    vdim(ax, ys_(lb[2]) + 1.0, mz(lb[5]), mz(zc), "%.1f″" % ((zc - lb[5]) / IN), fs=7.5)
    ax.text(40.3, 11.0, "красный —\nдатчик\nпропан/CO", fontsize=7.5, color=C_ALARM, ha="left", va="center")
    hdim(ax, mz(lb[5]) + 9.0, ys_(lb[3]), ys_(lb[2]), "%.1f″" % ((lb[3] - lb[2]) / IN), fs=8)
    r_yz(ax, "Safety_LPCO", fc=C_ALARM)
finish(ax, "Под кроватью по локеру пропана (взгляд к кабине); пунктир — дальше: стенка душа, нагреватель")
ax.set_ylim(-5, 84)
ax.set_xlim(-2, 50)

fig.suptitle("Душ (поддон-сектор 32″) с газовым нагревателем + кухня в 2 секции (вогнутый торец по шторке) + "
             "пропан под кроватью — 2026-11-07 (из модели)\n"
             "⚠️ Camplux по инструкции — только для улицы: дымоход через крышу, датчики CO и пропана, приток воздуха; "
             "локер — герметичный, вент через пол наружу",
             fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.975))
save(fig, "shower_kitchen_drawing.png")
