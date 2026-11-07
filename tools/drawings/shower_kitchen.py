"""Чертёж: душ 32×32″ + мини-кухня по водительскому борту (между кроватью и кабиной).
Дюймы. Вид на борт и план: x — вдоль борта, 0 = передний край настила кровати, + к кабине;
план: y — от стены в салон; разрезы: y — от стены, z — от чистового пола. Данные — из модели."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

from _common import IN, load, save

d = load()
B, G, K = d["boxes"], d["geo"], d["SHOWER_KITCHEN"]
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


def r_xz(ax, name, **kw):
    b = bx(name)
    ax.add_patch(Rectangle((mx(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, **kw))


def r_xy(ax, name, **kw):
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
SEAT = mx(3190.0)
sx0, sx1 = bx("Shower_WallRear")[0], bx("Shower_WallFront")[1]
kx0, kx1 = bx("Kitchen_Carcass")[0], bx("Kitchen_Carcass")[1]
z_pan = bx("Shower_Pan")[5]
z_ceil = bx("Shower_Ceiling")[4]
z_ct = bx("Kitchen_Countertop")[5]
z_up = bx("Kitchen_UpperCabinet")[4]
crown = half[-1][1]

fig = plt.figure(figsize=(19, 20), dpi=120)
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05])
axe = fig.add_subplot(gs[0, 0])
axp = fig.add_subplot(gs[0, 1])
axs = fig.add_subplot(gs[1, 0])
axk = fig.add_subplot(gs[1, 1])

# ───────── ВИД НА ВОДИТЕЛЬСКИЙ БОРТ ИЗ ПРОХОДА ─────────
ax = axe
ax.add_patch(Rectangle((-14, -1.8), 80, 1.8, color="#e8d9b5", zorder=1))
ax.text(-13.6, -1.2, "пол (фанера)", fontsize=8, zorder=2)
ax.plot([-14, 66], [mz(crown)] * 2, color="#757575", lw=1.2)
ax.text(-13.6, mz(crown) + 0.4, "крыша (железо, по центру)", fontsize=8, color="#616161")
ax.add_patch(Rectangle((SEAT, -1.8), 4, mz(crown) + 1.8, fc="#eeeeee", ec="#bdbdbd", hatch="//"))
ax.text(SEAT + 2, 40, "кабина: спинка\nводителя", ha="center", fontsize=8.5, rotation=90, va="center")
# кровать (край)
r_xz(ax, "BedDeck", fc="#d7ccc8", ec="#8d6e63")
r_xz(ax, "BedMattress", fc="#9fb4e0", alpha=0.45, ec="#5c6bc0")
r_xz(ax, "BedSideRail_pY", fc="#90a4ae")
r_xz(ax, "BedPost_pY_front", fc="#90a4ae", ec="#607d8b")
ax.text(-7, mz(bx("BedMattress")[5]) + 0.6, "кровать (край)", ha="center", fontsize=9)
TANK = next((n for n in ("WaterTank_T4100", "WaterTank_T3500") if n in d["boxes"]), None)
for n in ("TankShelf", "TankFloor_BasePly"):
    if n in d["boxes"]:
        r_xz(ax, n, fc="#d7b98e", alpha=0.8, ec="#8d6e63")
if TANK:
    r_xz(ax, TANK, fc="#4a90c2", alpha=0.25, ec="#4a90c2")
    ax.text(-12.5, mz(bx(TANK)[5]) - 3, "бак %s\n(%s)" % (TANK.split("_")[1].replace("T", "T-"),
            "на полке" if TANK.endswith("3500") else "на полу"), fontsize=8, color="#1f5f8b")
r_xz(ax, "Water_Heater12V", fc="#cfcfcf", ec="#424242", alpha=0.9)
ax.text(mx(bx("Water_Heater12V")[0]) + 0.3, mz(bx("Water_Heater12V")[5]) + 0.6, "бойлер 12V", fontsize=7.5)
# душ
for n in ("Shower_WallRear", "Shower_WallFront"):
    r_xz(ax, n, fc=C_WALL, ec="#78909c")
r_xz(ax, "Shower_WallBack", fc="#f5f7f9", ec="none", zorder=0)
r_xz(ax, "Shower_Ceiling", fc=C_WALL, ec="#78909c")
r_xz(ax, "Shower_Pan", fc=C_PAN, ec="#455a64", lw=1.2)
r_xz(ax, "Shower_CurtainRod", fc=C_ST)
r_xz(ax, "Shower_Head", fc=C_ST, ec="#455a64")
r_xz(ax, "Shower_ExhaustFan", fc="#263238")
ax.text(mx((sx0 + sx1) / 2), mz(1100), "ДУШ\n32×32″ внутри\n(шторка снята)", ha="center", fontsize=11, weight="bold",
        color="#37474f")
ax.text(mx(bx("Shower_Head")[1]) + 0.3, mz(bx("Shower_Head")[5]), "лейка", fontsize=8)
ax.text(mx(bx("Shower_ExhaustFan")[1]) + 0.3, mz(bx("Shower_ExhaustFan")[4]) - 1.2, "вытяжка 12V → в стену", fontsize=8)
# кухня
r_xz(ax, "Kitchen_Plinth", fc="#5d4037")
r_xz(ax, "Kitchen_Carcass", fc=C_CAB, ec="#8d6e63", alpha=0.35)
r_xz(ax, "Kitchen_Fridge", fc=C_FR, ec="#263238")
r_xz(ax, "Kitchen_FridgeSlide", fc=C_ST)
ax.text(mx((bx("Kitchen_Fridge")[0] + bx("Kitchen_Fridge")[1]) / 2), mz(bx("Kitchen_Fridge")[4]) + 8,
        "холодильник-ларь 12V\n~30 qt на салазках", ha="center", fontsize=8.5, color="white")
r_xz(ax, "Kitchen_DoorUpper", fill=False, ec="#8d6e63", ls="--")
ax.text(mx((kx0 + kx1) / 2), mz(bx("Kitchen_DoorUpper")[4]) + 2.6, "дверца: чашки, чай,\nфильтр, слив мойки",
        ha="center", fontsize=8)
sk = bx("Kitchen_Sink")
ax.add_patch(Rectangle((mx(sk[0]), mz(sk[4])), (sk[1] - sk[0]) / IN, (sk[5] - sk[4]) / IN, fill=False, ec="#546e7a",
                       ls=":", lw=1.2))
r_xz(ax, "Kitchen_Countertop", fc=C_TOP)
r_xz(ax, "Kitchen_Faucet", fc=C_ST)
r_xz(ax, "Kitchen_Kettle", fc="#cfd8dc", ec="#607d8b")
r_xz(ax, "Kitchen_Outlet", fc="#ffffff", ec="#424242")
r_xz(ax, "Kitchen_UpperCabinet", fc=C_CAB, ec="#8d6e63")
ax.text(mx((kx0 + kx1) / 2), mz(bx("Kitchen_UpperCabinet")[4]) + 5, "шкафчик\n(чашки, чай)", ha="center", fontsize=9)
ax.text(mx((sk[0] + sk[1]) / 2), mz(sk[4]) - 1.3, "мойка 12×12″", ha="center", fontsize=7.5)
ax.text(mx((bx("Kitchen_Kettle")[0] + bx("Kitchen_Kettle")[1]) / 2), mz(bx("Kitchen_Kettle")[5]) + 0.5, "чайник",
        ha="center", fontsize=8)
# сдвижная дверь напротив
slx = (bx("Opening_SlidingDoor")[0], bx("Opening_SlidingDoor")[1])
ax.plot([mx(slx[0]), mx(slx[1])], [-3.0, -3.0], color="#2e7d32", lw=4, solid_capstyle="butt")
ax.text(mx(slx[0]), -4.3, "сдвижная дверь — на противоположном борту", fontsize=8, color="#2e7d32")
# размеры
hdim(ax, mz(1990), mx(sx0), mx(sx1), "душ %.1f″ (%.0f)" % ((sx1 - sx0) / IN, sx1 - sx0))
hdim(ax, mz(1990), mx(kx0), mx(kx1), "кухня %.1f″ (%.0f)" % ((kx1 - kx0) / IN, kx1 - kx0))
hdim(ax, mz(2060), 0, SEAT, "от кровати до спинки водителя %.1f″ (%.0f)" % (SEAT, 3190.0 - X0))
vdim(ax, mx(sx0) + 2.2, mz(z_pan), mz(z_ceil), "%.1f″ (%.0f)\nот поддона до потолка" % ((z_ceil - z_pan) / IN, z_ceil - z_pan))
vdim(ax, mx(kx1) + 0.6, 0, mz(z_ct), "36″", fs=8.5)
vdim(ax, mx(kx1) + 0.6, mz(z_ct), mz(z_up), "%.1f″" % ((z_up - z_ct) / IN), fs=8.5)
vdim(ax, mx(kx1) + 0.6, 0, mz(z_pan), "", fs=7)
ax.set_xlim(-14, 66)
ax.set_ylim(-5.5, 84)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы (0 = передний край настила кровати; к кабине — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на водительский борт из прохода (шторка и дверца под мойкой сняты)", loc="left", fontsize=12)

# ───────── ПЛАН ─────────
ax = axp
ax.add_patch(Rectangle((-14, -1.5), 80, 1.5, color="#cfcfcf"))
ax.text(-13.5, -1.0, "водительская стена", fontsize=8)
yop = my(-wall_y(900.0))                                   # противоположная стена
ax.add_patch(Rectangle((-14, yop), 80, 1.5, color="#cfcfcf"))
ax.add_patch(Rectangle((mx(slx[0]), yop), mx(slx[1]) - mx(slx[0]), 1.5, color="#2e7d32"))
ax.text(mx((slx[0] + slx[1]) / 2), yop + 2.6, "сдвижная дверь (пассажирский борт)", ha="center", fontsize=8.5,
        color="#2e7d32")
ax.add_patch(Rectangle((SEAT, -1.5), 4, yop + 3, fc="#eeeeee", ec="#bdbdbd", hatch="//"))
ax.text(SEAT + 2, yop / 2, "сиденья", rotation=90, ha="center", va="center", fontsize=8.5)
r_xy(ax, "BedDeck", fc="#d7ccc8", ec="#8d6e63", alpha=0.6)
ax.text(-7, yop / 2, "кровать", ha="center", fontsize=10)
r_xy(ax, "BedPost_pY_front", fc="#607d8b")
r_xy(ax, "Shower_Pan", fc=C_PAN, ec="#455a64", lw=1.2)
ax.add_patch(Circle((mx((sx0 + sx1) / 2), my((bx("Shower_Pan")[2] + bx("Shower_Pan")[3]) / 2)), 0.8,
                    fc="#90a4ae", ec="#455a64"))
for n in ("Shower_WallRear", "Shower_WallFront"):
    r_xy(ax, n, fc="#b0bec5")
r_xy(ax, "Shower_Curtain", fc="#4fc3f7")
ax.text(mx((sx0 + sx1) / 2), my(bx("Shower_Pan")[2]) - 3.5, "ДУШ 32×32″\nслив в центре", ha="center", fontsize=10,
        weight="bold", color="#37474f")
ax.text(mx((sx0 + sx1) / 2), my(bx("Shower_Curtain")[2]) + 1.4, "шторка", ha="center", fontsize=8, color="#0277bd")
r_xy(ax, "Kitchen_Countertop", fc=C_TOP, alpha=0.85)
sk = bx("Kitchen_Sink")
r_xy(ax, "Kitchen_Sink", fc="#cfd8dc", ec="#546e7a")
ke = bx("Kitchen_Kettle")
ax.add_patch(Circle((mx((ke[0] + ke[1]) / 2), my((ke[2] + ke[3]) / 2)), (ke[1] - ke[0]) / 2 / IN, fc="#eceff1",
                    ec="#607d8b"))
fr = bx("Kitchen_Fridge")
ax.add_patch(Rectangle((mx(fr[0]), my(fr[3])), (fr[1] - fr[0]) / IN, (fr[3] - fr[2]) / IN, fill=False, ec=C_FR,
                       ls="--", lw=1.4))
slide = K["fridge_slide"]
ax.add_patch(Rectangle((mx(fr[0]), my(fr[3] - slide)), (fr[1] - fr[0]) / IN, (fr[3] - fr[2]) / IN, fill=False,
                       ec=C_FR, ls=":", lw=1.4))
ax.text(mx((fr[0] + fr[1]) / 2), my(fr[2] - slide) - 1.2, "холодильник выдвинут\n(открыть крышку)",
        ha="center", fontsize=8, color=C_FR)
uc = bx("Kitchen_UpperCabinet")
ax.add_patch(Rectangle((mx(uc[0]), 0), (uc[1] - uc[0]) / IN, my(uc[2]), fill=False, ec="#6d4c41", ls="-."))
ax.text(mx(kx1) + 0.3, my(uc[2]) + 0.3, "← верхний\n   шкафчик", fontsize=7.5, color="#6d4c41", va="top")
r_xy(ax, "Water_Heater12V", fc="#bdbdbd", ec="#424242", alpha=0.8)
ax.text(-3.5, my(bx("Water_Heater12V")[2]) + 1.0, "под кроватью:\nбойлер", ha="right", fontsize=7.5)
if TANK:
    r_xy(ax, TANK, fc="#4a90c2", alpha=0.25)
ax.text(-11, 9, "бак", fontsize=8, color="#1f5f8b")
a_sh = my(bx("Shower_Curtain")[2])
a_k = my(bx("Kitchen_Countertop")[2])
vdim(ax, mx(sx1) - 3, a_sh, yop, "проход %.1f″" % ((yop - a_sh)), fs=8.5)
vdim(ax, mx(kx1) - 2, a_k, yop, "%.1f″" % (yop - a_k), fs=8.5)
vdim(ax, mx(kx1) - 2, 0, a_k, "%.1f″" % a_k, fs=8.5)
vdim(ax, mx(sx0) + 2, 0, a_sh, "%.1f″" % a_sh, fs=8.5)
ax.set_xlim(-14, 66)
ax.set_ylim(yop + 3.5, -2.5)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы")
ax.set_ylabel("от водительской стены, дюймы")
ax.set_title("План (на высоте столешницы)", loc="left", fontsize=12)


# ───────── РАЗРЕЗЫ ПОПЕРЁК ─────────
def profile(ax):
    pts = [(0.0, mz(z)) for _, z in half]                    # стена — по y от неё
    ys = [((half[0][0] - y) / IN, mz(z)) for y, z in half]
    ax.plot([p[0] for p in ys], [p[1] for p in ys], color="#616161", lw=2)
    ax.add_patch(Rectangle((-2, -1.8), 50, 1.8, color="#e8d9b5"))


def secpoly(ax, wires, **kw):
    for w in wires:
        if len(w) > 2:
            ax.add_patch(Polygon([((half[0][0] - p[1]) / IN, mz(p[2])) for p in w], closed=True, **kw))


S = d["galley"]["shower"]
ax = axs
profile(ax)
secpoly(ax, S["Shower_WallFront"], fc=C_WALL, ec="#78909c", alpha=0.6)
secpoly(ax, S["Shower_WallBack"], fc="#b0bec5", ec="#78909c")
secpoly(ax, S["Shower_Ceiling"], fc="#b0bec5", ec="#78909c")
secpoly(ax, S["Shower_Pan"], fc=C_PAN, ec="#455a64", lw=1.3)
secpoly(ax, S["Shower_Curtain"], fc="#4fc3f7", ec="#0277bd")
secpoly(ax, S["Shower_CurtainRod"], fc=C_ST)
secpoly(ax, S["Shower_ExhaustFan"], fc="#263238")
# человек 70″ (178 см) на поддоне
zp = mz(z_pan)
hx = 18.0
H = float(int((z_ceil - z_pan) / IN))                      # человек ростом «впритык» к потолку
ax.add_patch(Circle((hx, zp + H - 4.3), 4.3, fc="none", ec="#d84315", lw=1.4))
ax.plot([hx, hx], [zp + H - 8.6, zp + 0.47 * H], color="#d84315", lw=1.4)
ax.plot([hx - 4, hx, hx + 4], [zp, zp + 0.47 * H, zp], color="#d84315", lw=1.4)
ax.plot([hx - 6, hx, hx + 6], [zp + 0.64 * H, zp + 0.81 * H, zp + 0.64 * H], color="#d84315", lw=1.4)
ax.text(hx + 5.0, zp + H - 12, "рост %.0f″\n(%.0f см)\nстоит прямо" % (H, H * 2.54), fontsize=8, color="#d84315")
vdim(ax, 31.5, mz(z_pan), mz(z_ceil), "%.1f″" % ((z_ceil - z_pan) / IN), side=1)
wy = half[0][0]
hdim(ax, mz(z_pan) + 2.2, (wy - bx("Shower_Pan")[3]) / IN, (wy - bx("Shower_Pan")[2]) / IN, "поддон 32″", fs=8)
ax.text(1.5, mz(crown) - 6, "борт заваливается\nк крыше", fontsize=7.5, color="#616161")
ax.set_xlim(-2, 44)
ax.set_ylim(-3, 80)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от стены в салон, дюймы")
ax.set_ylabel("от пола, дюймы")
ax.set_title("Разрез по душу (взгляд к кабине, стена слева); поддон утоплен в пол", loc="left", fontsize=11)

Kk = d["galley"]["kitchen"]
ax = axk
profile(ax)
for n, kw in (("Kitchen_Plinth", dict(fc="#5d4037")), ("Kitchen_Carcass", dict(fc=C_CAB, ec="#8d6e63")),
              ("Kitchen_FridgeSlide", dict(fc=C_ST)), ("Kitchen_Fridge", dict(fc=C_FR, ec="#263238")),
              ("Kitchen_DoorUpper", dict(fc="#e0b27a", ec="#8d6e63")), ("Kitchen_Countertop", dict(fc=C_TOP)),
              ("Kitchen_Sink", dict(fc="#cfd8dc", ec="#546e7a")), ("Kitchen_Faucet", dict(fc=C_ST)),
              ("Kitchen_UpperCabinet", dict(fc=C_CAB, ec="#8d6e63"))):
    secpoly(ax, Kk.get(n, []), **kw)
fr = bx("Kitchen_Fridge")
ax.add_patch(Rectangle(((wy - fr[2] + slide) / IN - (fr[3] - fr[2]) / IN, mz(fr[4])), (fr[3] - fr[2]) / IN,
                       (fr[5] - fr[4]) / IN, fill=False, ec=C_FR, ls=":", lw=1.4))
ax.text((wy - fr[2] + slide) / IN - (fr[3] - fr[2]) / IN / 2, mz(fr[5]) + 0.6, "выдвинут", ha="center", fontsize=8,
        color=C_FR)
vdim(ax, 29.5, 0, mz(z_ct), "36″")
vdim(ax, 29.5, mz(z_ct), mz(z_up), "%.1f″" % ((z_up - z_ct) / IN))
hdim(ax, mz(z_ct) + 1.4, 0, (wy - bx("Kitchen_Countertop")[2]) / IN, "%.1f″" % ((wy - bx("Kitchen_Countertop")[2]) / IN), fs=8)
ax.set_xlim(-2, 44)
ax.set_ylim(-3, 80)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от стены в салон, дюймы")
ax.set_title("Разрез по кухне (через мойку)", loc="left", fontsize=11)

fig.suptitle("Душ 32×32″ + мини-кухня «для чая» по водительскому борту — проект 2026-11-06 (из модели van_v0.py)\n"
             "кровать не сужали; бак — под кроватью у арки, 12V-бойлер — под передним краем кровати",
             fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.965))
save(fig, "shower_kitchen_drawing.png")
