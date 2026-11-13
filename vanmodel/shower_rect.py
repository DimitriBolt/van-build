# -*- coding: utf-8 -*-
"""Душ с ПРЯМОУГОЛЬНЫМ поддоном RecPro 36×24×5″ + туалет на платформе + кухня 24″ (вариант van_v1_rect_pan).

Заменяет раздел shower_kitchen.shower_kitchen (сектор 32″ Swiss Madison) — те же имена деталей (Shower_*, Toilet_*,
Kitchen_*), поэтому остальные разделы, анимации и проверки не меняются. Бака воды, локера/баллона пропана, ящиков и
полки 2-го этажа здесь нет — их положение Dimitri укажет следующим заданием.

Координаты поддона (ks = +1, водительский борт): u — вдоль X от узкой грани (u = 0 — вровень с краем щита кровати),
v — поперёк от края поддона у борта к проходу (X = x0 + u, |Y| = y_wall − v).
Угол поддона у арки (u, v ≈ 0) отпиливается ОДНИМ прямым срезом — треугольник (b, 0) — (0, a), минимальной площади, при
которой остаётся зазор до арки (corner_cut). Срез проходит через дно, поэтому в срезе стоит плотина (Shower_PanCutSeal).
"""

import math

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .params import KITCHEN_FLAP
from .params_rect import RECT_PAN, SHOWER_KITCHEN_RECT, TOILET_RECT
from .common import add_shape
from .scan import y_at_z

V = App.Vector

# Каждая функция-раздел получает контекст сборки S (state.py). Порядок разделов — в build.py.


# ═══════════════════════════ чистая геометрия (без FreeCAD — проверяется отдельно) ═══════════════════════════
def corner_cut(pts, gap, a_max, b_max):
    """Прямой срез угла прямоугольника (u ≥ 0, v ≥ 0): отсекается треугольник с вершинами (b, 0) и (0, a).

    pts — точки препятствия (u, v); каждая должна лежать внутри отсекаемого угла не ближе gap к линии среза.
    Возвращает (a, b) минимальной площади; None — препятствия в квадранте нет; ValueError — не получается (a ≤ a_max, b ≤ b_max)."""
    q = [(u, v) for u, v in pts if u >= 0.0 and v >= 0.0]
    # для ограничения важны только «крайние» точки: не доминируемые другой точкой (u' ≥ u и v' ≥ v)
    q = sorted(set((round(u, 3), round(v, 3)) for u, v in q), reverse=True)
    front, vmax = [], -1.0
    for u, v in q:
        if v > vmax + 1e-9:
            front.append((u, v))
            vmax = v
    if not front:
        return None

    def ok(a, b):
        h = math.hypot(a, b)
        return all((a * b - a * u - b * v) / h >= gap for u, v in front)

    best = None
    b = max(u for u, _ in front) + gap
    while b <= b_max:
        if ok(a_max, b):
            lo, hi = 0.0, a_max
            for _ in range(40):
                mid = (lo + hi) / 2.0
                lo, hi = (lo, mid) if ok(mid, b) else (mid, hi)
            area = hi * b / 2.0
            if best is None or area < best[0]:
                best = (area, hi, b)
        b += 1.0
    if best is None:
        raise ValueError("прямой срез угла не получается: арка заходит глубже, чем поддон позволяет")
    return best[1], best[2]


def rrect_wire(xa, ya, xb, yb, r, z):
    """Контур прямоугольника со скруглёнными углами (8 рёбер, против часовой) на высоте z."""
    r = max(0.5, min(r, (xb - xa) / 2.0 - 0.01, (yb - ya) / 2.0 - 0.01))
    d = r * math.sqrt(0.5)
    P = lambda x, y: V(x, y, z)
    arc = lambda p1, p2, p3: Part.Arc(p1, p2, p3).toShape()
    return Part.Wire([
        Part.makeLine(P(xa + r, ya), P(xb - r, ya)),
        arc(P(xb - r, ya), P(xb - r + d, ya + r - d), P(xb, ya + r)),
        Part.makeLine(P(xb, ya + r), P(xb, yb - r)),
        arc(P(xb, yb - r), P(xb - r + d, yb - r + d), P(xb - r, yb)),
        Part.makeLine(P(xb - r, yb), P(xa + r, yb)),
        arc(P(xa + r, yb), P(xa + r - d, yb - r + d), P(xa, yb - r)),
        Part.makeLine(P(xa, yb - r), P(xa, ya + r)),
        arc(P(xa, ya + r), P(xa + r - d, ya + r - d), P(xa + r, ya)),
    ])


# ═══════════════════════════════════════ раздел ═══════════════════════════════════════
def shower_kitchen(S):
    """Душ с прямоугольным поддоном, туалет на платформе, нагреватель, мини-кухня 24″ (водительский борт)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, P, W, WA, arch_shapes, arch_ywall, doc = S.B, S.P, S.W, S.WA, S.arch_shapes, S.arch_ywall, S.doc
    dx0, dx1, floor_top, half, post_out_s, sw = S.dx0, S.dx1, S.floor_top, S.half, S.post_out_s, S.sw
    ybase, z_rail_top = S.ybase, S.z_rail_top
    K, R, AR = SHOWER_KITCHEN_RECT, dict(RECT_PAN), ANCHORS["rect_pan"]
    AT = dict(ANCHORS["toilet"], **AR.get("toilet_wheels", {}))          # колёсики — как в ANCHORS["rect_pan"]
    R["wall_clear"] = AR.get("wall_clear", R["wall_clear"])
    rect_summary = None
    galley_summary = None
    if not (B.get("enable") and K.get("enable")):
        S.put(locals(), "galley_summary rect_summary")
        return
    ks = K["side"]
    if ks < 0:
        raise RuntimeError("SHOWER_KITCHEN_RECT: пока только водительский борт (side=+1)")
    gap, pt_ = K["wall_gap"], K["panel"]
    crown = half[-1][1]
    z_ceil = crown - K["roof_clear"]
    prof_z = sorted(z for _, z in half if z < crown)

    def yw(z):                                       # |Y| плоскости стенной панели (обшивка − gap) на высоте z
        return y_at_z(half, min(z, prof_z[-1])) - gap

    def env_solid(x0_, xl, y_front, z0, z1, g_extra=0.0):
        """Призма вдоль X: спереди |Y|=y_front, сзади — по завалу борта (обшивка − gap − g_extra)."""
        pts = [(y_front, z0), (y_front, z1)]
        zs = [z1] + [z for z in reversed(prof_z) if z0 < z < z1] + [z0]
        pts += [(yw(z) - g_extra, z) for z in zs]
        vec = [V(x0_, ks * y, z) for y, z in pts]
        return Part.Face(Part.makePolygon(vec + [vec[0]])).extrude(V(xl, 0, 0))

    sg = doc.addObject("App::DocumentObjectGroup", "Shower")
    sg.Label = "Душ — прямоугольный поддон RecPro 36×24×5″, газовый нагреватель (проект 2026-11-12)"
    kg = doc.addObject("App::DocumentObjectGroup", "Kitchen")
    kg.Label = "Кухня — блок шириной 24″ (= поддону): мойка | шкафчик + холодильник (проект 2026-11-12)"
    COL_WALL, COL_PAN, COL_STEEL = (0.93, 0.93, 0.90), (0.98, 0.98, 0.98), (0.70, 0.72, 0.75)
    COL_CAB, COL_TOP, COL_DARK, COL_FRIDGE = (0.80, 0.62, 0.40), (0.62, 0.42, 0.24), (0.18, 0.18, 0.18), (0.25, 0.42, 0.55)
    parts = {}

    def put(name, label, shape, color, tr=0, group=None):
        add_shape(doc, name, label, shape, color=color, transparency=tr,
                  group=group or (kg if name.startswith("Kitchen_") else sg))
        parts[name] = shape
        return shape

    # ═══════ ПОДДОН RecPro 36×24×5″: вплотную к кровати, угол у арки — прямой срез ═══════
    Lp, Wp, Hp = R["L"], R["W"], R["H"]
    z_pan0 = floor_top                                    # поддон стоит на чистовом полу
    z_pan = z_pan0 + Hp                                   # верх бортика
    z_in = z_pan0 + R["base_th"]                          # дно внутри
    y_wall = yw(z_pan) - R["wall_clear"]                  # |Y| края поддона у борта (панель 12 мм)
    y_aisle = y_wall - Wp                                 # |Y| края к проходу
    x0 = AR["x_rear"] if AR.get("x_rear") is not None else dx1 + AR.get("bed_gap", 0.0)   # узкая грань = край щита
    x1 = x0 + Lp
    fl, fw = R["floor"]
    t_end = (Lp - fl) / 2.0                               # бортик у коротких сторон до площадки дна
    t_side = (Wp - fw) / 2.0
    uv2xy = lambda u, v: (x0 + u, y_wall - v)

    # — чаша: усечённая пирамида от площадки дна (скруглённые углы) до проёма (бортик rim_top) —
    top_in = R["rim_top"]
    cav = Part.makeLoft([
        rrect_wire(x0 + t_end, y_aisle + t_side, x1 - t_end, y_wall - t_side, R["floor_r"], z_in),
        rrect_wire(x0 + top_in, y_aisle + top_in, x1 - top_in, y_wall - top_in, R["floor_r"] + 10.0, z_pan + 1.0)], True)
    body = Part.makeBox(Lp, Wp, Hp, V(x0, y_aisle, z_pan0)).cut(cav)
    # — слив: ⌀2″ в 5½″ от короткого края, по центру ширины; у кабины («front») или у кровати («rear») —
    dr_r = R["drain_d"] / 2.0
    dr_x = (x1 - R["drain_from_end"]) if AR.get("drain_end", "front") == "front" else (x0 + R["drain_from_end"])
    dr_y = y_aisle + Wp / 2.0
    body = body.cut(Part.makeCylinder(dr_r, R["base_th"] + 2.0, V(dr_x, dr_y, z_pan0 - 1.0)))

    # — прямой срез угла у арки: минимальный треугольник (b, 0) — (0, a), зазор до арки cut_gap —
    arch_s = arch_shapes[ks]
    probe = Part.makeBox(700.0, 900.0, Hp - 1.0, V(x0 - 100.0, y_wall - 700.0, z_pan0 + 0.5))
    sec = arch_s.common(probe)
    uv_pts = []
    if not sec.isNull():
        for e in sec.Edges:
            try:
                uv_pts += [(p.x - x0, y_wall - p.y) for p in e.discretize(Distance=3.0)]
            except Exception:
                pass
    cut_ab = AR.get("cut")
    if cut_ab is None:
        cut_ab = corner_cut(uv_pts, AR["cut_gap"] + 2.0, Wp * 0.9, Lp * 0.4)      # +2 мм — шаг дискретизации
    cut_a = cut_b = 0.0
    seal = None
    if cut_ab:
        cut_a, cut_b = cut_ab
        ext = lambda p, q_, t: (p[0] + t * (q_[0] - p[0]), p[1] + t * (q_[1] - p[1]))
        pa, pb = uv2xy(cut_b, 0.0), uv2xy(0.0, cut_a)                        # концы линии среза (XY)
        a_ext, b_ext = ext(pa, pb, -0.15), ext(pb, pa, -0.15)
        corner = (x0 - 20.0, y_wall + 20.0)
        poly = [V(a_ext[0], a_ext[1], z_pan0 - 2.0), V(b_ext[0], b_ext[1], z_pan0 - 2.0), V(corner[0], corner[1], z_pan0 - 2.0)]
        prism = Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, 0, Hp + 4.0))
        body = body.cut(prism)
        # плотина в срезе: полоса вдоль линии среза (внутрь поддона) ∩ чаша
        nu, nv = (1.0 / cut_b) / math.hypot(1.0 / cut_b, 1.0 / cut_a), (1.0 / cut_a) / math.hypot(1.0 / cut_b, 1.0 / cut_a)
        sl = R["seal_t"]
        a_u, a_v = cut_b * 1.15, -0.15 * cut_a                                 # A продлён за стенку (v < 0)
        b_u, b_v = -0.15 * cut_b, cut_a * 1.15                                 # B продлён за узкую грань (u < 0)
        pts_uv = [(a_u, a_v), (b_u, b_v), (b_u + sl * nu, b_v + sl * nv), (a_u + sl * nu, a_v + sl * nv)]
        vec = [V(*uv2xy(u_, v_), z_in - 1.0) for u_, v_ in pts_uv]
        strip = Part.Face(Part.makePolygon(vec + [vec[0]])).extrude(V(0, 0, z_pan - z_in + 1.0))
        seal = strip.common(cav)
    uc = (lambda v_: cut_b * (1.0 - v_ / cut_a) if cut_a and v_ < cut_a else 0.0)   # |u| линии среза на «глубине» v
    pan = body
    put("Shower_PanRect", "%s: на полу, узкая грань вровень с краем щита кровати (X=%.0f), слив %s, угол у арки срезан по "
        "прямой (%.1f″ вдоль узкой грани × %.1f″ вдоль борта)" % (R["title"], x0, "у кабины" if AR.get("drain_end", "front") == "front"
                                                            else "у кровати", cut_a / 25.4, cut_b / 25.4), pan, COL_PAN)
    if seal is not None and not seal.isNull() and seal.Volume > 1.0:
        put("Shower_PanCutSeal", "Плотина в срезе поддона (пластик/FRP %.0f мм + эпоксид/герметик по кромке): закрывает чашу "
            "по линии среза; платформа туалета проходит над ней" % R["seal_t"], seal, (0.98, 0.55, 0.20))
    put("Shower_Drain", "Слив поддона ⌀%.0f мм: %.1f″ от короткого края, по центру ширины (ANCHORS: drain_end)" % (
        R["drain_d"], R["drain_from_end"] / 25.4), Part.makeCylinder(dr_r, 3.0, V(dr_x, dr_y, z_in)), COL_DARK)
    trap = Part.makeCylinder(24.0, z_in + 150.0, V(dr_x, dr_y, -150.0))
    put("Shower_DrainTrap", "Сифон слива 1-1/2″ — вниз через пол в серый бак под днищем (место — по месту)", trap, COL_DARK)
    for fn in ("Floor_XPS", "Floor_Plywood"):
        fo = doc.getObject(fn)
        if fo is not None:
            fo.Shape = fo.Shape.cut(Part.makeCylinder(32.0, floor_top + 20.0, V(dr_x, dr_y, -10.0)))
    # пластина передней стойки кровати попадает под поддон → узкая (Simpson TP15) вдоль борта
    pl_o = doc.getObject("BedPostPlate_pY_front")
    plate_note = None
    if pl_o is not None and pl_o.Shape.distToShape(pan)[0] < 3.0:
        pb_ = pl_o.Shape.BoundBox
        ply_, plx_ = 46.0, 127.0
        pl_base = V((pb_.XMin + pb_.XMax) / 2.0 - plx_ / 2.0, ybase(ks, post_out_s[ks], ply_), pb_.ZMin)
        if hasattr(pl_o, "Length"):
            pl_o.Length, pl_o.Width, pl_o.Height = plx_, ply_, pb_.ZLength
            pl_o.Placement = App.Placement(pl_base, App.Rotation())
            pl_o.recompute()
        else:
            pl_o.Shape = Part.makeBox(plx_, ply_, pb_.ZLength, pl_base)
        plate_note = "пластина передней стойки кровати — узкая Simpson TP15 вдоль борта (широкая TP35 — под поддоном)"
    y_sf = y_aisle                                         # край поддона к проходу

    def pan_margin(xx, yy, in_u, in_v):
        """Запас (мм) от точки до внутренней границы: края площадки/проёма и линия среза с плотиной (+ — внутри)."""
        u_, v_ = xx - x0, y_wall - yy
        m_ = min(u_ - in_u, (Lp - in_u) - u_, v_ - in_v, (Wp - in_v) - v_)
        if cut_a:
            m_ = min(m_, (u_ / cut_b + v_ / cut_a - 1.0) * cut_a * cut_b / math.hypot(cut_a, cut_b) - R["seal_t"])
        return m_

    # ═══════ ТУАЛЕТ SEAFLO НА ПЛАТФОРМЕ С КОЛЁСАМИ (транспорт — под щитом; в душе — в поддоне) ═══════
    TT = TOILET_RECT
    tlx, tly, tlz = TT["dims"][0], TT["dims"][1], AT["toilet_h"]
    ty1 = arch_ywall - (WA[ks]["protrusion"] + AR["toilet_arch_gap"])      # |Y| грани туалета к борту (рядом с аркой)
    ty0 = ty1 - tly                                                        # … к проходу
    wd, ww = AT["wheel_d"], AT["wheel_w"]
    wr = wd / 2.0
    plate_th = AT["plate_th"] if AT.get("plate_th") is not None else z_in - floor_top
    z_pl = floor_top + plate_th                                            # верх плиты = дно поддона
    caster_h = AT["caster_h"] if AT.get("caster_h") is not None else max(
        AT["mount_h"], math.ceil(z_pan - z_pl + AT["rim_clear"]))          # платформа проходит над бортиком
    spacer = caster_h - AT["mount_h"]
    z_pf0 = z_pl + caster_h
    z_pf1 = z_pf0 + AT["platform_th"]
    z_tt1 = z_pf1 + tlz
    pfy0, pfy1 = ty0 - AT["aisle_margin"], ty1
    mpx, mpy = AT.get("mount_plate", (40.0, ww + 10.0))
    wx = max(wr, mpx / 2.0)
    nF = int(AT.get("front_n", 2))
    hw_ = max(ww, mpy) / 2.0                              # половина ширины колеса/площадки крепления
    yF_a = pfy0 + AT["wheel_inset"] + hw_
    yW = pfy1 - AT["wheel_inset"] - hw_
    ysF = [yF_a + (yW - yF_a) * i_ / (nF - 1) for i_ in range(nF)] if nF > 1 else [yW]
    tagsF = ["A"] + [str(i_) for i_ in range(2, nF)] + ["W"] if nF > 1 else ["W"]
    seal_t = R["seal_t"] if cut_a else 0.0
    # передние колёса в транспорте — у бортика/плотины: ближе всего к борту колесо упирается в линию среза
    v_wheel_min = y_wall - (yW + hw_)
    f0 = x0 + max(t_end, uc(v_wheel_min) + seal_t + 4.0) + wx
    d_fwd = AR.get("toilet_forward", 0.0)                                  # Dimitri 2026-11-12: туалет в транспорте торчит вперёд за край щита
    xt0 = dx1 - tlx + d_fwd                                                # туалет в транспорте: передом до края щита (+ d_fwd вперёд)
    v_toilet_min = y_wall - ty1
    u_in = max(t_end, uc(v_toilet_min) + seal_t) + AT["toilet_in"]         # туалет в душе: его задняя грань за бортиком
    travel = (x0 + u_in) - xt0
    WB = travel + f0 - (x0 - wx)                                           # колёсная база (задние колёса в душе — у края)
    xw_r0 = f0 - WB
    pfx0, pfx1 = xw_r0 - wx - AT["rear_over"], f0 + wx + AT["front_over"]
    plx0, plx1 = xw_r0 - wx - AT["rear_gap"], x0 - 2.0
    fg_t = sg
    fsh_t = {}
    put_t = lambda n_, l_, sh_, c_: (add_shape(doc, n_, l_, sh_, color=c_, group=fg_t), fsh_t.__setitem__(n_, sh_),
                                      parts.__setitem__(n_, sh_))
    if plate_th > 1.0:
        put_t("Toilet_Plate", "Плита под туалет — %.1f″ (%.0f мм): верх = дно поддона; X %.0f..%.0f — задние колёса по ней" % (
            plate_th / 25.4, plate_th, plx0, plx1),
            Part.makeBox(plx1 - plx0, pfy1 - pfy0, plate_th, V(plx0, ybase(ks, pfy1, pfy1 - pfy0), floor_top)),
            (0.55, 0.45, 0.35))
    f1 = f0 + travel
    pf_box = Part.makeBox(pfx1 - pfx0, pfy1 - pfy0, AT["platform_th"], V(pfx0, ybase(ks, pfy1, pfy1 - pfy0), z_pf0))
    put_t("Toilet_Platform", "Платформа туалета — фанера %.2f″ %.1f×%.1f″ на колёсиках ⌀%.0f″ (%d спереди, 2 сзади); передняя часть "
          "всегда в поддоне (за краем щита, внутри душа — согласованное исключение)" % (
              AT["platform_th"] / 25.4, (pfx1 - pfx0) / 25.4, (pfy1 - pfy0) / 25.4, wd / 25.4, nF), pf_box, (0.80, 0.66, 0.46))
    wheels = [("F", f0, t_, y_) for t_, y_ in zip(tagsF, ysF)] + [
        ("R", xw_r0, "A", yF_a), ("R", xw_r0, "W", yW)]
    for tag_, xc_, side_, yc_ in wheels:
        yy = ks * yc_
        wheel = Part.makeCylinder(wr, ww, V(xc_, yy - ww / 2.0, z_pl + wr), V(0, 1, 0)).fuse(
            Part.makeBox(mpx, mpy, z_pf0 - (z_pl + wd), V(xc_ - mpx / 2.0, yy - mpy / 2.0, z_pl + wd)))
        put_t("Toilet_Wheel_%s%s" % (tag_, side_), "Колёсико %s ⌀%.0f″ неповоротное, высота с креплением %.2f″ + брусок-проставка "
              "%.0f мм до платформы (%s)" % ("переднее — всегда в поддоне" if tag_ == "F" else "заднее — всегда на плите",
                                             wd / 25.4, AT["mount_h"] / 25.4, spacer,
                                             {"A": "к проходу", "W": "к борту"}.get(side_, "№%s от прохода" % side_)),
              wheel, (0.15, 0.15, 0.15))
        xl1 = dx1 + pt_ + 16.0                                 # линия нижней шторки — сразу за задней стенкой душа
    xl1 = dx1 + pt_ + 16.0                                 # линия нижней шторки — сразу за задней стенкой душа
    dam_x = max(xl1 - 16.0, xt0 + tlx + 4.0)               # порожек — за шторкой, но не под туалетом
    if dam_x + 10.0 < pfx1 - 3.0:
        put_t("Toilet_PlatformDam", "Порожек на платформе за нижней шторкой (в транспортном положении): вода с передней части "
              "платформы стекает в поддон, а не по платформе под кровать",
              Part.makeBox(10.0, pfy1 - pfy0, 10.0, V(dam_x, ybase(ks, pfy1, pfy1 - pfy0), z_pf1)), (0.25, 0.25, 0.25))
    tsh_ = Part.makeBox(tlx, tly, tlz, V(xt0, ybase(ks, ty1, tly), z_pf1))
    try:
        tsh_ = tsh_.makeFillet(25.0, [e for e in tsh_.Edges if abs(e.tangentAt(0).z) > 0.9])
    except Exception:
        pass
    put_t("Toilet_Camco", "%s — на платформе с колёсами, транспортное положение (под щитом, вплотную к краю щита); выезжает в душ "
          "на %.1f″" % (TT["title"], travel / 25.4), tsh_, (0.78, 0.78, 0.76))
    # ── проверки «в душе» — по формам (сдвиг на ход) ──
    mv = V(travel, 0, 0)
    t_sh = tsh_.translated(mv)
    wF = [fsh_t[n_] for n_ in fsh_t if n_.startswith("Toilet_Wheel_F")]
    wR = [fsh_t["Toilet_Wheel_R%s" % s_] for s_ in "AW"]
    pf_sh = fsh_t["Toilet_Platform"].translated(mv)
    tb1 = t_sh.BoundBox
    corners_t = [(x_, y_) for x_ in (tb1.XMin, tb1.XMax) for y_ in (ty0, ty1)]
    wc = lambda shapes, dx=0.0: [(b_.XMin + dx, b_.XMax + dx, abs(b_.YMin), abs(b_.YMax)) for b_ in (s_.BoundBox for s_ in shapes)]
    # передние колёса стоят на площадке дна ПРОТЕКТОРОМ (колесо ⌀ × ширина); площадка крепления — выше, над скосом дна
    tread = lambda dx: [(xc_ + dx + sx_ * wr, yc_ + sy_ * ww / 2.0) for xc_ in (f0,) for _, yc_ in zip(tagsF, ysF)
                        for sx_ in (-1, 1) for sy_ in (-1, 1)]
    corners_w, corners_w0 = tread(travel), tread(0.0)
    mounts = [Part.makeBox(mpx, mpy, 30.0, V(f0 - mpx / 2.0, ks * yc_ - mpy / 2.0, z_pl + wd)) for yc_ in ysF]
    pfb = fsh_t["Toilet_Platform"].BoundBox
    fit = dict(
        toilet_in_pan=min(pan_margin(x_, y_, top_in, top_in) for x_, y_ in corners_t),
        front_wheels_in_pan_shower=min(pan_margin(x_, y_, t_end, t_side) for x_, y_ in corners_w),
        front_wheels_in_pan_transport=min(pan_margin(x_, y_, t_end, t_side) for x_, y_ in corners_w0),
        rear_wheels_out_shower=x0 - max(w_.translated(mv).BoundBox.XMax for w_ in wR),
        rear_wheels_on_plate=min(w_.BoundBox.XMin for w_ in wR) - (plx0 + AT["rear_gap"]),
        toilet_under_deck=dx1 - tsh_.BoundBox.XMax,
        platform_over_rim=z_pf0 - z_pan - AT["rim_clear"],
        platform_front_in_pan_transport=min(pan_margin(pfb.XMax, y_, top_in, top_in) for y_ in (pfy0, pfy1)),
        platform_front_in_pan_shower=min(pan_margin(pfb.XMax + travel, y_, top_in, top_in) for y_ in (pfy0, pfy1)))
    chk_t = [("туалет в душе — внутри проёма поддона (запас)", fit["toilet_in_pan"]),
             ("передние колёса на площадке дна — в душе", fit["front_wheels_in_pan_shower"]),
             ("передние колёса на площадке дна — в транспорте", fit["front_wheels_in_pan_transport"]),
             ("передний край платформы в поддоне — в транспорте", fit["platform_front_in_pan_transport"]),
             ("передний край платформы в поддоне — в душе", fit["platform_front_in_pan_shower"]),
             ("задние колёса снаружи поддона — в душе", fit["rear_wheels_out_shower"]),
             ("задние колёса на плите — в транспорте (до её заднего края)", fit["rear_wheels_on_plate"]),
             ("туалет под щитом — в транспорте (< 0: торчит вперёд за край щита, по решению Dimitri)", fit["toilet_under_deck"]),
             ("платформа над бортиком поддона (сверх %.0f мм)" % AT["rim_clear"], fit["platform_over_rim"])]
    moving0 = [tsh_, fsh_t["Toilet_Platform"]] + wF + wR
    moving1 = [t_sh, pf_sh] + [w_.translated(mv) for w_ in wF + wR]
    for lab, pref in (("арка", ("WheelArch_",)), ("стойки/пластины кровати", ("BedPost",)), ("поперечины кровати", ("BedCross_",)),
                      ("этажерка батарей", ("Bank", "Battery_"))):
        ss = [o.Shape for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull()
              and o.Name.startswith(pref)]
        if ss:
            chk_t.append(("туалет/платформа/колёса ↔ %s — в транспорте" % lab, min(m_.distToShape(s_)[0] for m_ in moving0 for s_ in ss)))
            chk_t.append(("туалет/платформа/колёса ↔ %s — в душе" % lab, min(m_.distToShape(s_)[0] for m_ in moving1 for s_ in ss)))
    fit["mounts_to_pan_transport"] = min(m_.distToShape(pan)[0] for m_ in mounts)
    fit["mounts_to_pan_shower"] = min(m_.translated(mv).distToShape(pan)[0] for m_ in mounts)
    chk_t += [("крепления передних колёс ↔ поддон — в транспорте (над скосом дна)", fit["mounts_to_pan_transport"]),
              ("крепления передних колёс ↔ поддон — в душе", fit["mounts_to_pan_shower"])]
    toilet_pf = dict(plate=(plx0, plx1, plate_th), z=(z_pl, z_pf0, z_pf1, z_tt1), x0=(xt0, xt0 + tlx),
                     x1=(xt0 + travel, xt0 + tlx + travel), y=(ty0, ty1), pf_x=(pfx0, pfx1), pf_y=(pfy0, pfy1), WB=WB,
                     travel=travel, wheels_x=(f0, xw_r0), checks=chk_t, fit=fit, h_total=z_tt1 - floor_top, spacer=spacer,
                     from_wall=(y_wall - ty1, y_wall - ty0), n_front=nF)

    # ═══════ СТЕНКИ, ПОТОЛОК, ШТОРКА, НАГРЕВАТЕЛЬ ═══════
    x_rw = dx1                                             # задняя стенка душа — по краю щита, вниз — до верха туалета (+10 мм)
    z_rw0 = z_tt1 + 10.0                                   # Dimitri 2026-11-12: козырёк не нужен — стенка продлена вниз
    put("Shower_WallRear", "Задняя стенка душа по краю щита кровати: от потолка вниз до верха туалета + 10 мм (%.0f мм над полом) — "
        "ниже проём, под стенкой туалет на платформе выезжает в душ" % (z_rw0 - floor_top), env_solid(x_rw, pt_, y_sf, z_rw0, z_ceil),
        COL_WALL, 10)
    cur_lo = Part.makeBox(4.0, (y_wall - 30.0) - (y_sf + 80.0), (z_rw0 - 4.0) - (z_pan + 25.0),
                          V(xl1 - 6.0, y_sf + 80.0, z_pan + 25.0))
    cur_lo = cur_lo.cut(Part.makeBox(20.0, pfy1 - pfy0 + 2.0, z_pf1 - z_pan, V(xl1 - 16.0, ybase(ks, pfy1 + 1.0, pfy1 - pfy0 + 2.0), z_pan)))
    if xt0 + tlx > xl1 - 6.0:                              # туалет в транспорте торчит сквозь линию шторки — вырез по его сечению
        cur_lo = cur_lo.cut(Part.makeBox(30.0, tly + 10.0, z_tt1 - z_pan + 5.0, V(xl1 - 16.0, ybase(ks, ty1 + 5.0, tly + 10.0), z_pan)))
    put("Shower_CurtainLower", "Нижняя шторка с нижнего края задней стенки до поддона — закрывает проём; ложится на платформу туалета перед "
        "порожком; сдвигается, когда туалет выезжает в душ", cur_lo, (0.55, 0.75, 0.85), 55)
    pw_t = K["wall_panel_t"]
    back = env_solid(x_rw + pt_, x1 - (x_rw + pt_), y_sf, z_pan, z_ceil).cut(
        env_solid(x_rw + pt_ - 1, x1 - x_rw + 2, y_sf - 5, z_pan - 1, z_ceil + 1, g_extra=pw_t)).cut(arch_s)
    put("Shower_WallBack", "Стенка душа по борту (фанера 1/2″ + FRP) от задней стенки до торца кухни; у арки вырезана по её форме",
        back, COL_WALL, 10)
    GH = K.get("gas_heater")
    flue = None
    ghx = ghy = ghz = x_h0 = y_h0 = y_h1 = z_h0 = z_h1 = fx_c = fy_c = fr_ = z_fl1 = None
    if GH:                                                 # газовый проточный нагреватель — на задней стенке, внутри душа
        ghx, ghy, ghz = GH["dims"][1], GH["dims"][0], GH["dims"][2]
        z_h0 = floor_top + GH["z0"]
        z_h1 = z_h0 + ghz
        y_h1 = yw(z_h1) - 12.0 - GH["side_gap"]
        y_h0 = y_h1 - ghy
        x_h0 = x_rw + pt_
        heater = Part.makeBox(ghx, ghy, ghz, V(x_h0, ybase(ks, y_h1, ghy), z_h0))
        try:
            heater = heater.makeFillet(8.0, [e for e in heater.Edges if abs(e.tangentAt(0).z) > 0.9])
        except Exception:
            pass
        put("Shower_GasHeater", "Газовый проточный нагреватель Camplux 1.58 GPM 11.8×17.3×5.1″ на задней стенке (внутри душа); "
            "⚠️ производитель: только на улице — дымоход, датчики CO/пропана, приток воздуха", heater, (0.97, 0.97, 0.97))
        for i_, (dy_, col_) in enumerate(((0.25, (0.85, 0.20, 0.15)), (0.5, (0.6, 0.6, 0.6)), (0.75, (0.15, 0.40, 0.85)))):
            put("Shower_GasHeater_Knob%d" % (i_ + 1), "Ручка нагревателя (%s)" % ("газ", "режим", "вода")[i_],
                Part.makeCylinder(18.0, 15.0, V(x_h0 + ghx, ks * (y_h0 + dy_ * ghy), z_h0 + 120.0 + (40.0 if i_ == 1 else 0.0)),
                                  V(1, 0, 0)), col_)
        fx_c, fy_c = x_h0 + ghx / 2.0, ks * (y_h0 + ghy / 2.0)
        fr_ = GH["flue_d"] / 2.0
        z_fl1 = crown + GH["roof_out"]
        flue = Part.makeCylinder(fr_, z_fl1 - z_h1, V(fx_c, fy_c, z_h1))
        put("Shower_Flue", "Дымоход нагревателя ⌀%.0f″ нержавейка — вертикально вверх через потолок и крышу" % (GH["flue_d"] / 25.4),
            flue, (0.62, 0.64, 0.66))
        put("Shower_FlueCap", "Колпак дымохода на крыше (от дождя/ветра)",
            Part.makeCylinder(fr_ * 2.0, 60.0, V(fx_c, fy_c, z_fl1)), (0.35, 0.35, 0.35))
        put("Shower_FlueThimble", "Проходка дымохода через потолок/утеплитель (огнестойкая муфта)",
            Part.makeCylinder(fr_ + 25.0, 40.0, V(fx_c, fy_c, z_ceil - 20.0)).cut(
                Part.makeCylinder(fr_ + 0.5, 50.0, V(fx_c, fy_c, z_ceil - 25.0))), (0.30, 0.30, 0.30))
    y_ceil_back = yw(z_ceil)
    ceil = Part.makeBox(x1 - (x_rw + pt_), Wp, 12.0, V(x_rw + pt_, y_sf, z_ceil - 12.0)).common(
        Part.makeBox(3000.0, y_ceil_back, 40.0, V(x_rw, 0.0, z_ceil - 20.0)))
    if flue is not None:
        ceil = ceil.cut(Part.makeCylinder(fr_ + 25.0, 60.0, V(fx_c, fy_c, z_ceil - 30.0)))
    put("Shower_Ceiling", "Потолок душа (фанера 1/2″ + FRP), Z=%.0f: прямоугольник над поддоном" % z_ceil, ceil, COL_WALL, 10)
    # шторка — Г-образная (вдоль прохода и по торцу к кухне), на 60 мм внутрь от наружной кромки поддона
    ci_ = K.get("curtain_in", 60.0)
    z_c0, z_c1 = z_pan + 40.0, z_ceil - 60.0
    xc0, xc1 = x_rw + pt_ + 10.0, x1 - ci_
    put("Shower_Curtain", "Шторка душа вдоль прохода (36″ поддона, на %.0f мм внутрь от кромки) — Г-образная вместе с торцевой" % ci_,
        Part.makeBox(xc1 - xc0, 3.0, z_c1 - z_c0, V(xc0, y_sf + ci_, z_c0)), (0.55, 0.75, 0.85), 55)
    put("Shower_CurtainFront", "Шторка душа у торца к кухне (24″), на %.0f мм внутрь от кромки поддона" % ci_,
        Part.makeBox(3.0, (y_wall - 30.0) - (y_sf + ci_), z_c1 - z_c0, V(xc1, y_sf + ci_, z_c0)), (0.55, 0.75, 0.85), 55)
    put("Shower_CurtainRod", "Карниз шторки (под потолком): вдоль прохода и по торцу — Г-образный",
        Part.makeCylinder(8.0, xc1 - (x_rw + pt_), V(x_rw + pt_, y_sf + ci_ + 1.5, z_ceil - 40.0), V(1, 0, 0)).fuse(
            Part.makeCylinder(8.0, (y_wall - 30.0) - (y_sf + ci_), V(xc1 + 1.5, y_sf + ci_, z_ceil - 40.0), V(0, 1, 0))), COL_STEEL)
    yb_h = yw(1650.0) - 12.0
    put("Shower_Head", "Лейка душа на штанге / смеситель (на стенке по борту)",
        Part.makeCylinder(55.0, 25.0, V(x0 + 300.0, ks * (yb_h - 25.0), 1650.0 + floor_top), V(0, ks, 0)), COL_STEEL)
    put("Shower_ExhaustFan", "Вытяжка 12V ~4″ в потолке душа → небольшое отверстие в стене",
        Part.makeCylinder(60.0, 40.0, V(x0 + 250.0, ks * (y_ceil_back - 120.0), z_ceil - 12.0), V(0, 0, 1)), COL_DARK)

    # ═══════ КУХНЯ: блок шириной 24″ (= поддону), торец к душу — прямой, по краю поддона ═══════
    # поддон заходит за плоскость панели (слой утеплителя) — кухня туда не идёт (ребро кузова X≈3130 у её торца): фронт кухни — по панели
    y_sf_pan = y_sf
    y_wall0 = yw(z_pan)
    y_sf = y_wall0 - Wp
    kx0 = x1 + K["kitchen_gap"]
    kx1 = K["kitchen_end_x"]
    kl = kx1 - kx0
    z_ct = floor_top + K["counter_h"]
    z_cb = z_ct - K["counter_th"]
    dt_ = K["door_t"]
    y_kf = y_sf + dt_                                      # фронт короба; дверцы (12) — до края поддона к проходу
    y_ctf = y_sf                                           # столешница — вровень с дверцами: ширина блока = 24″ = поддон
    ph_k, pr_k = K["plinth"]
    dvt = K.get("divider", pt_)
    fx0_, fy0_, fz = K["fridge"]
    fx, fy = (fy0_, fx0_) if K.get("fridge_turn") else (fx0_, fy0_)     # холодильник повёрнут: 321 вдоль X, 603 поперёк
    fpad = K.get("fridge_pad", 10.0)
    x_div1 = kx1 - pt_ - fx - 2.0 * fpad                   # перегородка секций: грань к кабине
    x_div0 = x_div1 - dvt                                  # … к душу
    skx, sky, skz = K["sink"]
    sec1_in = x_div0 - (kx0 + pt_)                         # секция мойки внутри
    sk_x0 = kx0 + pt_ + (sec1_in - skx) / 2.0
    y_s0 = y_ctf + K.get("sink_margin", (40.0, 40.0))[1]
    y_s1 = y_s0 + sky
    sink_fit = sec1_in - skx
    z_b = floor_top + ph_k + pt_
    carc = env_solid(kx0, kl, y_kf, floor_top + ph_k, z_cb)
    y_back_in = lambda z: yw(z) - (0.0 if z < z_ct else pw_t)                     # передняя грань стенной панели (кухня стоит перед ней)
    y_kb = y_back_in(z_cb)
    cav1 = Part.makeBox(x_div0 - (kx0 + pt_), (y_kb - pt_) - (y_kf - 1.0), z_cb - z_b, V(kx0 + pt_, y_kf - 1.0, z_b))
    z_f0 = z_b + 15.0                                      # ларь на салазках над дном короба
    z_sh = z_f0 + fz + 40.0                                # полка над ларём (низ)
    cav_f = Part.makeBox(kx1 - pt_ - x_div1, (y_kb + 1.0) - (y_kf - 1.0), z_sh - z_b, V(x_div1, y_kf - 1.0, z_b))   # без задней стенки
    cav_u = Part.makeBox(kx1 - pt_ - x_div1, (y_kb - pt_) - (y_kf - 1.0), z_cb - (z_sh + pt_), V(x_div1, y_kf - 1.0, z_sh + pt_))
    carc = carc.cut(cav1).cut(cav_f).cut(cav_u)
    put("Kitchen_Carcass", "Короб кухни (фанера 3/4″) шириной 24″ вместе с дверцами (= поддон), 2 секции: мойка | шкафчик + "
        "холодильник; торец к душу — прямой, по краю поддона", carc, COL_CAB)
    put("Kitchen_WallPanel", "Стенная панель 1/2″ за кухней (продолжение панели душа): поддон и кухня стоят перед ней",
        env_solid(kx0, kl, y_sf, z_ct, z_ceil).cut(env_solid(kx0 - 1, kl + 2, y_sf - 5, z_ct - 1, z_ceil + 1, g_extra=pw_t)),
        COL_WALL, 10)
    put("Kitchen_Plinth", "Цоколь кухни", Part.makeBox(kl, (y_kb - y_kf) - pr_k, ph_k, V(kx0, y_kf + pr_k, floor_top)),
        (0.35, 0.30, 0.25))
    top = env_solid(kx0, kl, y_ctf, z_cb, z_ct).cut(Part.makeBox(skx, sky, K["counter_th"] + 2, V(sk_x0, y_s0, z_cb - 1)))
    put("Kitchen_Countertop", "Столешница 1″ (мебельный щит), верх %.0f над полом (36″); передняя кромка — вровень с краем поддона"
        % K["counter_h"], top, COL_TOP)
    sk_o = V(sk_x0, y_s0, z_ct - skz)
    sink = Part.makeBox(skx, sky, skz, sk_o).cut(Part.makeBox(skx - 4, sky - 4, skz, V(sk_o.x + 2, sk_o.y + 2, sk_o.z + 2)))
    put("Kitchen_Sink", "Барная мойка 10×10″ из нержавейки (секция у душа)", sink, COL_STEEL)
    fct = V(sk_o.x + skx / 2.0, y_s1 + 30.0, z_ct)
    faucet = Part.makeCylinder(12.0, 260.0, fct).fuse(Part.makeCylinder(10.0, 170.0, V(fct.x, fct.y, fct.z + 250.0), V(0, -1, 0)))
    put("Kitchen_Faucet", "Кран (насос 12V включается по давлению)", faucet, COL_STEEL)
    put("Kitchen_Kettle", "Электрочайник (от инвертора) или 12V-чайник",
        Part.makeCylinder(85.0, 230.0, V(kx1 - 150.0, (y_kf + y_kb) / 2.0, z_ct)), (0.85, 0.85, 0.88))
    put("Kitchen_Outlet", "Розетка 120V + USB над столешницей",
        Part.makeBox(70.0, 20.0, 115.0, V(kx1 - 150.0 - 35.0, yw(z_ct + 150.0) - 20.0, z_ct + 120.0)), (0.95, 0.95, 0.95))
    fridge_x0 = x_div1 + fpad
    y_f1 = y_back_in(z_f0 + fz / 2.0)                      # холодильник — задом к стенной панели (задней стенки короба в нише нет)
    y_f0 = y_f1 - fy
    put("Kitchen_Fridge", "Холодильник %s %.1f×%.1f×%.1f″ на салазках, повёрнут на 90°: длинная сторона — в глубину кухни; "
        "выдвигается в проход на %.0f мм (крышка сверху)" % (K.get("fridge_title", "12V"), fx0_ / 25.4, fy0_ / 25.4, fz / 25.4,
                                                              K["fridge_slide"]),
        Part.makeBox(fx, fy, fz, V(fridge_x0, y_f0, z_f0)), COL_FRIDGE)
    put("Kitchen_FridgeSlide", "Салазки холодильника (полного выдвижения, под ~45 кг)",
        Part.makeBox(fx, fy, 15.0, V(fridge_x0, y_f0, z_f0 - 15.0)), COL_STEEL)
    put("Kitchen_DoorSink", "Дверца под мойкой (чашки, чай, фильтр, сифон)",
        Part.makeBox(x_div0 + dvt / 2.0 - 2.0 - (kx0 + pt_ + 3.0), dt_, z_cb - z_b - 6.0, V(kx0 + pt_ + 3.0, y_kf - dt_, z_b + 3.0)),
        (0.86, 0.70, 0.48))
    put("Kitchen_DoorUpper", "Дверца шкафчика над холодильником",
        Part.makeBox(kx1 - 3.0 - (x_div0 + dvt / 2.0 + 2.0), dt_, z_cb - (z_sh + pt_) - 6.0,
                     V(x_div0 + dvt / 2.0 + 2.0, y_kf - dt_, z_sh + pt_ + 3.0)), (0.86, 0.70, 0.48))
    zu0 = floor_top + K["upper"][0]
    y_uf = yw(zu0) - pw_t - K["upper"][1]
    put("Kitchen_UpperCabinet", "Верхний шкафчик (чашки/чай), по завалу борта", env_solid(kx0, kl, y_uf, zu0, z_ceil, g_extra=pw_t),
        COL_CAB)
    KF = KITCHEN_FLAP
    flap_summary = None
    if KF.get("enable"):                                   # откидная часть столешницы на торце у сиденья
        fl_, fth = KF["len"], KF["th"]
        bt_, bw_, bl_ = KF["bracket"]
        fy0, fy1 = y_ctf, yw(z_ct) - 5.0
        yc_ = (fy0 + fy1) / 2.0
        for i_, yb_ in enumerate((yc_ - KF["spacing"] / 2.0, yc_ + KF["spacing"] / 2.0)):
            put("Kitchen_FlapBracket%d" % (i_ + 1), "Складной кронштейн %d (сложен) — на торце кухни, плечо %.0f″" % (i_ + 1, bl_ / 25.4),
                Part.makeBox(bt_, bw_, bl_, V(kx1, ks * yb_ - bw_ / 2.0, z_ct - fth - bl_)), COL_STEEL)
            put("Kitchen_FlapBracketOpen%d" % (i_ + 1), "Кронштейн %d разложен (сиденье развёрнуто на 180°)" % (i_ + 1),
                Part.makeBox(bl_, bw_, bt_, V(kx1, ks * yb_ - bw_ / 2.0, z_ct - fth - bt_)), COL_STEEL, 70)
        put("Kitchen_Flap", "Откидная столешница %.0f×%.0f″ (1/2″) — сложена, висит на торце кухни" % (fl_ / 25.4, (fy1 - fy0) / 25.4),
            Part.makeBox(fth, fy1 - fy0, fl_, V(kx1 + bt_, fy0, z_ct - fl_)), COL_TOP)
        put("Kitchen_FlapOpen", "Откидная столешница разложена — вровень со столешницей, над развёрнутым сиденьем",
            Part.makeBox(fl_, fy1 - fy0, fth, V(kx1, fy0, z_ct - fth)), COL_TOP, 65)
        flap_summary = dict(len=fl_, w=fy1 - fy0, x_open=(kx1, kx1 + fl_), to_seat=3190.0 - (kx1 + bt_ + fth),
                            z_fold_low=z_ct - fl_ - floor_top)

    y_sf = y_sf_pan
    # ═══════ ПРОВЕРКИ И СВОДНЫЕ ЧИСЛА ═══════
    _dd = lambda a, b: a.distToShape(b)[0]
    objs = lambda pfx: [o.Shape for o in doc.Objects if o.Name.startswith(pfx) and o.isDerivedFrom("Part::Feature")
                        and not o.Shape.isNull() and o.Shape.Solids]
    no_plate = lambda pfx: [o.Shape for o in doc.Objects if o.Name.startswith(pfx) and "Plate" not in o.Name
                            and o.isDerivedFrom("Part::Feature") and not o.Shape.isNull() and o.Shape.Solids]
    checks = []
    pall = [s_ for n_, s_ in parts.items() if n_ not in ("Shower_WallRear", "Shower_WallBack", "Shower_PanCutSeal", "Shower_PanRect",
                                                          "Shower_Drain", "Shower_DrainTrap", "Kitchen_WallPanel")
            and not n_.startswith(("Toilet_", "Kitchen_"))]
    bed_ss = no_plate("Bed")
    if bed_ss:
        checks.append(("кровать (стойки/рейки/настил/матрас) ↔ душ", min(_dd(p, s_) for p in pall for s_ in bed_ss)))
    pl = doc.getObject("BedPostPlate_pY_front")
    if pl is not None and min(_dd(p, pl.Shape) for p in pall) < 0.5 and not plate_note:
        checks.append(("пластина передней стойки кровати (1.6 мм) — душ заходит на её край: подложить", 0.0))
    if plate_note:
        checks.append((plate_note, 0.0))
    m0_, m1_ = moving0, moving1
    pass_ = [n_ for n_ in parts if n_.startswith(("Shower_", "Kitchen_")) and n_ not in (
        "Shower_CurtainLower", "Shower_PanRect", "Shower_PanCutSeal", "Shower_Drain")]
    for pos_, ms_ in (("в транспорте", m0_), ("в душе", m1_)):
        v_, n_min = min((_dd(m_, parts[n_]), n_) for m_ in ms_ for n_ in pass_)
        toilet_pf["checks"].append(("туалет/платформа ↔ душ/кухня — %s (ближе всего %s)" % (pos_, n_min), v_))
    toilet_pf["checks"].append(("платформа ↔ поддон — в транспорте", _dd(m0_[1], pan)))
    toilet_pf["checks"].append(("платформа ↔ поддон — в душе", _dd(m1_[1], pan)))
    checks += toilet_pf["checks"]
    d_arch = _dd(pan, arch_s)
    checks.append(("поддон ↔ арка", d_arch))
    checks.append(("поддон ↔ кровать (край щита, X)", x0 - dx1))
    kpart = [parts[n_] for n_ in parts if n_.startswith("Kitchen_") and n_ != "Kitchen_WallPanel"]
    checks.append(("кухня ↔ поддон", min(_dd(k_, pan) for k_ in kpart)))
    checks.append(("кухня ↔ шторка", min(_dd(k_, parts[n_]) for k_ in kpart for n_ in ("Shower_Curtain", "Shower_CurtainFront"))))
    checks.append(("мойка ↔ перегородка секций (запас)", sink_fit))
    post_f = [o.Shape for o in doc.Objects if o.Name in ("BedPost_pY_front",)]
    if post_f:
        checks.append(("поддон/стенка душа ↔ передняя стойка кровати", min(_dd(s_, post_f[0]) for s_ in (pan, parts["Shower_WallBack"]))))
    gas = {}
    if GH:
        hsh = parts["Shower_GasHeater"]
        gas.update(heater_x=(x_h0, x_h0 + ghx), heater_y=(y_h0, y_h1), heater_z=(z_h0, z_h1), over_pan=x_h0 + ghx - x0,
                   flue_c=(fx_c, abs(fy_c)), flue_top=z_fl1, top_to_ceil=(z_ceil - 12.0) - z_h1)
        checks += [("нагреватель ↔ поддон (по высоте)", _dd(hsh, pan)), ("нагреватель ↔ лейка", _dd(hsh, parts["Shower_Head"])),
                   ("нагреватель ↔ шторка", _dd(hsh, parts["Shower_Curtain"])),
                   ("дымоход ↔ вытяжка", _dd(flue, parts["Shower_ExhaustFan"])),
                   ("дымоход ↔ карниз", _dd(flue, parts["Shower_CurtainRod"])),
                   ("дымоход ↔ ребро крыши", min(_dd(flue, s_) for s_ in objs("Rib")) if objs("Rib") else 999.0)]
    rect_summary = dict(
        pan=dict(x=(x0, x1), y_wall=y_wall, y_aisle=y_aisle, z_pan=z_pan - floor_top, z_in=z_in - floor_top, L=Lp, W=Wp,
                 drain=(dr_x, dr_y), drain_end=AR.get("drain_end", "front"), t_end=t_end, t_side=t_side, top_in=top_in,
                 bed_x=dx1, d_arch=d_arch, cut=(cut_a, cut_b), seal_len=(math.hypot(cut_a, cut_b) if cut_a else 0.0),
                 cut_area=cut_a * cut_b / 2.0, title=R["title"]),
        toilet=toilet_pf,
        kitchen=dict(x=(kx0, kx1), kl=kl, y_front=y_wall0 - Wp, depth=Wp, sec1=(kx0, x_div0), sink_x=(sk_x0, sk_x0 + skx),
                     sec1_in=sec1_in, sink_fit=sink_fit, sec2=(x_div1, kx1), fridge=(fx, fy, fz), fridge_title=K.get("fridge_title"),
                     fridge_front_behind=(y_f0 - (y_wall0 - Wp)), fridge_back_gap=(y_f1 - (y_f0 + fy)), counter=K["counter_h"],
                     seat_gap=3190.0 - kx1, flap=flap_summary),
        gas=gas, checks=checks, aisle_sh=y_sf + y_at_z(half, 900.0),
        headroom=(z_ceil - 12.0) - z_pan, z_ceil=z_ceil, floor_top=floor_top, rear_wall_z=z_rw0, plate_note=plate_note)
    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "galley_summary rect_summary")


def report(S):
    """Сводка по душу с прямоугольным поддоном, туалету на платформе и кухне (печатается после общей сводки)."""
    k = S.rect_summary
    if not k:
        return
    f0 = k["floor_top"]
    p, t, q = k["pan"], k["toilet"], k["kitchen"]
    mm_in = lambda v: "%.0f мм (%.1f″)" % (v, v / 25.4)
    print("=" * 70)
    print("[Душ: прямоугольный поддон RecPro 36×24×5″ + туалет + кухня 24″ — ВАРИАНТ van_v1_rect_pan, 2026-11-12]")
    print("  Поддон: X %.0f..%.0f (%.0f″ вдоль борта); узкая грань X=%.0f — край щита кровати X=%.0f (разница %.1f мм); "
          "у борта |Y|=%.0f, к проходу |Y|=%.0f (%.0f″ поперёк)" % (
              p["x"][0], p["x"][1], p["L"] / 25.4, p["x"][0], p["bed_x"], p["x"][0] - p["bed_x"], p["y_wall"], p["y_aisle"], p["W"] / 25.4))
    print("  Высота верха бортика %s над полом; дно внутри %s; бортик у коротких сторон %.0f мм, у длинных %.0f мм до площадки дна "
          "(оценка); слив ⌀2″ %s: X=%.0f, |Y|=%.0f" % (
              mm_in(p["z_pan"]), mm_in(p["z_in"]), p["t_end"], p["t_side"],
              "у кабины" if p["drain_end"] == "front" else "у кровати", p["drain"][0], p["drain"][1]))
    a, b = p["cut"]
    if a:
        print("  СРЕЗ УГЛА (одна прямая): %.0f мм (%.1f″) вдоль узкой грани × %.0f мм (%.1f″) вдоль борта, линия %.0f мм (%.1f″), "
              "отпиливается %.0f см²; зазор до арки %.1f мм; плотина %.0f мм в чаше" % (
                  a, a / 25.4, b, b / 25.4, math.hypot(a, b), math.hypot(a, b) / 25.4, p["cut_area"] / 100.0, p["d_arch"],
                  RECT_PAN["seal_t"]))
    else:
        print("  Срез угла не нужен — поддон не задевает арку (зазор %.1f мм)" % p["d_arch"])
    print("  Туалет в транспорте: X %.0f..%.0f (под щитом, вплотную к краю щита), от борта %.1f″…%.1f″ (у пола), верх %.1f″ над полом; "
          "платформа X %.0f..%.0f, Y %.0f..%.0f" % (
              t["x0"][0], t["x0"][1], t["from_wall"][0] / 25.4, t["from_wall"][1] / 25.4, t["h_total"] / 25.4, t["pf_x"][0],
              t["pf_x"][1], t["pf_y"][0], t["pf_y"][1]))
    print("  Туалет в душе: X %.0f..%.0f; ход %s, колёсная база %s; плита %.1f″ X %.0f..%.0f; колёса ⌀%.0f″ (%d спереди, 2 сзади), "
          "брусок-проставка %.0f мм" % (t["x1"][0], t["x1"][1], mm_in(t["travel"]), mm_in(t["WB"]), t["plate"][2] / 25.4, t["plate"][0],
                                        t["plate"][1], dict(ANCHORS["toilet"], **ANCHORS["rect_pan"].get("toilet_wheels", {}))["wheel_d"] / 25.4, t["n_front"], t["spacer"]))
    print("  Кухня: X %.0f..%.0f (%.0f мм = %.1f″), глубина блока с дверцами и столешницей %s (= поддон), фронт |Y|=%.0f; секция "
          "мойки X %.0f..%.0f (внутри %.0f мм, мойка 10″: запас %.0f мм), секция холодильника X %.0f..%.0f; до спинок сидений %.0f мм" % (
              q["x"][0], q["x"][1], q["kl"], q["kl"] / 25.4, mm_in(q["depth"]), q["y_front"], q["sec1"][0], q["sec1"][1], q["sec1_in"],
              q["sink_fit"], q["sec2"][0], q["sec2"][1], q["seat_gap"]))
    print("  Холодильник %s повёрнут на 90°: %.0f (вдоль X) × %.0f (в глубину) × %.0f мм; фронт на %.1f мм глубже фасада, зазор до "
          "стенной панели %.1f мм" % (q["fridge_title"], q["fridge"][0], q["fridge"][1], q["fridge"][2], q["fridge_front_behind"],
                                      q["fridge_back_gap"]))
    if k["gas"]:
        g_ = k["gas"]
        print("  Нагреватель на задней стенке: X %.0f..%.0f (над поддоном %.0f мм), низ/верх %.1f″/%.1f″ над полом; до потолка %.0f мм; "
              "дымоход ⌀3″ X %.0f → до %.0f" % (g_["heater_x"][0], g_["heater_x"][1], g_["over_pan"], (g_["heater_z"][0] - f0) / 25.4,
                                                (g_["heater_z"][1] - f0) / 25.4, g_["top_to_ceil"], g_["flue_c"][0], g_["flue_top"]))
    print("  В душе: от верха бортика до потолка %s; проход напротив поддона %.0f мм (%.1f″)" % (
        mm_in(k["headroom"]), k["aisle_sh"], k["aisle_sh"] / 25.4))
    print("  Не нарисованы (по заданию): бак воды и насос, локер и баллон пропана, газовая линия, ящики багажника, полка 2-го этажа")
    print("  Зазоры/запасы: " + "; ".join("%s %.1f" % (n_, v_) for n_, v_ in k["checks"]))
    print("=" * 70)
