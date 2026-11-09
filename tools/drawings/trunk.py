"""Чертёж: багажник под кроватью — 1-й этаж (ящик на колёсиках по полу) и 2-й этаж (выдвижной поддон на
направляющих SLIDEWAY 44″ Full Extension). Дюймы. Разрезы — взгляд вперёд (водительский борт слева)."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

from _common import IN, load, save

d = load()
if "trunk" not in d:
    raise SystemExit("trunk: поддона нет в модели — пропуск")
B, G, T = d["boxes"], d["geo"], d["TRUNK_SHELF"]["_summary"]
FF = G["floor_top"]
half = G["half"]
mz = lambda Z: (Z - FF) / IN
hy = lambda Y: -Y / IN
px = lambda X: X / IN                          # от порога задних дверей (X=0)
py = lambda Y: Y / IN
C_ST, C_BAT, C_T, C_TRAY, C_BOX, C_SL = "#90a4ae", "#ef6c00", "#4a90c2", "#c9a27e", "#d4a373", "#cfd8dc"
NEW = "#26a69a"
STY = [("WheelArch_", dict(fc="#bdbdbd", ec="#9e9e9e")), ("BedSideRail", dict(fc=C_ST)), ("BedCross_", dict(fc=C_ST)),
       ("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")), ("BedMattress", dict(fc="#9fb4e0", alpha=0.5, ec="#5c6bc0")),
       ("BedPost_", dict(fc=C_ST)), ("BankPost", dict(fc=C_ST)), ("BankCross", dict(fc=C_ST)),
       ("BankRail", dict(fc=C_ST, ec="#37474f")), ("BankShelf", dict(fc="#d7b98e", ec="#8d6e63")),
       ("Battery_B", dict(fc=C_BAT, ec="#bf360c", alpha=0.85)), ("WaterTank_", dict(fc=C_T, alpha=0.5, ec="#1f5f8b")),
       ("TankFloor_", dict(fc="#a1887f", ec="#5d4037")), ("Toilet_", dict(fc="#bdbdbd", ec="#424242")),
       ("Propane_", dict(fc="#f3d98b", ec="#bf8f00")), ("Water_Pump", dict(fc="#3949ab")),
       ("Trunk1_Box", dict(fc=C_BOX, alpha=0.8, ec="#8d6e63", lw=1.2)), ("Trunk1_Caster", dict(fc="#212121")),
       ("Trunk2_Tray", dict(fc=C_TRAY, alpha=0.85, ec="#6d4c41", lw=1.2)), ("Trunk2_Slide", dict(fc=C_SL, ec="#455a64")),
       ("Trunk2_Drv", dict(fc=NEW, ec="#00695c")), ("Trunk2_PostP3m", dict(fc=NEW, ec="#00695c")),
       ("Trunk2_P3Shim", dict(fc="#424242")), ("Trunk2_Plate", dict(fc=C_ST))]


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
    ax.text(hy(op) + 0.3, 36.5, "проём задних\nдверей", fontsize=7.5, color="#1565c0")
    for txt, x, y in notes:
        ax.text(x, y, txt, fontsize=8.5, zorder=9, bbox=dict(fc="white", ec="#9e9e9e", alpha=0.9, pad=2))
    tr = T["tray"]
    vdim(ax, hy(tr["y"][1]) - 1.0, mz(tr["z"][0]), mz(tr["z"][1]), "%.1f″" % ((tr["z"][1] - tr["z"][0]) / IN), side=-1)
    vdim(ax, hy(tr["y"][1]) - 1.0, 0, mz(tr["z"][0]), "%.1f″" % mz(tr["z"][0]), side=-1)
    hdim(ax, mz(tr["z"][1]) + 1.0, hy(tr["y"][1]), hy(tr["y"][0]), "поддон %.1f″ (внутри %.1f″)" % (
        (tr["y"][1] - tr["y"][0]) / IN, tr["width_in"]))
    ax.set_xlim(hy(1010), hy(-1010))
    ax.set_ylim(-3, 40)
    ax.set_aspect("equal")
    ax.grid(True, color="#f2f2f2", lw=0.6)
    ax.set_xlabel("поперёк фургона, дюймы от оси (слева — водительский борт)")
    ax.set_ylabel("от чистового пола, дюймы")
    ax.set_title(title, loc="left", fontsize=12)


fig = plt.figure(figsize=(18, 34), dpi=110)
gs = fig.add_gridspec(4, 1, height_ratios=[0.9, 0.9, 0.75, 1.0])
ax1, ax2, axe, axp = (fig.add_subplot(gs[i]) for i in range(4))
section(ax1, d["trunk"], "Разрез X=%.1f″ от задних дверей — по P3 и стойке кровати pY rear (взгляд вперёд)" % px(377.3),
        [("поперечина 1 рейки над баком →\nстойка кровати", hy(850) - 2, 25.5),
         ("водительская направляющая\nна рейке над баком", hy(700) - 3, 12.0),
         ("пассажирская направляющая\nна P3 (проставка 4 мм)", hy(-700) - 9, 12.0)])
section(ax2, d["trunk3"], "Разрез X=%.1f″ — по подвесу у борта и P3m (взгляд вперёд)" % px(T["x_hanger"]),
        [("подвес у борта: от продольной\nрейки кровати вниз (над аркой)", hy(900) - 1, 34.0),
         ("ножка P3m (у B4)", hy(-650) - 6, 9.0), ("ящик 1-го этажа\n(выкачен вперёд — пунктир на плане)", hy(0) - 5, 5.0)])

# вид сбоку вдоль водительского борта: поддон задвинут / выдвинут
ax = axe
ax.add_patch(Rectangle((-48, -1.8), 110, 1.8, color="#e8d9b5"))
for n, kw in (("Trunk2_Tray", dict(fc=C_TRAY, alpha=0.85, ec="#6d4c41")),
              ("Trunk2_Tray_Out", dict(fill=False, ec="#6d4c41", ls="--", lw=1.5)),
              ("Trunk2_SlideDrv", dict(fc=C_SL, ec="#455a64")), ("Trunk2_DrvRail", dict(fc=NEW, ec="#00695c")),
              ("Trunk2_DrvHanger", dict(fc=NEW, ec="#00695c")), ("Trunk2_DrvCross_1", dict(fc=NEW)),
              ("Trunk2_DrvCross_2", dict(fc=NEW)), ("BedPost_pY_rear", dict(fc=C_ST, alpha=0.6)),
              ("BedSideRail_pY", dict(fc=C_ST)), ("BedDeck", dict(fc="#d7ccc8", ec="#8d6e63")),
              ("WaterTank_T4320", dict(fc=C_T, alpha=0.4)), ("Toilet_Camco", dict(fc="#bdbdbd")),
              ("Propane_Locker", dict(fc="#f3d98b")), ("Trunk1_Box", dict(fc=C_BOX, alpha=0.7)),
              ("Trunk1_Box_Front", dict(fill=False, ec="#8d6e63", ls="--"))):
    if n in B:
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, zorder=3, **kw))
for n in sorted(B):
    if n.startswith("BedCross_"):
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), mz(b[4])), (b[1] - b[0]) / IN, (b[5] - b[4]) / IN, fc=C_ST, zorder=3))
ax.axvline(px(0.0), color="#1565c0", lw=2)
ax.text(px(0.0) - 0.4, 34, "задние\nдвери", ha="right", fontsize=9, color="#1565c0")
ax.axvline(px(T["x_deck"]), color="#8d6e63", ls="-.", lw=1.2)
ax.text(px(T["x_deck"]) + 0.3, 34, "край щита", fontsize=8.5, color="#8d6e63")
tr = T["tray"]
hdim(ax, mz(tr["z"][1]) + 1.2, px(tr["x"][0] - tr["out"]), px(tr["x"][0]), "выдвинут целиком: %.0f″" % (tr["out"] / IN))
hdim(ax, mz(tr["z"][1]) + 1.2, px(tr["x"][0]), px(tr["x"][1]), "задвинут: %.0f″" % ((tr["x"][1] - tr["x"][0]) / IN))
q = T["boxes"].get("floor1")
if q:
    hdim(ax, 0.8 + mz(q["h_total"] + FF) / 2, px(q["x"][0]), px(q["x_front"][1]), "ящик 1-го эт.: ход %.1f″" % (q["travel"] / IN),
         fs=8)
ax.set_xlim(-48, 62)
ax.set_ylim(-3, 38)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от задних дверей вперёд, дюймы")
ax.set_ylabel("от пола, дюймы")
ax.set_title("Вид сбоку вдоль водительского борта: поддон задвинут (заливка) и выдвинут назад (пунктир)", loc="left",
             fontsize=12)

# план
ax = axp


def r(n, **kw):
    if n in B:
        b = B[n]
        ax.add_patch(Rectangle((px(b[0]), py(b[2])), (b[1] - b[0]) / IN, (b[3] - b[2]) / IN, **kw))


yw0 = G["arch_ywall"]
ax.add_patch(Rectangle((-48, py(yw0)), 110, 1.5, color="#cfcfcf"))
ax.add_patch(Rectangle((-48, py(-yw0) - 1.5), 110, 1.5, color="#cfcfcf"))
ax.axvline(px(0.0), color="#1565c0", lw=2)
r("BedDeck", fill=False, ec="#8d6e63", ls="--", lw=1.2)
for n in ("WheelArch_pY", "WheelArch_nY"):
    r(n, fc="#e0e0e0", ec="#9e9e9e")
for n in sorted(B):
    if n.startswith(("Battery_B", "BankShelf", "BankRail", "BankPost")):
        r(n, fc=C_BAT if n.startswith("Battery") else C_ST, alpha=0.8, zorder=3)
r("WaterTank_T4320", fc=C_T, alpha=0.45, zorder=3)
r("Toilet_Camco", fc="#bdbdbd", ec="#424242", zorder=3)
r("Water_Pump12V", fc="#3949ab", zorder=3)
r("Propane_Locker", fc="#f3d98b", ec="#bf8f00", zorder=3)
for n in sorted(B):
    if n.startswith("BedPost_"):
        r(n, fc="#607d8b", zorder=4)
r("Trunk1_Box", fc=C_BOX, alpha=0.6, ec="#8d6e63", zorder=5)
r("Trunk1_Box_Front", fill=False, ec="#8d6e63", ls="--", lw=1.4, zorder=5)
r("Trunk2_Tray", fill=False, ec="#6d4c41", lw=2.0, zorder=6)
r("Trunk2_Tray_Out", fill=False, ec="#6d4c41", ls="--", lw=1.6, zorder=6)
for n in ("Trunk2_SlidePass", "Trunk2_SlideDrv"):
    r(n, fc=C_SL, ec="#455a64", zorder=7)
for n in sorted(B):
    if n.startswith(("Trunk2_Drv", "Trunk2_PostP3m")):
        r(n, fc=NEW, ec="#00695c", zorder=8)
tb_ = B["Trunk2_Tray"]
ax.text(px((tb_[0] + tb_[1]) / 2), py(250), "ПОДДОН 2-го этажа\n(задвинут)", ha="center", fontsize=10.5, weight="bold",
        color="#4e342e", zorder=9)
tbo = B["Trunk2_Tray_Out"]
ax.text(px((tbo[0] + tbo[1]) / 2), py(0), "выдвинут целиком\nв задние двери", ha="center", fontsize=10, color="#4e342e",
        zorder=9)
b1 = B["Trunk1_Box"]
ax.text(px((b1[0] + b1[1]) / 2), py(b1[2]) + 2.5, "ящик 1-го эт.", ha="center", fontsize=9, zorder=9, color="#5d4037")
ax.axvline(px(T["x_deck"]), color="#8d6e63", ls="-.", lw=1.2)
ax.text(px(T["x_deck"]) + 0.3, py(yw0) - 3, "край щита", fontsize=8, color="#8d6e63")
ax.text(px(T["x_hanger"]) + 1.0, py(yw0) - 2.2, "подвес у борта", fontsize=8.5, color="#00695c", zorder=9)
ax.set_xlim(-48, 62)
ax.set_ylim(py(-yw0) - 4, py(yw0) + 4)
ax.set_aspect("equal")
ax.grid(True, color="#f2f2f2", lw=0.6)
ax.set_xlabel("от задних дверей вперёд, дюймы")
ax.set_ylabel("поперёк, дюймы от оси (+ — водительский борт)")
ax.set_title("План: поддон 2-го этажа (сплошной — задвинут, пунктир — выдвинут), ящик 1-го этажа; зелёное — новые детали",
             loc="left", fontsize=12)

fig.suptitle("Багажник под кроватью (2026-11-08, из модели): 2-й этаж — выдвижной поддон на SLIDEWAY 500 lb 44″ Full "
             "Extension,\nбез стоек посередине и без поперечин борт-борт; 1-й этаж — ящик на колёсиках по полу", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.97))
save(fig, "trunk_drawing.png")
