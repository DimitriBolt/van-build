"""Чертёж: шкафчики под потолком — пассажирский борт (12.2×12.2×16.5″, стоя) и над изголовьем по водительскому борту
(13.4×11.3×11.3″) + откидная столешница кухни. Дюймы: x — от задних дверей, z — от чистового пола. Данные — из модели."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from _common import IN, load, save

d = load()
if "cabinets" not in d:
    raise SystemExit("wall_cabinets: шкафчиков нет в модели — пропуск")
B, G, C = d["boxes"], d["geo"], d["cabinets"]
FF = G["floor_top"]
half = G["half"]
mz = lambda Z: (Z - FF) / IN
mx = lambda X: X / IN


def has(n):
    return n in B


def r_xz(ax, n, **kw):
    if has(n):
        b = B[n]
        ax.add_patch(Rectangle((mx(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, **kw))


def vdim(ax, x, z0, z1, txt, side=1, fs=8.5):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9), zorder=9)
    ax.text(x + 0.35 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right", fontsize=fs, zorder=9,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.4))


def hdim(ax, z, x0, x1, txt, fs=8.5):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9), zorder=9)
    ax.text((x0 + x1) / 2, z + 0.5, txt, ha="center", fontsize=fs, zorder=9, bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.4))


fig = plt.figure(figsize=(18, 19), dpi=110)
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], width_ratios=[1.55, 1])
axP = fig.add_subplot(gs[0, 0])
axD = fig.add_subplot(gs[1, 0])
axS = fig.add_subplot(gs[0, 1])
axF = fig.add_subplot(gs[1, 1])
crown = half[-1][1]
C_CAB, C_DOOR = "#dcae66", "#efc781"


def wall_view(ax, pref, title, extra):
    ax.add_patch(Rectangle((-2, -1.8), 130, 1.8, color="#e8d9b5"))
    ax.plot([-2, 128], [mz(crown)] * 2, color="#757575", lw=1.2)
    ax.text(0, mz(crown) + 0.5, "крыша (железо, по центру)", fontsize=8, color="#616161")
    for n in extra:
        for k in sorted(B):
            if k.startswith(n[0]):
                r_xz(ax, k, **n[1])
    cabs = sorted(k for k in B if k.startswith(pref) and not k.endswith("_Door"))
    for k in cabs:
        r_xz(ax, k, fc=C_CAB, ec="#8d6e63", lw=1.2, zorder=4)
        r_xz(ax, k + "_Door", fill=False, ec="#8d6e63", ls="--", zorder=5)
        b = B[k]
        ax.text(mx((b[0] + b[1]) / 2), mz((b[4] + b[5]) / 2), k.split("_")[1], ha="center", va="center", fontsize=11,
                weight="bold", color="#5d4037", zorder=6)
    b0, b1 = B[cabs[0]], B[cabs[-1]]
    hdim(ax, mz(b0[5]) + 2.2, mx(b0[0]), mx(b1[1]), "%d × %.1f″ = %.1f″" % (len(cabs), (b0[1] - b0[0]) / IN,
                                                                         (b1[1] - b0[0]) / IN))
    vdim(ax, mx(b1[1]) + 1.2, 0, mz(b0[4]), "%.1f″" % mz(b0[4]))
    vdim(ax, mx(b1[1]) + 1.2, mz(b0[4]), mz(b0[5]), "%.1f″" % ((b0[5] - b0[4]) / IN))
    if has("BedMattress"):
        mt = B["BedMattress"][5]
        vdim(ax, mx(b0[0]) + 1.5, mz(mt), mz(b0[4]), "%.1f″ над\nматрасом" % ((b0[4] - mt) / IN), fs=8)
    ax.set_xlim(-2, 75)
    ax.set_ylim(-3, 82)
    ax.set_aspect("equal")
    ax.grid(True, color="#f2f2f2", lw=0.6)
    ax.set_xlabel("от задних дверей вперёд, дюймы")
    ax.set_ylabel("от чистового пола, дюймы")
    ax.set_title(title, loc="left", fontsize=12)


ctx = [("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")), ("BedMattress", dict(fc="#9fb4e0", alpha=0.45, ec="#5c6bc0")),
       ("BedPost_", dict(fc="#90a4ae", alpha=0.6))]
wall_view(axP, "CabPass", "Пассажирский борт изнутри: шкафчики 12.2×12.2×16.5″ стоя — от задней двери до сдвижной",
          ctx + [("Battery_B", dict(fc="#ef6c00", alpha=0.7)), ("BankShelf", dict(fc="#d7b98e")),
                 ("Elec_Board", dict(fc="#d7b98e", ec="#8d6e63"))])
slx = B["Opening_SlidingDoor"][0]
axP.axvline(mx(slx), color="#2e7d32", lw=2, ls="--")
axP.text(mx(slx) + 0.4, 40, "проём\nсдвижной двери", color="#2e7d32", fontsize=9)
wall_view(axD, "CabDrv", "Водительский борт изнутри: шкафчики 13.4×11.3×11.3″ над изголовьем — до задней стенки душа",
          ctx + [("WaterTank_", dict(fc="#4a90c2", alpha=0.35)), ("Toilet_", dict(fc="#bdbdbd")),
                 ("Propane_Locker", dict(fc="#f3d98b")), ("Shower_WallRear", dict(fc="#b0bec5")),
                 ("Shower_GasHeater", dict(fc="#fafafa", ec="#c62828")), ("Shower_Flue", dict(fc="#b0bec5"))])
for ax in (axP, axD):
    rb = [k for k in B if k.startswith("Rib_x")]
    for k in rb:
        b = B[k]
        ax.add_patch(Rectangle((mx(b[0]), mz(crown) - 14), (b[1] - b[0]) / IN, 14, fc="#607d8b", alpha=0.4))
    ax.text(mx(B["Rib_x0160"][1]) + 0.3, mz(crown) - 15.5, "ребро крыши", fontsize=7.5, color="#455a64")

# поперечный разрез: оба ряда (взгляд вперёд, водительский борт слева)
ax = axS
hy = lambda Y: -Y / IN
wl = [(hy(y), mz(z)) for y, z in half]
ax.plot([p[0] for p in wl], [p[1] for p in wl], color="#616161", lw=2)
ax.plot([-p[0] for p in wl], [p[1] for p in wl], color="#616161", lw=2)
ax.add_patch(Rectangle((-41, -1.8), 82, 1.8, color="#e8d9b5"))
for k, w in C.get("_ctx", {}).items():
    nm = k.split("@")[0]
    kw = dict(BedMattress=dict(fc="#9fb4e0", alpha=0.45), BedDeck=dict(fc="#d7ccc8", ec="#8d6e63"),
              Battery_B2=dict(fc="#ef6c00", alpha=0.7), BankShelf=dict(fc="#d7b98e")).get(nm, dict(fc="#eee"))
    for ww in w:
        ax.add_patch(Polygon([(hy(p[1]), mz(p[2])) for p in ww], closed=True, **kw))
for nm in ("CabPass_1", "CabDrv_1"):
    for ww in C.get(nm, []):
        ax.add_patch(Polygon([(hy(p[1]), mz(p[2])) for p in ww], closed=True, fc=C_CAB, ec="#8d6e63", lw=1.3, zorder=4))
    b = B[nm]
    side = 1 if b[2] < 0 else -1
    xf = hy(b[3]) if b[2] >= 0 else hy(b[2])
    ax.text(hy((b[2] + b[3]) / 2), mz(b[4]) - 2.0, "%s\nглубина внизу %.1f″" % (
        "пассажирский" if b[2] < 0 else "над изголовьем", (b[3] - b[2]) / IN), ha="center", va="top", fontsize=8.5)
ax.set_xlim(-41, 41)
ax.set_ylim(-3, 82)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("поперёк, дюймы от оси (слева — водительский борт)")
ax.set_title("Разрез (взгляд вперёд): боковины по профилю борта", loc="left", fontsize=12)

# откидная столешница — вид на водительский борт у кухни
ax = axF
X0 = 2700.0
fx = lambda X: (X - X0) / IN
ax.add_patch(Rectangle((-2, -1.8), 40, 1.8, color="#e8d9b5"))
for n, kw in (("Kitchen_Carcass", dict(fc="#d9a066", alpha=0.35, ec="#8d6e63")), ("Kitchen_Fridge", dict(fc="#3f6b8c")),
              ("Kitchen_Countertop", dict(fc="#9c6b3c")), ("Kitchen_UpperCabinet", dict(fc="#d9a066", ec="#8d6e63")),
              ("Kitchen_Plinth", dict(fc="#5d4037")), ("Kitchen_FlapBracket1", dict(fc="#9aa4ad")),
              ("Kitchen_Flap", dict(fc="#9c6b3c", ec="#5d4037")),
              ("Kitchen_FlapOpen", dict(fill=False, ec="#9c6b3c", ls="--", lw=1.5)),
              ("Kitchen_FlapBracketOpen1", dict(fill=False, ec="#607d8b", ls="--"))):
    if has(n):
        b = B[n]
        ax.add_patch(Rectangle((fx(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, **kw))
seat = fx(3190.0)
ax.add_patch(Rectangle((seat, 0), 0.25, 50, fc="#bdbdbd"))
ax.text(seat + 0.4, 46, "плоскость спинки\nводителя (сиденье\nвперёд)", fontsize=8)
fo = B["Kitchen_FlapOpen"]
hdim(ax, mz(fo[5]) + 1.5, fx(fo[0]), fx(fo[1]), "разложена %.0f″ (сиденье на 180°)" % ((fo[1] - fo[0]) / IN))
fl = B["Kitchen_Flap"]
vdim(ax, fx(fl[1]) + 2.5, mz(fl[4]), mz(fl[5]), "сложена\n%.0f″" % ((fl[5] - fl[4]) / IN))
ax.annotate("до спинки %.0f мм" % (3190.0 - fl[1]), xy=(fx(fl[1]), mz(fl[4]) + 3), xytext=(fx(fl[1]) + 3, mz(fl[4]) - 4),
            fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))
ax.set_xlim(-2, 36)
ax.set_ylim(-3, 70)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("вдоль борта, дюймы (0 = X %.0f)" % X0)
ax.set_title("Откидная столешница у сиденья водителя", loc="left", fontsize=12)

fig.suptitle("Шкафчики под потолком + откидная столешница — проект 2026-11-07 (из модели)", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, 0.97))
save(fig, "wall_cabinets_drawing.png")
