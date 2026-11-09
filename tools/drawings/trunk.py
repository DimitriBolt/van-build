"""Чертёж: багажник под кроватью — 1-й этаж (пол) и 2-й этаж (перфолист на полку батарей и бак T-4320).
Дюймы. Разрез — взгляд вперёд от задних дверей (водительский борт слева); план — X от задних дверей."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

from _common import IN, load, save

d = load()
if "trunk" not in d:
    raise SystemExit("trunk: 2-й этаж не построен (нужен вариант T4320_floor) — пропуск")
B, G, T = d["boxes"], d["geo"], d["TRUNK_SHELF"]["_summary"]
SEC = d["trunk"]
FF = G["floor_top"]
half = G["half"]
mz = lambda Z: (Z - FF) / IN
hy = lambda Y: -Y / IN                                  # разрез: водительский борт (+Y) слева
X0 = T["x_rear"]
px = lambda X: (X - X0) / IN
py = lambda Y: Y / IN

C_BAT, C_T, C_ST, C_SH, C_DECK = "#ef6c00", "#4a90c2", "#78909c", "#b0bec5", "#d7ccc8"


def has(n):
    return n in B


def vdim(ax, x, z0, z1, txt, side=1, fs=8.5, color="k"):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=9)
    ax.text(x + 0.35 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right", fontsize=fs,
            color=color, zorder=9, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.4))


def hdim(ax, z, x0, x1, txt, fs=8.5, dz=0.45, color="k"):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color), zorder=9)
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs, color=color, zorder=9,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.4))


fig = plt.figure(figsize=(17, 21), dpi=110)
gs = fig.add_gridspec(2, 1, height_ratios=[0.95, 1.0])
axs = fig.add_subplot(gs[0])
axp = fig.add_subplot(gs[1])

# ───────── РАЗРЕЗ (взгляд вперёд) ─────────
ax = axs
wl = [(hy(y), mz(z)) for y, z in half if z < FF + 1150]
wr = [(-p[0], p[1]) for p in wl]
ax.plot([p[0] for p in wl], [p[1] for p in wl], color="#616161", lw=2)
ax.plot([p[0] for p in wr], [p[1] for p in wr], color="#616161", lw=2)
ax.add_patch(Rectangle((hy(1000), -1.8), 2000 / IN, 1.8, color="#e8d9b5"))
STY = [("WheelArch_", dict(fc="#bdbdbd", ec="#9e9e9e")), ("BedSideRail", dict(fc=C_ST)), ("BedDeck", dict(fc=C_DECK, ec="#8d6e63")),
       ("BedMattress", dict(fc="#9fb4e0", alpha=0.5, ec="#5c6bc0")), ("BankPost", dict(fc=C_ST)), ("BedPost_", dict(fc=C_ST)), ("Trunk2_Tongue", dict(fc="#37474f")),
       ("Trunk2_Bolt", dict(fc="#f9a825")), ("BankCross", dict(fc=C_ST)),
       ("BankRail", dict(fc=C_ST, ec="#37474f")), ("BankShelf", dict(fc="#d7b98e", ec="#8d6e63")),
       ("Battery_B", dict(fc=C_BAT, ec="#bf360c", alpha=0.85)), ("WaterTank_", dict(fc=C_T, alpha=0.55, ec="#1f5f8b", lw=1.4)),
       ("TankFloor_", dict(fc="#a1887f", ec="#5d4037")), ("Trunk2_Pad", dict(fc="#212121")),
       ("Trunk2_Angle", dict(fc=C_ST)), ("Trunk2_Cross", dict(fc=C_ST, ec="#37474f")),
       ("Trunk2_Sheet", dict(fc="#90a4ae", ec="#263238", lw=1.2))]
for pref, kw in STY:
    for n in sorted(SEC):
        if n.startswith(pref) and n != "x":
            for w in SEC[n]:
                if len(w) > 2:
                    ax.add_patch(Polygon([(hy(p[1]), mz(p[2])) for p in w], closed=True, zorder=3, **kw))
# поперечины 2-го этажа — за разрезом (пунктир) и поперечины кровати
for n in sorted(B):
    if n.startswith("Trunk2_Cross_"):
        b = B[n]
        ax.add_patch(Rectangle((hy(b[3]), mz(b[4])), (b[3] - b[2]) / IN, (b[5] - b[4]) / IN, fill=False, ec="#37474f",
                               ls="--", lw=1.0, zorder=4))
cb = B["BedCross_1"]
ax.add_patch(Rectangle((hy(cb[3]), mz(cb[4])), (cb[3] - cb[2]) / IN, (cb[5] - cb[4]) / IN, fill=False, ec="#263238",
                       ls="-.", lw=0.9, zorder=4))
ax.text(hy(-600), mz(cb[5]) + 0.4, "поперечина кровати #1 (за разрезом)", fontsize=7.5, color="#263238")
zs2 = mz(T["z_cross"][1])                                   # верх поперечин 2-го этажа
y_r1, y_c1 = T["y1"]                                        # грань рейки батарей / брусок бака (|Y| со знаком)
# 1-й этаж
ax.add_patch(Rectangle((hy(y_c1), 0), (y_c1 - y_r1) / IN, mz(T["z_cross"][0]), fc="#fff8e1", ec="none", zorder=1))
ax.text((hy(y_c1) + hy(y_r1)) / 2, 6.5, "1-й ЭТАЖ\n(пол багажника)", ha="center", fontsize=12, weight="bold",
        color="#6d4c41", zorder=5)
ax.text(hy(0), zs2 + 8.5, "поперечина 2-го этажа #1 (P3 ↔ стойка кровати), лист — позже", ha="center", fontsize=11,
        weight="bold", color="#37474f", zorder=5)
hdim(ax, 3.0, hy(y_c1), hy(y_r1), "%.1f″ (рейка батарей ↔ брусок бака)" % (T["w1"] / IN))
vdim(ax, hy(y_r1) - 2.0, 0, mz(T["z_cross"][0]), "%.1f″\nпод поперечинами" % mz(T["z_cross"][0]), side=-1)
vdim(ax, hy(y_r1) - 9.0, 0, zs2, "%.2f″\nверх поперечины" % zs2, side=-1)
vdim(ax, hy(400), zs2, mz(B["BedDeck"][4]), "%.1f″ до щита\n(между поперечинами)" % (T["h2_deck"] / IN), fs=8)
vdim(ax, hy(-350), zs2, mz(cb[4]), "%.1f″ до поперечины\nкровати" % (T["h2_cross"] / IN), fs=8)
tk = next(n for n in B if n.startswith("WaterTank_"))
ax.text((hy(B[tk][2]) + hy(B[tk][3])) / 2, mz(B[tk][5]) / 2, "бак\nT-4320", ha="center", fontsize=10, color="#0d47a1",
        weight="bold", zorder=6)
ax.text(hy(-850), mz(B["Battery_B2"][5]) - 4.0, "батареи\nна полке", ha="center", fontsize=9, color="white", weight="bold",
        zorder=6)
ax.text(hy(-850), 6.0, "B1", ha="center", fontsize=9, color="white", weight="bold", zorder=6)
ax.set_xlim(hy(1010), hy(-1010))
ax.set_ylim(-3, 40)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("поперёк фургона, дюймы от оси (слева — водительский борт)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Разрез по багажнику X=%.1f″ от задних дверей (взгляд вперёд, к кабине)" % px(SEC["x"]), loc="left",
             fontsize=12)

# ───────── ПЛАН ─────────
ax = axp


def r(n, **kw):
    if not has(n):
        return
    b = B[n]
    ax.add_patch(Rectangle((px(b[0]), py(b[2])), (b[1] - b[0]) / IN, (b[3] - b[2]) / IN, **kw))


yw0 = G["arch_ywall"]
ax.add_patch(Rectangle((-2, py(yw0)), 60, 1.5, color="#cfcfcf"))
ax.add_patch(Rectangle((-2, py(-yw0) - 1.5), 60, 1.5, color="#cfcfcf"))
ax.text(0.2, py(yw0) + 2.0, "водительский борт", fontsize=8.5)
ax.text(0.2, py(-yw0) - 3.2, "пассажирский борт", fontsize=8.5)
ax.add_patch(Rectangle((-2, py(-yw0)), 2, 2 * yw0 / IN, fc="#e3f2fd", ec="#1565c0"))
ax.text(-1.0, 0, "задние двери", rotation=90, ha="center", va="center", fontsize=9, color="#1565c0")
r("BedDeck", fill=False, ec="#8d6e63", ls="--", lw=1.2)
for n in ("WheelArch_pY", "WheelArch_nY"):
    r(n, fc="#e0e0e0", ec="#9e9e9e")
# 1-й этаж (заливка — свободный пол)
y_l = T["y_lock"]
poly = [(px(T["x_rear"]), py(y_r1)), (px(T["x_deck"]), py(y_r1)), (px(T["x_deck"]), py(y_l)), (px(T["x_lock"]), py(y_l)),
        (px(T["x_lock"]), py(y_c1)), (px(T["x_rear"]), py(y_c1))]
ax.add_patch(Polygon(poly, closed=True, fc="#fff8e1", ec="#8d6e63", lw=1.0, zorder=1))
for n in sorted(B):
    if n.startswith(("Battery_B", "BankShelf", "BankRail", "BankPost")):
        r(n, fc=C_BAT if n.startswith("Battery") else C_ST, alpha=0.8, zorder=3)
r(tk, fc=C_T, alpha=0.5, ec="#1f5f8b", zorder=3)
for n in sorted(B):
    if n.startswith(("TankFloor_Cleat", "TankFloor_Strap")):
        r(n, fc="#a1887f", zorder=4)
r("Toilet_Camco", fc="#bdbdbd", ec="#424242", zorder=3)
r("Water_Pump12V", fc="#3949ab", zorder=3)
r("Propane_Locker", fc="#f3d98b", ec="#bf8f00", zorder=3)
if has("Propane_Cylinder"):
    c = B["Propane_Cylinder"]
    ax.add_patch(Circle((px((c[0] + c[1]) / 2), py((c[2] + c[3]) / 2)), (c[1] - c[0]) / 2 / IN, fill=False, ec="#616161",
                        zorder=4))
for n in sorted(B):
    if n.startswith("BedPost_") and not n.startswith("BedPost_nY_rackP2"):
        r(n, fc="#607d8b", zorder=4)
for n in sorted(B):
    if n.startswith("Trunk2_Cross_"):
        r(n, fc=C_ST, ec="#37474f", zorder=6)
r("Trunk2_Sheet", fc="#90a4ae", alpha=0.35, ec="#263238", lw=1.5, hatch="..", zorder=5)
ax.text(px(1000.0), py(-400), "1-й этаж\n(здесь — до\nпоперечин\nкровати 30″)", ha="center",
        va="center", fontsize=9.5, color="#6d4c41", zorder=7)
for n, lab in ((tk, "бак T-4320"), ("Toilet_Camco", "туалет"), ("Propane_Locker", "пропан\n20 lb")):
    if has(n):
        b = B[n]
        ax.text(px((b[0] + b[1]) / 2), py(b[3] - 80.0) if n == tk else py((b[2] + b[3]) / 2), lab, ha="center", va="center",
                fontsize=8.5, zorder=8)
ax.text(px(700), py(-870), "батареи (полка 17.85″)", ha="center", fontsize=8.5, color="white", weight="bold", zorder=8)
hdim(ax, py(y_r1) + 1.6, px(T["x_rear"]), px(T["x_deck"]), "1-й этаж: %.1f″ до края щита" % ((T["x_deck"] - T["x_rear"]) / IN))
hdim(ax, py(y_c1) - 1.8, px(T["x_rear"]), px(T["x_lock"]), "%.1f″ до локера" % ((T["x_lock"] - T["x_rear"]) / IN), fs=8)
vdim(ax, px(T["x_deck"]) - 1.5, py(y_r1), py(y_l), "%.1f″" % ((y_l - y_r1) / IN), side=-1, fs=8)
vdim(ax, px(T["x_rear"]) + 1.0, py(y_r1), py(y_c1), "%.1f″" % (T["w1"] / IN), fs=8.5)
ax.set_xlim(-2.5, 66)
ax.set_ylim(py(-yw0) - 4.5, py(yw0) + 4)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от задних дверей вперёд, дюймы")
ax.set_ylabel("поперёк, дюймы от оси (+ — водительский борт)")
ax.set_title("План под кроватью: 1-й этаж (жёлтый — свободный пол), поперечины 2-го этажа (#3 — через душ, ждёт решения)", loc="left",
             fontsize=12)

fig.suptitle("Багажник под кроватью (2026-11-08, из модели): поперечины 2-го этажа от борта до борта на язычках —\n"
             "#1 P3 ↔ стойка кровати pY rear; #3 P3f ↔ pY front (красная — через душ, ждёт решения); перфолист — позже",
             fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.965))
save(fig, "trunk_drawing.png")
