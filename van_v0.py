#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
van_v0.py — КАРКАСНАЯ модель RAM ProMaster 136" High Roof, повторяющая 3D-скан.

ИДЕЯ (по требованию заказчика):
  • CAD-модель = ТОЛЬКО КАРКАС (к нему крепится оборудование). Обшивки в CAD нет.
  • Обшивка — это сам 3D-скан кузова (Mesh), он лежит ПОВЕРХ каркаса.
  • Внутренний объём — НЕ «коробка», а сложная форма: гнутые борта + округлая крыша,
    снятая с реального скана. Рёбра каркаса — гнутые обручи по контуру скана.

СИСТЕМА КООРДИНАТ:
  ноль — пол у порога ЗАДНИХ дверей, на центральной оси.
  X = длина:  0 сзади, +X к кабине;  Y = ширина: 0 центр, +Y пассажир;  Z = высота: 0 пол.

ОТКУДА ГЕОМЕТРИЯ:
  Профиль сечения каркаса измеряется из Ducato_L2H2_body_reference.stl (наружная
  оболочка кузова, выровненная в СК модели через SCAN_ALIGN). По облаку точек в
  карго-зоне строится усреднённый ПОЛУ-ПРОФИЛЬ (полуширина борта в зависимости от Z),
  смещённый внутрь на frame_clearance (толщина обшивки/панели). Из него — гнутые рёбра.

СЛОИ (группы):
  Scan_Skin   — меш-обшивка (реальный кузов), полупрозрачная.
  Frame       — каркас:
      Ribs                — гнутые поперечные обручи (борт+крыша) по контуру скана
      Longitudinals       — продольные рейки вдоль X на заданных высотах
      CorrugatedFloor      — рефлёный пол: продольные рёбра жесткости, не отдельные поперечины
      Pillars             — стойки у проёмов
      HoleMarkers         — точки крепления на рёбрах (по реальной поверхности борта)
      FactoryThreadedMounts — заводские резьбовые точки на продольных рейках (M8/M10 — уточнить)
  Openings    — реф-рамки проёмов (сдвижная дверь, задние двери)

ПЕРЕЗАПУСК: правишь PARAMS → запускаешь снова → документ van_v0 пересобирается и
  пересохраняется в van_v0.FCStd.  ЗАПУСК: headless `FreeCAD.AppImage --console van_v0.py`
  или живьём через RPC execute_code(open(path).read()).
"""

import os
import math
import struct
import FreeCAD as App
import Part
import Mesh

try:
    import numpy as np
    _HAVE_NP = True
except Exception:
    _HAVE_NP = False

# ──────────────────────────── PARAMS (мм) ────────────────────────────
PARAMS = {
    # — габариты (измерено по STL); нужны для проёмов, стоек, клампов —
    "interior_length":   3190,   # измерено по STL (зад. порог X=0 → перед короба ~3190)
    "interior_width_max": 1862,  # измерено по STL (внутр.; наруж. кузов ~2060)
    "interior_height":   1930,   # измерено по STL (наруж. свод 1971 − пол 41)

    # — построение профиля каркаса из скана —
    "profile_x_lo":        100,  # X-зона карго для усреднения профиля (низ)
    "profile_x_hi":       3050,  # X-зона карго для усреднения профиля (верх)
    "frame_clearance":      40,  # смещение профиля внутрь от наруж. оболочки (панель), мм
    "profile_dz":           55,  # шаг по Z при снятии профиля, мм
    "rib_center_z":        950,  # центр, к которому смещаются точки при создании толщины ребра

    # — рёбра (гнутые обручи борт+крыша) —
    "rib_positions_x": [160, 1880, 3130],  # SEED: задняя рама + 2 рамы сдвижной двери по окну STL
    "rib_width":            45,  # ширина ребра вдоль X
    "rib_depth":            55,  # толщина ребра внутрь (по нормали к борту)

    # — продольные рейки вдоль X (на стенах, обе стороны) —
    "wall_rail_z":     [20, 980, 1700],   # SEED: низовая у пола / средняя / верхняя рейки
    "wall_rail_section":   40,   # сечение рейки (□), мм
    "wall_rail_inset":      8,   # отступ внутрь от поверхности борта, мм
    "wall_rail_min_segment": 180, # не рисовать короткие хвостики после разрывов
    "wheel_arch_x_range": (520, 1650),  # SEED по STL: зона задних колёсных арок
    "wheel_arch_block_z": 650,    # ниже этой высоты низовая рейка прерывается аркой
    "wheel_arch_margin": 40,      # запас по X вокруг арки

    # — рефлёный пол (визуал; полосы идут вдоль X, как профнастил C-8) —
    "floor_corrugation_pitch": 115,
    "floor_corrugation_rib_width": 38,
    "floor_corrugation_height": 8,

    # — стойки у проёмов —
    "pillar_width":   70,        # вдоль X
    "pillar_depth":   80,        # внутрь
    "pillar_height": 1700,       # SEED — высота стойки

    # — точки крепления (маркеры) на рёбрах —
    "hole_marker_z":  [350, 800, 1250, 1650],  # SEED — высоты точек на борту
    "hole_marker_radius": 16,    # только визуал
    "factory_threaded_rail_z": 980,
    "factory_threaded_offset_from_rib": 200,
    "factory_threaded_radius": 24,  # визуальный маркер резьбовой точки
    "factory_threaded_thread": "M8/M10 (уточнить)",

    # — проёмы дверей (реф-рамки; SEED — уточнить по замеру) —
    "slider_w":  1250, "slider_h": 1755, "slider_front_from_rear": 3130, "slider_sill_z": 0,  # каталог/Ducato: ~1250x1755 мм
    "slider_side": -1,  # -1 = левый/driver борт (-Y); +1 = passenger борт (+Y)
    "rear_w":    1562, "rear_h":   1572, "rear_sill_z": 0,
    "frame_thickness": 15,
}

# ──────────────────────── КРОВАТЬ (strut channel) ────────────────────────
# Поперечная кровать в задней части: ДЛИНА (спим поперёк) = от борта до борта;
# ШИРИНА вдоль X = от задних дверей вперёд. Каркас из strut channel (Unistrut),
# БЕЗ СВАРКИ, разборный, на fittings (угловые кронштейны типа p1325, channel nuts).
# Ноги — strut, болтятся к борту в заводских резьбовых точках Z=980 (см.
# FactoryThreadedMounts) и идут от пола вверх под крышу, заодно служа
# направляющими для обшивки/оборудования.
BED = {
    "enable": True,
    "mattress_width_x": 1400,   # передний край настила = bed_cx + это/2 (перед к кабине)
    "deck_rear_x":      20,     # задний край настила — почти у задней двери (X≈0), по просьбе
    "top_z":            980,    # верх продольных несущих ≈ высота заводской резьбовой точки
    "wall_clear":       30,     # отступ центра ноги от внутр. поверхности борта
    "strut_deep_w":     41.3,   # 1-5/8" глубокий профиль (ноги + продольные несущие)
    "strut_deep_h":     41.3,
    "cross_w":          41.3,   # поперечины: 1-5/8×13/16 неглубокий профиль — дешевле/легче
    "cross_h":          21.0,
    "deck_th":          18,     # фанерный настил 3/4"
    "mattress_th":      150,    # матрас из поролона (визуал; режется по форме)
    "n_cross":          5,      # число поперечин под фанеру
    "rear_feet":        True,   # задние опорные ножки на полу под свес настила к двери
    "foot_inset":       40,     # отступ задней ножки от заднего края настила, мм
    "post_margin_top":  30,     # запас под крышей сверху стойки
}
# Прайс-ориентир (США, июнь 2026; Home Depot/Lowe's/Amazon) — оценка, уточнять при заказе.
BED_PRICES = {
    "deep_10ft":    40.0,   # Superstrut ZA12HS10EG 1-5/8×1-5/8 12ga 10ft (Home Depot ~$40)
    "shallow_10ft": 33.0,   # Superstrut ZB1400HS 1-5/8×13/16 14ga 10ft (~$32–40)
    "angle_fitting": 3.2,   # Superstrut ZAB205 4-отв. угол 90° (~$3.1–3.5; на Amazon мультипак дешевле)
    "spring_set":    0.8,   # пружинная гайка+болт, набор 50шт на Amazon ~$40 → ~$0.8/комплект
    "wall_bolt":     1.0,   # болт M8/M10 в заводскую резьбовую точку
    "end_cap":       0.4,   # пластиковая заглушка на рез
    "post_base":     6.0,   # опорная пятка ножки на пол (опц.)
    "ply_sheet":    45.0,   # лист фанеры 3/4" 4×8 ft (~$40–60)
}

DOC_NAME    = "van_v0"
_REAL_HOME  = os.environ.get("SNAP_REAL_HOME") or os.path.expanduser("~")
SAVE_PATH   = os.path.join(_REAL_HOME, "van-build", "van_v0.FCStd")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
              else os.path.join(_REAL_HOME, "van-build")
BODY_STL_PATH = os.path.join(PROJECT_DIR, "Ducato_L2H2_body_reference.stl")

# ── Выравнивание скан → СК модели (измерено по body_reference) ──
SCAN_REAR_X   = -460.0
SCAN_CENTER_Y = 2380.0
SCAN_FLOOR_Z  = 41.0
SCAN_ALIGN = (-SCAN_REAR_X, -SCAN_CENTER_Y, -SCAN_FLOOR_Z)   # (+460, −2380, −41)

# Цвета
COL_SKIN   = (0.80, 0.83, 0.86)   # обшивка-скан — светло-серая
COL_RIB    = (0.90, 0.10, 0.06)   # рёбра-обручи — красные
COL_RAIL   = (0.05, 0.38, 0.95)   # продольные рейки — синие
COL_FLOOR  = (0.34, 0.36, 0.38)   # рефлёный металлический пол
COL_PILLAR = (0.82, 0.15, 0.15)   # стойки — красные
COL_HOLE   = (1.00, 0.92, 0.10)   # маркеры — жёлтые
COL_FACTORY_THREAD = (0.00, 0.85, 1.00)  # заводские резьбовые точки — голубые
COL_SLIDER = (0.20, 0.70, 0.30)
COL_REAR   = (0.25, 0.45, 0.85)
COL_STRUT    = (0.55, 0.57, 0.62)   # strut channel — сталь/оцинковка
COL_PLY      = (0.80, 0.66, 0.42)   # фанерный настил
COL_MATTRESS = (0.40, 0.55, 0.85)   # матрас (визуал)

_SCAN_PTS = None   # кэш облака точек скана в СК модели


# ──────────────────────────── helpers ────────────────────────────
def _style(obj, color=None, transparency=None):
    vo = getattr(obj, "ViewObject", None)
    if vo is None:
        return
    try:
        if color is not None:
            vo.ShapeColor = color
        if transparency is not None:
            vo.Transparency = int(transparency)
    except Exception:
        pass


def add_box(doc, name, label, dims, base, color=None, transparency=None, group=None):
    o = doc.addObject("Part::Box", name)
    o.Length, o.Width, o.Height = (float(d) for d in dims)
    o.Placement.Base = App.Vector(*[float(v) for v in base])
    o.Label = label
    _style(o, color, transparency)
    if group is not None:
        group.addObject(o)
    return o


def add_sphere(doc, name, label, radius, center, color=None, group=None):
    o = doc.addObject("Part::Sphere", name)
    o.Radius = float(radius)
    o.Placement.Base = App.Vector(*[float(v) for v in center])
    o.Label = label
    _style(o, color)
    if group is not None:
        group.addObject(o)
    return o


def add_shape(doc, name, label, shape, color=None, transparency=None, group=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.Label = label
    _style(o, color, transparency)
    if group is not None:
        group.addObject(o)
    return o


# ── чтение скана и снятие профиля ──
def _read_stl_points(path):
    """Бинарный STL → массив вершин Nx3 (numpy)."""
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    a = np.frombuffer(data[84:84 + 50 * n], dtype=np.uint8).reshape(n, 50)
    return a[:, 12:48].copy().view("<f4").reshape(n * 3, 3).astype(float)


def scan_points():
    global _SCAN_PTS
    if _SCAN_PTS is None:
        pts = _read_stl_points(BODY_STL_PATH)
        pts += np.array(SCAN_ALIGN)
        _SCAN_PTS = pts
    return _SCAN_PTS


def measured_half_profile(P):
    """Усреднённый полу-профиль борта по карго-зоне: список (y>=0, z), z по возрастанию.

    y — внутренняя поверхность борта (наруж. оболочка минус frame_clearance).
    Верх крыши делаем монотонным (убираем шум скана), завершаем точкой свода (0, крышаZ).
    """
    pp = PARAMS
    X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
    m = (X > pp["profile_x_lo"]) & (X < pp["profile_x_hi"]) & (Z > 15)
    y, z = np.abs(Y[m]), Z[m]
    dz = pp["profile_dz"]
    crown = pp["interior_height"] - 5.0
    hw_list, z_list = [], []
    for z0 in np.arange(0, crown, dz):
        b = (z >= z0 - dz / 2) & (z < z0 + dz / 2)
        if b.sum() < 5:
            continue
        hw_list.append(float(np.percentile(y[b], 93)) - pp["frame_clearance"])
        z_list.append(float(z0))
    if len(hw_list) < 6:
        raise RuntimeError("слишком мало точек скана для профиля")
    hw = np.array(hw_list)
    zz = np.array(z_list)
    # сглаживание полуширины (убираем шум скана), скользящее среднее окно 5,
    # концы сохраняем, чтобы не «утянуть» пол и плечо
    k = 5
    sm = np.convolve(hw, np.ones(k) / k, mode="same")
    sm[:2] = hw[:2]
    sm[-2:] = hw[-2:]
    # монотонность крыши: выше плеча полуширина не растёт с высотой
    shoulder = 1400.0
    for i in range(1, len(sm)):
        if zz[i] >= shoulder and sm[i] > sm[i - 1]:
            sm[i] = sm[i - 1]
    prof = [(max(float(w), 0.0), float(zv)) for w, zv in zip(sm, zz)]
    prof.append((0.0, crown))
    return prof


def full_hoop(half):
    """Полный обруч (борт+крыша) из полу-профиля: правый борт→свод→левый борт.
    Открыт снизу (U), пол не пересекает. Возвращает список (y, z)."""
    right = list(half)                       # (y, z) от пола до свода, y>=0
    left = [(-y, z) for (y, z) in reversed(right[:-1])]  # свод-1 … пол, y<=0
    return right + left


def y_at_z(half, z_query):
    """Линейная интерполяция полуширины борта на высоте z."""
    pts = sorted(half, key=lambda p: p[1])
    if z_query <= pts[0][1]:
        return pts[0][0]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z0 <= z_query <= z1:
            t = (z_query - z0) / (z1 - z0) if z1 > z0 else 0.0
            return y0 + (y1 - y0) * t
    return pts[-1][0]


def _rib_face(bx, outer, inner, smooth=True):
    """Плоская грань-лента (в X=bx) между внешним и внутренним контурами.
    smooth=True — контуры как BSpline (гладко), иначе полигон (надёжный fallback)."""
    o3 = [App.Vector(bx, y, z) for (y, z) in outer]
    i3 = [App.Vector(bx, y, z) for (y, z) in inner]
    if smooth:
        try:
            # аппроксимация (МНК, степень 3, допуск) — гладко, без перестрела на плече
            oc = Part.BSplineCurve(); oc.approximate(Points=o3, DegMin=3, DegMax=3, Tolerance=6.0)
            ic = Part.BSplineCurve(); ic.approximate(Points=i3[::-1], DegMin=3, DegMax=3, Tolerance=6.0)
            oa, ob = oc.value(oc.FirstParameter), oc.value(oc.LastParameter)
            ia, ib = ic.value(ic.FirstParameter), ic.value(ic.LastParameter)
            wire = Part.Wire([
                oc.toShape(),
                Part.LineSegment(ob, ia).toShape(),   # конец внешнего → начало внутреннего
                ic.toShape(),
                Part.LineSegment(ib, oa).toShape(),   # конец внутреннего → начало внешнего
            ])
            return Part.Face(wire)
        except Exception as e:
            print("! сплайн-ребро → полигон (fallback):", e)
    return Part.Face(Part.makePolygon(o3 + i3[::-1] + [o3[0]]))


def rib_solid(x0, hoop, width, depth, zc, smooth=False):
    """Гнутое ребро: лента между обручем (внешняя грань) и его смещением внутрь,
    протянутая на width вдоль X. Контур — полигон по сглаженному профилю скана
    (надёжно, грани ~6 см почти незаметны). smooth=True пробует BSpline, но
    на сломе борт→плечо→свод сплайн перестреливает — по умолчанию выкл."""
    bx = x0 - width / 2.0
    inner = []
    for (y, z) in hoop:
        d = math.hypot(y, z - zc) or 1.0
        inner.append((y + (0 - y) / d * depth, z + (zc - z) / d * depth))
    return _rib_face(bx, hoop, inner, smooth).extrude(App.Vector(width, 0.0, 0.0))


def hoop_wire(x0, hoop):
    """Полилиния обруча (для возможной справки)."""
    return Part.makePolygon([App.Vector(x0, y, z) for (y, z) in hoop])


def add_mesh_skin(doc, group):
    if not os.path.exists(BODY_STL_PATH):
        print("! STL обшивки не найден:", BODY_STL_PATH)
        return None
    mesh = Mesh.Mesh(BODY_STL_PATH)
    o = doc.addObject("Mesh::Feature", "Scan_Skin_Body")
    o.Mesh = mesh
    o.Placement.Base = App.Vector(*SCAN_ALIGN)
    o.Label = "Обшивка — 3D-скан кузова (выровнен на каркас)"
    _style(o, COL_SKIN, 60)
    group.addObject(o)
    return o


def _segments_with_openings(length, z, h, openings, min_len=1.0):
    blocked = []
    for ox0, ox1, oz0, oz1, margin in openings:
        if z < oz1 and z + h > oz0:
            blocked.append((max(0.0, ox0 - margin), min(length, ox1 + margin)))
    blocked.sort()
    segs, cur = [], 0.0
    for s, e in blocked:
        if s > cur:
            segs.append((cur, s))
        cur = max(cur, e)
    if cur < length:
        segs.append((cur, length))
    return [(a, b) for a, b in segs if b - a > min_len]


def overall_bbox(doc):
    bb = None
    for o in doc.Objects:
        sh = getattr(o, "Shape", None)
        me = getattr(o, "Mesh", None)
        b = None
        if me is not None and getattr(me, "CountFacets", 0) > 0:
            b = me.BoundBox
        elif sh is not None and not sh.isNull():
            b = sh.BoundBox
        if b is None:
            continue
        bb = b if bb is None else bb.united(b)
    return bb


# ──────────────────────────── build ────────────────────────────
def build():
    P = PARAMS
    if not _HAVE_NP:
        raise RuntimeError("numpy недоступен — профиль из скана снять нельзя")

    pts = scan_points()
    half = measured_half_profile(pts)
    hoop = full_hoop(half)
    zc = P["rib_center_z"]
    crown_z = half[-1][1]
    floor_hw = half[0][0]
    L = P["interior_length"]

    if DOC_NAME in App.listDocuments():
        App.closeDocument(DOC_NAME)
    doc = App.newDocument(DOC_NAME)

    # ═══════ ОБШИВКА (скан) ═══════
    skin = doc.addObject("App::DocumentObjectGroup", "Scan_Skin")
    skin.Label = "Обшивка — 3D-скан кузова (лежит на каркасе)"
    mesh_obj = add_mesh_skin(doc, skin)

    # ═══════ КАРКАС ═══════
    frame = doc.addObject("App::DocumentObjectGroup", "Frame")
    frame.Label = "Каркас (к нему крепится оборудование)"

    ribs_g = doc.addObject("App::DocumentObjectGroup", "Ribs")
    ribs_g.Label = "Рёбра — гнутые обручи по контуру скана"
    frame.addObject(ribs_g)
    rib_xs = [x for x in P["rib_positions_x"] if 0 <= x <= L]
    rib_roles = {
        160: "задняя рама распашной двери, смещена внутрь обшивки",
        1880: "задняя/средняя рама сдвижной двери по окну STL",
        3130: "передняя рама сдвижной двери у кабины по окну STL",
    }
    for x in rib_xs:
        role = rib_roles.get(int(round(x)), "обруч каркаса")
        add_shape(doc, "Rib_x%04d" % int(round(x)),
                  "Ребро X=%g — %s" % (x, role),
                  rib_solid(x, hoop, P["rib_width"], P["rib_depth"], zc),
                  color=COL_RIB, group=ribs_g)

    # продольные рейки вдоль X на стенах (обе стороны).
    # Сдвижная дверь прерывает все рейки на своём борту; колёсные арки — только низовую.
    longs_g = doc.addObject("App::DocumentObjectGroup", "Longitudinals")
    longs_g.Label = "Продольные рейки вдоль X"
    frame.addObject(longs_g)
    sec = P["wall_rail_section"]
    slider_x0 = P["slider_front_from_rear"] - P["slider_w"]
    slider_side = P["slider_side"]
    rail_open_slider = [(slider_x0, P["slider_front_from_rear"],
                     P["slider_sill_z"], P["slider_sill_z"] + P["slider_h"], 30.0)]
    wheel_x0, wheel_x1 = P["wheel_arch_x_range"]
    rail_open_wheel = [(wheel_x0, wheel_x1, 0.0, P["wheel_arch_block_z"], P["wheel_arch_margin"])]
    lower_rail_z = min(P["wall_rail_z"])
    n_rails = 0
    for z in P["wall_rail_z"]:
        yw = y_at_z(half, z) - P["wall_rail_inset"]
        for tag, ysign in (("pY", +1), ("nY", -1)):
            side_role = "борт сдвижной двери" if ysign == slider_side else "противоположный борт"
            side_label = "%s (%s)" % (tag, side_role)
            openings = []
            if ysign == slider_side:
                openings += rail_open_slider
            if abs(z - lower_rail_z) < 1e-6:
                openings += rail_open_wheel
            for i, (xa, xb) in enumerate(_segments_with_openings(
                    L, z, sec, openings, P["wall_rail_min_segment"]), 1):
                n_rails += 1
                ybase = ysign * yw - sec / 2.0
                add_box(doc, "Rail_%s_z%04d_s%d" % (tag, int(round(z)), i),
                        "Рейка %s Z=%g сегм.%d" % (side_label, z, i),
                        (xb - xa, sec, sec), (xa, ybase, z - sec / 2.0),
                        color=COL_RAIL, group=longs_g)

    # рефлёный пол: продольные гребни идут вдоль X; отдельных поперечин нет.
    floor_g = doc.addObject("App::DocumentObjectGroup", "CorrugatedFloor")
    floor_g.Label = "Рефлёный пол — продольные рёбра жесткости (визуал)"
    frame.addObject(floor_g)
    fw = 2.0 * floor_hw
    pitch = P["floor_corrugation_pitch"]
    rib_w = P["floor_corrugation_rib_width"]
    rib_h = P["floor_corrugation_height"]
    n_floor_ribs = 0
    y = -floor_hw + pitch / 2.0
    while y < floor_hw - pitch / 2.0:
        n_floor_ribs += 1
        add_box(doc, "FloorCorrugation_y%+05d" % int(round(y)),
                "Продольный гребень пола Y=%g" % y,
                (L, rib_w, rib_h), (0.0, y - rib_w / 2.0, 0.0),
                color=COL_FLOOR, transparency=18, group=floor_g)
        y += pitch

    # стойки у проёмов
    pil_g = doc.addObject("App::DocumentObjectGroup", "Pillars")
    pil_g.Label = "Стойки у проёмов"
    frame.addObject(pil_g)
    ph = P["pillar_height"]
    yw_pillar = y_at_z(half, ph * 0.5)
    slider_label = "-Y" if slider_side < 0 else "+Y"
    slider_pillar_y = -yw_pillar if slider_side < 0 else yw_pillar - P["pillar_depth"]
    add_box(doc, "Pillar_B_slider", "B-стойка (перед сдвижного проёма, %s)" % slider_label,
            (P["pillar_width"], P["pillar_depth"], ph),
            (P["slider_front_from_rear"] - P["pillar_width"] / 2.0,
             slider_pillar_y, 0.0), color=COL_PILLAR, group=pil_g)
    for sgn, tag in ((+1, "pY"), (-1, "nY")):
        ye = sgn * (P["rear_w"] / 2.0)
        add_box(doc, "Pillar_Rear_" + tag, "Задняя стойка %s (край проёма X=0)" % tag,
                (P["pillar_depth"], P["pillar_width"], ph),
                (0.0, ye - P["pillar_width"] / 2.0, 0.0), color=COL_PILLAR, group=pil_g)

    # маркеры точек крепления на рёбрах — по реальной поверхности борта
    holes_g = doc.addObject("App::DocumentObjectGroup", "HoleMarkers")
    holes_g.Label = "Точки крепления на рёбрах (по борту)"
    frame.addObject(holes_g)
    n_holes = 0
    for x in rib_xs:
        role = rib_roles.get(int(round(x)), "обруч каркаса")
        for z in P["hole_marker_z"]:
            yw = y_at_z(half, z)
            for tag, ysign in (("pY", +1), ("nY", -1)):
                n_holes += 1
                add_sphere(doc, "Hole_%s_x%04d_z%04d" % (tag, int(round(x)), int(round(z))),
                           "Точка %s X=%g Z=%g" % (tag, x, z),
                           P["hole_marker_radius"], (x, ysign * yw, z),
                           color=COL_HOLE, group=holes_g)

    # заводские резьбовые точки на средней продольной рейке (M8/M10 — уточнить)
    threaded_g = doc.addObject("App::DocumentObjectGroup", "FactoryThreadedMounts")
    threaded_g.Label = "Заводские резьбовые точки на рейках (M8/M10, SEED)"
    frame.addObject(threaded_g)
    threaded_z = P["factory_threaded_rail_z"]
    threaded_yw = y_at_z(half, threaded_z) - P["wall_rail_inset"]
    thread_dx = P["factory_threaded_offset_from_rib"]
    rear_thread_x = rib_xs[0] + thread_dx
    middle_thread_x = rib_xs[1] - thread_dx
    front_thread_x = rib_xs[2] - thread_dx
    factory_mounts = [
        ("pY_rear", +1, rear_thread_x, "около 200 мм вперед от заднего ребра"),
        ("nY_rear", -1, rear_thread_x, "около 200 мм вперед от заднего ребра"),
        ("pY_middle", +1, middle_thread_x, "около 200 мм назад от среднего ребра"),
        ("nY_middle", -1, middle_thread_x, "около 200 мм назад от среднего ребра"),
        ("pY_front", +1, front_thread_x, "около 200 мм назад от переднего ребра; только длинная рейка"),
    ]
    n_factory_threads = 0
    for name, ysign, x, note in factory_mounts:
        if not (0 <= x <= L):
            continue
        n_factory_threads += 1
        tag = "pY" if ysign > 0 else "nY"
        add_sphere(doc, "FactoryThread_%s_x%04d_z%04d" % (name, int(round(x)), int(round(threaded_z))),
                   "Заводская резьбовая точка %s, %s, %s" % (tag, P["factory_threaded_thread"], note),
                   P["factory_threaded_radius"], (x, ysign * threaded_yw, threaded_z),
                   color=COL_FACTORY_THREAD, group=threaded_g)

    # ═══════ КРОВАТЬ — каркас из strut channel (без сварки, разборная) ═══════
    bed_summary = None
    B = BED
    if B.get("enable"):
        bed_g = doc.addObject("App::DocumentObjectGroup", "Bed_StrutFrame")
        bed_g.Label = "Кровать — каркас strut channel (разборный, без сварки)"
        sw, sh = B["strut_deep_w"], B["strut_deep_h"]
        csw, csh = B["cross_w"], B["cross_h"]
        bz = B["top_z"]
        yL = y_at_z(half, bz) - B["wall_clear"]          # центр ноги у борта
        leg_xs = [rear_thread_x, middle_thread_x]         # 360, 1680 (заводские точки)
        bed_cx = sum(leg_xs) / 2.0
        bw = B["mattress_width_x"]
        # передний край — от bed_cx; задний край тянем почти до задней двери (X≈0) по просьбе
        deck_x1 = bed_cx + bw / 2.0
        deck_x0 = B.get("deck_rear_x", bed_cx - bw / 2.0)

        # высота стойки: вверх до Z, где борт ещё не ушёл внутрь Y ноги (под крышу)
        crown = half[-1][1]
        post_top, zq = bz, bz
        while zq <= crown:
            if y_at_z(half, zq) >= yL:
                post_top = zq
            zq += 10.0
        post_top -= B["post_margin_top"]

        cutlist = []  # (label, length_mm, section_key)

        def strut(name, label, dims, base, section_key, group=bed_g):
            add_box(doc, name, label, dims, base, color=COL_STRUT, group=group)
            cutlist.append((label, float(max(dims)), section_key))

        # 4 ноги-стойки (пол → под крышу); болт к борту в заводской точке Z=bz,
        # заодно направляющие под обшивку/оборудование
        for lx, xr in ((leg_xs[0], "rear"), (leg_xs[1], "mid")):
            for ysign, tag in ((+1, "pY"), (-1, "nY")):
                strut("BedLeg_%s_%s" % (tag, xr),
                      "Нога кровати strut %s X=%g (болт к борту Z=%g, до Z=%.0f)"
                      % (tag, lx, bz, post_top),
                      (sw, sw, post_top),
                      (lx - sw / 2.0, ysign * yL - sw / 2.0, 0.0), "deep")

        # 2 продольные несущие (вдоль X) — к внутренней грани ног
        for ysign, tag in ((+1, "pY"), (-1, "nY")):
            ly = ysign * (yL - sw)
            strut("BedRailLong_%s" % tag,
                  "Продольная несущая strut %s (X %.0f..%.0f)" % (tag, deck_x0, deck_x1),
                  (deck_x1 - deck_x0, sw, sh),
                  (deck_x0, ly - sw / 2.0, bz - sh), "deep")

        # задние опорные ножки на полу: настил вынесен назад к двери за ноги (X=360),
        # поэтому продольные свешиваются ~340 мм назад — подпираем их ножками у пола.
        foot_h = bz - sh
        if B.get("rear_feet"):
            fx = deck_x0 + B.get("foot_inset", 40)
            for ysign, tag in ((+1, "pY"), (-1, "nY")):
                ly = ysign * (yL - sw)
                strut("BedRearFoot_%s" % tag,
                      "Задняя опорная ножка strut %s X=%.0f (пол→настил, под свес)" % (tag, fx),
                      (sw, sw, foot_h),
                      (fx - sw / 2.0, ly - sw / 2.0, 0.0), "deep")

        # поперечины (вдоль Y) поверх продольных, под фанеру; неглубокий профиль
        cross_span = yL - sw / 2.0                # до внутр. грани ноги
        nC = B["n_cross"]
        cross_xs = [deck_x0 + (deck_x1 - deck_x0) * i / (nC - 1) for i in range(nC)]
        for i, cx in enumerate(cross_xs, 1):
            strut("BedCross_%02d" % i,
                  "Поперечина strut #%d X=%.0f (под фанеру)" % (i, cx),
                  (csw, 2 * cross_span, csh),
                  (cx - csw / 2.0, -cross_span, bz), "shallow")

        # фанерный настил + матрас (визуал)
        deck_z = bz + csh
        add_box(doc, "BedDeck_Plywood", "Настил — фанера %gмм (на поперечинах)" % B["deck_th"],
                (deck_x1 - deck_x0, 2 * cross_span, B["deck_th"]),
                (deck_x0, -cross_span, deck_z), color=COL_PLY, transparency=10, group=bed_g)
        matt_z = deck_z + B["deck_th"]
        add_box(doc, "BedMattress", "Матрас (визуал, %g×%.0f)" % (bw, 2 * cross_span),
                (bw, 2 * cross_span, B["mattress_th"]),
                (deck_x0, -cross_span, matt_z), color=COL_MATTRESS, transparency=55, group=bed_g)

        # 5-я стойка — под оборудование (pY front, X=2930), НЕ для кровати
        if 0 <= front_thread_x <= L:
            strut("EquipPost_pY_front",
                  "Стойка под оборудование strut pY X=%g (НЕ кровать; болт Z=%g)"
                  % (front_thread_x, bz),
                  (sw, sw, post_top),
                  (front_thread_x - sw / 2.0, yL - sw / 2.0, 0.0), "deep")

        # ── смета / cut-list ──
        # Хлысты считаем УПАКОВКОЙ (First-Fit-Decreasing): длинные ~1.8 м куски часто
        # дают 1 шт на 10-фт хлыст + большой остаток — обычный ceil(сумма/хлыст) врёт.
        STICK = 3048.0  # 10 ft
        KERF = 4.0      # пропил
        def _pack(lengths):
            bins = []
            for Lp in sorted(lengths, reverse=True):
                for b in range(len(bins)):
                    if bins[b] + Lp + KERF <= STICK:
                        bins[b] += Lp + KERF
                        break
                else:
                    bins.append(Lp + KERF)
            return len(bins)
        deep_L = [Lp for _, Lp, k in cutlist if k == "deep"]
        shal_L = [Lp for _, Lp, k in cutlist if k == "shallow"]
        deep_mm, shal_mm = sum(deep_L), sum(shal_L)
        deep_sticks, shal_sticks = _pack(deep_L), _pack(shal_L)

        # — крепёж (реалистично; см. BOM в FURNITURE_MEMORY.md) —
        n_wall_mounts = 5                 # 4 ноги кровати + 1 стойка оборудования → к борту
        n_leg_rail    = 4                 # ноги ↔ продольные несущие (2 ноги × 2 борта)
        n_foot_rail   = 2 if B.get("rear_feet") else 0   # задние ножки ↔ продольные
        n_angles  = n_wall_mounts + n_leg_rail + n_foot_rail
        n_spring  = 2 * n_angles + 2 * nC   # ~2 комплекта на угол + по 2 на поперечину
        n_wall_bolts = n_wall_mounts
        n_end_caps   = len(cutlist)          # по заглушке на видимый рез
        n_bases      = n_foot_rail
        n_ply        = 2                     # листа фанеры на настил

        pr = BED_PRICES
        cost_strut = deep_sticks * pr["deep_10ft"] + shal_sticks * pr["shallow_10ft"]
        cost_fit   = (n_angles * pr["angle_fitting"] + n_spring * pr["spring_set"]
                      + n_wall_bolts * pr["wall_bolt"] + n_end_caps * pr["end_cap"]
                      + n_bases * pr["post_base"])
        cost_ply   = n_ply * pr["ply_sheet"]
        cost = cost_strut + cost_fit + cost_ply
        bed_summary = dict(
            yL=yL, post_top=post_top, deck=(deck_x0, deck_x1), span_y=2 * cross_span,
            deep_mm=deep_mm, shal_mm=shal_mm, deep_sticks=deep_sticks, shal_sticks=shal_sticks,
            n_angles=n_angles, n_spring=n_spring, n_wall_bolts=n_wall_bolts,
            n_end_caps=n_end_caps, n_ply=n_ply,
            cost_strut=cost_strut, cost_fit=cost_fit, cost_ply=cost_ply, cost=cost,
            n_members=len(cutlist) + 2)

    # ═══════ ПРОЁМЫ (реф-рамки) ═══════
    op = doc.addObject("App::DocumentObjectGroup", "Openings")
    op.Label = "Проёмы дверей (реф-рамки, SEED)"
    t = P["frame_thickness"]
    yw_sl = y_at_z(half, P["slider_sill_z"] + P["slider_h"] / 2.0)
    slider_opening_y = -yw_sl if slider_side < 0 else yw_sl - t
    add_box(doc, "Opening_SlidingDoor", "Проём сдвижной двери (%s, реф)" % slider_label,
            (P["slider_w"], t, P["slider_h"]),
            (slider_x0, slider_opening_y, P["slider_sill_z"]),
            color=COL_SLIDER, transparency=35, group=op)
    add_box(doc, "Opening_RearDoors", "Проём задних дверей (X=0, реф)",
            (t, P["rear_w"], P["rear_h"]),
            (0.0, -P["rear_w"] / 2.0, P["rear_sill_z"]),
            color=COL_REAR, transparency=35, group=op)
    leaf_w = P["rear_w"] / 2.0
    add_box(doc, "RearDoorLeaf_Driver", "Левая половина задней распашной двери (реф)",
            (t, leaf_w, P["rear_h"]),
            (-t, -leaf_w, P["rear_sill_z"]),
            color=COL_REAR, transparency=72, group=op)
    add_box(doc, "RearDoorLeaf_Passenger", "Правая половина задней распашной двери (реф)",
            (t, leaf_w, P["rear_h"]),
            (-t, 0.0, P["rear_sill_z"]),
            color=COL_REAR, transparency=72, group=op)

    doc.recompute()
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    doc.saveAs(SAVE_PATH)

    try:
        import FreeCADGui as Gui
        if Gui.activeDocument():
            Gui.activeDocument().activeView().viewIsometric()
            Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass

    # ─── сводка ───
    bb = overall_bbox(doc)
    n_solid = len([o for o in doc.Objects if o.isDerivedFrom("Part::Feature")])
    print("=" * 70)
    print("VAN v0 — КАРКАС ProMaster 136 по 3D-скану  (обшивка = меш-скан)")
    print("Документ:", doc.Name, " Сохранён:", SAVE_PATH)
    print("-" * 70)
    print("Профиль борта (измерен по скану, внутр. поверхность, n=%d точек):" % len(half))
    print("  пол: полуширина %.0f → у свода %.0f;  свод Z=%.0f" % (floor_hw, half[-2][0], crown_z))
    print("  выборка: полуширина@Z500=%.0f  @Z1000=%.0f  @Z1500=%.0f  @Z1700=%.0f" % (
        y_at_z(half, 500), y_at_z(half, 1000), y_at_z(half, 1500), y_at_z(half, 1700)))
    print("-" * 70)
    print("[Каркас]")
    print("  Рёбра (гнутые обручи): %d @X=%s, %gx%g (ШxТ)" % (
        len(rib_xs), rib_xs, P["rib_width"], P["rib_depth"]))
    print("  Продольные рейки: %d сегм. @Z=%s, □%g" % (n_rails, P["wall_rail_z"], sec))
    print("    низовая рейка Z=%g прервана колёсными арками X=%g..%g и дверью" % (
        lower_rail_z, wheel_x0, wheel_x1))
    print("  Рефлёный пол: %d продольных гребней вдоль X, шаг %g, высота %g" % (
        n_floor_ribs, pitch, rib_h))
    print("  Стойки: 3 (B @X=%.0f + 2 задние @Y=±%.0f), %gx%g h=%g" % (
        P["slider_front_from_rear"], P["rear_w"] / 2.0,
        P["pillar_width"], P["pillar_depth"], ph))
    print("  Маркеры крепления: %d (на %d рёбрах × Z=%s × 2 борта)" % (
        n_holes, len(rib_xs), P["hole_marker_z"]))
    print("  Заводские резьбовые точки: %d на рейках Z=%g, резьба %s" % (
        n_factory_threads, threaded_z, P["factory_threaded_thread"]))
    print("  Обшивка-скан: %s" % ("загружена" if mesh_obj else "НЕТ"))
    if bed_summary:
        bs = bed_summary
        print("-" * 70)
        print("[Кровать — strut channel, поперечная, разборная, без сварки]")
        print("  Ноги: 4 у бортов (X=%s, Y=±%.0f) + 1 под оборудование (pY X=%g)" % (
            [int(rear_thread_x), int(middle_thread_x)], bs["yL"], front_thread_x))
        print("  Стойки от пола Z=0 до Z=%.0f (под крышу; служат направляющими)" % bs["post_top"])
        print("  Настил (фанера) X=%.0f..%.0f (задний край у двери), спим поперёк %.0f мм" % (
            bs["deck"][0], bs["deck"][1], bs["span_y"]))
        print("  Strut: глубокий %.2f м (%d×10ft) + неглубокий %.2f м (%d×10ft)" % (
            bs["deep_mm"] / 1000, bs["deep_sticks"], bs["shal_mm"] / 1000, bs["shal_sticks"]))
        print("  Крепёж: %d уголков, %d компл. гайка+болт, %d болтов в борт, %d заглушек" % (
            bs["n_angles"], bs["n_spring"], bs["n_wall_bolts"], bs["n_end_caps"]))
        print("  ОЦЕНКА (США, июнь 2026): strut ~$%.0f + крепёж ~$%.0f + фанера ~$%.0f = ~$%.0f" % (
            bs["cost_strut"], bs["cost_fit"], bs["cost_ply"], bs["cost"]))
    print("-" * 70)
    if bb:
        print("Bounding box (вкл. обшивку): %.0f x %.0f x %.0f мм" % (
            bb.XLength, bb.YLength, bb.ZLength))
    print("Объектов Part::Feature: %d" % n_solid)
    print("=" * 70)
    return doc


DOC = build()
