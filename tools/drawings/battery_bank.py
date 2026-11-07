"""Этажерка на 4 батареи по пассажирскому борту + электрика рядом (проект 2026-11-07).
B1 — на полу в углу «короб D-стойки ↔ арка»; полка-«лестница» сразу над аркой несёт B2 (над B1), B3, B4;
перед B4 — панель на борту с MPPT, DC-DC и предохранителями, на полке — шины + и −; трассы кабелей.
Дюймы: x — вдоль борта от передней грани короба D-стойки (вперёд — вправо), y — от стены у пола в салон,
z — от чистового пола. Все числа — из модели (docs/drawing_data.json)."""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

from _common import IN, load, arch_profile, save

d = load()
G, W, R, DP, EL = d["geo"], d["WHEEL_ARCH"], d["BATTERY_RACK"], d["DPILLAR"], d["ELECTRICAL"]
FF, XDP, YW = G["floor_top"], G["x_dp"], G["arch_ywall"]
B = d["boxes"]
mx = lambda X: (X - XDP) / IN
my = lambda Y: (YW - abs(Y)) / IN
mz = lambda Z: (Z - FF) / IN


def xr_(n):
    return mx(B[n][0]), mx(B[n][1])


def yr(n):                                   # от стены у пола, деталь на −Y
    a, c = (YW + B[n][2]) / IN, (YW + B[n][3]) / IN
    return min(a, c), max(a, c)


def zr(n):
    return mz(B[n][4]), mz(B[n][5])


def rect_xy(ax, n, **kw):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **kw))


def rect_xz(ax, n, **kw):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, **kw))


C_S, C_BAT, C_ARCH, C_PLY, C_DECK = "#607d8b", "#ef6c00", "#9e9e9e", "#d7b98e", "#d7ccc8"
BATS = ["Battery_B%d" % i for i in range(1, 5) if "Battery_B%d" % i in B]
SHELF_BATS = BATS[1:]
CROSS = [n for n in ("BedCross_1", "BedCross_2", "BedCross_3") if n in B]
POSTS_W = ("BedPost_nY_rear", "BedPost_nY_front")
POSTS_I = ("BankPost_P3", "BankPost_P3f")
DOOR = mx(B["Opening_SlidingDoor"][0])
DECK1 = mx(B["BedDeck"][1])
ROUTES = EL.get("_routes", {})
C_RT = {"batteries": "#c62828", "alternator": "#ef6c00", "solar": "#1565c0", "ground": "#2e7d32"}
LAB_RT = {"batteries": "жгут от батарей (вдоль борта)", "alternator": "от генератора (по полу из-под порога)",
          "solar": "от солнечных панелей (с крыши)", "ground": "масса → C-стойка"}
EL_BOX = {"Elec_Board": ("#d7b98e", "панель (фанера)"), "Elec_MPPT": ("#212121", "MPPT"),
          "Elec_DCDC": ("#455a64", "DC-DC\n60 A"), "Elec_FuseBlock": ("#f9a825", "предохр."),
          "Elec_BusPos": ("#c62828", "шина +"), "Elec_BusNeg": ("#212121", "шина −")}
XL, XR = -7, DOOR + 2.5

fig, (axt, axe) = plt.subplots(2, 1, figsize=(17.5, 16.5), dpi=140,
                               gridspec_kw=dict(height_ratios=[17.0 + 3.9, 34.5 + FF / IN]))

# ───────── ВИД СВЕРХУ ─────────
ax = axt
ax.add_patch(Rectangle((XL, -1.2), XR - XL, 1.2, color="#cfcfcf"))
ax.text(XL + 0.4, -0.6, "борт", va="center", fontsize=9)
for w in d["corners"]["nY"]["dpillar"]:
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
for w in d["corners"]["nY"]["arch"]:
    ax.add_patch(Polygon([(mx(x), (YW + y) / IN) for x, y in w], color=C_ARCH, alpha=0.5))
ax.text(mx(W["center_x"]) - 12, 12.3, "колёсная арка (у пола) — под полкой", ha="center", fontsize=9, color="#616161")
for n in CROSS:
    x0, x1 = xr_(n)
    ax.add_patch(Rectangle((x0, -1.2), x1 - x0, 18.0, fill=False, ec="#263238", ls="-.", lw=0.9))
    ax.text((x0 + x1) / 2, 16.2, n.replace("BedCross_", "#"), ha="center", fontsize=7.5, color="#263238")
ax.text(mx(B["BedCross_1"][0]) - 0.3, 15.2, "поперечины кровати (над этажеркой):", ha="right", fontsize=7.5,
        color="#263238")
for xx, lab, col in ((DECK1, "передний край\nщита кровати", "#6d4c41"), (DOOR, "край проёма\nсдвижной двери", "#212121")):
    ax.plot([xx, xx], [-1.2, 16.8], color=col, ls="--", lw=1.2)
    ax.text(xx + 0.2, 13.6, lab, fontsize=8, color=col)
rect_xy(ax, "BankShelf", fc=C_PLY, alpha=0.30, ec="#a1887f")
for n in ("BankRail_Wall", "BankRail_Inner") + tuple(k for k in B if k.startswith("BankCross_")):
    rect_xy(ax, n, fc=C_S, alpha=0.8)
for n in [k for k in B if k.startswith("BankPostPlate_")] + ["BedPostPlate_nY_rear", "BedPostPlate_nY_front"]:
    rect_xy(ax, n, fill=False, ec="#90a4ae", ls=":", lw=0.8)
for n in SHELF_BATS:
    rect_xy(ax, n, fc=C_BAT, alpha=0.35, ec=C_BAT, lw=2)
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    for xc, col in ((x0 + 1.1, "#c62828"), (x1 - 1.1, "#212121")):    # клеммы — по краю длинной стороны, к борту
        ax.add_patch(Circle((xc, y0 + 0.9), 0.45, fc=col, zorder=6))
rect_xy(ax, "BankWedge_B1Arch", fc="#a0703c", ec="#5d4037")
for n in POSTS_W + POSTS_I:
    rect_xy(ax, n, color="#37474f", zorder=5)
for n, lab in (("BedPost_nY_rear", "P1 (стойка\nкровати)"), ("BedPost_nY_front", "Pf (передняя\nстойка кровати)")):
    (x0, x1) = xr_(n)
    ax.text((x0 + x1) / 2, -3.3, lab, ha="center", fontsize=8, color="#263238")
for n, lab in (("BankPost_P3", "P3"), ("BankPost_P3f", "P3f")):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.text((x0 + x1) / 2, y1 + 0.35, lab, ha="center", fontsize=8, color="#263238", weight="bold")
for i, n in enumerate(SHELF_BATS):
    (x0, x1), (y0, y1) = xr_(n), yr(n)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.3, "B%d%s" % (i + 2, "\n(под ней B1)" if i == 0 else ""), ha="center",
            va="center", fontsize=9, color="#e65100", weight="bold")
for n, (col, lab) in EL_BOX.items():
    if n in B:
        rect_xy(ax, n, fc=col, alpha=0.85 if n != "Elec_Board" else 0.6, ec="#424242", zorder=6)
        (x0, x1), (y0, y1) = xr_(n), yr(n)
        if n in ("Elec_BusPos", "Elec_BusNeg"):
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, lab, ha="center", va="center", fontsize=7.5, color="white", zorder=7)
ax.text(xr_("Elec_MPPT")[0], yr("Elec_MPPT")[1] + 0.35, "на борту: MPPT, DC-DC, предохранители", fontsize=7.5)
for k, pts in ROUTES.items():
    ax.plot([mx(p[0]) for p in pts], [my(p[1]) for p in pts], color=C_RT[k], lw=2.0, zorder=8,
            label=LAB_RT[k])
gx, gy, gz = EL["_ground"]
ax.plot(mx(gx), my(gy), "o", ms=9, color="#2e7d32", zorder=9)
ax.text(mx(gx) - 0.3, my(gy) + 1.0, "масса:\nC-стойка", ha="right", fontsize=7.5, color="#2e7d32")
yl = yr(SHELF_BATS[0])[1]
ax.plot([XL, DOOR], [yl, yl], color="#e65100", ls=":", lw=0.8)
ax.text(mx(W["center_x"]) - 6, yl + 1.45, "все 4 батареи — в полосе %.1f″ от стены (арка — %.1f″); клеммы — к борту" % (
    yl, W["protrusion"] / IN), ha="center", fontsize=8, color="#e65100")
ax.legend(loc="upper left", bbox_to_anchor=(0.42, 0.995), fontsize=7.5, framealpha=0.92, title="кабели",
          title_fontsize=8)
ax.set_xlim(XL, XR)
ax.set_ylim(-4.0, 17.3)
ax.set_aspect("equal")
ax.set_ylabel("от стены (у пола) в салон, дюймы")
ax.set_title("Вид сверху (щит и матрас не показаны; ● — клеммы батарей)", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)

# ───────── ВИД НА БОРТ ИЗНУТРИ ─────────
ax = axe
zs = -FF / IN
ax.add_patch(Rectangle((XL, zs), XR - XL, -zs - 0.47, color="#f8bbd0"))
ax.add_patch(Rectangle((XL, -0.47), XR - XL, 0.47, color=C_PLY))
ax.add_patch(Rectangle((XL, zs), -XL, DP["box_h"] / IN - zs, fc="#e0e0e0", ec="#9e9e9e", hatch="///"))
ax.text(XL + 0.3, DP["box_h"] / IN + 0.4, "короб D-стойки", fontsize=7.5, color="#616161")
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "wall")], color="#cfcfcf"))
ax.add_patch(Polygon([(mx(x), mz(z)) for x, z in arch_profile(d, "inner")], color=C_ARCH))
ax.text(mx(W["center_x"]), 5.5, "арка: верх %.2f″ над фанерой\n(по фото 2026-11-07)" % (W["height"] / IN), ha="center",
        color="white", fontsize=10)
ax.add_patch(Rectangle((DOOR, zs), 0.9, 35, color="#212121"))
ax.text(DOOR + 0.45, 17, "проём сдвижной двери", rotation=90, ha="center", va="center", color="white", fontsize=8)
ax.text(DOOR - 0.3, 30.5, "C-стойка", ha="right", fontsize=8, color="#2e7d32")
rect_xz(ax, "BedSideRail_nY", color=C_S, alpha=0.55)
rect_xz(ax, "BedDeck", color=C_DECK, ec="#8d6e63")
for n in CROSS:
    rect_xz(ax, n, color="#263238")
ax.text(mx(B["BedDeck"][0]) + 0.3, zr("BedDeck")[1] + 0.35, "щит кровати (в модели поднят на %.0f″)" % (
    d["BED"]["rail_raise"] / IN), fontsize=8, color="#6d4c41")
for n in POSTS_W:
    rect_xz(ax, n, color="#90a4ae", zorder=1)
for n in POSTS_I:
    rect_xz(ax, n, fc="none", ec="#263238", lw=1.1, ls="--", zorder=4)
for n in ("BankRail_Wall",) + tuple(k for k in B if k.startswith("BankCross_")):
    rect_xz(ax, n, color=C_S, alpha=0.9, zorder=3)
rect_xz(ax, "BankShelf", color=C_PLY, zorder=3)
for n in [k for k in B if k.startswith("BankArchPad_")]:
    rect_xz(ax, n, color="#212121", zorder=4)
for n in BATS:
    rect_xz(ax, n, fc=C_BAT, ec="#bf360c", zorder=2)
for n in [k for k in B if k.startswith("BankStop_")] + ["BankHolddown_B1"]:
    rect_xz(ax, n, color="#37474f", zorder=5)
rect_xz(ax, "BankWedge_B1Arch", fc="#a0703c", ec="#5d4037", zorder=5)
for i, n in enumerate(BATS):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.text((x0 + x1) / 2, (z0 + z1) / 2, "B%d" % (i + 1), ha="center", va="center", fontsize=11, color="white",
            weight="bold", zorder=6)
    for xc, col in ((x0 + 1.1, "#c62828"), (x1 - 1.1, "#212121")):
        ax.add_patch(Rectangle((xc - 0.35, z1), 0.7, 0.45, color=col, zorder=6))
for n, (col, lab) in EL_BOX.items():
    if n in B:
        rect_xz(ax, n, fc=col, ec="#424242", alpha=0.95 if n != "Elec_Board" else 0.55, zorder=5 if n != "Elec_Board" else 2)
        (x0, x1), (z0, z1) = xr_(n), zr(n)
        if n != "Elec_Board":
            ax.text((x0 + x1) / 2, (z0 + z1) / 2, lab, ha="center", va="center", fontsize=7.5,
                    color="black" if n == "Elec_FuseBlock" else "white", zorder=6)
for k, pts in ROUTES.items():
    ax.plot([mx(p[0]) for p in pts], [mz(p[2]) for p in pts], color=C_RT[k], lw=2.0, zorder=8)
ax.plot(mx(gx), mz(gz), "o", ms=9, color="#2e7d32", zorder=9)
ax.annotate("масса: болт на C-стойке\n(зачистить до металла)", xy=(mx(gx), mz(gz)), xytext=(mx(gx) - 9.5, mz(gz) - 5.0),
            fontsize=7.5, color="#2e7d32", arrowprops=dict(arrowstyle="-", lw=0.7, color="#2e7d32"))
sol = ROUTES.get("solar")
if sol:
    ax.annotate("с крыши", xy=(mx(sol[0][0]), 33.8), xytext=(mx(sol[0][0]) + 1.0, 33.0), fontsize=7.5, color="#1565c0")
alt = ROUTES.get("alternator")
if alt:
    ax.text(mx(alt[0][0]) - 0.3, mz(alt[0][2]) + 0.6, "из-под порога сдвижной двери", ha="right", fontsize=7.5,
            color="#ef6c00")


def vdim(x, z0, z1, txt, fs=8, color="black"):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=color))
    ax.text(x + 0.25, (z0 + z1) / 2, txt, va="center", fontsize=fs, color=color)


def hdim(z, x0, x1, txt, fs=8, dz=0.35):
    ax.annotate("", xy=(x0, z), xytext=(x1, z), arrowprops=dict(arrowstyle="<->", lw=0.9))
    ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=fs)


zt_arch = W["height"] / IN
zs1 = zr("BankShelf")[1]
zb_top = zr(SHELF_BATS[0])[1]
zc_b = zr("BedCross_2")[0]
xm = xr_("Battery_B3")[0] + 1.0
vdim(xm, 0, zt_arch, "верх арки %.2f″" % zt_arch)
vdim(xm + 4.0, 0, zs1, "полка %.1f″" % zs1)
vdim(xr_("Battery_B4")[1] + 0.45, zs1, zb_top, "")
ax.text((xr_("Battery_B4")[0] + xr_("Battery_B4")[1]) / 2, zs1 + 2.2, "верх батарей %.1f″" % zb_top, ha="center",
        fontsize=8, color="white", zorder=7)
vdim(xr_("Battery_B4")[1] - 0.6, zb_top, zc_b, "", color="#1565c0")
ax.text(xr_("Battery_B4")[1] - 0.4, zc_b + 1.8, "%.1f″ (%.0f) до поперечин" % (zc_b - zb_top, (zc_b - zb_top) * IN),
        fontsize=7.5, color="#1565c0", ha="right")
hdim(zr("BankRail_Wall")[0] - 1.1, *xr_("BankRail_Wall"),
     "рейка у борта %.1f″ (%.0f): между стойками кровати P1 ↔ Pf, посередине — на верх арки через резину %.0f мм" % (
         (B["BankRail_Wall"][1] - B["BankRail_Wall"][0]) / IN, B["BankRail_Wall"][1] - B["BankRail_Wall"][0],
         R["bank"]["pad"]), fs=7.5, dz=-0.95)
for n in SHELF_BATS:
    hdim(zb_top + 0.9, *xr_(n), "10.07″", fs=7.5)
ax.annotate("прижимная планка над B1", xy=(mx(B["BankHolddown_B1"][1]), zr("BankHolddown_B1")[1]),
            xytext=(-6.6, 13.0), fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.annotate("клин в арку", xy=(xr_("BankWedge_B1Arch")[1], zr("BankWedge_B1Arch")[1]), xytext=(17.0, 12.0),
            fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.text(mx(B["BankPost_P3f"][0]) - 0.2, zr("BankPost_P3f")[1] - 3.0, "P3, P3f — пунктир\n(со стороны прохода)",
        fontsize=7.5, ha="right")
for n, lab in (("BedPost_nY_rear", "P1"), ("BedPost_nY_front", "Pf")):
    (x0, x1), (z0, z1) = xr_(n), zr(n)
    ax.text((x0 + x1) / 2, min(z1, 33.5) + 0.3, lab, ha="center", fontsize=8.5, weight="bold")
ax.set_xlim(XL, XR)
ax.set_ylim(zs - 0.2, 34.5)
ax.set_aspect("equal")
ax.set_xlabel("вдоль борта, дюймы (0 = передняя грань короба D-стойки; вперёд — вправо)")
ax.set_ylabel("от чистового пола, дюймы")
ax.set_title("Вид на пассажирский борт изнутри", fontsize=11, loc="left")
ax.grid(True, color="#f0f0f0", lw=0.6)
fig.suptitle("Этажерка на 4 батареи Buknuwo 150Ah + электрика (пассажирский борт), проект 2026-11-07\n"
             "лестница: 2 продольные рейки + 2 поперечины strut, фанера 1/2″; опоры — стойки кровати P1/Pf (M8 в кузов), "
             "P3, P3f, верх арки; клеммы и кабели — к борту", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.965))
save(fig, "battery_bank_drawing.png")
