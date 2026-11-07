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
    "len_x":       757,   # длина по полу по ВНУТРЕННЕЙ грани (до острых углов, без скруглений в плане):
                          # рулетка фото 2 (2026-11-05) — 29.8″
    "len_x_wall":  900,   # длина у СТЕНЫ у пола: 35.4″ (Upfit Supply «Wheel Well 35″ W × 17″ H × 9″ D» — 35″).
                          # Фото сверху 2026-11-06: задняя грань арки к центру уходит ВПЕРЁД 0.30″ на 1″
                          # (4 фото: 0.24–0.34) → (900 − 757)/2/239 = 0.30 ✓ (было 879 — от старого зазора 7.4″)
    "protrusion":  239,   # выступ от стены (скан) у пола: фото сверху 2026-11-06 — 8.78″ (223 мм) от края
                          # фанеры (пасс. 8.89″, вод. 8.66″) + 16 мм край фанеры ↔ стена. Upfit: «9″ D» ✓.
                          # (было 270 — рулетка 2026-11-05, 10-5/8″, база не та)
    "plan_round":   58,   # скругление углов арки в плане у пола: задний внутренний угол по фото — R≈2.3″
    "height":      432,   # верх над чистовым полом: 17″ — Upfit Supply (по фото 2 — 16–19″)
    # форма (2026-11-06, по фото 7 и 1): сбоку — суперэллипс |x/a|^n + (z/b)^n = 1 (n=2 — эллипс);
    # по силуэту на фото 7 на 84% высоты арка ещё 78% длины → n≈3.4 («квадратнее» эллипса).
    # Верхняя внутренняя кромка скруглена (купол, фото 1/7) — радиус оценочный, промерить.
    "profile_n":   3.4,
    "top_round":   100,
}

# ─────────────── D-СТОЙКИ у пола (оба борта) — по 4 фото сверху с рулеткой, 2026-11-06 ───────────────
# Внизу D-стойки — штампованный короб (с овальными отверстиями), в него упирается фанера пола; позади
# короба — уплотнитель задней двери. Привязка — к задней грани арки (абсолютный X от порога не промерен):
# зазор «передняя грань короба ↔ задняя грань арки» по полу у края фанеры: пасс. 10.60″, вод. 10.54″
# (±0.2″); в 1.1″ от стены — 11.0″, в 2.4″ — 11.6″, в 5″ — 12.9″ (арка к центру уходит вперёд, короб — назад).
# Пиксельные точки и расчёт: tools/photo_corners_2026-11-06.py → docs/rear_corners_points.json.
# Проверка: уплотнитель двери выходит на X≈144 — рядом с задней рамой по скану (X≈160).
DPILLAR = {
    "to_arch":     268.5,   # 10.57″: передняя грань короба ↔ задняя грань арки, по полу у края фанеры
    "photo_wall":   16.0,   # край фанеры («стена» на фото) — на 16 мм внутрь от стены скана у пола
    "box_depth":   132.0,   # короб выступает от края фанеры на 5.2″ (4 фото: 4.9–5.5″)
    "box_slant":    26.0,   # его передняя грань к центру уходит НАЗАД 0.20″ на 1″ (−0.18…−0.22) → 26 мм
    "box_len":     142.0,   # от передней грани назад до уплотнителя задней двери ~5.6″ (фото 1, 3)
    "box_h":       100.0,   # ⚠️ высота короба над чистовым полом — ОЦЕНКА (~4″), промерить
    "body_depth":  157.0,   # сама стойка выше короба: выступ ~6.2″ (проём 1562 при полу ~1880)
    "body_slant":  125.0,   # её передняя грань к центру уходит назад ~5″ на 6.2″ (оценка по фото 2026-11-05)
    "ref_top":     850.0,   # реф в модели — до уровня настила кровати (выше не мешает и закрывает виды)
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
    "rib_positions_x": [160, 1818, 3068],  # SEED: задняя рама + 2 рамы сдвижной двери (края проёма, см. slider_*)
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
    # проём сдвижной: 1250×1755 (каталог Ducato). Передний край 3068 — задний край 1818: по фото 20
    # (2026-11-06) край проёма в 8.6″ перед передней стойкой кровати; сходится с окном на скане (≈3066)
    "slider_w":  1250, "slider_h": 1755, "slider_front_from_rear": 3068, "slider_sill_z": 0,
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
    # 2026-11-06 (фото сверху с рулеткой): центр задней стойки — в 3.24″ (пасс.) / 3.96″ (вод.) от передней
    # грани короба D-стойки → берём среднее 91 мм (стойки по бортам в модели одинаковые; разница 18 мм).
    # Старый замер «от арки» (7.7″/7.1″ по полу, ±0.5″) давал на 27 мм дальше вперёд — фото сверху точнее.
    "post_rear_x":   None,   # None = от D-стойки через post_from_dpillar (или задать число)
    "post_front_x":  None,   # None = post_rear_x + post_spacing
    "post_from_dpillar": 91.0,
    "post_spacing":  1174.3, # = 1220 (лист настила) − 41 (ширина стойки): настил перекрывает обе стойки
    "post_len":      1257,   # ≈49.5″ — грубо (фото 3, 9), уточнить
    "post_wall_gap":    8,   # зелёная проставка между стойкой и ребром кузова
    "plate":   (79.4, 127, 0.9),  # пластина под стойкой — Simpson TP35 3-1/8×5″, 20 ga (опознана и промерена
                                  # на фото сверху 2026-11-06), длинной стороной поперёк, шурупы в фанеру
    "body_bolt_h":    762,   # болт стойки в заводское ребро: ~30″ над чистовым полом (фото 2, 3, 4)
    # рама настила
    "rail_top_h":     701,   # верх продольных реек и поперечин: ~27.6″ над чистовым полом (фото 2, 14)
    "rail_raise":    50.8,   # подъём кровати (рейки скользят по прорезям стоек). 2026-11-06: +2″ (один шаг
                             # прорезей strut) — над баком для воды ~62 мм вместо 12 (ремни, штуцеры, запас
                             # на форму арки). Dimitri: «кровать можно поднимать на любую высоту — это не сложно».
                             # P3/P4 этажерок и бака доходят до поперечин → удлиняются на ту же величину.
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
# внутренней грани задней стойки кровати (стойка — между батареей и бортом). 2026-11-07 — развёрнута
# длинной стороной (10.07″) вдоль борта: по фото сверху до арки 11.1″ (было «≈0, запихает»). Этажерка (проект 2026-11-06): у борта — задняя стойка кровати P1 и НОВАЯ
# такая же P2 у переднего края батареи; со стороны салона — короткие P3, P4 по углам батарей;
# полка — 2 рейки strut поперёк + фанера 1/2″. Сборка при снятом настиле: нижняя батарея → полка
# на болтах → верхняя батарея. Координаты привязаны к задней стойке кровати (не к порогу).
BATTERY_RACK = {
    "enable": True,
    "upper":  True,                     # вторая батарея на полке
    "battery": (193.8, 255.8, 249.4),   # Buknuwo 12.8V 150Ah: 7.63″ × 10.07″ × 9.82″ (выс.), 18.8 кг
    # блоки, где батареи стоят ДЛИННОЙ стороной (10.07″) вдоль борта; в остальных — узкой (7.63″).
    # Задний — развёрнут 2026-11-07 (Dimitri): по фото сверху D-стойка ↔ арка 11.1″ → 10.07″ + 5 мм влезают,
    # проход шире на 2.4″
    "long_along_wall": ("rear",),
    "dpillar_gap":    5.0,              # задняя грань батарей → передняя грань короба D-стойки (резина);
                                        # форма D-стойки — DPILLAR (фото сверху 2026-11-06)
    "p2_front_inset":   6.0,            # грань P2 со стороны арки — на 6 мм внутрь от грани батареи
    "p2_plate": (46.0, 127.0, 0.9),     # пластина под P2 — Simpson TP15 1-13/16×5″ (TP35 3-1/8″ не помещается:
                                        # заходит на пластину P1 или под арку), уходит от арки
    # блоки: "rear" — D-стойка ↔ арка (утв. 2026-11-06); "front" — арка ↔ сдвижная дверь (2026-11-06):
    # то же самое зеркально, задом в передний край арки; P1 — передняя стойка кровати, новая P2 у арки
    "stacks":        ("rear", "front"),
    "arch_gap":         1.5,            # переднему блоку: зазор от батареи до переднего края арки
    "lower_front_stop": (41.3, 60.0),   # обоим блокам: упор нижней батареи вперёд (высота, низ над полом)
    "gap_above_b1":    38.0,            # 1.5″ над нижней батареей — клеммы и кабели
    "shelf_th":        12.0,            # фанера 1/2″ поверх реек
    "post_above_b2":   25.0,            # P3/P4 выше верхней батареи (если без стяжек)
    # верхние стяжки: "bed" — это поперечины кровати (задняя — существующая BedCross_1, передняя —
    # новая), P3/P4 доходят до них (решение Dimitri 2026-11-06); "short" — отдельные короткие
    # стяжки над верхней батареей (нужен подъём кровати на 1″); None — без стяжек
    "top_ties":       "bed",
    "front_cross_full": True,           # передняя стяжка-поперечина на всю ширину (до противоп. рейки)
    "gap_above_b2":    38.0,            # 1.5″ над верхней батареей — клеммы (для "short")
    "p2_body_bolt":    True,            # P2 ↔ силовая рама кузова на высоте болта P1: новая резьба M6
                                        # (Dimitri: там толстый металл, не 1.5 мм)
    "front_stop":     (3.2, 38.0),      # упор-уголок по переднему краю полки: толщина, высота над полкой
    "rubber_block":   (60.0, 120.0),    # резиновый брусок над нижней батареей (X×Y), до низа полки
    "p34_plate": (76, 102, 1.6),        # пластины под P3/P4 (X×Y×толщ.), уходят к центру
}

# ─────────── БАК ДЛЯ ВОДЫ у водительской арки (между D-стойкой и аркой) — УТВЕРЖДЕНО 2026-11-06 ───────────
# (схема утверждена; подъём и отступ уточнить замерами арки — FURNITURE_MEMORY.md §1d)
# TORVA 33 gal (125 л), Amazon B0FBLCF2DN — по форме клон NW Conversions SP-L-33 (водительская версия:
# «нога» бака позади арки). 48 × 12.5 × 20″, пустой 11 кг, полный ≈136 кг. Продавец: «для ProMaster
# поднять на 3.5″»; «не подвешивать на ремнях и не класть на бак груз» → дно опирается на подставку.
# Тоннель под арку — со стороны стены, открыт спереди и снизу (чертёж продавца: 235 × 325, R≈121).
# Локальные координаты бака: u — от ПЕРЕДНЕГО (открытого) торца назад, v — от задней (к стене) грани
# в салон, h — от дна вверх. Стойки кровати у стены оказываются между баком и бортом.
WATER_TANK = {
    "enable": True,
    "side":   +1,                       # +1 = водительский борт (+Y)
    "size":   (1220.0, 320.0, 508.0),   # u × v × h
    "tunnel_depth": 235.0,              # от задней грани (стены) — внутренняя стенка тоннеля
    "tunnel_r":     121.0,              # скругление потолок↔внутренняя стенка (по скрытым линиям; R146 — по воде)
    # профиль тоннеля (u, h) у стены (потолок 325) и у внутренней стенки (там, где кончается скругление, h=204)
    "tunnel_wall": [(-10, -10), (-10, 325), (618, 325), (808, 261), (863, 220), (899, 165), (925, 120),
                    (945, 82), (982, 16), (995, -10)],
    "tunnel_in":   [(-10, -10), (-10, 204), (618, 204), (680, 196), (725, 179), (760, 147), (794, 101),
                    (820, 60), (838, 27), (850, -10)],
    "foot_u":       985.0,              # «нога» (сплошная часть позади арки) — от u=985 до 1220 по дну
    # зад бака от стены у пола, мм. Стойки кровати — между баком и бортом. None = вплотную к стойкам кровати
    # (их внутренняя грань + post_gap). До фото сверху 2026-11-06 зазор D-стойка ↔ арка считался 7.2″, и бак
    # отодвигали от стены на 120 мм ради скошенной D-стойки; по фото он 10.6″ — «нога» бака влезает и у стены.
    "wall_standoff": None,
    "dpillar_gap":    5.0,              # задний торец бака → передняя грань короба D-стойки (резиновая прокладка)
    "over_box":      15.0,              # торец бака нависает над коробом D-стойки (дно бака выше короба; доски
                                        # подставки — перед коробом). Нужный подъём (фото 2026-11-06): 0 → 142 мм,
                                        # 10 → 136, 15 → ~134, 20 → 133, 30 → 129 (до стойки над коробом 4 мм).
                                        # ⚠️ высота короба не промерена: если она > ~5″ — ставить 0 (+фанера 3/4″)
    "lift":          None,              # подъём дна над чистовым полом; None = подобрать из riser_stacks
    "arch_clear":     8.0,              # минимальный зазор бак ↔ арка при подборе подъёма
    # подставка: доски на ребро (+ фанера сверху); варианты (высота мм, что, толщина фанеры сверху) —
    # берётся первый ≥ нужного подъёма
    "riser_stacks": ((38.0, "доски 2×4 плашмя (1.5″), без фанеры", 0.0),
                     (57.0, "доски 2×4 плашмя (1.5″) + фанера 3/4″", 19.0),
                     (89.0, "2×4 на ребро (3.5″), без фанеры; под полосой — 2 доски рядом", 0.0),
                     (108.0, "2×4 на ребро (3.5″) + фанера 3/4″", 19.0),
                     (120.0, "2×4 на ребро (3.5″) + фанера 3/4″ + 1/2″", 31.0),
                     (127.0, "2×4 на ребро (3.5″) + фанера 3/4″ × 2", 38.0),
                     (140.0, "2×6 на ребро (5.5″), без фанеры; под полосой — 2 доски рядом", 0.0),
                     (159.0, "2×6 на ребро (5.5″) + фанера 3/4″", 19.0)),
    "post_gap":       3.0,              # P3/P4 → грань бака со стороны салона (резина)
    "p34_plate":  (76, 102, 1.6),
}

# ─────────── ДУШ + МИНИ-КУХНЯ по водительскому борту: от кровати к кабине — проект 2026-11-06 ───────────
# Dimitri: «между кроватью и водительским сиденьем — душевая и кухонный блок; придумывай сам»;
# кухня — совсем маленькая: вскипятить чай и помыть одну чашку. Место у водительской стены от края
# настила (X≈1604) до плоскости спинок сидений (X≈3190; Upfit: стена водителя 111″ от задней рамы) ≈62.7″.
# Задние панели — в wall_gap от обшивки (рёбра кузова ~55 мм + будущий утеплитель); всё, что выше
# ~1.1 м, повторяет завал борта к крыше (профиль из скана).
SHOWER_KITCHEN = {
    "enable": True,
    "side": +1,                     # водительский борт
    "wall_gap": 60.0,
    "gap_bed": 27.0,                # от переднего края настила до задней стенки душа (пластина передней
                                    # стойки кровати 4×5″ выступает на ~1″ вперёд — душ её не задевает)
    "panel": 19.0,                  # стенки — фанера 3/4″ (в душе — + панели FRP)
    # душ: поддон RV 32×32″ низкий (~3.5″) прямо на фанере пола; потолок душа — под крышей
    "shower_in": (813.0, 813.0),    # внутри: вдоль борта × от стены
    "pan_h": 89.0,
    "pan_recess": True,             # поддон утоплен в пол: под ним вырезаны фанера+XPS, стоит на железе (+1.5″ высоты)
    "roof_clear": 55.0,             # потолок душа ниже железа крыши (под дугами крыши + утеплитель)
    # мини-кухня
    "kitchen_end_x": 3150.0,        # ~40 мм до плоскости спинок (сиденье не упирается)
    "kitchen_depth": 560.0,         # 22″ от задней панели
    "counter_h": 914.0,             # 36″ — верх столешницы над чистовым полом
    "counter_th": 25.0,             # мебельный щит/butcher block 1″
    "sink": (305.0, 305.0, 140.0),  # барная мойка 12×12″, глубина 5.5″
    "fridge": (597.0, 368.0, 445.0),  # 12V ларь ~30 qt (габарит-заглушка: подобрать модель ≤$300, кувшин 10″)
    "fridge_slide": 400.0,          # выдвигается в проход на 400 мм, чтобы открыть крышку
    "plinth": (80.0, 60.0),         # цоколь: высота, отступ
    "upper": (1450.0, 300.0),       # верхний шкафчик: низ над полом, глубина
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

    def arch_a_lin(d):
        """Полудлина арки у пола на расстоянии d от стены (грани скошены, без скругления углов)."""
        return (W["len_x_wall"] - (W["len_x_wall"] - W["len_x"]) * d / W["protrusion"]) / 2.0

    # D-стойки у пола: передняя грань короба (X) у края фанеры — от задней грани арки (фото сверху 2026-11-06)
    DP = DPILLAR
    x_dp = W["center_x"] - arch_a_lin(DP["photo_wall"]) - DP["to_arch"]

    def dp_box_x(d):
        """X передней грани короба D-стойки на расстоянии d от стены (у пола, до box_h)."""
        return x_dp - DP["box_slant"] * (d - DP["photo_wall"]) / DP["box_depth"]

    def dp_body_x(d):
        """X передней грани самой D-стойки (выше короба) на расстоянии d от стены."""
        return x_dp - DP["body_slant"] * d / DP["body_depth"]

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
        n_seg = 72
        n_exp = float(W.get("profile_n", 2.0))
        r_top = float(W.get("top_round", 0.0))
        prot = W["protrusion"]

        def _half_super(a_half, y, b):
            """Сечение арки в плоскости |Y|=const: суперэллипс от пола (Z=0) до b."""
            pts = []
            for i in range(n_seg + 1):
                t = math.pi * i / n_seg
                c, s_ = math.cos(t), math.sin(t)
                pts.append(App.Vector(W["center_x"] + a_half * math.copysign(abs(c) ** (2.0 / n_exp), c), y,
                                      b * abs(s_) ** (2.0 / n_exp)))
            return Part.makePolygon(pts + [pts[0]])

        # сечения от стены (d=0) к внутренней грани (d=prot): длина сужается линейно (len_x_wall → len_x,
        # грани скошены), у внутренней грани углы в плане скруглены r_pl; высота — постоянна до начала
        # скругления верхней внутренней кромки, дальше — по дуге r_top
        r_pl = float(W.get("plan_round", 0.0))
        ds = [0.0, prot]
        for r_ in (r_top, r_pl):
            if r_ > 0:
                ds += [prot - r_ + r_ * math.sin(math.radians(ph)) for ph in (0.0, 30.0, 55.0, 75.0)]
        ds = sorted(ds)
        ds = [d for i, d in enumerate(ds) if i == 0 or d - ds[i - 1] > 1.5]

        def _b_at(d):
            if r_top > 0 and d > prot - r_top:
                return b_top - r_top + math.sqrt(max(0.0, r_top ** 2 - (d - (prot - r_top)) ** 2))
            return b_top

        def _a_at(d):
            a = arch_a_lin(d)
            if r_pl > 0 and d > prot - r_pl:
                a -= r_pl - math.sqrt(max(0.0, r_pl ** 2 - (d - (prot - r_pl)) ** 2))
            return a

        secs = [(d, _b_at(d)) for d in ds]

        for sgn, tag in ((+1, "pY"), (-1, "nY")):
            wires = [_half_super(_a_at(d), sgn * (arch_ywall - d), b) for d, b in secs]
            arch_shapes[sgn] = Part.makeLoft(wires, True, True)
            add_shape(doc, "WheelArch_%s" % tag,
                      "Колёсная арка %s: у стены %g, по внутр. грани %g, выступ %g, верх Z=%.0f; "
                      "сбоку суперэллипс n=%g, скругление верхней внутр. кромки R%g, углов в плане R%g "
                      "(фото сверху 2026-11-06)" % (
                          tag, W["len_x_wall"], W["len_x"], W["protrusion"], b_top, n_exp, r_top, r_pl),
                      arch_shapes[sgn], color=COL_ARCH, transparency=15, group=arch_g)

    # ═══════ D-СТОЙКИ у пола (реф): короб у основания + передняя грань стойки выше него ═══════
    dp_shapes = {}
    dp_g = doc.addObject("App::DocumentObjectGroup", "DPillars")
    dp_g.Label = "D-стойки у пола (реф): короб + грань стойки — фото сверху 2026-11-06"
    frame.addObject(dp_g)
    z_box = floor_top + DP["box_h"]
    d_box = DP["photo_wall"] + DP["box_depth"]
    for sgn, tag in ((+1, "pY"), (-1, "nY")):
        def _prism(pts_xd, z0, z1):
            v = [App.Vector(x, sgn * (arch_ywall - d), z0) for x, d in pts_xd]
            return Part.Face(Part.makePolygon(v + [v[0]])).extrude(App.Vector(0, 0, z1 - z0))
        box_ = _prism([(dp_box_x(0.0), 0.0), (dp_box_x(d_box), d_box),
                       (x_dp - DP["box_len"], d_box), (x_dp - DP["box_len"], 0.0)], 0.0, z_box)
        body_ = _prism([(dp_body_x(0.0), 0.0), (dp_body_x(DP["body_depth"]), DP["body_depth"]),
                        (dp_body_x(DP["body_depth"]) - 40.0, DP["body_depth"]), (dp_body_x(0.0) - 40.0, 0.0)],
                       z_box, DP["ref_top"])
        dp_shapes[sgn] = box_.fuse(body_).removeSplitter()
        add_shape(doc, "DPillarFace_%s_ref" % tag,
                  "D-стойка %s (реф): короб у пола %.1f″ от края фанеры, грань скошена назад 0.2″/1″, высота "
                  "~%.0f″ (оценка); выше — грань стойки (уходит назад ~%.0f мм на выступе %.0f)" % (
                      tag, DP["box_depth"] / 25.4, DP["box_h"] / 25.4, DP["body_slant"], DP["body_depth"]),
                  dp_shapes[sgn], color=COL_DPILLAR, transparency=40, group=dp_g)

    # ═══════ КРОВАТЬ — как построена (strut SC14-10-EG), реконструкция по фото ═══════
    bed_summary = None
    B = BED
    if B.get("enable"):
        bed_g = doc.addObject("App::DocumentObjectGroup", "Bed_StrutFrame")
        bed_g.Label = "Кровать (построена) — strut SC14-10-EG, реконструкция по фото 2026-11-05/06"
        sw, sd = B["strut_w"], B["strut_d"]
        xr, xf = B["post_rear_x"], B["post_front_x"]
        if xr is None:
            xr = x_dp + B["post_from_dpillar"]
        if xf is None:
            xf = xr + B["post_spacing"]
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

    # ═══════ ЭТАЖЕРКИ ПОД БАТАРЕИ (борт −Y): «rear» — D-стойка ↔ арка, «front» — арка ↔ сдвижная ═══════
    rack_summary = []
    R = BATTERY_RACK
    if B.get("enable") and R.get("enable"):
        ps = P["slider_side"]                          # пассажирский борт (−Y)
        b_short, b_long, bz = R["battery"]
        y_wall_side = post_in                          # батареи прижаты к внутр. граням стоек у борта
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
        ppx, ppy, _ = B["plate"]
        qx, qy, qt = R["p34_plate"]

        # передний край арки на расстоянии |Y|=post_in (кожух сужается от стены к центру)
        a_at_post = arch_a_lin(arch_ywall - post_in)
        p2px, p2py, p2pt = R.get("p2_plate", B["plate"])

        for stack in R.get("stacks", ("rear",)):
            front = (stack == "front")
            sfx = "_fwd" if front else ""
            along = stack in R.get("long_along_wall", ())
            bx, by = (b_long, b_short) if along else (b_short, b_long)   # bx — вдоль борта (X)
            y_in_side = post_in - by                   # грань батарей к центру фургона
            rk_g = doc.addObject("App::DocumentObjectGroup", "BatteryRack" + sfx)
            rk_g.Label = ("Этажерка: 2 батареи Buknuwo 150Ah, %s (пассажирский борт) — УТВЕРЖДЕНО 2026-11-06"
                          % ("арка ↔ сдвижная дверь" if front else "D-стойка ↔ арка"))
            shapes = {}

            def rk_box(name, label, dims, base, color, tr=0):
                add_box(doc, name + sfx, label, dims, base, color=color, transparency=tr, group=rk_g)
                shapes[name] = Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base))
                return shapes[name]

            if front:      # батарея задом в передний край арки, к сдвижной двери
                X0 = W["center_x"] + a_at_post + R["arch_gap"]
                X1 = X0 + bx
                p1x = xf                                   # существующая передняя стойка кровати
                p2x0 = X0 + R["p2_front_inset"]; p2x1 = p2x0 + sw
                p2_plate_x0 = p2x0                         # пластина уходит от арки
                p4x0 = X0
                cross_x0 = X0 - sd                         # новая поперечина — со стороны арки от P4
            else:          # батарея задом в короб D-стойки, передом к арке
                # грань короба скошена назад к центру → ближе всего к батарее она у её грани к борту
                X0 = dp_box_x(arch_ywall - post_in) + R["dpillar_gap"]
                X1 = X0 + bx
                p1x = xr
                p2x1 = X1 - R["p2_front_inset"]; p2x0 = p2x1 - sw
                p2_plate_x0 = p2x1 - p2px                  # пластина P2 — назад, от арки
                p4x0 = X1 - sw
                cross_x0 = X1

            # батареи
            bat1 = rk_box("Battery_Lower", "Батарея нижняя Buknuwo 12.8V 150Ah (%.2f″ вдоль борта)" % (bx / 25.4),
                          (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b1), COL_BATTERY)
            if R.get("upper"):
                rk_box("Battery_Upper", "Батарея верхняя Buknuwo 12.8V 150Ah (на полке)",
                       (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b2), COL_BATTERY)

            # P2 — новая стойка у борта, как стойки кровати; со стороны арки
            rk_box("RackPostPlate_P2", "Пластина под новой стойкой P2 — Simpson TP15 1-13/16×5″ (сдвинута от арки)",
                   (p2px, p2py, p2pt), (p2_plate_x0, ybase(ps, post_out, p2py), floor_top), COL_STRUT)
            rk_box("BedPost_nY_rackP2", "Стойка P2 (новая, как стойки кровати; L=%g) — болт к продольной рейке" % B["post_len"],
                   (sw, sd, B["post_len"]), (p2x0, ybase(ps, post_out, sd), floor_top + pt), COL_STRUT)
            add_sphere(doc, "RackP2_RailBolt" + sfx, "Болт P2 ↔ продольная рейка кровати", 9,
                       ((p2x0 + p2x1) / 2.0, ps * post_in, z_rail_top - sw / 2.0), color=COL_BOLT, group=rk_g)
            if R.get("p2_body_bolt"):
                add_sphere(doc, "RackP2_BodyBolt" + sfx,
                           "Болт P2 в раму кузова M6 (новая резьба) на высоте болтов стоек кровати, Z=%.0f" % z_bolt,
                           9, ((p2x0 + p2x1) / 2.0, ps * (post_out + B["post_wall_gap"] / 2.0), z_bolt),
                           color=COL_BOLT, group=rk_g)

            # полка: 2 рейки поперёк фургона под краями батареи + фанера
            for nm, x0 in (("Rear", X0), ("Front", X1 - sd)):
                rk_box("RackShelfRail_%s" % nm, "Рейка полки %s strut, L=%.0f" % (nm, by + sd),
                       (sd, by + sd, sw), (x0, ybase(ps, y_wall_side, by + sd), z_rail0), COL_STRUT)
            rk_box("RackShelfPlate", "Полка — фанера 1/2″ %.0f×%.0f" % (bx, by),
                   (bx, by, R["shelf_th"]), (X0, ybase(ps, y_wall_side, by), z_rail1), COL_PLY, tr=10)
            # упор верхней батареи вперёд (по ходу машины, +X)
            if R.get("front_stop"):
                st, sh = R["front_stop"]
                rk_box("RackShelfFrontStop", "Упор-уголок по переднему краю полки (держит верхнюю батарею вперёд)",
                       (st, by, (z_b2 + sh) - z_rail0), (X1, ybase(ps, y_wall_side, by), z_rail0), COL_STRUT)
            # упор нижней батареи вперёд: у переднего блока спереди арки нет вовсе, у заднего — до арки 3″+
            # (фото сверху 2026-11-06; раньше считали, что нижнюю держит арка)
            if R.get("lower_front_stop"):
                lh, lz = R["lower_front_stop"]
                gap_a = W["center_x"] - arch_a_lin(arch_ywall - post_in) - X1 if not front else 1e9
                if gap_a >= sd + 5.0:          # strut поперёк
                    rk_box("RackLowerFrontStop", "Упор нижней батареи вперёд: strut поперёк, болты к %s" % (
                               "P1/P3" if front else "P2/P4 (уголки)"),
                           (sd, by + sd, lh), (X1, ybase(ps, y_wall_side, by + sd), floor_top + lz), COL_STRUT)
                else:                          # до арки меньше strut → уголок, как у верхней
                    st, sh = R["front_stop"]
                    rk_box("RackLowerFrontStop", "Упор нижней батареи вперёд: уголок 1-1/2″ поперёк, болты к P2/P4 "
                           "(до арки %.0f мм — strut не влезает)" % gap_a,
                           (st, by, sh), (X1, ybase(ps, y_wall_side, by), floor_top + lz), COL_STRUT)
            # резиновый брусок: нижняя батарея не подпрыгивает (ставить не над клеммами)
            if R.get("rubber_block"):
                rbx, rby = R["rubber_block"]
                rk_box("RackRubberBlock", "Резиновый брусок над нижней батареей (до низа полки)",
                       (rbx, rby, z_rail1 - z_b1_top),
                       ((X0 + X1 - rbx) / 2.0, ybase(ps, y_wall_side - (by - rby) / 2.0, rby), z_b1_top),
                       (0.15, 0.15, 0.15))

            # P3/P4 — стойки со стороны салона: P3 по X как стойка кровати P1, P4 — у арки
            p3x0 = p1x - sw / 2.0 if ties == "bed" else (X0 if not front else X1 - sw)
            for nm, x0 in (("P3", p3x0), ("P4", p4x0)):
                rk_box("RackPostPlate_%s" % nm, "Пластина под %s" % nm,
                       (qx, qy, qt), (x0 + sw / 2.0 - qx / 2.0, ybase(ps, y_in_side, qy), floor_top), COL_STRUT)
                rk_box("RackPost_%s" % nm, "Стойка %s (со стороны салона), L=%.0f" % (nm, z_p34_top - floor_top - qt),
                       (sw, sd, z_p34_top - floor_top - qt), (x0, ybase(ps, y_in_side, sd), floor_top + qt), COL_STRUT)

            # верхние стяжки
            cross_len = None
            if ties == "short":
                for nm, x0 in (("Rear", X0), ("Front", X1 - sd)):
                    rk_box("RackTopTie_%s" % nm, "Верхняя стяжка %s strut, L=%.0f" % (nm, by + sd),
                           (sd, by + sd, sw), (x0, ybase(ps, y_wall_side, by + sd), z_tie0), COL_STRUT)
            elif ties == "bed":
                # одна стяжка — существующая поперечина кровати у P1/P3, вторая — новая, у P4 со стороны арки
                if R.get("front_cross_full"):
                    cross_len, fy0 = 2 * rail_in, -rail_in
                else:
                    cross_len = rail_in - (y_in_side - sd)
                    fy0 = ybase(ps, rail_in, cross_len)
                add_box(doc, ("BedCross_RackFront" if not front else "BedCross_Rack_fwd"),
                        "Поперечина-стяжка у P4 (под настилом), L=%.0f%s" % (
                            cross_len, " — на всю ширину" if R.get("front_cross_full") else ""),
                        (sd, cross_len, sw), (cross_x0, fy0, z_tie0), color=COL_STRUT, group=rk_g)
                cutlist.append(("поперечина-стяжка", float(cross_len)))

            arch = arch_shapes.get(ps)
            p1_plate = doc.getObject("BedPostPlate_%s_%s" % ("pY" if ps > 0 else "nY", "front" if front else "rear"))
            rack_summary.append(dict(
                stack=stack, X=(X0, X1), p2=(p2x0, p2x1), bx=bx, by=by, inner_from_wall=arch_ywall - y_in_side,
                gap_arch=bat1.distToShape(arch)[0] if arch else None,
                gap_dpillar=None if front else bat1.distToShape(dp_shapes[ps])[0],
                plates_gap=shapes["RackPostPlate_P2"].distToShape(p1_plate.Shape)[0],
                p2_plate_arch=shapes["RackPostPlate_P2"].distToShape(arch)[0] if arch else None,
                p2_arch=shapes["BedPost_nY_rackP2"].distToShape(arch)[0] if arch else None,
                to_slider=(slider_x0 - X1) if front else None,
                to_deck_edge=(X1 - (xf + sw / 2.0)) if front else None,
                z_b1=(z_b1, z_b1_top), z_rail=(z_rail0, z_rail1), z_b2=(z_b2, z_b2_top),
                above_b2=(z_rail_top - sw) - z_b2_top, p34_len=z_p34_top - floor_top - qt,
                rail_len=by + sd, floor_top=floor_top, ties=ties, cross_len=cross_len,
                tie=(z_tie0, z_tie1) if ties else None,
                tie_to_bed=(z_rail_top - sw) - z_tie1 if ties == "short" else None))

    # ═══════ БАК ДЛЯ ВОДЫ у водительской арки (D-стойка ↔ арка), на подставке ═══════
    tank_summary = None
    T = WATER_TANK
    if B.get("enable") and T.get("enable") and W.get("enable"):
        ts = T["side"]
        tg = doc.addObject("App::DocumentObjectGroup", "WaterTank")
        tg.Label = "Бак для воды TORVA 33 gal (125 л) — водительский борт, D-стойка ↔ арка — УТВЕРЖДЕНО 2026-11-06"
        TL, TD, TH = T["size"]
        tdep, tr = T["tunnel_depth"], T["tunnel_r"]

        # — тело бака в локальных координатах (u→x, v→y, h→z) —
        def _sec(pts, v):
            return Part.makePolygon([App.Vector(u, v, h) for u, h in pts] +
                                    [App.Vector(pts[0][0], v, pts[0][1])])
        pw, pi_ = T["tunnel_wall"], T["tunnel_in"]
        v_flat = tdep - tr
        secs_t = [_sec(pw, -10.0), _sec(pw, v_flat)]
        for ph in (30.0, 55.0, 75.0, 90.0):
            f = math.radians(ph)
            wgt = 1.0 - math.cos(f)
            blend = [((1 - wgt) * a[0] + wgt * b[0], (1 - wgt) * a[1] + wgt * b[1]) for a, b in zip(pw, pi_)]
            secs_t.append(_sec(blend, v_flat + tr * math.sin(f)))
        tunnel_loc = Part.makeLoft(secs_t, True, True)
        tank_loc = Part.makeBox(TL, TD, TH).cut(tunnel_loc)

        # — положение: зад бака в standoff от стены (у пола), задний торец — в короб D-стойки —
        standoff = T["wall_standoff"]
        if standoff is None:                                           # вплотную к стойкам кровати у стены
            standoff = (arch_ywall - post_in) + T["post_gap"]
        y_back = arch_ywall - standoff                                 # |Y| задней грани бака
        # грань короба скошена назад к центру → ближе всего к баку она у его задней (к стене) грани;
        # торец бака может нависать над коробом на over_box (дно выше короба), подставка — перед коробом
        x_dp_tank = dp_box_x(standoff)
        x_riser_r = x_dp_tank + T["dpillar_gap"]                       # задний край подставки
        x_r = x_riser_r - T.get("over_box", 0.0)                       # задний торец бака
        x_f = x_r + TL

        def _place(shape_loc, z_b):
            s = shape_loc.copy()
            if ts > 0:     # u→−X, v→−Y (поворот 180° вокруг Z): зад бака к +Y-стене
                s.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0)
                s.translate(App.Vector(x_f, y_back, z_b))
            else:          # зеркально для −Y (на будущее): u→−X, v→+Y
                s = s.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
                s.translate(App.Vector(x_f, -y_back, z_b))
            return s

        arch = arch_shapes[ts]
        lift = T.get("lift")
        lift_min = None
        stack_txt = ""
        if lift is None:                                               # минимальный подъём по зазору до арки
            lo, hi = 0.0, 200.0
            for _ in range(14):
                mid = (lo + hi) / 2.0
                if _place(tank_loc, floor_top + mid).distToShape(arch)[0] >= T["arch_clear"]:
                    hi = mid
                else:
                    lo = mid
            lift_min = hi
            lift, stack_txt, ply_top = T["riser_stacks"][-1]
            for hgt, txt, pt_ in T["riser_stacks"]:
                if hgt >= lift_min:
                    lift, stack_txt, ply_top = hgt, txt, pt_
                    break
        else:
            ply_top = 19.0
        z_b = floor_top + lift
        tank = _place(tank_loc, z_b)
        add_shape(doc, "WaterTank_TORVA33",
                  "Бак TORVA 33 gal 48×12.5×20″ (полный ≈136 кг), дно %.0f над полом, зад %.0f от стены" % (
                      lift, standoff),
                  tank, color=(0.70, 0.86, 0.98), transparency=25, group=tg)

        # — D-стойка этого борта (реф, общий с этажерками) —
        dpf = dp_shapes[ts]

        # — подставка: фанера сверху по «ноге» и по полосе под внутренней стенкой, доски на ребро/плашмя —
        tp = ply_top                                                  # фанера сверху (0 — без неё)
        fu = T["foot_u"]
        sk_v0 = tdep                                                  # полоса под внутренней стенкой: v 235..320
        riser_parts = []
        riser_notes = []

        def _riser(name, label, dims_loc, base_loc, color, cut=None):
            b = Part.makeBox(dims_loc[0], dims_loc[1], dims_loc[2], App.Vector(*base_loc))
            s = _place(b, floor_top)
            if cut is not None:
                s = s.cut(cut)
            add_shape(doc, name, label, s, color=color, group=tg)
            riser_parts.append(s)
            return s
        if tp > 0:
            _riser("TankRiser_TopFoot", "Подставка: фанера %.0f мм под «ногой» бака %.0f×%.0f" % (tp, TL - fu, TD),
                   (TL - fu, TD, tp), (fu, 0.0, lift - tp), COL_PLY)
            _riser("TankRiser_TopStrip", "Подставка: фанера %.0f мм полосой под внутренней стенкой %.0f×%.0f" % (
                       tp, fu, TD - sk_v0), (fu, TD - sk_v0, tp), (0.0, sk_v0, lift - tp), COL_PLY)
        slh = lift - tp                                               # высота досок
        flat = slh <= 40.0
        bw = 89.0 if flat else 38.0                                   # 2×4 плашмя — 3.5″ вдоль бака
        board = "2×4 плашмя" if flat else ("2×6 на ребро" if slh > 100 else "2×4 на ребро")
        # пластина задней стойки кровати у стены лежит под «ногой»: средняя доска — мимо неё, крайняя — с
        # выборкой 1.5 мм снизу (x = x_f − u)
        pl_bb = doc.getObject("BedPostPlate_%s_rear" % ("pY" if ts > 0 else "nY")).Shape.BoundBox
        keep0, keep1 = pl_bb.XMin - 3.0, pl_bb.XMax + 3.0
        notch = Part.makeBox(pl_bb.XLength + 4.0, pl_bb.YLength + 4.0, pl_bb.ZLength + 0.6 + (floor_top - pl_bb.ZMin),
                             App.Vector(pl_bb.XMin - 2.0, pl_bb.YMin - 2.0, pl_bb.ZMin - 0.1))
        u_rear, u_front = x_f - max(x_r, x_riser_r) - bw, fu          # задняя доска — перед коробом D-стойки
        u_mid = (fu + TL - bw) / 2.0
        x_mid0 = x_f - u_mid - bw
        if x_mid0 < keep1 and x_mid0 + bw > keep0:                    # попала на пластину → вперёд от неё
            x_new = keep1
            if x_new + bw <= x_f - u_front - bw - 3.0:
                u_mid = x_f - x_new - bw
                riser_notes.append("средняя доска «ноги» — перед пластиной задней стойки кровати")
            else:
                u_mid = None
                riser_notes.append("средняя доска «ноги» не нужна (между крайними < 4″)")
        for i, u0 in enumerate(u for u in (u_rear, u_mid, u_front) if u is not None):
            xs0 = x_f - u0 - bw
            over = xs0 < keep1 and xs0 + bw > keep0
            if over:
                riser_notes.append("доска «ноги» #%d — выборка 1.5 мм снизу над пластиной стойки кровати" % (i + 1))
            _riser("TankRiser_Sleeper_Foot%d" % (i + 1), "Доска %s под «ногой», L=%.0f%s" % (
                       board, TD, " (выборка снизу под пластину стойки)" if over else ""),
                   (bw, TD, slh), (u0, 0.0, 0.0), COL_WOOD, cut=notch if over else None)
        n_strip = 1 if (tp > 0 or flat) else 2                        # на ребро без фанеры — 2 доски рядом
        for j in range(n_strip):
            v0 = (sk_v0 + (TD - sk_v0 - bw) / 2.0) if n_strip == 1 else (sk_v0 + 4.0 + j * (bw + 1.0))
            _riser("TankRiser_Sleeper_Strip%d" % (j + 1), "Доска %s вдоль полосы под стенкой бака, L=%.0f" % (
                       board, fu), (fu, bw, slh), (0.0, v0, 0.0), COL_WOOD)

        # — P3/P4 со стороны салона: до верха поперечин кровати, болтами к ним (как у этажерок) —
        qx, qy, qt = T["p34_plate"]
        y_cab = y_back - TD                                           # |Y| грани бака со стороны салона
        y_p_out = y_cab - T["post_gap"]                               # грань стоек к баку
        z_top = z_rail_top
        p_len = z_top - floor_top - qt
        tank_posts = {}
        # P3 — по X как задняя стойка кровати (передней гранью в BedCross_1, как у этажерок);
        # P4 — позади поперечины-стяжки переднего блока батарей (она на всю ширину), передней гранью в неё;
        # если её нет — позади BedCross_3. Обе — в пределах длины бака.
        x4_tie = doc.getObject("BedCross_Rack_fwd")
        if x4_tie is not None and x4_tie.Shape.BoundBox.XMin - sw > x_r + 200.0:
            p4x0, p4note = x4_tie.Shape.BoundBox.XMin - sw, "позади поперечины BedCross_Rack_fwd, болт к ней"
        else:
            p4x0, p4note = xf - sw / 2.0 - sd - sw, "позади поперечины BedCross_3, болт к ней"
        if p4x0 + sw > x_f - 20.0:
            p4x0 = x_f - 20.0 - sw
        for nm, x0, note in (("P3", xr - sw / 2.0, "по X как задняя стойка кровати, болт к BedCross_1"),
                             ("P4", p4x0, p4note)):
            add_box(doc, "TankPostPlate_%s" % nm, "Пластина под %s бака" % nm,
                    (qx, qy, qt), (x0 + sw / 2.0 - qx / 2.0, ybase(ts, y_p_out, qy), floor_top),
                    color=COL_STRUT, group=tg)
            add_box(doc, "TankPost_%s" % nm, "Стойка %s бака (со стороны салона), L=%.0f — %s" % (nm, p_len, note),
                    (sw, sd, p_len), (x0, ybase(ts, y_p_out, sd), floor_top + qt), color=COL_STRUT, group=tg)
            tank_posts[nm] = Part.makeBox(sw, sd, p_len, App.Vector(x0, ybase(ts, y_p_out, sd), floor_top + qt))
            cutlist.append(("стойка бака", float(p_len)))

        # — проставка между задней стойкой кровати (у стены) и задом бака —
        sp_t = post_in - y_back                                       # зазор стойка ↔ бак
        if sp_t > 1.0:
            add_box(doc, "TankSpacer_RearBedPost",
                    "Проставка (резина/брус) между задней стойкой кровати и баком, %.0f мм" % sp_t,
                    (sw, sp_t, 300.0), (xr - sw / 2.0, ybase(ts, post_in, sp_t), z_b + 100.0),
                    color=(0.15, 0.15, 0.15), group=tg)

        # — проверки —
        def _d(a, b):
            return a.distToShape(b)[0]
        obj = lambda n: doc.getObject(n).Shape
        tag = "pY" if ts > 0 else "nY"
        checks = [
            ("арка", _d(tank, arch)),
            ("D-стойка", _d(tank, dpf)),
            ("задняя стойка кровати", _d(tank, obj("BedPost_%s_rear" % tag))),
            ("передняя стойка кровати", _d(tank, obj("BedPost_%s_front" % tag))),
            ("P3", _d(tank, tank_posts["P3"])), ("P4", _d(tank, tank_posts["P4"])),
            ("продольная рейка кровати", _d(tank, obj("BedSideRail_%s" % tag))),
            ("поперечины кровати", min(_d(tank, o.Shape) for o in doc.Objects
                                        if o.Name.startswith("BedCross") and not o.isDerivedFrom("App::DocumentObjectGroup"))),
            ("подставка ↔ арка", min(_d(s, arch) for s in riser_parts)),
            ("подставка ↔ пластина задней стойки", min(_d(s, obj("BedPostPlate_%s_rear" % tag)) for s in riser_parts)),
            ("подставка ↔ D-стойка", min(_d(s, dpf) for s in riser_parts)),
        ]
        # зазоры по сторонам (в X у дна «ноги» и в Y у внутренней стенки тоннеля)
        tank_summary = dict(lift=lift, lift_min=lift_min, stack=stack_txt, x=(x_r, x_f), y_back=y_back,
                            y_cab=y_cab, standoff=standoff, top=z_b + TH, checks=checks, notes=riser_notes,
                            over_box=x_dp_tank - x_r, z_box=z_box,
                            spacer=sp_t, p_len=p_len, x_dp=x_dp_tank, floor_top=floor_top,
                            under_cross=(z_rail_top - sw) - (z_b + TH),
                            vol=tank.Volume / 1e6)

    # ═══════ ДУШ + МИНИ-КУХНЯ (водительский борт, между кроватью и кабиной) ═══════
    galley_summary = None
    K = SHOWER_KITCHEN
    if B.get("enable") and K.get("enable"):
        ks = K["side"]
        if ks < 0:
            raise RuntimeError("SHOWER_KITCHEN: пока только водительский борт (side=+1)")
        gap, pt_ = K["wall_gap"], K["panel"]
        crown = half[-1][1]
        z_ceil = crown - K["roof_clear"]
        prof_z = sorted(z for _, z in half if z < crown)

        def yw(z):                                   # |Y| задней плоскости (обшивка − gap) на высоте z
            return y_at_z(half, min(z, prof_z[-1])) - gap

        def env_solid(x0, xl, y_front, z0, z1, g_extra=0.0):
            """Призма вдоль X: спереди |Y|=y_front, сзади — по завалу борта (обшивка − gap − g_extra)."""
            pts = [(y_front, z0), (y_front, z1)]
            zs = [z1] + [z for z in reversed(prof_z) if z0 < z < z1] + [z0]
            pts += [(yw(z) - g_extra, z) for z in zs]
            vec = [App.Vector(x0, ks * y, z) for y, z in pts]
            face = Part.Face(Part.makePolygon(vec + [vec[0]]))
            return face.extrude(App.Vector(xl, 0, 0))

        sg = doc.addObject("App::DocumentObjectGroup", "ShowerKitchen")
        sg.Label = "Душ 32×32″ + мини-кухня (чай) — водительский борт, кровать ↔ кабина (проект 2026-11-06)"
        COL_WALL = (0.93, 0.93, 0.90)
        COL_PAN = (0.98, 0.98, 0.98)
        COL_STEEL = (0.70, 0.72, 0.75)
        COL_CAB = (0.80, 0.62, 0.40)
        COL_TOP = (0.62, 0.42, 0.24)
        COL_DARK = (0.18, 0.18, 0.18)
        COL_FRIDGE = (0.25, 0.42, 0.55)
        parts = {}

        def put(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr, group=sg)
            parts[name] = shape
            return shape

        # — душ —
        sx0 = (dx1 if B.get("deck_len") else xf + sw / 2.0) + K["gap_bed"]   # задняя (к кровати) стенка
        six, siy = K["shower_in"]
        sx1 = sx0 + pt_ + six + pt_
        z_pan0 = P["floor_corrugation_height"] if K.get("pan_recess") else floor_top
        z_pan = z_pan0 + K["pan_h"]
        y_back_pan = yw(z_pan) - 12.0                                # поддон упирается в заднюю панель (12 мм)
        y_sf = y_back_pan - siy                                      # фронт душа (линия шторки)
        put("Shower_Pan", "Поддон душа RV 32×32″ низкий (~3.5″), слив в центре → серый бак%s" % (
                "; утоплен в пол (вырез фанеры+XPS)" if K.get("pan_recess") else ""),
            Part.makeBox(six, siy, K["pan_h"], App.Vector(sx0 + pt_, y_sf, z_pan0)), COL_PAN)
        if K.get("pan_recess"):                                      # вырез в полу под поддон
            hole = Part.makeBox(six, siy, floor_top + 1.0, App.Vector(sx0 + pt_, y_sf, 0.5))
            for fn in ("Floor_XPS", "Floor_Plywood"):
                fo = doc.getObject(fn)
                if fo is not None:
                    fo.Shape = fo.Shape.cut(hole)
        for nm, x0 in (("Shower_WallRear", sx0), ("Shower_WallFront", sx1 - pt_)):
            put(nm, "Стенка душа %s (фанера 3/4″ + FRP), по завалу борта" % ("к кровати" if "Rear" in nm else "к кухне"),
                env_solid(x0, pt_, y_sf, floor_top, z_ceil), COL_WALL, 10)
        back = env_solid(sx0 + pt_, six, y_sf, floor_top, z_ceil).cut(
            env_solid(sx0 + pt_ - 1, six + 2, y_sf - 5, floor_top - 1, z_ceil + 1, g_extra=12.0))
        put("Shower_WallBack", "Задняя стенка душа по борту (фанера 1/2″ + FRP)", back, COL_WALL, 10)
        y_ceil_back = yw(z_ceil)
        put("Shower_Ceiling", "Потолок душа (фанера 1/2″ + FRP), Z=%.0f" % z_ceil,
            Part.makeBox(six, y_ceil_back - y_sf, 12.0,
                         App.Vector(sx0 + pt_, y_sf if ks > 0 else -y_ceil_back, z_ceil - 12.0)), COL_WALL, 10)
        rod = Part.makeCylinder(10.0, six, App.Vector(sx0 + pt_, ks * (y_sf + 15.0), z_ceil - 40.0), App.Vector(1, 0, 0))
        put("Shower_CurtainRod", "Карниз шторки", rod, COL_STEEL)
        put("Shower_Curtain", "Шторка душа (со стороны прохода)",
            Part.makeBox(six - 40, 3.0, z_ceil - 60.0 - (z_pan + 40.0),
                         App.Vector(sx0 + pt_ + 20, ks * (y_sf + 20.0) - (0 if ks > 0 else 3.0), z_pan + 40.0)),
            (0.55, 0.75, 0.85), 55)
        yb_h = yw(1650.0) - 12.0
        head = Part.makeCylinder(55.0, 25.0, App.Vector(sx0 + pt_ + six / 2.0, ks * (yb_h - 25.0), 1650.0 + floor_top),
                                 App.Vector(0, ks, 0))
        put("Shower_Head", "Лейка душа на штанге / смеситель", head, COL_STEEL)
        fan = Part.makeCylinder(60.0, 40.0, App.Vector(sx0 + pt_ + six / 2.0, ks * (y_ceil_back - 120.0), z_ceil - 12.0),
                                App.Vector(0, 0, 1))
        put("Shower_ExhaustFan", "Вытяжка 12V ~4″ в потолке душа → небольшое отверстие в стене", fan, COL_DARK)

        # — мини-кухня —
        kx0 = sx1 + 5.0
        kx1 = K["kitchen_end_x"]
        kl = kx1 - kx0
        z_ct = floor_top + K["counter_h"]
        z_cb = z_ct - K["counter_th"]
        y_kb = yw(z_cb)                                              # задняя плоскость у столешницы
        y_kf = yw(500.0) - K["kitchen_depth"]                        # фронт короба
        ph, pr = K["plinth"]
        carc = env_solid(kx0, kl, y_kf, floor_top + ph, z_cb)
        fx, fy, fz = K["fridge"]
        z_f0 = floor_top + ph + pt_ + 15.0                           # ларь на салазках над дном короба
        cav_f = Part.makeBox(kl - 2 * pt_, fy + 40.0, fz + 35.0, App.Vector(kx0 + pt_, y_kf - 1.0, z_f0 - 15.0))
        z_shelf = z_f0 + fz + 20.0
        cav_u = Part.makeBox(kl - 2 * pt_, (y_kb - y_kf) - pt_, (z_cb - z_shelf - pt_),
                             App.Vector(kx0 + pt_, y_kf - 1.0, z_shelf + pt_))
        carc = carc.cut(cav_f).cut(cav_u)
        put("Kitchen_Carcass", "Короб мини-кухни (фанера 3/4″), %.0f×%.0f, открыт спереди" % (kl, K["kitchen_depth"]),
            carc, COL_CAB)
        put("Kitchen_Plinth", "Цоколь кухни",
            Part.makeBox(kl, (y_kb - y_kf) - pr, ph, App.Vector(kx0, y_kf + pr, floor_top)), (0.35, 0.30, 0.25))
        top = env_solid(kx0, kl, y_kf - 20.0, z_cb, z_ct).cut(
            Part.makeBox(K["sink"][0], K["sink"][1], K["counter_th"] + 2,
                         App.Vector(kx0 + 60.0, (y_kf + y_kb) / 2.0 - K["sink"][1] / 2.0 + 40.0, z_cb - 1)))
        put("Kitchen_Countertop", "Столешница 1″ (мебельный щит), верх %.0f над полом (36″)" % K["counter_h"], top, COL_TOP)
        skx, sky, skz = K["sink"]
        sk_o = App.Vector(kx0 + 60.0, (y_kf + y_kb) / 2.0 - sky / 2.0 + 40.0, z_ct - skz)
        sink = Part.makeBox(skx, sky, skz, sk_o).cut(
            Part.makeBox(skx - 4, sky - 4, skz, App.Vector(sk_o.x + 2, sk_o.y + 2, sk_o.z + 2)))
        put("Kitchen_Sink", "Барная мойка 12×12″ из нержавейки", sink, COL_STEEL)
        fct = App.Vector(sk_o.x + skx / 2.0, sk_o.y + sky + 30.0, z_ct)
        faucet = Part.makeCylinder(12.0, 260.0, fct).fuse(
            Part.makeCylinder(10.0, 170.0, App.Vector(fct.x, fct.y, fct.z + 250.0), App.Vector(0, -1, 0)))
        put("Kitchen_Faucet", "Кран (насос 12V включается по давлению)", faucet, COL_STEEL)
        put("Kitchen_Kettle", "Электрочайник (от инвертора) или 12V-чайник",
            Part.makeCylinder(85.0, 230.0, App.Vector(kx1 - 150.0, (y_kf + y_kb) / 2.0, z_ct)), (0.85, 0.85, 0.88))
        put("Kitchen_Outlet", "Розетка 120V + USB над столешницей",
            Part.makeBox(70.0, 20.0, 115.0, App.Vector(kx1 - 150.0 - 35.0, yw(z_ct + 150.0) - 20.0, z_ct + 120.0)),
            (0.95, 0.95, 0.95))
        fridge_x0 = kx0 + (kl - fx) / 2.0
        put("Kitchen_Fridge", "12V холодильник-ларь ~30 qt на салазках (выдвигается в проход на %.0f мм)" % K["fridge_slide"],
            Part.makeBox(fx, fy, fz, App.Vector(fridge_x0, y_kf + 8.0, z_f0)), COL_FRIDGE)
        put("Kitchen_FridgeSlide", "Салазки холодильника (полного выдвижения, под ~45 кг)",
            Part.makeBox(fx, fy, 15.0, App.Vector(fridge_x0, y_kf + 8.0, z_f0 - 15.0)), COL_STEEL)
        put("Kitchen_DoorUpper", "Дверца под мойкой (чашки, чай, фильтр)",
            Part.makeBox(kl - 6.0, 12.0, z_cb - z_shelf - 6.0, App.Vector(kx0 + 3.0, y_kf - 12.0, z_shelf + 3.0)),
            (0.86, 0.70, 0.48))
        zu0 = floor_top + K["upper"][0]
        zu1 = z_ceil
        y_uf = yw(zu0) - K["upper"][1]
        put("Kitchen_UpperCabinet", "Верхний шкафчик (чашки/чай), по завалу борта",
            env_solid(kx0, kl, y_uf, zu0, zu1), COL_CAB)

        # — техотсек под передним краем кровати: насос, бойлер (рядом с баком) —
        tb_x0 = 1440.0
        put("Water_Pump12V", "Насос 12V + фильтр + гидроаккумулятор (под кроватью, у переднего торца бака)",
            Part.makeBox(150.0, 120.0, 130.0, App.Vector(tb_x0, 400.0, floor_top)), (0.20, 0.35, 0.75))
        put("Water_Heater12V", "Место под бойлер 12V ~6–10 л (под кроватью)",
            Part.makeCylinder(130.0, 380.0, App.Vector(1465.0, 230.0, floor_top)), (0.85, 0.85, 0.85))

        # — проверки —
        def _dd(a, b):
            return a.distToShape(b)[0]
        objs = lambda pfx: [o.Shape for o in doc.Objects
                            if o.Name.startswith(pfx) and o.isDerivedFrom("Part::Feature") and not o.Shape.isNull()]
        pall = list(parts.values())
        checks = []
        no_plate = lambda pfx: [s_ for o, s_ in ((o, o.Shape) for o in doc.Objects
                                                if o.Name.startswith(pfx) and "Plate" not in o.Name
                                                and o.isDerivedFrom("Part::Feature") and not o.Shape.isNull())]
        for lab, ss in (("кровать (стойки/рейки/настил/матрас)", no_plate("Bed")), ("бак", objs("WaterTank")),
                        ("подставка бака", objs("TankRiser")), ("стойки бака", objs("TankPost"))):
            if ss:
                checks.append((lab, min(_dd(p, s_) for p in pall for s_ in ss)))
        pl = doc.getObject("BedPostPlate_pY_front")
        if pl is not None and min(_dd(p, pl.Shape) for p in pall) < 0.5:
            checks.append(("пластина передней стойки кровати (1.6 мм) — душ заходит на её край: подложить", 0.0))
        aisle_sh = y_sf + y_at_z(half, 900.0)                       # от шторки до противоположной стены
        aisle_k = (y_kf - 20.0) + y_at_z(half, 900.0)
        galley_summary = dict(
            shower_x=(sx0, sx1), shower_in=(six, siy), y_sf=y_sf, z_pan=z_pan, z_ceil=z_ceil,
            headroom=(z_ceil - 12.0) - z_pan, kitchen_x=(kx0, kx1), kl=kl, y_kf=y_kf, counter=K["counter_h"],
            seat_gap=3190.0 - kx1, aisle_sh=aisle_sh, aisle_k=aisle_k, checks=checks,
            floor_top=floor_top, wall_y=y_at_z(half, 900.0))

    # ═══════ НАСТИЛ: вырезы под новые стойки P2 и под головки болтов в кузов ═══════
    # (при подъёме кровати настил может оказаться на высоте болтов стоек — головки торчат из стоек в салон)
    deck_notes = []
    deck_o = doc.getObject("BedDeck") if B.get("enable") else None
    if deck_o is not None:
        dsh = deck_o.Shape
        dz0, dz1 = dsh.BoundBox.ZMin, dsh.BoundBox.ZMax
        cut = []
        for o in doc.Objects:
            if o.Name.startswith("BedPost_nY_rackP2"):                      # P2 обоих блоков
                bb = o.Shape.BoundBox
                cut.append(Part.makeBox(bb.XLength + 6, bb.YLength + 6, bb.ZLength,
                                        App.Vector(bb.XMin - 3, bb.YMin - 3, bb.ZMin)))
        n_bolt = 0
        bh, bw_, bd = 14.0, 30.0, 12.0                                       # головка+шайба: ⌀~14, выступ ~12
        for o in doc.Objects:
            if o.Name.startswith("BedPostBodyBolt_") or o.Name.startswith("RackP2_BodyBolt"):
                c = o.Placement.Base                                 # Part::Sphere: центр (Shape — после recompute)
                if c.z + bh / 2.0 > dz0 and c.z - bh / 2.0 < dz1:
                    # вырез: от внутренней грани стойки (|Y|=post_in) на bd+3 в салон
                    y0 = (post_in - bd - 3.0) if c.y > 0 else -post_in
                    cut.append(Part.makeBox(bw_, bd + 3.0, dz1 - dz0 + 2.0,
                                            App.Vector(c.x - bw_ / 2.0, y0, dz0 - 1.0)))
                    n_bolt += 1
        if cut:
            for s in cut:
                dsh = dsh.cut(s)
            deck_o.Shape = dsh
        if n_bolt:
            deck_notes.append("настил на высоте болтов стоек в кузов: %d выреза %g×%g мм под головки" % (
                n_bolt, bw_, bd + 3.0))

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
    print("-" * 70)
    print("[Задние углы у пола: D-стойка ↔ арка — фото сверху 2026-11-06]")
    print("  Передняя грань короба D-стойки у края фанеры: X=%.0f; уплотнитель задней двери X≈%.0f" % (
        x_dp, x_dp - DP["box_len"]))
    print("  Задняя грань арки у края фанеры: X=%.0f;  выступ арки от края фанеры %.0f мм (%.2f″)" % (
        W["center_x"] - arch_a_lin(DP["photo_wall"]), W["protrusion"] - DP["photo_wall"],
        (W["protrusion"] - DP["photo_wall"]) / 25.4))
    print("  Зазор короб ↔ арка по полу (от края фанеры): " + ";  ".join(
        "%.1f″ → %.2f″" % (yi, (W["center_x"] - arch_a_lin(DP["photo_wall"] + yi * 25.4)
                               - dp_box_x(min(DP["photo_wall"] + yi * 25.4, DP["photo_wall"] + DP["box_depth"]))) / 25.4)
        for yi in (0.0, 1.1, 2.4, 5.0)))
    if bed_summary:
        print("  Центр задней стойки кровати от грани короба: %.0f мм (%.2f″)" % (
            bed_summary["posts"][0] - x_dp, (bed_summary["posts"][0] - x_dp) / 25.4))
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
        for note in deck_notes:
            print("  ⚠ " + note)
    for rs in rack_summary:
        f0 = rs["floor_top"]
        mm = lambda v: ("%.1f мм" % v) if v is not None else "—"
        print("[Этажерка, 2 батареи Buknuwo 150Ah — пассажирский борт, %s]" % (
            "арка ↔ сдвижная дверь" if rs["stack"] == "front" else "D-стойка ↔ арка"))
        print("  Батареи по X: %.0f..%.0f (%.2f″ вдоль борта); грань в салон — %.0f мм (%.1f″) от стены у пола" % (
            rs["X"][0], rs["X"][1], rs["bx"] / 25.4, rs["inner_from_wall"], rs["inner_from_wall"] / 25.4))
        print("  Нижняя до арки: %s%s" % (mm(rs["gap_arch"]),
            ("; до короба D-стойки: %s" % mm(rs["gap_dpillar"])) if rs["gap_dpillar"] is not None else ""))
        print("  Пластина P2 (TP15): до пластины P1 %s, до арки %s" % (mm(rs["plates_gap"]), mm(rs["p2_plate_arch"])))
        if rs["stack"] == "front":
            print("  До края сдвижной двери: %.0f мм (%.1f″); за передний край настила: %.0f мм" % (
                rs["to_slider"], rs["to_slider"] / 25.4, rs["to_deck_edge"]))
        print("  Нижняя: %.0f..%.0f мм над полом;  рейки полки: %.0f..%.0f;  верхняя: %.0f..%.0f" % (
            rs["z_b1"][0] - f0, rs["z_b1"][1] - f0, rs["z_rail"][0] - f0, rs["z_rail"][1] - f0,
            rs["z_b2"][0] - f0, rs["z_b2"][1] - f0))
        print("  От верхней батареи до низа поперечин/реек кровати: %.0f мм (%.1f″)" % (
            rs["above_b2"], rs["above_b2"] / 25.4))
        if rs["ties"] == "short":
            print("  Верхние стяжки: %.0f..%.0f над полом; до низа реек кровати: %.0f мм" % (
                rs["tie"][0] - f0, rs["tie"][1] - f0, rs["tie_to_bed"]))
        elif rs["ties"] == "bed":
            print("  Стяжки = поперечины кровати: существующая + новая L=%.0f" % rs["cross_len"])
        print("  Новая стойка P2 X=%.0f..%.0f, до арки %s;  P3/P4 L=%.0f;  рейки полки 2×%.0f" % (
            rs["p2"][0], rs["p2"][1], mm(rs["p2_arch"]), rs["p34_len"], rs["rail_len"]))
    if tank_summary:
        t = tank_summary
        f0 = t["floor_top"]
        print("[Бак для воды TORVA 33 gal — водительский борт, D-стойка ↔ арка]")
        if t["lift_min"] is not None:
            print("  Нужный подъём дна (зазор до арки ≥ %.0f мм): %.0f мм (%.1f″) → подставка %.0f мм (%.2f″): %s" % (
                WATER_TANK["arch_clear"], t["lift_min"], t["lift_min"] / 25.4, t["lift"], t["lift"] / 25.4, t["stack"]))
        else:
            print("  Подъём дна (задан): %.0f мм" % t["lift"])
        print("  X бака %.0f..%.0f; зад бака в %.0f мм от стены, грань в салон в %.0f мм от стены (у пола)" % (
            t["x"][0], t["x"][1], t["standoff"], t["standoff"] + WATER_TANK["size"][1]))
        print("  Верх бака %.0f мм над полом; до низа поперечин кровати %.0f мм" % (t["top"] - f0, t["under_cross"]))
        if t["over_box"] > 0:
            print("  Торец бака нависает над коробом D-стойки на %.0f мм: дно %.0f над полом, короб ~%.0f (оценка) → запас %.0f" % (
                t["over_box"], t["lift"], t["z_box"] - f0, t["lift"] - (t["z_box"] - f0)))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in t["checks"]))
        print("  Проставка задняя стойка кровати ↔ бак: %.0f мм;  P3/P4 L=%.0f;  объём тела в модели %.0f л" % (
            t["spacer"], t["p_len"], t["vol"]))
        for note in t.get("notes", []):
            print("  ⚠ " + note)
    if galley_summary:
        k = galley_summary
        f0 = k["floor_top"]
        print("[Душ + мини-кухня — водительский борт, кровать ↔ кабина]")
        print("  Душ X %.0f..%.0f (%.0f мм / %.1f″ вдоль борта), внутри %.0f×%.0f (32×32″); шторка в %.0f мм от стены" % (
            k["shower_x"][0], k["shower_x"][1], k["shower_x"][1] - k["shower_x"][0],
            (k["shower_x"][1] - k["shower_x"][0]) / 25.4, k["shower_in"][0], k["shower_in"][1], k["wall_y"] - k["y_sf"]))
        print("  В душе: верх поддона %.0f над полом, низ потолка %.0f → от поддона до потолка %.0f мм (%.1f″)" % (
            k["z_pan"] - f0, k["z_ceil"] - 12.0 - f0, k["headroom"], k["headroom"] / 25.4))
        print("  Кухня X %.0f..%.0f (%.0f мм / %.1f″), глубина до %.0f мм от стены, столешница %.0f (36″); до спинок сидений %.0f мм" % (
            k["kitchen_x"][0], k["kitchen_x"][1], k["kl"], k["kl"] / 25.4, k["wall_y"] - k["y_kf"] + 20, k["counter"], k["seat_gap"]))
        print("  Проход: у душа %.0f мм (%.1f″), у кухни %.0f мм (%.1f″)" % (
            k["aisle_sh"], k["aisle_sh"] / 25.4, k["aisle_k"], k["aisle_k"] / 25.4))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in k["checks"]))
    print("-" * 70)
    if bb:
        print("Bounding box (вкл. обшивку): %.0f x %.0f x %.0f мм" % (
            bb.XLength, bb.YLength, bb.ZLength))
    print("Объектов Part::Feature: %d" % n_solid)
    print("=" * 70)
    return doc


DOC = build()
