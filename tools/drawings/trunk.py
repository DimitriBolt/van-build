"""Чертёж: багажник под кроватью — 3 выдвижных ящика на направляющих SLIDEWAY и хребет посередине.
2-й этаж: передний ящик (пасс. половина) — вперёд в салон, задний (водит. половина) — назад в задние двери;
1-й этаж: ящик — назад. Дюймы. Разрезы — взгляд вперёд (водительский борт слева)."""
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Polygon, Rectangle

from _common import IN, load, save

d = load()
if "trunk" not in d:
    raise SystemExit("trunk: ящиков нет в модели — пропуск")
B, G, T = d["boxes"], d["geo"], d["TRUNK_SHELF"]["_summary"]
FF = G["floor_top"]
half = G["half"]
DR = T["drawers"]
mz = lambda Z: (Z - FF) / IN
hy = lambda Y: -Y / IN
px = lambda X: X / IN                          # от порога задних дверей (X=0)
py = lambda Y: Y / IN
C_ST, C_BAT, C_T, C_SL = "#90a4ae", "#ef6c00", "#4a90c2", "#cfd8dc"
C_F, C_R, C_1 = "#c9a27e", "#b08968", "#e0b98a"      # ящики: передний, задний, 1-го этажа
NEW = "#26a69a"
STY = [("WheelArch_", dict(fc="#bdbdbd", ec="#9e9e9e")), ("BedSideRail", dict(fc=C_ST)), ("BedCross_", dict(fc=C_ST)),
       ("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")), ("BedMattress", dict(fc="#9fb4e0", alpha=0.5, ec="#5c6bc0")),
       ("BedPost_", dict(fc=C_ST)), ("BankPost", dict(fc=C_ST)), ("BankCross", dict(fc=C_ST)),
       ("BankRail", dict(fc=C_ST, ec="#37474f")), ("BankShelf", dict(fc="#d7b98e", ec="#8d6e63")),
       ("Battery_B", dict(fc=C_BAT, ec="#bf360c", alpha=0.85)), ("WaterTank_", dict(fc=C_T, alpha=0.5, ec="#1f5f8b")),
       ("TankFloor_", dict(fc="#a1887f", ec="#5d4037")), ("Toilet_", dict(fc="#bdbdbd", ec="#424242")),
       ("Propane_", dict(fc="#f3d98b", ec="#bf8f00")), ("Water_Pump", dict(fc="#3949ab")),
       ("Trunk1_Drawer", dict(fc=C_1, alpha=0.85, ec="#8d6e63", lw=1.2)),
       ("Trunk2_TrayFwd", dict(fc=C_F, alpha=0.85, ec="#6d4c41", lw=1.2)),
       ("Trunk2_TrayRear", dict(fc=C_R, alpha=0.85, ec="#5d4037", lw=1.2)),
       ("Trunk2_Slide", dict(fc=C_SL, ec="#455a64")), ("Trunk1_Slide", dict(fc=C_SL, ec="#455a64")),
       ("Trunk2_Drv", dict(fc=C_ST, ec="#37474f")), ("Trunk2_PostP3m", dict(fc=C_ST, ec="#37474f")),
       ("Trunk2_Spine", dict(fc=NEW, ec="#00695c")), ("Trunk1_SpineRail", dict(fc=NEW, ec="#00695c")),
       ("Trunk2_P3Shim", dict(fc="#424242")), ("Trunk1_P3Shim", dict(fc="#424242")), ("Trunk2_Plate", dict(fc=C_ST))]


def vdim(ax, x, z0, z1, txt, side=1, fs=8.5):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9), zorder=9)
    ax.text(x + 0.35 * side, (z0 + z1) / 2, txt, va="center", ha="left" if side > 0 else "right", fontsize=fs, zorder=9,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.4))


def hdim(ax, z, x0, x1, txt, fs=8.5, dz=0.45):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9), zorder=9)
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs, zorder=9, bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.4))


def section(ax, S, title, notes):
    wl = [(hy(y), mz(z)) for y, z in half if z < FF + 1150]
    ax.plot([p[0] for p in wl], [p[1] for p in wl], color="#616161", lw=2)
    ax.plot([-p[0] for p in wl], [p[1] for p in wl], color="#616161", lw=2)
    ax.add_patch(Rectangle((hy(1000), -1.8), 2000 / IN, 1.8, color="#e8d9b5"))
    for pref, kw in STY:
        for n in sorted(S):
            if n.startswith(pref) and n != "x":
                for w in S[n]:
                    if len(w) > 2:
                        ax.add_patch(Polygon([(hy(p[1]), mz(p[2])) for p in w], closed=True, zorder=3, **kw))
    op = T["opening"]
    for sg in (1, -1):
        ax.axvline(hy(sg * op), color="#1565c0", ls=":", lw=1.2)
    ax.text(hy(op) + 0.3, 37.0, "проём задних\nдверей", fontsize=7.5, color="#1565c0")
    for txt, x, y in notes:
        ax.text(x, y, txt, fontsize=8.5, zorder=9, bbox=dict(fc="white", ec="#9e9e9e", alpha=0.9, pad=2))
    for k_, xd in (("rear", hy(DR["rear"]["y"][1]) - 1.0), ("floor1", hy(DR["floor1"]["y"][0]) + 1.0)):
        q = DR[k_]
        vdim(ax, xd, mz(q["z"][0]), mz(q["z"][1]), "%.1f″" % ((q["z"][1] - q["z"][0]) / IN), side=-1 if k_ == "rear" else 1)
    q = DR["fwd"]
    vdim(ax, hy(q["y"][0]) + 1.0, mz(q["z"][0]), mz(q["z"][1]), "%.1f″" % ((q["z"][1] - q["z"][0]) / IN))
    for k_ in ("rear", "fwd"):
        q = DR[k_]
        hdim(ax, mz(q["z"][1]) + 1.0, hy(q["y"][1]), hy(q["y"][0]), "%.1f″ (внутри %.1f″)" % (
            (q["y"][1] - q["y"][0]) / IN, q["inside"][1]), fs=8)
    ax.set_xlim(hy(1010), hy(-1010))
    ax.set_ylim(-3, 40)
    ax.set_aspect("equal")
    ax.grid(True, color="#f2f2f2", lw=0.6)
    ax.set_xlabel("поперёк фургона, дюймы от оси (слева — водительский борт)")
    ax.set_ylabel("от чистового пола, дюймы")
    ax.set_title(title, loc="left", fontsize=12)


fig = plt.figure(figsize=(18, 40), dpi=110)
gs = fig.add_gridspec(4, 1, height_ratios=[0.85, 0.85, 0.75, 1.05])
ax1, ax2, axe, axp = (fig.add_subplot(gs[i]) for i in range(4))
section(ax1, d["trunk"], "Разрез X=%.1f″ от задних дверей — по P3, стойке хребта 1 и стойке кровати pY rear (взгляд вперёд)"
        % px(d["trunk"]["x"]),
        [("ЗАДНИЙ ящик →\nназад (водит.)", hy(560), 25.0), ("ПЕРЕДНИЙ ящик →\nвперёд (пасс.)", hy(-280), 25.0),
         ("ящик 1-го этажа →\nназад", hy(-260), 10.0), ("ХРЕБЕТ: стойка +\nрейки + направляющие", hy(-20) + 0.5, 33.5),
         ("бак T-4320", hy(560), 10.0)])
section(ax2, d["trunk3"], "Разрез X=%.1f″ — по подвесу у борта, P3m и стойке хребта 2 (взгляд вперёд)" % px(d["trunk3"]["x"]),
        [("подвес у борта\n(над аркой)", hy(930) - 0.3, 33.5), ("ножка P3m (у B4)", hy(-560), 5.0),
         ("насос", hy(300), 6.0)])

# вид сбоку по хребту (Y≈0): стойки, рейки, направляющие; ящики закрыты (заливка) и выдвинуты (пунктир)
ax = axe
ax.add_patch(Rectangle((-48, -1.8), 152, 1.8, color="#e8d9b5"))
for n, kw in (("Trunk2_TrayFwd", dict(fc=C_F, alpha=0.8, ec="#6d4c41")),
              ("Trunk2_TrayFwd_Out", dict(fill=False, ec="#6d4c41", ls="--", lw=1.5)),
              ("Trunk2_TrayRear_Out", dict(fill=False, ec="#5d4037", ls="--", lw=1.5)),
              ("Trunk1_Drawer", dict(fc=C_1, alpha=0.8, ec="#8d6e63")),
              ("Trunk1_Drawer_Out", dict(fill=False, ec="#8d6e63", ls="--", lw=1.5)),
              ("Propane_Locker", dict(fc="#f3d98b", alpha=0.6)), ("Shower_Pan", dict(fc="#e0e0e0", ec="#9e9e9e")),
              ("Shower_WallRear", dict(fc="#b0bec5")), ("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")),
              ("Trunk2_SpineRail_P", dict(fc=NEW, ec="#00695c")), ("Trunk1_SpineRail", dict(fc=NEW, ec="#00695c")),
              ("Trunk2_SlideSpineP", dict(fc=C_SL, ec="#455a64", alpha=0.9)),
              ("Trunk1_SlideSpine", dict(fc=C_SL, ec="#455a64", alpha=0.9)),
              ("Trunk2_SpinePost_1", dict(fc=NEW, ec="#00695c")), ("Trunk2_SpinePost_2", dict(fc=NEW, ec="#00695c"))):
    if n in B:
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, zorder=3, **kw))
for n in sorted(B):
    if n.startswith("BedCross_"):
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, fc=C_ST, zorder=4))
ax.axvline(px(0.0), color="#1565c0", lw=2)
ax.text(px(0.0) - 0.4, 36, "задние\nдвери", ha="right", fontsize=9, color="#1565c0")
ax.axvline(px(T["x_deck"]), color="#8d6e63", ls="-.", lw=1.2)
ax.text(px(T["x_deck"]) + 0.3, 36, "край щита", fontsize=8.5, color="#8d6e63")
qf, qr, q1 = DR["fwd"], DR["rear"], DR["floor1"]
hdim(ax, mz(qf["z"][1]) + 1.2, px(qf["x"][1]), px(qf["x"][1] + qf["out"]), "передний: вперёд %.0f″" % (qf["out"] / IN))
hdim(ax, mz(qr["z"][1]) + 1.2, px(qr["x"][0] + qr["out"]), px(qr["x"][0]), "задний: назад %.0f″" % (-qr["out"] / IN))
hdim(ax, mz(q1["z"][1]) - 3.0, px(q1["x"][0] + q1["out"]), px(q1["x"][0]), "1-й этаж: назад %.0f″" % (-q1["out"] / IN))
ld = T["locker_door"]
ax.annotate("дверца локера\n(должна открываться)", xy=(px((ld[0] + ld[1]) / 2), 9), xytext=(px(ld[1]) + 3, 4),
            fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8), zorder=9)
ax.set_xlim(-48, 100)
ax.set_ylim(-3, 40)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от задних дверей вперёд, дюймы")
ax.set_ylabel("от пола, дюймы")
ax.set_title("Вид сбоку по хребту (с пассажирской стороны): зелёное — хребет; ящики закрыты (заливка) и выдвинуты (пунктир)",
             loc="left", fontsize=12)

# план
ax = axp


def r(n, **kw):
    if n in B:
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), py(b[2])), (b[1] - b[0]) / IN, (b[3] - b[2]) / IN, **kw))


yw0 = G["arch_ywall"]
ax.add_patch(Rectangle((-48, py(yw0)), 152, 1.5, color="#cfcfcf"))
ax.add_patch(Rectangle((-48, py(-yw0) - 1.5), 152, 1.5, color="#cfcfcf"))
ax.axvline(px(0.0), color="#1565c0", lw=2)
r("BedDeck", fill=False, ec="#8d6e63", ls="--", lw=1.2)
for n in ("WheelArch_pY", "WheelArch_nY"):
    r(n, fc="#e0e0e0", ec="#9e9e9e")
for n in sorted(B):
    if n.startswith(("Battery_B", "BankShelf", "BankRail", "BankPost")):
        r(n, fc=C_BAT if n.startswith("Battery") else C_ST, alpha=0.8, zorder=3)
r("Shower_Pan", fc="#eceff1", ec="#90a4ae", zorder=2)
r("Kitchen_Carcass", fc="#f3e0c8", ec="#a1887f", zorder=2)
r("WaterTank_T4320", fc=C_T, alpha=0.45, zorder=3)
r("Toilet_Camco", fc="#bdbdbd", ec="#424242", zorder=3)
r("Water_Pump12V", fc="#3949ab", zorder=3)
r("Propane_Locker", fc="#f3d98b", ec="#bf8f00", zorder=3)
r("Propane_LockerDoor", fc="#bf8f00", zorder=4)
ax.add_patch(Arc((px(ld[0]), py(ld[2])), 2 * (ld[1] - ld[0]) / IN, 2 * (ld[1] - ld[0]) / IN, theta1=270, theta2=360,
                 color="#bf8f00", ls="--", lw=1.2, zorder=4))
for n in sorted(B):
    if n.startswith("BedPost_"):
        r(n, fc="#607d8b", zorder=4)
r("Trunk1_Drawer", fc=C_1, alpha=0.55, ec="#8d6e63", zorder=5)
r("Trunk1_Drawer_Out", fill=False, ec="#8d6e63", ls=":", lw=1.6, zorder=5)
r("Trunk2_TrayFwd", fill=False, ec="#6d4c41", lw=2.0, zorder=6)
r("Trunk2_TrayFwd_Out", fill=False, ec="#6d4c41", ls="--", lw=1.6, zorder=6)
r("Trunk2_TrayRear", fill=False, ec="#4e342e", lw=2.0, zorder=6)
r("Trunk2_TrayRear_Out", fill=False, ec="#4e342e", ls="--", lw=1.6, zorder=6)
for n in sorted(B):
    if n.startswith(("Trunk2_Slide", "Trunk1_Slide")) and not n.endswith("_Out"):
        r(n, fc=C_SL, ec="#455a64", zorder=7)
    if n.startswith(("Trunk2_Spine", "Trunk1_SpineRail")) and "Bolt" not in n:
        r(n, fc=NEW, ec="#00695c", zorder=8)
    if n.startswith(("Trunk2_Drv", "Trunk2_PostP3m")):
        r(n, fc=C_ST, ec="#37474f", zorder=8)
lab = dict(ha="center", fontsize=10, weight="bold", zorder=9)
ax.text(px(sum(qr["x"]) / 2), py(sum(qr["y"]) / 2) + 3, "ЗАДНИЙ ящик 2-го эт.\n%.0f × %.1f″ → назад %.0f″" % (
    (qr["x"][1] - qr["x"][0]) / IN, (qr["y"][1] - qr["y"][0]) / IN, -qr["out"] / IN), color="#4e342e", **lab)
ax.text(px(sum(qf["x"]) / 2) + 6, py(sum(qf["y"]) / 2) + 2.5, "ПЕРЕДНИЙ ящик 2-го эт.\n%.1f × %.1f″ → вперёд %.0f″" % (
    (qf["x"][1] - qf["x"][0]) / IN, (qf["y"][1] - qf["y"][0]) / IN, qf["out"] / IN), color="#6d4c41", **lab)
ax.text(px(sum(q1["x"]) / 2), py(sum(q1["y"]) / 2) - 4.5, "ящик 1-го эт. %.0f × %.1f″\n→ назад %.0f″" % (
    (q1["x"][1] - q1["x"][0]) / IN, (q1["y"][1] - q1["y"][0]) / IN, -q1["out"] / IN), ha="center", fontsize=9.5,
    color="#795548", zorder=9)
bo = B["Trunk2_TrayFwd_Out"]
ax.text(px((bo[0] + bo[1]) / 2) + 8, py(sum(qf["y"]) / 2), "передний —\nвыдвинут в салон", ha="center", fontsize=9.5,
        color="#6d4c41", zorder=9)
ax.text(px(-560), py(sum(qr["y"]) / 2), "задний —\nвыдвинут", ha="center", fontsize=9.5, color="#4e342e", zorder=9)
ax.text(px(B["Shower_Pan"][0]) + 1, py(B["Shower_Pan"][3]) - 3, "душ", fontsize=10, color="#607d8b", zorder=9)
ax.text(px(B["Kitchen_Carcass"][0]) + 1, py(B["Kitchen_Carcass"][3]) - 3, "кухня", fontsize=10, color="#8d6e63", zorder=9)
ax.text(px(T["posts_x"][1]) + 1.2, py(T["y_spine"][1]) + 0.6, "хребет", fontsize=9, color="#00695c", zorder=9)
ax.axvline(px(T["x_deck"]), color="#8d6e63", ls="-.", lw=1.2)
ax.text(px(T["x_deck"]) + 0.3, py(-yw0) + 0.8, "край щита", fontsize=8, color="#8d6e63")
ax.set_xlim(-48, 100)
ax.set_ylim(py(-yw0) - 4, py(yw0) + 4)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от задних дверей вперёд, дюймы")
ax.set_ylabel("поперёк, дюймы от оси (+ — водительский борт)")
ax.set_title("План: ящики закрыты (сплошная) и выдвинуты (пунктир); зелёное — хребет; дуга — открывание дверцы локера",
             loc="left", fontsize=12)

fig.suptitle("Багажник под кроватью (2026-11-08, из модели): 3 ящика на SLIDEWAY 500 lb — 2-й этаж: передний → в салон, "
             "задний → в задние двери;\n1-й этаж → в задние двери; хребет посередине: 2 стойки (упираются в поперечины "
             "кровати #1 и #2) + рейки", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.975))
save(fig, "trunk_drawing.png")
