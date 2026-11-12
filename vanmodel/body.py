# -*- coding: utf-8 -*-
"""Кузов: профиль по скану, обшивка, каркас, пол, колёсные арки, D-стойки, клапан сброса давления, проёмы дверей.

Здесь же считается общая для всей мебели геометрия: чистовой пол (floor_top), стена у пола (arch_ywall),
задние углы «арка ↔ D-стойка» (arch_a_lin, dp_box_x, dp_body_x).
"""

import math

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .params import DPILLAR, FLOOR, PARAMS, WATER_VARIANT, WHEEL_ARCH
from .common import (COL_ARCH, COL_DPILLAR, COL_FACTORY_THREAD, COL_FLOOR, COL_HOLE, COL_PILLAR, COL_PLY,
                     COL_RAIL, COL_REAR, COL_RIB, COL_SLIDER, COL_XPS, DOC_NAME, add_box, add_shape, add_sphere)
from .scan import _HAVE_NP, add_mesh_skin, full_hoop, measured_half_profile, scan_points, y_at_z


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


# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def start(S):
    """Профиль борта (снимается со скана кузова) и новый документ FreeCAD."""
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
    doc.Label = "%s — бак %s" % (DOC_NAME, {"T4100_floor": "T-4100 на полу", "T3500_shelf": "T-3500 на полке",
                                         "T4320_floor": "T-4320 на полу",
                                         "TORVA": "TORVA 33 gal"}.get(WATER_VARIANT, WATER_VARIANT))

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "L P crown_z doc floor_hw half hoop zc")


def skin(S):
    """Обшивка — меш 3D-скана кузова."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    doc = S.doc
    # ═══════ ОБШИВКА (скан) ═══════
    skin = doc.addObject("App::DocumentObjectGroup", "Scan_Skin")
    skin.Label = "Обшивка — 3D-скан кузова (лежит на каркасе)"
    mesh_obj = add_mesh_skin(doc, skin)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "mesh_obj")


def frame(S):
    """Каркас: рёбра-обручи, продольные рейки, рефлёный пол, стойки, точки крепления."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    L, P, doc, floor_hw, half, hoop, zc = S.L, S.P, S.doc, S.floor_hw, S.half, S.hoop, S.zc
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

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "frame lower_rail_z n_factory_threads n_floor_ribs n_holes n_rails ph pitch rib_h rib_xs "
                     "sec slider_label slider_side slider_x0 threaded_z wheel_x0 wheel_x1 ybase")


def floor(S):
    """Чистовой пол (XPS + фанера) и общая геометрия задних углов: арка ↔ D-стойка."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    L, P, doc, floor_hw, frame, half = S.L, S.P, S.doc, S.floor_hw, S.frame, S.half
    # ═══════ ПОЛ: XPS + фанера (чистовой пол) ═══════
    floor_top = P["floor_corrugation_height"]          # верх гребней железного пола
    W = WHEEL_ARCH                                     # = пассажирская арка (nY); по бортам — WA[+1] / WA[-1]
    # 2026-11-09: арки и D-стойки — каждый борт по своим ANCHORS (после замера могут различаться)
    WA = {sg_: dict(WHEEL_ARCH, **ANCHORS["arch"][tg_]) for sg_, tg_ in ((+1, "pY"), (-1, "nY"))}
    DPs = {sg_: dict(DPILLAR, **ANCHORS["dpillar"][tg_]) for sg_, tg_ in ((+1, "pY"), (-1, "nY"))}
    arch_ywall = y_at_z(half, 0.0)                     # стена у пола (внутр. поверхность)
    arch_x0 = W["center_x"] - W["len_x_wall"] / 2.0
    arch_x1 = W["center_x"] + W["len_x_wall"] / 2.0

    def arch_a_lin(d, sgn=-1):
        """Полудлина арки борта sgn у пола на расстоянии d от стены (грани скошены, без скругления углов)."""
        Ws = WA[sgn]
        return (Ws["len_x_wall"] - (Ws["len_x_wall"] - Ws["len_x"]) * d / Ws["protrusion"]) / 2.0

    # D-стойки у пола: передняя грань короба (X) у края фанеры — от задней грани арки (фото сверху 2026-11-06)
    DP = DPILLAR
    x_dp_s = {sg_: WA[sg_]["center_x"] - arch_a_lin(DPs[sg_]["photo_wall"], sg_) - DPs[sg_]["to_arch"] for sg_ in (1, -1)}
    x_dp = x_dp_s[-1]

    def dp_box_x(d, sgn=-1):
        """X передней грани короба D-стойки борта sgn на расстоянии d от стены (у пола, до box_h)."""
        D_ = DPs[sgn]
        return x_dp_s[sgn] - D_["box_slant"] * (d - D_["photo_wall"]) / D_["box_depth"]

    def dp_body_x(d, sgn=-1):
        """X передней грани самой D-стойки (выше короба) на расстоянии d от стены."""
        D_ = DPs[sgn]
        return x_dp_s[sgn] - D_["body_slant"] * d / D_["body_depth"]

    def _arch_footprint(sgn, zh):
        """Коробка-габарит арки на борту sgn (для вырезов в полу)."""
        Ws = WA[sgn]
        y0 = arch_ywall - Ws["protrusion"] if sgn > 0 else -arch_ywall
        ax0 = Ws["center_x"] - Ws["len_x_wall"] / 2.0
        return Part.makeBox(Ws["len_x_wall"], Ws["protrusion"], zh, App.Vector(ax0, y0, -1.0))

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

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "DP DPs W WA arch_a_lin arch_ywall dp_body_x dp_box_x floor_top x_dp x_dp_s")


def wheel_arches(S):
    """Колёсные арки (внутренние кожухи)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    W, WA, arch_a_lin, arch_ywall, doc = S.W, S.WA, S.arch_a_lin, S.arch_ywall, S.doc
    floor_top, frame = S.floor_top, S.frame
    # ═══════ КОЛЁСНЫЕ АРКИ (внутренние кожухи, упрощённо: полуэллипс по X-Z) ═══════
    arch_shapes = {}
    if W.get("enable"):
        arch_g = doc.addObject("App::DocumentObjectGroup", "WheelArches")
        arch_g.Label = "Колёсные арки (рулетка на фото + Upfit Supply 35×17″)"
        frame.addObject(arch_g)
        n_seg = 72
        n_exp = float(W.get("profile_n", 2.0))
        r_top = float(W.get("top_round", 0.0))

        def _half_super(a_half, y, b, cx):
            """Сечение арки в плоскости |Y|=const: суперэллипс от пола (Z=0) до b."""
            pts = []
            for i in range(n_seg + 1):
                t = math.pi * i / n_seg
                c, s_ = math.cos(t), math.sin(t)
                pts.append(App.Vector(cx + a_half * math.copysign(abs(c) ** (2.0 / n_exp), c), y,
                                      b * abs(s_) ** (2.0 / n_exp)))
            return Part.makePolygon(pts + [pts[0]])

        # сечения от стены (d=0) к внутренней грани (d=prot): длина сужается линейно (len_x_wall → len_x,
        # грани скошены), у внутренней грани углы в плане скруглены r_pl; высота — постоянна до начала
        # скругления верхней внутренней кромки, дальше — по дуге r_top
        r_pl = float(W.get("plan_round", 0.0))

        for sgn, tag in ((+1, "pY"), (-1, "nY")):
            Ws = WA[sgn]
            b_top = floor_top + Ws["height"]
            prot = Ws["protrusion"]
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
                a = arch_a_lin(d, sgn)
                if r_pl > 0 and d > prot - r_pl:
                    a -= r_pl - math.sqrt(max(0.0, r_pl ** 2 - (d - (prot - r_pl)) ** 2))
                return a

            wires = [_half_super(_a_at(d), sgn * (arch_ywall - d), _b_at(d), Ws["center_x"]) for d in ds]
            arch_shapes[sgn] = Part.makeLoft(wires, True, True)
            add_shape(doc, "WheelArch_%s" % tag,
                      "Колёсная арка %s: у стены %g, по внутр. грани %g, выступ %g, верх Z=%.0f; "
                      "сбоку суперэллипс n=%g, скругление верхней внутр. кромки R%g, углов в плане R%g "
                      "(ANCHORS: %s)" % (
                          tag, Ws["len_x_wall"], Ws["len_x"], prot, b_top, n_exp, r_top, r_pl, ANCHORS["arch"]["status"]),
                      arch_shapes[sgn], color=COL_ARCH, transparency=15, group=arch_g)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "arch_shapes")


def dpillars(S):
    """D-стойки у пола: короб у основания и передняя грань стойки."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    DPs, arch_ywall, doc, dp_body_x, dp_box_x = S.DPs, S.arch_ywall, S.doc, S.dp_body_x, S.dp_box_x
    floor_top, frame, x_dp_s = S.floor_top, S.frame, S.x_dp_s
    # ═══════ D-СТОЙКИ у пола (реф): короб у основания + передняя грань стойки выше него ═══════
    dp_shapes = {}
    dp_g = doc.addObject("App::DocumentObjectGroup", "DPillars")
    dp_g.Label = "D-стойки у пола (реф): короб + грань стойки — фото сверху 2026-11-06"
    frame.addObject(dp_g)
    for sgn, tag in ((+1, "pY"), (-1, "nY")):
        DP_ = DPs[sgn]
        z_box = floor_top + DP_["box_h"]
        d_box = DP_["photo_wall"] + DP_["box_depth"]

        def _prism(pts_xd, z0, z1):
            v = [App.Vector(x, sgn * (arch_ywall - d), z0) for x, d in pts_xd]
            return Part.Face(Part.makePolygon(v + [v[0]])).extrude(App.Vector(0, 0, z1 - z0))
        box_ = _prism([(dp_box_x(0.0, sgn), 0.0), (dp_box_x(d_box, sgn), d_box),
                       (x_dp_s[sgn] - DP_["box_len"], d_box), (x_dp_s[sgn] - DP_["box_len"], 0.0)], 0.0, z_box)
        body_ = _prism([(dp_body_x(0.0, sgn), 0.0), (dp_body_x(DP_["body_depth"], sgn), DP_["body_depth"]),
                        (dp_body_x(DP_["body_depth"], sgn) - 40.0, DP_["body_depth"]),
                        (dp_body_x(0.0, sgn) - 40.0, 0.0)], z_box, DP_["ref_top"])
        dp_shapes[sgn] = box_.fuse(body_).removeSplitter()
        add_shape(doc, "DPillarFace_%s_ref" % tag,
                  "D-стойка %s (реф): короб у пола %.1f″ от края фанеры, грань скошена назад 0.2″/1″, высота "
                  "~%.0f″ (оценка); выше — грань стойки (уходит назад ~%.0f мм на выступе %.0f)" % (
                      tag, DP_["box_depth"] / 25.4, DP_["box_h"] / 25.4, DP_["body_slant"], DP_["body_depth"]),
                  dp_shapes[sgn], color=COL_DPILLAR, transparency=40, group=dp_g)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "dp_shapes z_box")


def relief_valve(S):
    """Клапан сброса давления кузова (решётка у пола, пассажирский борт)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    doc, floor_top, half = S.doc, S.floor_top, S.half
    # ═══════ КЛАПАН СБРОСА ДАВЛЕНИЯ КУЗОВА (решётка с жалюзи у пола, пасс. борт) — 2026-11-09, ANCHORS ═══════
    RV = ANCHORS.get("relief_valve")
    relief = None
    if RV:
        rvg = doc.addObject("App::DocumentObjectGroup", "BodyReliefValves")
        rvg.Label = "Клапан сброса давления кузова"
        rvs = RV["side"]
        rz0, rz1 = floor_top + RV["z0"], floor_top + RV["z1"]
        y_wall_rv = y_at_z(half, (rz0 + rz1) / 2.0)                  # стена (обшивка) на высоте решётки
        relief = Part.makeBox(RV["x1"] - RV["x0"], RV["proud"], rz1 - rz0,
                              App.Vector(RV["x0"], (y_wall_rv - RV["proud"]) if rvs > 0 else -y_wall_rv, rz0))
        add_shape(doc, "BodyReliefValve_%s" % ("pY" if rvs > 0 else "nY"),
                  "Клапан сброса давления — решётка с жалюзи %.1f×%.1f″, %.1f..%.1f″ над полом, выступ %.1f″ (%s); "
                  "вплотную не закрывать" % ((RV["x1"] - RV["x0"]) / 25.4, (rz1 - rz0) / 25.4, RV["z0"] / 25.4,
                                             RV["z1"] / 25.4, RV["proud"] / 25.4, RV["status"]),
                  relief, color=(0.08, 0.08, 0.08), group=rvg)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "RV relief")


def openings(S):
    """Проёмы дверей (реф-рамки)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    P, doc, half, slider_label, slider_side = S.P, S.doc, S.half, S.slider_label, S.slider_side
    slider_x0 = S.slider_x0
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
