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
      FloorCrossmembers   — поперечины пола
      Pillars             — стойки у проёмов
      HoleMarkers         — точки крепления на рёбрах (по реальной поверхности борта)
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
    "rib_positions_x": [250, 700, 1150, 1600, 2050, 2500, 2950],  # SEED — уточнить по замеру
    "rib_width":            45,  # ширина ребра вдоль X
    "rib_depth":            55,  # толщина ребра внутрь (по нормали к борту)

    # — продольные рейки вдоль X (на стенах, обе стороны) —
    "wall_rail_z":     [430, 980, 1500],  # SEED — высоты реек
    "wall_rail_section":   40,   # сечение рейки (□), мм
    "wall_rail_inset":      8,   # отступ внутрь от поверхности борта, мм

    # — поперечины пола —
    "floor_crossmember_positions_x": [120, 600, 1080, 1560, 2040, 2520, 3000],
    "floor_crossmember_width":  45,  # вдоль X
    "floor_crossmember_height": 30,  # высота над полом

    # — стойки у проёмов —
    "pillar_width":   70,        # вдоль X
    "pillar_depth":   80,        # внутрь
    "pillar_height": 1700,       # SEED — высота стойки

    # — точки крепления (маркеры) на рёбрах —
    "hole_marker_z":  [350, 800, 1250, 1650],  # SEED — высоты точек на борту
    "hole_marker_radius": 16,    # только визуал

    # — проёмы дверей (реф-рамки; SEED — уточнить по замеру) —
    "slider_w":  1250, "slider_h": 1755, "slider_front_from_rear": 2750, "slider_sill_z": 0,
    "rear_w":    1562, "rear_h":   1572, "rear_sill_z": 0,
    "frame_thickness": 15,
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
COL_RIB    = (0.90, 0.45, 0.10)   # рёбра — оранжевые
COL_RAIL   = (0.95, 0.72, 0.18)   # продольные рейки — жёлто-оранжевые
COL_FLOOR  = (0.40, 0.40, 0.45)   # поперечины пола
COL_PILLAR = (0.82, 0.15, 0.15)   # стойки — красные
COL_HOLE   = (1.00, 0.92, 0.10)   # маркеры — жёлтые
COL_SLIDER = (0.20, 0.70, 0.30)
COL_REAR   = (0.25, 0.45, 0.85)

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


def _segments_with_openings(length, z, h, openings):
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
    return [(a, b) for a, b in segs if b - a > 1.0]


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
    for x in rib_xs:
        add_shape(doc, "Rib_x%04d" % int(round(x)),
                  "Ребро (обруч) X=%g" % x,
                  rib_solid(x, hoop, P["rib_width"], P["rib_depth"], zc),
                  color=COL_RIB, group=ribs_g)

    # продольные рейки вдоль X на стенах (обе стороны), с разрывом у сдвижного проёма
    longs_g = doc.addObject("App::DocumentObjectGroup", "Longitudinals")
    longs_g.Label = "Продольные рейки вдоль X"
    frame.addObject(longs_g)
    sec = P["wall_rail_section"]
    slider_x0 = P["slider_front_from_rear"] - P["slider_w"]
    rail_open_pY = [(slider_x0, P["slider_front_from_rear"],
                     P["slider_sill_z"], P["slider_sill_z"] + P["slider_h"], 30.0)]
    n_rails = 0
    for z in P["wall_rail_z"]:
        yw = y_at_z(half, z) - P["wall_rail_inset"]
        for tag, ysign, openings in (("pY", +1, rail_open_pY), ("nY", -1, [])):
            for i, (xa, xb) in enumerate(_segments_with_openings(L, z, sec, openings), 1):
                n_rails += 1
                ybase = ysign * yw - sec / 2.0
                add_box(doc, "Rail_%s_z%04d_s%d" % (tag, int(round(z)), i),
                        "Рейка %s Z=%g сегм.%d" % (tag, z, i),
                        (xb - xa, sec, sec), (xa, ybase, z - sec / 2.0),
                        color=COL_RAIL, group=longs_g)

    # поперечины пола (ширина = по борту у пола)
    floor_g = doc.addObject("App::DocumentObjectGroup", "FloorCrossmembers")
    floor_g.Label = "Поперечины пола"
    frame.addObject(floor_g)
    fw = 2.0 * floor_hw
    n_floor = 0
    for x in P["floor_crossmember_positions_x"]:
        if not (0 <= x <= L):
            continue
        n_floor += 1
        add_box(doc, "FloorXmember_x%04d" % int(round(x)), "Поперечина пола X=%g" % x,
                (P["floor_crossmember_width"], fw, P["floor_crossmember_height"]),
                (x - P["floor_crossmember_width"] / 2.0, -floor_hw, 0.0),
                color=COL_FLOOR, group=floor_g)

    # стойки у проёмов
    pil_g = doc.addObject("App::DocumentObjectGroup", "Pillars")
    pil_g.Label = "Стойки у проёмов"
    frame.addObject(pil_g)
    ph = P["pillar_height"]
    yw_pillar = y_at_z(half, ph * 0.5)
    add_box(doc, "Pillar_B_slider", "B-стойка (перед сдвижного проёма, +Y)",
            (P["pillar_width"], P["pillar_depth"], ph),
            (P["slider_front_from_rear"] - P["pillar_width"] / 2.0,
             yw_pillar - P["pillar_depth"], 0.0), color=COL_PILLAR, group=pil_g)
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
        for z in P["hole_marker_z"]:
            yw = y_at_z(half, z)
            for tag, ysign in (("pY", +1), ("nY", -1)):
                n_holes += 1
                add_sphere(doc, "Hole_%s_x%04d_z%04d" % (tag, int(round(x)), int(round(z))),
                           "Точка %s X=%g Z=%g" % (tag, x, z),
                           P["hole_marker_radius"], (x, ysign * yw, z),
                           color=COL_HOLE, group=holes_g)

    # ═══════ ПРОЁМЫ (реф-рамки) ═══════
    op = doc.addObject("App::DocumentObjectGroup", "Openings")
    op.Label = "Проёмы дверей (реф-рамки, SEED)"
    t = P["frame_thickness"]
    yw_sl = y_at_z(half, P["slider_sill_z"] + P["slider_h"] / 2.0)
    add_box(doc, "Opening_SlidingDoor", "Проём сдвижной двери (+Y, реф)",
            (P["slider_w"], t, P["slider_h"]),
            (slider_x0, yw_sl - t, P["slider_sill_z"]),
            color=COL_SLIDER, transparency=35, group=op)
    add_box(doc, "Opening_RearDoors", "Проём задних дверей (X=0, реф)",
            (t, P["rear_w"], P["rear_h"]),
            (0.0, -P["rear_w"] / 2.0, P["rear_sill_z"]),
            color=COL_REAR, transparency=35, group=op)

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
    print("  Поперечины пола: %d @X=%s (ширина по борту %.0f)" % (
        n_floor, P["floor_crossmember_positions_x"], fw))
    print("  Стойки: 3 (B @X=%.0f + 2 задние @Y=±%.0f), %gx%g h=%g" % (
        P["slider_front_from_rear"], P["rear_w"] / 2.0,
        P["pillar_width"], P["pillar_depth"], ph))
    print("  Маркеры крепления: %d (на %d рёбрах × Z=%s × 2 борта)" % (
        n_holes, len(rib_xs), P["hole_marker_z"]))
    print("  Обшивка-скан: %s" % ("загружена" if mesh_obj else "НЕТ"))
    print("-" * 70)
    if bb:
        print("Bounding box (вкл. обшивку): %.0f x %.0f x %.0f мм" % (
            bb.XLength, bb.YLength, bb.ZLength))
    print("Объектов Part::Feature: %d" % n_solid)
    print("=" * 70)
    return doc


DOC = build()
