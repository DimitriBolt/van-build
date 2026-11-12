# -*- coding: utf-8 -*-
"""Бак для чистой воды (водительский борт, +Y) — варианты T-4320 / T-4100 / T-3500 / TORVA; активный выбирает WATER_VARIANT в params.py."""

import math

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .params import DPILLAR, TANK_FLOOR, TANK_RACK, WATER_TANK
from .common import COL_PLY, COL_STRUT, COL_WOOD, add_box, add_shape

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def torva(S):
    """Бак TORVA 33 gal на подставке (вариант WATER_VARIANT = "TORVA")."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, W, arch_shapes, arch_ywall, cutlist, doc = S.B, S.W, S.arch_shapes, S.arch_ywall, S.cutlist, S.doc
    dp_box_x, dp_shapes, floor_top, post_in, sd = S.dp_box_x, S.dp_shapes, S.floor_top, S.post_in, S.sd
    sw, xr, ybase, z_box, z_rail_top = S.sw, S.xr, S.ybase, S.z_box, S.z_rail_top
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
            # нависание над коробом D-стойки — только если дно бака (и фанера подставки) заметно выше короба
            for over in ([T.get("over_box", 0.0), 0.0] if T.get("over_box") else [0.0]):
                x_r = x_riser_r - over
                x_f = x_r + TL
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
                if over == 0.0 or (lift - ply_top) >= DPILLAR["box_h"] + 30.0:
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
        c_last = doc.getObject("BedCross_%d" % max(2, int(B["cross_n"])))
        if x4_tie is not None and x4_tie.Shape.BoundBox.XMin - sw > x_r + 200.0:
            p4x0, p4note = x4_tie.Shape.BoundBox.XMin - sw, "позади поперечины BedCross_Rack_fwd, болт к ней"
        else:
            p4x0 = c_last.Shape.BoundBox.XMin - sw
            p4note = "позади поперечины %s (под передним краем щита), болт к ней" % c_last.Name
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

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "ph tank_summary")


def t3500_shelf(S):
    """Бак T-3500 на полке над водительской аркой (вариант "T3500_shelf")."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, DP, W, arch_shapes, arch_ywall, cutlist = S.B, S.DP, S.W, S.arch_shapes, S.arch_ywall, S.cutlist
    doc, dp_body_x, dp_shapes, dx1, floor_top = S.doc, S.dp_body_x, S.dp_shapes, S.dx1, S.floor_top
    post_in, sd, sw, x_dp, xf, xr, ybase = S.post_in, S.sd, S.sw, S.x_dp, S.xf, S.xr, S.ybase
    z_rail_top = S.z_rail_top
    # ═══════ БАК T-3500 НА ПОЛКЕ НАД ВОДИТЕЛЬСКОЙ АРКОЙ (этажерка как у батарей, но без рейки у борта) ═══════
    trk_summary = None
    TR = TANK_RACK
    if B.get("enable") and TR.get("enable") and W.get("enable"):
        ts = TR["side"]
        ttag = "pY" if ts > 0 else "nY"
        rg = doc.addObject("App::DocumentObjectGroup", "TankRack")
        rg.Label = "Бак для воды T-3500 35 gal на полке над водительской аркой — ПРОЕКТ 2026-11-07"
        tsh = {}

        def tr_shape(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr, group=rg)
            tsh[name] = shape
            return shape

        def tr_box(name, label, dims, base, color, tr=0):
            return tr_shape(name, label, Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base)), color, tr)

        TLx, TWy, THz = TR["tank"]
        qx, qy, qt = TR["p_plate"]
        st, sh_ = TR["stop"]
        # по Y (|Y|): бак — вплотную к внутренним граням стоек кровати у борта; рейка в салон — под гранью бака
        y_w = post_in - TR["post_gap"]                   # грань бака к борту
        y_i = y_w - TWy                                  # грань бака к проходу = наружная грань рейки
        # по Z: полка лежит на ровном верху арки через резину; поперечины и рейка — под полкой, верх вровень
        z_arch = floor_top + W["height"]
        z_sh0 = z_arch + TR["pad"]                       # низ полки
        z_c0 = z_sh0 - sw                                # низ поперечин и рейки
        z_sh1 = z_sh0 + TR["shelf_th"]                   # верх полки = дно бака
        z_t1 = z_sh1 + THz
        # стойки со стороны прохода: P3 (напротив задней стойки кровати), P3f (напротив передней)
        L_tp = z_c0 - floor_top - qt
        for nm, x0, note in (("P3", xr - sw / 2.0, "напротив задней стойки кровати"),
                             ("P3f", xf - sw / 2.0, "напротив передней стойки кровати")):
            tr_box("TankPostPlate_%s" % nm, "Пластина под %s бака" % nm, (qx, qy, qt),
                   (x0 + sw / 2.0 - qx / 2.0, ybase(ts, y_i, qy), floor_top), COL_STRUT)
            tr_box("TankPost_%s" % nm, "Стойка %s бака (короткая, со стороны прохода, %s), L=%.0f — под рейку" % (
                       nm, note, L_tp), (sw, sd, L_tp), (x0, ybase(ts, y_i, sd), floor_top + qt), COL_STRUT)
        xi0, xi1 = xr - sw / 2.0, xf + sw / 2.0
        tr_box("TankRail_Inner", "Продольная рейка бака со стороны прохода strut, L=%.0f: по верху P3 и P3f" % (xi1 - xi0),
               (xi1 - xi0, sd, sw), (xi0, ybase(ts, y_i, sd), z_c0), COL_STRUT)
        L_tc = post_in - y_i
        for nm, xc in (("Rear", xr), ("Front", xf)):
            tr_box("TankCross_%s" % nm, "Поперечина бака %s strut, L=%.0f: уголок к стойке кровати ↔ уголок к рейке" % (
                       nm, L_tc), (sd, L_tc, sw), (xc - sd / 2.0, ybase(ts, post_in, L_tc), z_c0), COL_STRUT)
        # бак по X: «rear» — задним торцом к D-стойке (её грань скошена назад к центру → ближе всего у борта),
        #           «front» — передним торцом в упор на передней поперечине
        if TR.get("tank_pos") == "rear":
            x_t0 = dp_body_x(arch_ywall - y_w) + TR["dpillar_gap"]
            x_t1 = x_t0 + TLx
            xs_r = x_t0 - TR["stop_gap"] - st
            xs_f = x_t1 + TR["stop_gap"]
        else:
            xs_f = xf - sd / 2.0 - st                    # вертикальная полка переднего упора
            x_t1 = xs_f - TR["stop_gap"]
            x_t0 = x_t1 - TLx
            xs_r = x_t0 - TR["stop_gap"] - st
        # полка: от упора за баком (сзади — консоль за поперечиной, угол у борта срезан по D-стойке) до передних стоек
        xsh0 = min(xi0, xs_r - 3.0)
        sw_sh = post_in - (y_i - sd)
        d_pi = arch_ywall - post_in
        pts_sh = [(xsh0, y_i - sd), (xi1, y_i - sd), (xi1, post_in)]
        x_c = dp_body_x(d_pi) + 5.0
        if x_c > xsh0:                                   # срез угла у борта по грани D-стойки (+5 мм)
            d_e = (x_dp + 5.0 - xsh0) * DP["body_depth"] / DP["body_slant"]
            pts_sh += [(x_c, post_in), (xsh0, arch_ywall - d_e)]
        else:
            pts_sh += [(xsh0, post_in)]
        v_sh = [App.Vector(x_, ts * y_, z_sh0) for x_, y_ in pts_sh]
        shelf = Part.Face(Part.makePolygon(v_sh + [v_sh[0]])).extrude(App.Vector(0, 0, TR["shelf_th"]))
        tr_shape("TankShelf", "Полка бака — фанера 3/4″ %.0f×%.0f: на поперечинах, рейке и (через резину) на верху арки%s" % (
                     xi1 - xsh0, sw_sh, "; сзади консоль %.0f мм за поперечиной, угол у борта срезан по D-стойке" % (
                         xi0 - xsh0) if xsh0 < xi0 - 1.0 else ""), shelf, COL_PLY, 10)
        for i, dx in enumerate(TR["arch_pads_dx"]):
            tr_box("TankArchPad_%d" % (i + 1), "Резина %.0f мм: верх арки ↔ полка (подогнать по месту)" % TR["pad"],
                   (100.0, 90.0, TR["pad"]), (W["center_x"] + dx - 50.0, ybase(ts, arch_ywall - 45.0, 90.0), z_arch),
                   (0.15, 0.15, 0.15))
        tank = Part.makeBox(TLx, TWy, THz, App.Vector(x_t0, ybase(ts, y_w, TWy), z_sh1))
        try:
            tank = tank.makeFillet(TR["tank_r"], tank.Edges)
        except Exception:
            pass
        tr_shape("WaterTank_T3500", "Бак T-3500 (Class A Customs) 38.5×17.25×12″, 35 gal, полный ≈%.0f кг — штуцеры на "
                 "%s торце" % (TR["full_kg"], "заднем" if TR["fittings_end"] == "rear" else "переднем"),
                 tank, (0.70, 0.86, 0.98), 25)
        # штуцеры (бобышки) на торце: «left/right» — если смотреть на торец снаружи
        nrm = -1.0 if TR["fittings_end"] == "rear" else 1.0
        x_e = x_t0 if nrm < 0 else x_t1
        s_left = -nrm                                    # «лево» наблюдателя = знак Y
        ya, yb = sorted((ts * y_i, ts * y_w))
        fit_pts = []
        for k, (dia, lr, tb, off, what) in enumerate(TR["fittings"]):
            sY = s_left if lr == "left" else -s_left
            yc = (yb - off) if sY > 0 else (ya + off)
            zc_ = (z_t1 - off) if tb == "top" else (z_sh1 + off)
            r_b = (31.0 if dia >= 1.0 else 16.0)
            cyl = Part.makeCylinder(r_b, 16.0, App.Vector(x_e - nrm * 1.0, yc, zc_), App.Vector(nrm, 0, 0))
            tr_shape("TankFitting_%d" % (k + 1), "Штуцер %.1f″ FNPT — %s (%s, %s)" % (dia, what,
                     "у борта" if (yc * ts) > (y_i + y_w) / 2.0 else "к проходу", "верх" if tb == "top" else "низ"),
                     cyl, (0.95, 0.95, 0.95) if dia >= 1.0 else (0.20, 0.20, 0.20))
            fit_pts.append(dict(d=dia, what=what, x=x_e, y=yc, z=zc_, r=r_b, lr=lr, tb=tb))
        # упоры по торцам; на торце со штуцерами — в обход нижних штуцеров (самый длинный свободный участок)
        rear_pos = TR.get("tank_pos") == "rear"
        for nm, xs0, note in (("Front", xs_f, "болты через полку (полоса снизу) и в рейку" if rear_pos else
                               "на передней поперечине (болты через полку в неё)"),
                              ("Rear", xs_r, "у D-стойки, болты через полку (полоса снизу)" if rear_pos else
                               "болты через полку: в рейку и с шайбой под полкой")):
            segs = [(ya, yb)]
            if (nm == "Rear") == (nrm < 0):
                for f_ in fit_pts:
                    if f_["z"] - f_["r"] < z_sh1 + sh_ + 5.0:
                        c0, c1 = f_["y"] - f_["r"] - 10.0, f_["y"] + f_["r"] + 10.0
                        segs = [s_ for a_, b_ in segs for s_ in ((a_, min(b_, c0)), (max(a_, c1), b_)) if s_[1] - s_[0] > 1.0]
            s0, s1 = max(segs, key=lambda s_: s_[1] - s_[0])
            tr_box("TankStop_%s" % nm, "Упор-уголок 1-1/2″ у %s торца бака, L=%.0f, %s" % (
                       "переднего" if nm == "Front" else "заднего", s1 - s0, note), (st, s1 - s0, sh_), (xs0, s0, z_sh1),
                   COL_STRUT)
        # ремни: вокруг бака, полки и рейки (под полкой — в зазоре над аркой)
        th_s = TR["strap_th"]
        strap_x = (x_t0 + TLx / 4.0, x_t1 - TLx / 4.0)
        for k, xc in enumerate(strap_x):
            def _loop(pts):
                v = [App.Vector(xc - TR["strap_w"] / 2.0, ts * yy, zz) for yy, zz in pts]
                return Part.Face(Part.makePolygon(v + [v[0]])).extrude(App.Vector(TR["strap_w"], 0, 0))
            outer = _loop([(y_i - th_s, z_t1 + th_s), (post_in + th_s, z_t1 + th_s), (post_in + th_s, z_sh0 - th_s),
                           (y_i + th_s, z_sh0 - th_s), (y_i + th_s, z_c0 - th_s), (y_i - sd - th_s, z_c0 - th_s),
                           (y_i - sd - th_s, z_sh1 + th_s), (y_i - th_s, z_sh1 + th_s)])
            inner = _loop([(y_i, z_t1), (post_in, z_t1), (post_in, z_sh0), (y_i, z_sh0), (y_i, z_c0),
                           (y_i - sd, z_c0), (y_i - sd, z_sh1), (y_i, z_sh1)])
            tr_shape("TankStrap_%d" % (k + 1), "Ремень 1″ с кулачковой пряжкой вокруг бака и полки (пряжка — сбоку, "
                     "со стороны прохода)", outer.cut(inner), (0.85, 0.35, 0.10))
        # насос с фильтром — на полу под полкой, ниже штуцера «к насосу»: штуцеры сзади → в углу за аркой;
        # спереди → в нише между аркой и рейкой, передним краем под краем щита кровати
        pX, pY_, pZ = TR["pump"]
        if nrm < 0:
            pl_bb = doc.getObject("BedPostPlate_%s_rear" % ttag).Shape.BoundBox
            px0 = pl_bb.XMax + 5.0
            p_y = ybase(ts, arch_ywall - 45.0, pY_)
            p_note = "на полу за аркой"
        else:
            px0 = min(dx1 - 5.0, x_t1 + 60.0) - pX
            p_y = ybase(ts, y_i + 6.0 + pY_, pY_)
            p_note = "на полу в нише под полкой (между аркой и рейкой), под краем щита"
        tr_box("Water_Pump12V", "Насос 12V + фильтр (габарит-заглушка) — %s, ниже штуцера бака" % p_note,
               (pX, pY_, pZ), (px0, p_y, floor_top), (0.20, 0.35, 0.75))
        cutlist += [("рейка бака", float(xi1 - xi0)), ("поперечина бака", float(L_tc)), ("поперечина бака", float(L_tc)),
                    ("стойка бака", float(L_tp)), ("стойка бака", float(L_tp))]
        # проверки
        obj = lambda n: doc.getObject(n).Shape
        arch = arch_shapes[ts]
        dpf = dp_shapes[ts]
        frame_parts = [tsh[n] for n in tsh if n.startswith(("TankRail", "TankCross", "TankPost_"))]
        crosses_bed = [o.Shape for o in doc.Objects if o.Name.startswith("BedCross_") and o.isDerivedFrom("Part::Feature")]
        checks = [("бак ↔ арка", tank.distToShape(arch)[0]), ("бак ↔ D-стойка", tank.distToShape(dpf)[0]),
                  ("бак ↔ стойки кровати", min(tank.distToShape(obj("BedPost_%s_%s" % (ttag, w)))[0]
                                              for w in ("rear", "front"))),
                  ("бак ↔ поперечины кровати", min(tank.distToShape(c)[0] for c in crosses_bed)),
                  ("бак ↔ продольная рейка кровати", tank.distToShape(obj("BedSideRail_%s" % ttag))[0]),
                  ("бак ↔ щит", tank.distToShape(obj("BedDeck"))[0]),
                  ("бак ↔ стойки P3/P3f", min(tank.distToShape(tsh["TankPost_%s" % n])[0] for n in ("P3", "P3f"))),
                  ("упоры ↔ D-стойка", min(tsh["TankStop_%s" % n].distToShape(dpf)[0] for n in ("Rear", "Front"))),
                  ("полка ↔ арка", tsh["TankShelf"].distToShape(arch)[0]),
                  ("полка ↔ D-стойка", tsh["TankShelf"].distToShape(dpf)[0]),
                  ("поперечины/рейка/стойки ↔ арка", min(s_.distToShape(arch)[0] for s_ in frame_parts)),
                  ("насос ↔ арка", tsh["Water_Pump12V"].distToShape(arch)[0]),
                  ("насос ↔ D-стойка", tsh["Water_Pump12V"].distToShape(dpf)[0]),
                  ("насос ↔ пластина стойки", tsh["Water_Pump12V"].distToShape(obj("BedPostPlate_%s_rear" % ttag))[0]),
                  ("ремни ↔ арка", min(tsh["TankStrap_%d" % (k + 1)].distToShape(arch)[0] for k in range(2))),
                  ("ремни ↔ поперечины кровати", min(tsh["TankStrap_%d" % (k + 1)].distToShape(c)[0]
                                                     for k in range(2) for c in crosses_bed))]
        # прочность рейки в салон: доля бака на рейку (опоры полки — рейка и резина на арке), пролёт P3 ↔ P3f
        g_ = 9.81
        y_cg = y_i + TWy / 2.0
        y_rail = y_i - sd / 2.0
        y_pad = arch_ywall - 90.0
        share = (y_pad - y_cg) / (y_pad - y_rail)
        P_r = TR["full_kg"] * g_ * share
        Ls = xf - xr
        a0, a1 = x_t0 - xr, x_t1 - xr
        w_ = P_r / (a1 - a0)
        R1 = P_r * (Ls - (a0 + a1) / 2.0) / Ls
        M = max(R1 * x - (w_ * (x - a0) ** 2 / 2.0 if x > a0 else 0.0) + (w_ * (x - a1) ** 2 / 2.0 if x > a1 else 0.0)
                for x in [Ls * i / 400.0 for i in range(401)])          # Н·мм
        sig = M / (TR["rail_S_cm3"] * 1000.0)
        defl = 5.0 * P_r * Ls ** 3 / (384.0 * 200000.0 * TR["rail_I_cm4"] * 1e4)
        trk_summary = dict(floor_top=floor_top, x=(x_t0, x_t1), y=(y_i, y_w), z=(z_sh1, z_t1), z_arch=z_arch,
                           z_c=(z_c0, z_sh0), shelf=(xi1 - xsh0, sw_sh), rail=xi1 - xi0, cross=L_tc, post=L_tp,
                           under_cross=(z_rail_top - sw) - z_t1, tol=TR["tank_tol"], checks=checks,
                           from_wall=(arch_ywall - y_w, arch_ywall - y_i), fittings=fit_pts, straps=strap_x,
                           stops=(xs_r, xs_f), free_rear=xs_r - xsh0 if nrm < 0 else xsh0 - xi0, share=share, P_rail=P_r, sigma=sig,
                           sigma3=3 * sig, defl=defl, pump=(px0, px0 + pX), deck_front=dx1,
                           in_deck=dx1 - x_t1, in_deck_fit=dx1 - (x_e + 16.0 * nrm) if nrm > 0 else dx1 - x_t1,
                           to_dpillar=x_t0 - dp_body_x(arch_ywall - y_w), p1_rear=xr - sw / 2.0,
                           fittings_end=TR["fittings_end"], tank_pos=TR.get("tank_pos"))
        TR["_summary"] = {k: v for k, v in trk_summary.items() if k != "checks"}

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "trk_summary")


def floor_tank(S):
    """Бак на полу рядом с водительской аркой: T-4100 или T-4320 (варианты "T4100_floor" / "T4320_floor")."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, W, WA, arch_a_lin, arch_shapes = S.B, S.W, S.WA, S.arch_a_lin, S.arch_shapes
    arch_ywall, bank_summary, doc, dp_shapes, dx0 = S.arch_ywall, S.bank_summary, S.doc, S.dp_shapes, S.dx0
    dx1, floor_top, sd, sw, ybase, z_rail_top = S.dx1, S.floor_top, S.sd, S.sw, S.ybase, S.z_rail_top
    # ═══════ БАК НА ПОЛУ рядом с водительской аркой: T-4100 (поддон) или T-4320 (прямо на пол, коврик) ═══════
    tfl_summary = None
    TF = TANK_FLOOR
    if B.get("enable") and TF.get("enable") and W.get("enable"):
        ts = TF["side"]
        Wt = WA[ts]                                      # арка этого борта (ANCHORS)
        ttag = "pY" if ts > 0 else "nY"
        fg = doc.addObject("App::DocumentObjectGroup", "TankFloor")
        fg.Label = "Бак для воды %s на полу рядом с водительской аркой — ВАРИАНТ 2026-11-07" % TF["title"]
        fsh = {}

        def tf_shape(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr, group=fg)
            fsh[name] = shape
            return shape

        def tf_box(name, label, dims, base, color, tr=0):
            return tf_shape(name, label, Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base)), color, tr)

        TLx, TWy, THz = TF["tank"]
        cw, ch = TF["cleat"]
        pallet = TF.get("base") == "pallet"
        y_w = arch_ywall - Wt["protrusion"] - TF["arch_gap"]   # грань бака к борту (|Y|)
        y_i = y_w - TWy                                         # грань бака к проходу
        x_t0 = dx0 + TF["rear_clear"]                           # задний торец: от линии заднего края щита (двери)
        x_t1 = x_t0 + TLx
        n_r, rlen = 0, 0.0
        if pallet:                                              # поддон: бруски 2×4 плашмя поперёк + фанера
            rh, rw = TF["runner"]
            z_r1 = floor_top + rh
            z_b1 = z_r1 + TF["base_ply"]
            px0, px1 = x_t0 - cw, x_t1 + cw
            py_o, py_i = y_w, y_i - cw
            rlen = py_o - py_i
            tf_box("TankFloor_BasePly", "Поддон бака — фанера 1/2″ %.0f×%.0f" % (px1 - px0, py_o - py_i),
                   (px1 - px0, py_o - py_i, TF["base_ply"]), (px0, ybase(ts, py_o, py_o - py_i), z_r1), COL_PLY)
            n_r = 4
            for k in range(n_r):
                xk = px0 + (px1 - px0 - rw) * k / (n_r - 1)
                tf_box("TankFloor_Runner_%d" % (k + 1), "Брусок поддона 2×4 плашмя поперёк, L=%.0f (болт M8 в пол)" % (
                           rlen), (rw, rlen, rh), (xk, ybase(ts, py_o, rlen), floor_top), COL_WOOD)
            z_c = z_b1                                          # бруски-упоры — на фанере поддона
        else:                                                   # прямо на пол через резиновый коврик
            z_b1 = floor_top + TF["mat_th"]
            px0, px1 = x_t0, x_t1 + cw
            py_o, py_i = y_w, y_i - cw
            tf_box("TankFloor_Mat", "Резиновый коврик 1/8″ под баком (полосы-прижимы пола под баком сняты)",
                   (TLx, TWy, TF["mat_th"]), (x_t0, ybase(ts, y_w, TWy), floor_top), (0.15, 0.15, 0.15))
            z_c = floor_top                                     # бруски — на шурупах в фанеру пола
        z_t1 = z_b1 + THz
        tank = Part.makeBox(TLx, TWy, THz, App.Vector(x_t0, ybase(ts, y_w, TWy), z_b1))
        try:
            tank = tank.makeFillet(TF["tank_r"], tank.Edges)
        except Exception:
            pass
        tank_name = "WaterTank_%s" % TF["name"]
        tf_shape(tank_name, "Бак %s, полный ≈%.0f кг — штуцеры на %s торце" % (
                     TF["title"], TF["full_kg"], "заднем" if TF["fittings_end"] == "rear" else "переднем"),
                 tank, (0.70, 0.86, 0.98), 25)
        # штуцеры (положение — по картинке продавца, уточнить на баке)
        nrm = -1.0 if TF["fittings_end"] == "rear" else 1.0
        x_e = x_t0 if nrm < 0 else x_t1
        s_left = -nrm
        ya, yb = sorted((ts * y_i, ts * y_w))
        fit_pts = []
        for k, (dia, lr, tb, off, what) in enumerate(TF["fittings"]):
            sY = s_left if lr == "left" else -s_left
            yc = (yb - off) if sY > 0 else (ya + off)
            zc_ = (z_t1 - off) if tb == "top" else (z_b1 + off)
            r_b = 31.0 if dia >= 1.0 else 16.0
            tf_shape("TankFloor_Fitting_%d" % (k + 1), "Штуцер %.1f″ FNPT — %s (%s, %s)" % (
                         dia, what, "у борта" if (yc * ts) > (y_i + y_w) / 2.0 else "к проходу",
                         "верх" if tb == "top" else "низ"),
                     Part.makeCylinder(r_b, 16.0, App.Vector(x_e - nrm * 1.0, yc, zc_), App.Vector(nrm, 0, 0)),
                     (0.95, 0.95, 0.95) if dia >= 1.0 else (0.20, 0.20, 0.20))
            fit_pts.append(dict(d=dia, what=what, x=x_e, y=yc, z=zc_, r=r_b))
        # бруски-упоры 2×2: со стороны прохода — во всю длину; по торцам — в обход нижних штуцеров; сзади — только
        # если есть место (у T-4320 сзади дверь в 1/4″ — упора нет: держат коврик и ремни)
        tf_box("TankFloor_Cleat_Aisle", "Брусок 2×2 вдоль бака со стороны прохода", (px1 - px0, cw, ch),
               (px0, ybase(ts, y_i, cw), z_c), COL_WOOD)
        ends = [("Front", x_t1)] + ([("Rear", x_t0 - cw)] if x_t0 - cw >= dx0 - 1.0 else [])
        for nm, xc0 in ends:
            segs = [(ya, yb)]
            if (nm == "Rear") == (nrm < 0):
                for f_ in fit_pts:
                    if f_["z"] - f_["r"] < z_c + ch + 5.0:
                        c0, c1 = f_["y"] - f_["r"] - 10.0, f_["y"] + f_["r"] + 10.0
                        segs = [s_ for a_, b_ in segs for s_ in ((a_, min(b_, c0)), (max(a_, c1), b_)) if s_[1] - s_[0] > 1.0]
            s0, s1 = max(segs, key=lambda s_: s_[1] - s_[0])
            tf_box("TankFloor_Cleat_%s" % nm, "Брусок 2×2 у %s торца бака, L=%.0f" % (
                       "переднего" if nm == "Front" else "заднего", s1 - s0), (cw, s1 - s0, ch), (xc0, s0, z_c), COL_WOOD)
        # проставки к внутренней грани арки — там, где арка рядом с баком (прямой участок её грани)
        xa0 = Wt["center_x"] - Wt["len_x"] / 2.0 + Wt.get("plan_round", 0.0)
        xa1 = Wt["center_x"] + Wt["len_x"] / 2.0 - Wt.get("plan_round", 0.0)
        o0, o1 = max(x_t0, xa0), min(x_t1, xa1)
        sp_x = [Wt["center_x"] - 200.0, Wt["center_x"] + 200.0] if pallet else \
            ([(o0 + o1) / 2.0] if o1 - o0 < 400.0 else [o0 + 100.0, o1 - 100.0])
        for k, xs_ in enumerate(sp_x):
            tf_box("TankFloor_ArchSpacer_%d" % (k + 1), "Проставка (резина/брусок) %.0f мм: бак ↔ внутренняя грань арки" %
                   TF["arch_gap"], (100.0, TF["arch_gap"] - 1.0, 150.0),
                   (xs_ - 50.0, ybase(ts, y_w + TF["arch_gap"] - 0.5, TF["arch_gap"] - 1.0), z_b1 + 60.0),
                   (0.15, 0.15, 0.15))
        th_s = TF["strap_th"]
        anchors = []
        if pallet:                                              # ремни вокруг бака и фанеры поддона
            strap_x = (x_t0 + TLx / 4.0, x_t1 - TLx / 4.0)
            for k, xc in enumerate(strap_x):
                def _loop(pts):
                    v = [App.Vector(xc - TF["strap_w"] / 2.0, ts * yy, zz) for yy, zz in pts]
                    return Part.Face(Part.makePolygon(v + [v[0]])).extrude(App.Vector(TF["strap_w"], 0, 0))
                outer = _loop([(py_i - th_s, z_t1 + th_s), (y_w + th_s, z_t1 + th_s), (y_w + th_s, z_r1 - th_s),
                               (py_i - th_s, z_r1 - th_s)])
                inner = _loop([(py_i, z_t1), (y_w, z_t1), (y_w, z_r1), (py_i, z_r1)])
                tf_shape("TankFloor_Strap_%d" % (k + 1), "Ремень 1″ с кулачковой пряжкой вокруг бака и фанеры поддона "
                         "(под фанерой — между брусками)", outer.cut(inner), (0.85, 0.35, 0.10))
        else:                                                   # ремни поверх бака к 4 анкерам в железном полу
            ax_, ay_, az_ = TF["anchor"]
            yw_a0 = y_w + 6.0                                   # анкер у борта — за гранью бака (там, где нет арки)
            d_a = arch_ywall - (yw_a0 + ay_)
            x_lim = Wt["center_x"] - arch_a_lin(max(0.0, min(d_a, Wt["protrusion"])), ts) - 15.0 - ax_ / 2.0
            lo, hi = x_t0 + 60.0, min(x_t1 - 60.0, x_lim)
            strap_x = (lo + (hi - lo) * 0.2, lo + (hi - lo) * 0.85)
            ya_o, yw_o = y_i - cw - 4.0, y_w + 4.0
            for k, xc in enumerate(strap_x):
                def _ext(pts):
                    v = [App.Vector(xc - TF["strap_w"] / 2.0, ts * yy, zz) for yy, zz in pts]
                    return Part.Face(Part.makePolygon(v + [v[0]])).extrude(App.Vector(TF["strap_w"], 0, 0))
                outer = _ext([(ya_o, floor_top + az_), (ya_o, z_t1 + th_s), (yw_o + th_s, z_t1 + th_s),
                              (yw_o + th_s, floor_top + az_)])
                inner = _ext([(ya_o + th_s, floor_top - 1.0), (ya_o + th_s, z_t1), (yw_o, z_t1), (yw_o, floor_top - 1.0)])
                tf_shape("TankFloor_Strap_%d" % (k + 1), "Ремень 1″ с кулачковой пряжкой поверх бака к анкерам в полу",
                         outer.cut(inner), (0.85, 0.35, 0.10))
                for side_, y0_ in (("A", ya_o - 2.0), ("W", yw_a0 + ay_)):
                    nm_ = "TankFloor_Anchor_%d%s" % (k + 1, side_)
                    tf_box(nm_, "Анкер (проушина / кусок L-track) на болтах M8 в железный пол — %s" % (
                               "со стороны прохода" if side_ == "A" else "у борта, за аркой"),
                           (ax_, ay_, az_), (xc - ax_ / 2.0, ybase(ts, y0_, ay_), floor_top), (0.55, 0.55, 0.58))
                    anchors.append(nm_)
            # брусок-упор к борту за аркой (между ремнями), чтобы бак не уходил к борту сзади
            xb0 = strap_x[0] + ax_ / 2.0 + 15.0
            xb1 = min(strap_x[1] - ax_ / 2.0 - 15.0, xb0 + 120.0)
            if xb1 - xb0 > 60.0:
                tf_box("TankFloor_Cleat_Wall", "Брусок 2×2 у борта за аркой (между ремнями)", (xb1 - xb0, cw, ch),
                       (xb0, ybase(ts, y_w + cw, cw), z_c), COL_WOOD)
        pX, pY_, pZ = TF["pump"]
        if TF.get("pump_at") == "front":
            tf_box("Water_Pump12V", "Насос 12V + фильтр (заглушка) — на полу перед баком, у нижнего штуцера",
                   (pX, pY_, pZ), (x_t1 + cw + TF.get("pump_gap", 40.0), ybase(ts, y_i + 10.0 + pY_, pY_), floor_top),
                   (0.20, 0.35, 0.75))
        else:
            pl_bb = doc.getObject("BedPostPlate_%s_rear" % ttag).Shape.BoundBox
            tf_box("Water_Pump12V", "Насос 12V + фильтр (заглушка) — на полу в углу за аркой, у заднего торца бака",
                   (pX, pY_, pZ), (pl_bb.XMax + 5.0, ybase(ts, arch_ywall - 45.0, pY_), floor_top), (0.20, 0.35, 0.75))
        # туалет перед баком (по линии грани бака к борту), выезжает потом вперёд в душ
        toilet = None
        # 2026-11-09: туалет — на платформе с колёсами (ANCHORS["toilet"]); строится в разделе душа (от поддона)
        if TF.get("toilet") and not ANCHORS.get("toilet"):
            TT = TF["toilet"]
            tlx, tly, tlz = TT["dims"]
            tx0 = x_t1 + TT["gap_rear"]
            tsh_ = Part.makeBox(tlx, tly, tlz, App.Vector(tx0, ybase(ts, y_w, tly), floor_top))
            try:
                tsh_ = tsh_.makeFillet(25.0, [e for e in tsh_.Edges if abs(e.tangentAt(0).z) > 0.9])
            except Exception:
                pass
            toilet = tf_shape("Toilet_Camco", "%s — под щитом перед баком; позже — на платформе с колёсиками, выезжает "
                              "вперёд в душ" % TT["title"], tsh_, (0.78, 0.78, 0.76))
            fsh["Toilet_Camco"] = toilet
        # проверки
        obj = lambda n: doc.getObject(n).Shape
        arch = arch_shapes[ts]
        dpf = dp_shapes[ts]
        crosses_bed = [o.Shape for o in doc.Objects if o.Name.startswith("BedCross_") and o.isDerivedFrom("Part::Feature")]
        base_parts = [fsh[n] for n in fsh if n.startswith(("TankFloor_BasePly", "TankFloor_Runner", "TankFloor_Cleat",
                                                           "TankFloor_Anchor", "TankFloor_Mat"))]
        checks = [("бак ↔ арка", tank.distToShape(arch)[0]), ("бак ↔ D-стойка", tank.distToShape(dpf)[0]),
                  ("бак ↔ стойки кровати", min(tank.distToShape(obj("BedPost_%s_%s" % (ttag, w_)))[0]
                                              for w_ in ("rear", "front"))),
                  ("бак ↔ поперечины кровати", min(tank.distToShape(c)[0] for c in crosses_bed)),
                  ("поддон/бруски/анкеры ↔ арка", min(s_.distToShape(arch)[0] for s_ in base_parts)),
                  ("поддон/бруски/анкеры ↔ D-стойка", min(s_.distToShape(dpf)[0] for s_ in base_parts)),
                  ("ремни ↔ арка", min(fsh["TankFloor_Strap_%d" % (k + 1)].distToShape(arch)[0] for k in range(2))),
                  ("насос ↔ арка", fsh["Water_Pump12V"].distToShape(arch)[0]),
                  ("насос ↔ бак/бруски", min(fsh["Water_Pump12V"].distToShape(s_)[0] for s_ in base_parts + [tank])),
                  ("насос ↔ пластина стойки", fsh["Water_Pump12V"].distToShape(obj("BedPostPlate_%s_rear" % ttag))[0])]
        if toilet is not None:
            fits_ = [fsh[n] for n in fsh if n.startswith("TankFloor_Fitting")]
            checks += [("туалет ↔ бак", toilet.distToShape(tank)[0]),
                       ("туалет ↔ бобышки штуцеров", min(toilet.distToShape(f_)[0] for f_ in fits_)),
                       ("туалет ↔ арка", toilet.distToShape(arch)[0]),
                       ("туалет ↔ насос", toilet.distToShape(fsh["Water_Pump12V"])[0]),
                       ("туалет ↔ бруски", min(toilet.distToShape(s_)[0] for s_ in base_parts)),
                       ("туалет ↔ поперечины кровати", min(toilet.distToShape(c)[0] for c in crosses_bed))]
        bank_rail_in = None
        bank_top = None
        if bank_summary:
            bank_rail_in = arch_ywall - bank_summary["inner"] - sd       # |Y| грани рейки батарей к проходу
            bank_top = bank_summary["z_s1"]
        fit_tip = x_e + 16.0 * nrm
        tfl_summary = dict(floor_top=floor_top, x=(x_t0, x_t1), y=(y_i, y_w), z=(z_b1, z_t1), base=(px0, px1, py_i, py_o),
                           from_wall=(arch_ywall - y_w, arch_ywall - y_i, arch_ywall - py_i),
                           in_deck=dx1 - x_t1, behind=x_t0 - dx0, deck=(dx0, dx1),
                           in_deck_fit=dx1 - max(x_t1, fit_tip + 50.0 * nrm) if nrm > 0 else dx1 - x_t1,
                           level=(z_t1 - bank_top) if bank_top else None, bank_top=bank_top,
                           trunk=(bank_rail_in + py_i) if bank_rail_in else None,
                           under_cross=(z_rail_top - sw) - z_t1, fittings=fit_pts, straps=strap_x, checks=checks,
                           runner_len=rlen, n_runner=n_r, fittings_end=TF["fittings_end"], tank_name=tank_name,
                           base_mode=TF.get("base"), title=TF["title"], name=TF["name"], anchors=anchors,
                           toilet_y=(y_w - TF["toilet"]["dims"][1], y_w) if TF.get("toilet") else None,
                           toilet=None if toilet is None else dict(
                               x=(toilet.BoundBox.XMin, toilet.BoundBox.XMax), y=(y_w - TF["toilet"]["dims"][1], y_w),
                               z=(toilet.BoundBox.ZMin, toilet.BoundBox.ZMax), in_deck=dx1 - toilet.BoundBox.XMax,
                               from_wall=(arch_ywall - y_w, arch_ywall - y_w + TF["toilet"]["dims"][1])))
        TF["_summary"] = {k: v for k, v in tfl_summary.items() if k != "checks"}

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "tfl_summary")
