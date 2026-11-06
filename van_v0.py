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
  X = длина:  0 сзади, +X к кабине;  Y = ширина: 0 центр;  Z = высота: 0 пол.
  СК правая (как во FreeCAD): если смотреть вперёд на кабину (+X), то
    +Y = ЛЕВЫЙ борт  = сторона ВОДИТЕЛЯ (US),
    −Y = ПРАВЫЙ борт = сторона ПАССАЖИРА, там штатная сдвижная дверь US ProMaster.
  (До 2026-11-05 в подписях было наоборот, «+Y пассажир», — геометрия была верной,
   ошибочными были только подписи.)

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

# ─────────────── КОЛЁСНЫЕ АРКИ (внутренние кожухи) — по фото 2026-11-05 ───────────────
WHEEL_ARCH = {
    "enable":     True,
    "center_x":   1000,   # центр колеса: по скану вырез колеса в обшивке X≈700..1300 (на Z=100).
                          # ⚠️ абсолютный X не промерен: по фото 5 задняя стойка ближе к двери → центр может быть ~800
    "len_x":       757,   # длина по полу по ВНУТРЕННЕЙ грани: рулетка фото 2 — 29.8″
    "len_x_wall":  879,   # длина у СТЕНЫ: 34.6″ — так зазор «D-стойка → арка» у стены = 7.4″ (фото 2);
                          # Upfit Supply (ProMaster «Wheel Well 35″ W × 17″ H × 9″ D») — 35″
    "protrusion":  270,   # выступ от стены внутрь, рулетка (фото 1): 10-5/8″ (Upfit: 9″ — от другой базы)
    "height":      432,   # верх над чистовым полом: 17″ — Upfit Supply (по фото 2 — 16–19″)
}

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
    "wheel_arch_x_range": (WHEEL_ARCH["center_x"] - WHEEL_ARCH["len_x_wall"] / 2.0,
                           WHEEL_ARCH["center_x"] + WHEEL_ARCH["len_x_wall"] / 2.0),  # из WHEEL_ARCH (было SEED 520..1650)
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
    "slider_side": -1,  # -1 = правый/passenger борт (-Y) — так у этого фургона (подтверждено 2026-11-05); +1 = левый/driver борт (+Y)
    "rear_w":    1562, "rear_h":   1572, "rear_sill_z": 0,
    "frame_thickness": 15,
}

# ─────────────── ПОЛ: утепление + фанера (по факту, 2026-11-05) ───────────────
# XPS лежит на гребнях рефлёного железного пола, сверху фанера; фанеру прижимают
# металлические полосы поперёк фургона (в модели не рисуем). Все высоты кровати
# ниже (BED[...]_h) отсчитаны от ВЕРХА этой фанеры = «чистовой пол».
FLOOR = {
    "enable":   True,
    "xps_th":   25.4,   # Owens Corning FOAMULAR NGX F-150, 1″ (R-5), 4×8 ft (Home Depot 20WENGX)
    "ply_th":   11.9,   # фанера 1/2″ (фактически 15/32″ = 11.9 мм)
    "edge_gap":  5,     # зазор до борта
}

# ──────────────────────── КРОВАТЬ — как ПОСТРОЕНА (strut) ────────────────────────
# Реконструкция по 16 фото (2026-11-05), см. FURNITURE_MEMORY.md §1a. Масштаб —
# шаг прорезей strut 2″ и рулетка у арки. Точность: высоты ±25 мм, X ±50 мм.
# Поперечная кровать у задних дверей: 4 стойки (по 2 на борт) на пластинах в пол,
# каждая прикручена к заводскому ребру кузова; по бортам — продольные рейки strut,
# между ними 3 съёмные поперечины strut; настил — плита MR ~3/4″; матрас ~10 см.
# Проект июня (ноги до Z=980, 2×4-лаги, фанера 1/2″, смета ~$165) — в git-истории
# и в FURNITURE_MEMORY.md §1.
BED = {
    "enable": True,
    # профиль — Newhouse SC14-10-EG (наклейка на стойках): 1-5/8″ × 13/16″, 14 ga,
    # half-slot, прорези 9/16″ × 1-1/8″ с шагом 2″
    "strut_w":       41.3,   # 1-5/8″
    "strut_d":       20.6,   # 13/16″
    # стойки: прорезями в салон; водительский борт пока считаем симметричным (не подтверждено)
    # X стоек — ОТ АРКИ (фото 2, 2026-11-05): поперечные полосы на полу переносят показания
    # рулетки на стену, масштаб на стене — шаг прорезей стойки. Зазор по полу от внутренней
    # грани арки до грани стойки: сзади 7.7″, спереди 7.1″ (±0.5″). Шаг стоек выходит 1174 мм
    # = 1220 (лист настила) − 41 (ширина стойки): настил перекрывает обе стойки.
    "post_rear_x":   None,   # None = от арки через arch_gap_rear (или задать число)
    "post_front_x":  None,   # None = от арки через arch_gap_front
    "arch_gap_rear":  196,   # 7.7″: грань задней стойки → задний край арки (по внутренней грани)
    "arch_gap_front": 180,   # 7.1″: передний край арки (по внутр. грани) → грань передней стойки
    "post_len":      1257,   # ≈49.5″ — грубо (фото 3, 9), уточнить
    "post_wall_gap":    8,   # зелёная проставка между стойкой и ребром кузова
    "plate":   (102, 127, 1.6),  # оцинк. пластина под стойкой ~4×5″ (X×Y×толщ.), шурупы в фанеру пола
    "body_bolt_h":    762,   # болт стойки в заводское ребро: ~30″ над чистовым полом (фото 2, 3, 4)
    # рама настила
    "rail_top_h":     701,   # верх продольных реек и поперечин: ~27.6″ над чистовым полом (фото 2, 14)
    "rail_raise":     0.0,   # подъём кровати (рейки скользят по прорезям стоек). Был +1″ под отдельные
                             # стяжки этажерки; с 2026-11-06 стяжки = поперечины кровати → не нужен
    "cross_n":          3,   # поперечины strut: у задней стойки, посередине, у передней (съёмные)
    "deck_th":         19,   # плита «MR TIPO/TYPE II … 1220 mm» (влагостойкая MDF/ДСП) ~3/4″
    "deck_len":      1220,   # = ширина листа (маркировка «1220 mm»), от задней грани задней стойки;
                             # None = до передней грани передней стойки (уточнить)
    "mattress_th":    100,   # ~10 см (со слов Dimitri)
    # над настилом, только пассажирский борт: стеновая фанера + брус 2×4 по её верху (фото 3, 4, 15)
    "wall_panel":    True,
    "wall_panel_th":  11.9,
    "ledger_center_above_deck": 450,   # ~17.7″ над настилом
    "ledger_w":        38,   # 2×4: 1.5″ от стены внутрь
    "ledger_h":        89,   #      3.5″ по вертикали
}

# ─────────── ЭТАЖЕРКА ПОД 2 БАТАРЕИ — пассажирский борт, между D-стойкой и аркой ───────────
# Принято 2026-11-05: батарея узкой стороной (7.63″) вдоль борта, задом в D-стойку, прижата к
# внутренней грани задней стойки кровати (стойка — между батареей и бортом). Зазор до арки ≈0 —
# Dimitri «запихает». Этажерка (проект 2026-11-06): у борта — задняя стойка кровати P1 и НОВАЯ
# такая же P2 у переднего края батареи; со стороны салона — короткие P3, P4 по углам батарей;
# полка — 2 рейки strut поперёк + фанера 1/2″. Сборка при снятом настиле: нижняя батарея → полка
# на болтах → верхняя батарея. Координаты привязаны к задней стойке кровати (не к порогу).
BATTERY_RACK = {
    "enable": True,
    "upper":  True,                     # вторая батарея на полке
    "battery": (193.8, 255.8, 249.4),   # Buknuwo 12.8V 150Ah: 7.63″ вдоль X × 10.07″ поперёк × 9.82″, 18.8 кг
    "dpillar_gap":    7.6,              # 0.3″: угол стены (передняя грань D-стойки) за задней гранью P1
    "dpillar_depth":  157.0,            # D-стойка выступает от борта ~6.2″ (проём 1562 при полу ~1880)
    "dpillar_slant":   25.0,            # «уже к центру»: грань уходит назад ~1″ к краю — SEED
    "p2_front_inset":   6.0,            # передняя грань P2 на 6 мм позади передней грани батареи (арка)
    "gap_above_b1":    38.0,            # 1.5″ над нижней батареей — клеммы и кабели
    "shelf_th":        12.0,            # фанера 1/2″ поверх реек
    "post_above_b2":   25.0,            # P3/P4 выше верхней батареи (если без стяжек)
    # верхние стяжки: "bed" — это поперечины кровати (задняя — существующая BedCross_1, передняя —
    # новая), P3/P4 доходят до них (решение Dimitri 2026-11-06); "short" — отдельные короткие
    # стяжки над верхней батареей (нужен подъём кровати на 1″); None — без стяжек
    "top_ties":       "bed",
    "front_cross_full": True,           # передняя стяжка-поперечина на всю ширину (до противоп. рейки)
    "gap_above_b2":    38.0,            # 1.5″ над верхней батареей — клеммы (для "short")
    "p2_body_bolt":    True,            # P2 ↔ ребро кузова на высоте болта P1 (M6: резьба/ривнат)
    "front_stop":     (3.2, 38.0),      # упор-уголок по переднему краю полки: толщина, высота над полкой
    "rubber_block":   (60.0, 120.0),    # резиновый брусок над нижней батареей (X×Y), до низа полки
    "p34_plate": (76, 102, 1.6),        # пластины под P3/P4 (X×Y×толщ.), уходят к центру
}

DOC_NAME    = "van_v0"
_REAL_HOME  = os.environ.get("SNAP_REAL_HOME") or os.path.expanduser("~")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
              else os.path.join(_REAL_HOME, "van-build")
SAVE_PATH   = os.path.join(PROJECT_DIR, "van_v0.FCStd")   # рядом со скриптом (на M6800 = ~/van-build)
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
COL_WOOD     = (0.72, 0.52, 0.30)   # 2×4 деревянные лаги
COL_MATTRESS = (0.40, 0.55, 0.85)   # матрас (визуал)
COL_DECK     = (0.86, 0.80, 0.68)   # настил — плита MR (бежевая)
COL_XPS      = (0.95, 0.62, 0.72)   # XPS FOAMULAR — розовый
COL_ARCH     = (0.78, 0.78, 0.76)   # кожух колёсной арки
COL_BOLT     = (0.15, 0.80, 0.30)   # болт стойки в кузов (зелёная проставка)
COL_BATTERY  = (0.95, 0.42, 0.08)   # LiFePO4 Buknuwo (оранжевый)
COL_DPILLAR  = (0.55, 0.60, 0.65)   # передняя грань D-стойки (реф)

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
    """Полный обруч (борт+крыша) из полу-профиля: борт +Y (левый, водитель)→свод→борт −Y (правый, пассажир).
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

    # ═══════ ПОЛ: XPS + фанера (чистовой пол) ═══════
    floor_top = P["floor_corrugation_height"]          # верх гребней железного пола
    W = WHEEL_ARCH
    arch_ywall = y_at_z(half, 0.0)                     # стена у пола (внутр. поверхность)
    arch_x0 = W["center_x"] - W["len_x_wall"] / 2.0
    arch_x1 = W["center_x"] + W["len_x_wall"] / 2.0

    def _arch_footprint(sgn, zh):
        """Коробка-габарит арки на борту sgn (для вырезов в полу)."""
        y0 = arch_ywall - W["protrusion"] if sgn > 0 else -arch_ywall
        return Part.makeBox(arch_x1 - arch_x0, W["protrusion"], zh,
                            App.Vector(arch_x0, y0, -1.0))

    if FLOOR.get("enable"):
        fl_g = doc.addObject("App::DocumentObjectGroup", "FloorBuildup")
        fl_g.Label = "Пол: XPS F-150 1″ + фанера 1/2″ (по факту)"
        frame.addObject(fl_g)
        fhw = floor_hw - FLOOR["edge_gap"]
        z_xps = floor_top
        z_ply = z_xps + FLOOR["xps_th"]
        cut_h = z_ply + FLOOR["ply_th"] + 10.0
        xps = Part.makeBox(L, 2 * fhw, FLOOR["xps_th"], App.Vector(0.0, -fhw, z_xps))
        ply = Part.makeBox(L, 2 * fhw, FLOOR["ply_th"], App.Vector(0.0, -fhw, z_ply))
        if W.get("enable"):
            for sgn in (+1, -1):
                xps = xps.cut(_arch_footprint(sgn, cut_h))
                ply = ply.cut(_arch_footprint(sgn, cut_h))
        add_shape(doc, "Floor_XPS", "XPS Owens Corning FOAMULAR NGX F-150, %.1f мм (1″)" % FLOOR["xps_th"],
                  xps, color=COL_XPS, transparency=30, group=fl_g)
        add_shape(doc, "Floor_Plywood", "Фанера пола 1/2″ (%.1f мм), прижата полосами" % FLOOR["ply_th"],
                  ply, color=COL_PLY, transparency=20, group=fl_g)
        floor_top = z_ply + FLOOR["ply_th"]            # чистовой пол — от него все высоты кровати

    # ═══════ КОЛЁСНЫЕ АРКИ (внутренние кожухи, упрощённо: полуэллипс по X-Z) ═══════
    arch_shapes = {}
    if W.get("enable"):
        arch_g = doc.addObject("App::DocumentObjectGroup", "WheelArches")
        arch_g.Label = "Колёсные арки (рулетка на фото + Upfit Supply 35×17″)"
        frame.addObject(arch_g)
        b_top = floor_top + W["height"]
        n_seg = 36

        def _half_ellipse(a_half, y):
            pts = [App.Vector(W["center_x"] + a_half * math.cos(math.pi * i / n_seg), y,
                              b_top * math.sin(math.pi * i / n_seg)) for i in range(n_seg + 1)]
            return Part.makePolygon(pts + [pts[0]])

        for sgn, tag in ((+1, "pY"), (-1, "nY")):
            # кожух сужается от стены (len_x_wall) к внутренней грани (len_x): loft двух полуэллипсов
            w_wall = _half_ellipse(W["len_x_wall"] / 2.0, sgn * arch_ywall)
            w_in = _half_ellipse(W["len_x"] / 2.0, sgn * (arch_ywall - W["protrusion"]))
            arch_shapes[sgn] = Part.makeLoft([w_wall, w_in], True)
            add_shape(doc, "WheelArch_%s" % tag,
                      "Колёсная арка %s: у стены %g, по внутр. грани %g, выступ %g, верх Z=%.0f" % (
                          tag, W["len_x_wall"], W["len_x"], W["protrusion"], b_top),
                      arch_shapes[sgn], color=COL_ARCH, transparency=15, group=arch_g)

    # ═══════ КРОВАТЬ — как построена (strut SC14-10-EG), реконструкция по фото ═══════
    bed_summary = None
    B = BED
    if B.get("enable"):
        bed_g = doc.addObject("App::DocumentObjectGroup", "Bed_StrutFrame")
        bed_g.Label = "Кровать (построена) — strut SC14-10-EG, реконструкция по фото 2026-11-05"
        sw, sd = B["strut_w"], B["strut_d"]
        xr, xf = B["post_rear_x"], B["post_front_x"]
        if xr is None:
            xr = W["center_x"] - W["len_x"] / 2.0 - B["arch_gap_rear"] - sw / 2.0
        if xf is None:
            xf = W["center_x"] + W["len_x"] / 2.0 + B["arch_gap_front"] + sw / 2.0
        z_bolt = floor_top + B["body_bolt_h"]
        z_rail_top = floor_top + B["rail_top_h"] + B.get("rail_raise", 0.0)
        z_deck_top = z_rail_top + B["deck_th"]
        z_deck_top_photo = floor_top + B["rail_top_h"] + B["deck_th"]   # брус 2×4 на стойках — не двигается
        yw_post = y_at_z(half, z_bolt)                 # стена (рёбра) на высоте болта
        post_out = yw_post - B["post_wall_gap"]        # грань стойки к стене (|Y|)
        post_in = post_out - sd                        # грань стойки в салон
        rail_in = post_in - sd                         # грань продольной рейки в салон

        def ybase(sgn, y_outer, depth):
            """Y-начало коробки толщиной depth, прижатой к |Y|=y_outer изнутри."""
            return y_outer - depth if sgn > 0 else -y_outer

        cutlist = []   # (что, длина мм) — strut SC14-10-EG

        def strut(name, label, dims, base, what):
            add_box(doc, name, label, dims, base, color=COL_STRUT, group=bed_g)
            cutlist.append((what, float(max(dims))))

        # стойки + пластины + болты в кузов
        px, py, pt = B["plate"]
        post_solids = []
        for x, xtag in ((xr, "rear"), (xf, "front")):
            for sgn, tag in ((+1, "pY"), (-1, "nY")):
                add_box(doc, "BedPostPlate_%s_%s" % (tag, xtag),
                        "Пластина под стойкой %s %s (~4×5″, шурупы в фанеру пола)" % (tag, xtag),
                        (px, py, pt), (x - px / 2.0, ybase(sgn, post_out, py), floor_top),
                        color=COL_STRUT, group=bed_g)
                base = (x - sw / 2.0, ybase(sgn, post_out, sd), floor_top + pt)
                strut("BedPost_%s_%s" % (tag, xtag),
                      "Стойка %s %s X=%g, L=%g (болт в кузов на %.0f над полом)" % (
                          tag, xtag, x, B["post_len"], B["body_bolt_h"]),
                      (sw, sd, B["post_len"]), base, "стойка")
                post_solids.append(Part.makeBox(sw + 6, sd + 6, B["post_len"],
                                                App.Vector(base[0] - 3, base[1] - 3, base[2])))
                add_sphere(doc, "BedPostBodyBolt_%s_%s" % (tag, xtag),
                           "Болт стойки %s %s в заводское ребро, Z=%.0f (~30″ над полом)" % (tag, xtag, z_bolt),
                           9, (x, sgn * (post_out + B["post_wall_gap"] / 2.0), z_bolt),
                           color=COL_BOLT, group=bed_g)

        # продольные рейки по бортам (1-5/8″ по вертикали, открытой стороной в салон)
        rx0, rx1 = xr - sw / 2.0, xf + sw / 2.0
        for sgn, tag in ((+1, "pY"), (-1, "nY")):
            strut("BedSideRail_%s" % tag,
                  "Продольная рейка %s X %.0f..%.0f, верх Z=%.0f" % (tag, rx0, rx1, z_rail_top),
                  (rx1 - rx0, sd, sw), (rx0, ybase(sgn, post_in, sd), z_rail_top - sw), "продольная")

        # 3 съёмные поперечины между рейками
        nC = max(2, int(B["cross_n"]))
        cx0, cx1 = xr + sw / 2.0 + sd / 2.0, xf - sw / 2.0 - sd / 2.0
        for i in range(nC):
            cx = cx0 + (cx1 - cx0) * i / (nC - 1)
            strut("BedCross_%d" % (i + 1),
                  "Поперечина #%d X=%.0f (съёмная), L=%.0f" % (i + 1, cx, 2 * rail_in),
                  (sd, 2 * rail_in, sw), (cx - sd / 2.0, -rail_in, z_rail_top - sw), "поперечина")

        # настил (MR-плита) с вырезами под стойки + матрас
        dx0 = xr - sw / 2.0
        dx1 = xf + sw / 2.0 if not B.get("deck_len") else dx0 + B["deck_len"]
        dhw = y_at_z(half, z_rail_top) - 5.0
        deck = Part.makeBox(dx1 - dx0, 2 * dhw, B["deck_th"], App.Vector(dx0, -dhw, z_rail_top))
        for s in post_solids:
            deck = deck.cut(s)
        add_shape(doc, "BedDeck", "Настил — плита MR Type II %g мм, %.0f×%.0f (вырезы под стойки)" % (
                      B["deck_th"], dx1 - dx0, 2 * dhw),
                  deck, color=COL_DECK, transparency=10, group=bed_g)
        add_box(doc, "BedMattress", "Матрас ~%g мм" % B["mattress_th"],
                (dx1 - dx0, 2 * post_in, B["mattress_th"]), (dx0, -post_in, z_deck_top),
                color=COL_MATTRESS, transparency=55, group=bed_g)

        # над настилом, пассажирский борт (= борт сдвижной двери): стеновая фанера + 2×4
        if B.get("wall_panel"):
            ps = P["slider_side"]
            z_led = z_deck_top_photo + B["ledger_center_above_deck"]
            lx0, lx1 = xr + sw / 2.0, xf - sw / 2.0
            yw_l = y_at_z(half, z_led)
            add_box(doc, "BedWallLedger2x4",
                    "Брус 2×4 по верху стеновой фанеры, центр Z=%.0f (~%.0f над настилом)" % (
                        z_led, B["ledger_center_above_deck"]),
                    (lx1 - lx0, B["ledger_w"], B["ledger_h"]),
                    (lx0, ybase(ps, yw_l, B["ledger_w"]), z_led - B["ledger_h"] / 2.0),
                    color=COL_WOOD, group=bed_g)
            zp0, zp1 = z_deck_top, z_led - B["ledger_h"] / 2.0
            yw_p = y_at_z(half, (zp0 + zp1) / 2.0)
            add_box(doc, "BedWallPanel", "Стеновая фанера над настилом (%s)" % ("-Y" if ps < 0 else "+Y"),
                    (lx1 - lx0, B["wall_panel_th"], zp1 - zp0),
                    (lx0, ybase(ps, yw_p, B["wall_panel_th"]), zp0),
                    color=COL_PLY, transparency=25, group=bed_g)

        bed_summary = dict(
            floor_top=floor_top, z_rail_top=z_rail_top, z_deck_top=z_deck_top, z_bolt=z_bolt,
            posts=(xr, xf), post_y=post_out - sd / 2.0, deck=(dx0, dx1), deck_w=2 * dhw,
            garage=z_rail_top - sw - floor_top, arch_top=floor_top + W["height"],
            cutlist=cutlist)

    # ═══════ ЭТАЖЕРКА ПОД 2 БАТАРЕИ (борт −Y, между D-стойкой и аркой) ═══════
    rack_summary = None
    R = BATTERY_RACK
    if B.get("enable") and R.get("enable"):
        rk_g = doc.addObject("App::DocumentObjectGroup", "BatteryRack")
        rk_g.Label = ("Этажерка: батареи Buknuwo 150Ah между D-стойкой и аркой (пассажирский борт)"
                      " — УТВЕРЖДЕНО 2026-11-06")
        ps = P["slider_side"]                          # пассажирский борт (−Y)
        bx, by, bz = R["battery"]
        X0 = xr - sw / 2.0 - R["dpillar_gap"]          # задняя грань батарей = передняя грань D-стойки
        X1 = X0 + bx                                   # передняя грань батарей (к арке)
        y_wall_side = post_in                          # батареи прижаты к внутр. граням стоек у борта
        y_in_side = post_in - by                       # грань батарей к центру фургона
        pt = B["plate"][2]
        z_b1 = floor_top + pt                          # нижняя стоит на пластинах стоек
        z_b1_top = z_b1 + bz
        z_rail0 = z_b1_top + R["gap_above_b1"]
        z_rail1 = z_rail0 + sw                         # рейки полки 1-5/8″ по вертикали
        z_b2 = z_rail1 + R["shelf_th"]
        z_b2_top = z_b2 + bz
        ties = R.get("top_ties")
        if ties == "bed":                              # стяжки = поперечины кровати (под настилом)
            z_tie0, z_tie1 = z_rail_top - sw, z_rail_top
        else:                                          # отдельные стяжки над верхней батареей
            z_tie0 = z_b2_top + R["gap_above_b2"]
            z_tie1 = z_tie0 + sw
        z_p34_top = z_tie1 if ties else z_b2_top + R["post_above_b2"]
        shapes = {}

        def rk_box(name, label, dims, base, color, tr=0):
            add_box(doc, name, label, dims, base, color=color, transparency=tr, group=rk_g)
            shapes[name] = Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base))
            return shapes[name]

        # передняя грань D-стойки (реф): от борта на dpillar_depth, к центру уходит назад на slant
        ywall0 = y_at_z(half, 0.0)
        y_dp_in = ywall0 - R["dpillar_depth"]
        dz = z_b2_top + 100.0
        pts = [App.Vector(X0, ps * ywall0, 0.0), App.Vector(X0 - R["dpillar_slant"], ps * y_dp_in, 0.0),
               App.Vector(X0 - R["dpillar_slant"] - 12.0, ps * y_dp_in, 0.0), App.Vector(X0 - 12.0, ps * ywall0, 0.0)]
        dp = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0, 0, dz))
        add_shape(doc, "DPillarFace_nY_ref",
                  "Передняя грань D-стойки (реф; привязана к задней стойке кровати, скос — SEED)",
                  dp, color=COL_DPILLAR, transparency=40, group=rk_g)

        # батареи
        bat1 = rk_box("Battery_Lower", "Батарея нижняя Buknuwo 12.8V 150Ah (7.63″ вдоль борта)",
                      (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b1), COL_BATTERY)
        if R.get("upper"):
            rk_box("Battery_Upper", "Батарея верхняя Buknuwo 12.8V 150Ah (на полке)",
                   (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b2), COL_BATTERY)

        # P2 — новая стойка у борта, такая же, как задняя P1; передняя грань — у арки
        p2x1 = X1 - R["p2_front_inset"]
        p2x0 = p2x1 - sw
        ppx, ppy, _ = B["plate"]
        rk_box("RackPostPlate_P2", "Пластина под новой стойкой P2 (сдвинута назад — спереди арка)",
               (ppx, ppy, pt), (p2x1 - ppx, ybase(ps, post_out, ppy), floor_top), COL_STRUT)
        rk_box("BedPost_nY_rackP2", "Стойка P2 (новая, как задняя; L=%g) — болт к продольной рейке кровати" % B["post_len"],
               (sw, sd, B["post_len"]), (p2x0, ybase(ps, post_out, sd), floor_top + pt), COL_STRUT)
        add_sphere(doc, "RackP2_RailBolt", "Болт P2 ↔ продольная рейка кровати", 9,
                   ((p2x0 + p2x1) / 2.0, ps * post_in, z_rail_top - sw / 2.0), color=COL_BOLT, group=rk_g)
        if R.get("p2_body_bolt"):
            add_sphere(doc, "RackP2_BodyBolt",
                       "Болт P2 в ребро кузова M6 (новая резьба/ривнат) на высоте болта P1, Z=%.0f" % z_bolt,
                       9, ((p2x0 + p2x1) / 2.0, ps * (post_out + B["post_wall_gap"] / 2.0), z_bolt),
                       color=COL_BOLT, group=rk_g)

        # рейки полки поперёк фургона (под краями батареи), от стоек у борта до P3/P4
        for nm, x0 in (("Rear", X0), ("Front", X1 - sd)):
            rk_box("RackShelfRail_%s" % nm, "Рейка полки %s strut, L=%.0f" % (nm, by + sd),
                   (sd, by + sd, sw), (x0, ybase(ps, y_wall_side, by + sd), z_rail0), COL_STRUT)
        rk_box("RackShelfPlate", "Полка — фанера 1/2″ %.0f×%.0f" % (bx, by),
               (bx, by, R["shelf_th"]), (X0, ybase(ps, y_wall_side, by), z_rail1), COL_PLY, tr=10)
        # упор верхней батареи вперёд (арка на этой высоте уже не держит): уголок на передней рейке
        if R.get("front_stop"):
            st, sh = R["front_stop"]
            rk_box("RackShelfFrontStop", "Упор-уголок по переднему краю полки (держит верхнюю батарею вперёд)",
                   (st, by, (z_b2 + sh) - z_rail0), (X1, ybase(ps, y_wall_side, by), z_rail0), COL_STRUT)
        # резиновый брусок: нижняя батарея не подпрыгивает (ставить не над клеммами)
        if R.get("rubber_block"):
            rbx, rby = R["rubber_block"]
            rk_box("RackRubberBlock", "Резиновый брусок над нижней батареей (до низа полки)",
                   (rbx, rby, z_rail1 - z_b1_top),
                   ((X0 + X1 - rbx) / 2.0, ybase(ps, y_wall_side - (by - rby) / 2.0, rby), z_b1_top),
                   (0.15, 0.15, 0.15))

        # P3/P4 — короткие стойки со стороны салона, по углам батарей
        qx, qy, qt = R["p34_plate"]
        # P3 — по X как P1 (передняя грань упирается в заднюю поперечину кровати), P4 — у переднего угла
        p3x0 = xr - sw / 2.0 if ties == "bed" else X0
        for nm, x0 in (("P3", p3x0), ("P4", X1 - sw)):
            rk_box("RackPostPlate_%s" % nm, "Пластина под %s" % nm,
                   (qx, qy, qt), (x0 + sw / 2.0 - qx / 2.0, ybase(ps, y_in_side, qy), floor_top), COL_STRUT)
            rk_box("RackPost_%s" % nm, "Стойка %s (со стороны салона), L=%.0f" % (nm, z_p34_top - floor_top - qt),
                   (sw, sd, z_p34_top - floor_top - qt), (x0, ybase(ps, y_in_side, sd), floor_top + qt), COL_STRUT)

        # верхние стяжки
        front_cross_len = None
        if ties == "short":                            # над верхней батареей, от стоек у борта до P3/P4
            for nm, x0 in (("Rear", X0), ("Front", X1 - sd)):
                rk_box("RackTopTie_%s" % nm, "Верхняя стяжка %s strut, L=%.0f" % (nm, by + sd),
                       (sd, by + sd, sw), (x0, ybase(ps, y_wall_side, by + sd), z_tie0), COL_STRUT)
        elif ties == "bed":
            # задняя = BedCross_1 (передняя грань P1 и P3); передняя — новая, сразу перед P4
            if R.get("front_cross_full"):
                front_cross_len = 2 * rail_in
                fy0 = -rail_in
            else:
                front_cross_len = rail_in - (y_in_side - sd)
                fy0 = ybase(ps, rail_in, front_cross_len)
            rk_box("BedCross_RackFront",
                   "Поперечина-стяжка перед P4 (под настилом), L=%.0f%s" % (
                       front_cross_len, " — на всю ширину" if R.get("front_cross_full") else ""),
                   (sd, front_cross_len, sw), (X1, fy0, z_tie0), COL_STRUT)
            cutlist.append(("поперечина-стяжка", float(front_cross_len)))

        # зазоры для сводки
        gap_arch = bat1.distToShape(arch_shapes[ps])[0] if ps in arch_shapes else None
        p2_arch = shapes["BedPost_nY_rackP2"].distToShape(arch_shapes[ps])[0] if ps in arch_shapes else None
        rack_summary = dict(
            X=(X0, X1), z_b1=(z_b1, z_b1_top), z_rail=(z_rail0, z_rail1), z_b2=(z_b2, z_b2_top),
            p2=(p2x0, p2x1), gap_arch=gap_arch, p2_arch=p2_arch,
            above_b2=(z_rail_top - sw) - z_b2_top, p34_len=z_p34_top - floor_top - qt,
            rail_len=by + sd, floor_top=floor_top,
            tie=(z_tie0, z_tie1) if ties else None, ties=ties, front_cross_len=front_cross_len,
            tie_to_bed=(z_rail_top - sw) - z_tie1 if ties == "short" else None,
            b2_to_tie=z_tie0 - z_b2_top if ties else None)

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
    # створки задней двери: водительская на +Y (слева по ходу), пассажирская на −Y
    add_box(doc, "RearDoorLeaf_Driver", "Створка задней двери со стороны водителя (+Y, слева по ходу; реф)",
            (t, leaf_w, P["rear_h"]),
            (-t, 0.0, P["rear_sill_z"]),
            color=COL_REAR, transparency=72, group=op)
    add_box(doc, "RearDoorLeaf_Passenger", "Створка задней двери со стороны пассажира (−Y, справа по ходу; реф)",
            (t, leaf_w, P["rear_h"]),
            (-t, -leaf_w, P["rear_sill_z"]),
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
        ff = bs["floor_top"]
        def _h(z):
            return "Z=%.0f (%.0f мм / %.1f″ над чистовым полом)" % (z, z - ff, (z - ff) / 25.4)
        print("[Кровать — как построена; strut SC14-10-EG; реконструкция по фото 2026-11-05]")
        print("  Чистовой пол (верх фанеры): Z=%.1f  (гребни %.0f + XPS %.1f + фанера %.1f)" % (
            ff, P["floor_corrugation_height"], FLOOR["xps_th"], FLOOR["ply_th"]))
        print("  Стойки: 4, X=%s, |Y|=%.0f; болт в кузов %s" % (
            [int(v) for v in bs["posts"]], bs["post_y"], _h(bs["z_bolt"])))
        print("  Верх реек/поперечин: %s;  верх настила: %s" % (_h(bs["z_rail_top"]), _h(bs["z_deck_top"])))
        print("  Настил X=%.0f..%.0f (%.0f мм), поперёк %.0f мм" % (
            bs["deck"][0], bs["deck"][1], bs["deck"][1] - bs["deck"][0], bs["deck_w"]))
        print("  «Гараж» под кроватью: %.0f мм (%.1f″);  над аркой: %.0f мм" % (
            bs["garage"], bs["garage"] / 25.4, bs["z_rail_top"] - 41.3 - bs["arch_top"]))
        kinds = {}
        for what, Lp in bs["cutlist"]:
            kinds.setdefault(what, []).append(Lp)
        print("  Strut по деталям: " + "; ".join(
            "%s %d×%.0f" % (k, len(v), v[0]) for k, v in kinds.items()))
        print("  Strut всего: %.2f м" % (sum(Lp for _, Lp in bs["cutlist"]) / 1000.0))
    if rack_summary:
        rs = rack_summary
        f0 = rs["floor_top"]
        print("[Этажерка под 2 батареи Buknuwo 150Ah — пассажирский борт, D-стойка ↔ арка]")
        print("  Батареи по X: %.0f..%.0f (7.63″ вдоль борта); зазор нижней до арки: %s" % (
            rs["X"][0], rs["X"][1], "%.1f мм" % rs["gap_arch"] if rs["gap_arch"] is not None else "—"))
        print("  Нижняя: %.0f..%.0f мм над полом;  рейки полки: %.0f..%.0f;  верхняя: %.0f..%.0f" % (
            rs["z_b1"][0] - f0, rs["z_b1"][1] - f0, rs["z_rail"][0] - f0, rs["z_rail"][1] - f0,
            rs["z_b2"][0] - f0, rs["z_b2"][1] - f0))
        print("  Над верхней батареей до низа реек кровати: %.0f мм (%.1f″)" % (rs["above_b2"], rs["above_b2"] / 25.4))
        if rs["ties"] == "short":
            print("  Верхние стяжки: %.0f..%.0f над полом; до низа реек кровати: %.0f мм" % (
                rs["tie"][0] - f0, rs["tie"][1] - f0, rs["tie_to_bed"]))
        elif rs["ties"] == "bed":
            print("  Стяжки = поперечины кровати (%.0f..%.0f над полом): задняя BedCross_1 + передняя L=%.0f;"
                  " от верхней батареи до них %.0f мм" % (
                      rs["tie"][0] - f0, rs["tie"][1] - f0, rs["front_cross_len"], rs["b2_to_tie"]))
        print("  Новая стойка P2 X=%.0f..%.0f, до арки %s;  P3/P4 L=%.0f;  рейки полки 2×%.0f" % (
            rs["p2"][0], rs["p2"][1], "%.1f мм" % rs["p2_arch"] if rs["p2_arch"] is not None else "—",
            rs["p34_len"], rs["rail_len"]))
    print("-" * 70)
    if bb:
        print("Bounding box (вкл. обшивку): %.0f x %.0f x %.0f мм" % (
            bb.XLength, bb.YLength, bb.ZLength))
    print("Объектов Part::Feature: %d" % n_solid)
    print("=" * 70)
    return doc


DOC = build()
