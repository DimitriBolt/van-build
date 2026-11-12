# -*- coding: utf-8 -*-
"""Душ + мини-кухня по водительскому борту: поддон, шторки, туалет на платформе, нагреватель, пропан, кухня."""

import math

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .params import KITCHEN_FLAP, SHOWER_KITCHEN, TANK_FLOOR
from .common import add_shape
from .scan import y_at_z

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def shower_kitchen(S):
    """Душ, туалет на платформе, локер пропана, нагреватель и мини-кухня по водительскому борту."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, P, arch_shapes, arch_ywall, doc, dx0 = S.B, S.P, S.arch_shapes, S.arch_ywall, S.doc, S.dx0
    dx1, floor_top, half, post_out_s, sw = S.dx1, S.floor_top, S.half, S.post_out_s, S.sw
    tfl_summary, ybase, z_rail_top = S.tfl_summary, S.ybase, S.z_rail_top
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

        # 2026-11-07 (Dimitri): одна группа «Душ + мини-кухня» → две: «Душ» (с газовым нагревателем, пропаном, газом
        # и датчиками) и «Кухня»
        sg = doc.addObject("App::DocumentObjectGroup", "Shower")
        sg.Label = "Душ — поддон-сектор 32″, газовый нагреватель, пропан под кроватью (проект 2026-11-06/07)"
        kg = doc.addObject("App::DocumentObjectGroup", "Kitchen")
        kg.Label = "Кухня — 2 секции: мойка | шкафчик + холодильник (проект 2026-11-06/07)"
        COL_WALL = (0.93, 0.93, 0.90)
        COL_PAN = (0.98, 0.98, 0.98)
        COL_STEEL = (0.70, 0.72, 0.75)
        COL_CAB = (0.80, 0.62, 0.40)
        COL_TOP = (0.62, 0.42, 0.24)
        COL_DARK = (0.18, 0.18, 0.18)
        COL_FRIDGE = (0.25, 0.42, 0.55)
        parts = {}

        def put(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr,
                      group=kg if name.startswith("Kitchen_") else sg)
            parts[name] = shape
            return shape

        # — душ: поддон-сектор 32″ в углу «край щита кровати × борт», задняя стенка — только сверху —
        R_ = K["pan_r"]
        AS = ANCHORS["shower_pan"]
        z_pan0 = P["floor_corrugation_height"] if K.get("pan_recess") else floor_top
        z_pan = z_pan0 + K["pan_h"]
        base_th = AS["base_th"] if AS.get("base_th") is not None else K["pan_h"] - K["pan_rim"]
        z_pin = z_pan0 + base_th                                     # дно поддона внутри
        t_rim = AS["rim_t"]
        t_curb = AS.get("curb_t", t_rim)
        y_back_pan = (AS["y_wall"] if AS.get("y_wall") is not None else
                      yw(z_pan) - 12.0)                              # поддон упирается в панель у борта (12 мм)
        Rc = AS.get("corner_r", R_)                                  # 2026-11-09: передний угол R22″ (Swiss Madison)

        def pshape(xc, d, z0, h):
            """Контур поддона (квадрат R_ × R_, передний угол — R Rc с центром в (R_−Rc) от прямых сторон), смещённый
            внутрь на d по передней стороне и стороне к проходу; задняя (к кровати) и у борта — на месте. Только ks>0."""
            L, rc = R_ - d, Rc - d
            cx, cy = xc + R_ - Rc, y_back_pan - (R_ - Rc)
            y0 = y_back_pan - L
            b = Part.makeBox(L, L, h, V(xc, y0, z0))
            if rc > 0 and cx < xc + L and cy > y0:
                cor = Part.makeBox(xc + L - cx + 1.0, cy - y0 + 1.0, h + 2.0, V(cx, y0 - 1.0, z0 - 1.0)).cut(
                    Part.makeCylinder(rc, h + 4.0, V(cx, cy, z0 - 2.0)))
                b = b.cut(cor)
            return b

        def xline(d, y):
            """X контура pshape(xp0, d) на |Y| = y (передняя сторона / дуга)."""
            cx, cy, rc = xp0 + R_ - Rc, y_back_pan - (R_ - Rc), Rc - d
            if y >= cy:
                return xp0 + R_ - d
            q = rc ** 2 - (cy - y) ** 2
            return cx + math.sqrt(q) if q > 0 else xp0
        y_sf = y_back_pan - R_                                       # край поддона к проходу (у задней стенки)
        x_rw = dx1                                                   # задняя стенка — по переднему краю щита
        z_rw0 = z_rail_top                                           # … от уровня щита (низ настила) до потолка
        V = App.Vector

        def _q(shape, xc):                                           # четверть: x ≥ xc, |y| ≤ y_back_pan
            shape.rotate(V(xc, ks * y_back_pan, 0), V(0, 0, 1), -90.0 if ks > 0 else 0.0)
            return shape

        def qcyl(xc, r, z0, h):
            return _q(Part.makeCylinder(r, h, V(xc, ks * y_back_pan, z0), V(0, 0, 1), 90.0), xc)
        V = App.Vector

        arch_s = arch_shapes[ks]
        lo_, hi_ = x_rw, x_rw + 400.0                                # как можно дальше назад, но не в арку
        if pshape(lo_, 0.0, z_pan0, K["pan_h"]).distToShape(arch_s)[0] >= K["pan_arch_gap"]:
            hi_ = lo_
        else:
            for _ in range(16):
                mid = (lo_ + hi_) / 2.0
                if pshape(mid, 0.0, z_pan0, K["pan_h"]).distToShape(arch_s)[0] >= K["pan_arch_gap"]:
                    hi_ = mid
                else:
                    lo_ = mid
        xp0 = AS["x_rear"] if AS.get("x_rear") is not None else hi_   # задний (прямой) край поддона
        sx0, sx1 = x_rw, xp0 + R_
        six, siy = R_, R_
        pan = pshape(xp0, 0.0, z_pan0, K["pan_h"])
        # 2026-11-09: поддон полый — дно base_th, бортик t_rim у стен, порог t_curb спереди/к проходу (передние колёса — внутри)
        pan_in = pshape(xp0, t_curb, z_pin, K["pan_h"]).cut(
            Part.makeBox(t_rim, 4000.0, K["pan_h"] + 2.0, V(xp0 - 1.0, -2000.0, z_pan0 - 1.0))).cut(
            Part.makeBox(4000.0, t_rim + 1.0, K["pan_h"] + 2.0,
                         V(xp0 - 1.0, ks * (y_back_pan - t_rim) if ks > 0 else -y_back_pan - 1.0, z_pan0 - 1.0)))
        pan = pan.cut(pan_in)
        put("Shower_Pan", "Поддон душа Swiss Madison 32×32×4″, передний угол R22″, слив ⌀3.5″ в центре скругления%s" % (
                "; утоплен в пол (вырез фанеры+XPS)" if K.get("pan_recess") else "; стоит прямо на полу"), pan, COL_PAN)
        dr_r = K["pan_drain"][1]
        dr_x, dr_y = xp0 + AS["drain"][0], ks * (y_back_pan - AS["drain"][1])
        put("Shower_Drain", "Слив поддона ⌀3.5″ (ANCHORS: %.1f″ от прямой стороны, %.1f″ от борта)" % (
            AS["drain"][0] / 25.4, AS["drain"][1] / 25.4), Part.makeCylinder(dr_r, 3.0, V(dr_x, dr_y, z_pin)), COL_DARK)
        # обычный сифон вниз через пол → серый бак под днищем (бак пока не рисуем; место — по форме днища)
        trap = Part.makeCylinder(24.0, z_pin + 150.0, V(dr_x, dr_y, -150.0))
        put("Shower_DrainTrap", "Сифон слива 1-1/2″ — вниз через пол в серый бак под днищем (место — по месту)",
            trap, COL_DARK)
        if not K.get("pan_recess"):
            for fn in ("Floor_XPS", "Floor_Plywood"):
                fo = doc.getObject(fn)
                if fo is not None:
                    fo.Shape = fo.Shape.cut(Part.makeCylinder(32.0, floor_top + 20.0, V(dr_x, dr_y, -10.0)))
        if K.get("pan_recess"):                                      # вырез в полу под поддон
            hole = pshape(xp0, 0.0, 0.5, floor_top + 1.0)
            for fn in ("Floor_XPS", "Floor_Plywood"):
                fo = doc.getObject(fn)
                if fo is not None:
                    fo.Shape = fo.Shape.cut(hole)
        # пластина передней стойки кровати попадает под поддон → узкая (Simpson TP15) вдоль борта
        pl_o = doc.getObject("BedPostPlate_pY_front" if ks > 0 else "BedPostPlate_nY_front")
        plate_note = None
        if pl_o is not None and pl_o.Shape.distToShape(pan)[0] < 3.0:
            pb_ = pl_o.Shape.BoundBox
            ply_, plx_ = 46.0, 127.0
            pl_base = V((pb_.XMin + pb_.XMax) / 2.0 - plx_ / 2.0, ybase(ks, post_out_s[ks], ply_), pb_.ZMin)
            if hasattr(pl_o, "Length"):                              # Part::Box — параметры (Shape перестроится)
                pl_o.Length, pl_o.Width, pl_o.Height = plx_, ply_, pb_.ZLength
                pl_o.Placement = App.Placement(pl_base, App.Rotation())
                pl_o.recompute()
            else:
                pl_o.Shape = Part.makeBox(plx_, ply_, pb_.ZLength, pl_base)
            plate_note = "пластина передней стойки кровати — узкая Simpson TP15 вдоль борта (широкая TP35 — под поддоном)"
        # — ТУАЛЕТ CAMCO НА ПЛАТФОРМЕ С КОЛЁСАМИ (2026-11-09, Dimitri; ANCHORS["toilet"]) —
        # Плита — на месте транспортного положения, верх = дно поддона у бортика. Передние колёса ВСЕГДА в поддоне, задние
        # ВСЕГДА снаружи на плите: бортик — упор в обе стороны (транспорт: передние колёса у бортика изнутри; в душе:
        # задние у бортика снаружи). Ход = колёсная база − бортик − ⌀ колеса. В модели — только транспортное положение;
        # «в душе» — проверками по формам (без отдельного объекта).
        AT = ANCHORS.get("toilet")
        toilet_pf = None
        toilet_moving = None
        if AT and tfl_summary and tfl_summary.get("toilet_y") and TANK_FLOOR.get("toilet"):
            TT = TANK_FLOOR["toilet"]
            tlx, tly = TT["dims"][0], TT["dims"][1]
            tlz = AT["toilet_h"]
            ty0, ty1 = tfl_summary["toilet_y"]                         # |Y| туалета: к проходу / к борту (как раньше)
            wd, ww = AT["wheel_d"], AT["wheel_w"]
            wr = wd / 2.0
            plate_th = AT["plate_th"] if AT.get("plate_th") is not None else z_pin - floor_top
            z_pl = floor_top + plate_th                                # верх плиты = дно поддона
            z_pf0 = z_pl + AT["caster_h"]                              # низ платформы
            z_pf1 = z_pf0 + AT["platform_th"]                          # верх платформы = низ туалета
            z_tt1 = z_pf1 + tlz                                        # верх туалета
            pfy0, pfy1 = ty0 - AT["aisle_margin"], ty1                 # платформа по Y (к борту — вровень: арка)
            f0 = xp0 + t_rim + wr                                      # передние колёса (центр) — транспорт
            xt0 = dx1 - tlx                                            # туалет в транспорте: передом — до края щита
            a_t = f0 - xt0                                             # от передних колёс назад до туалета
            WB = a_t + t_rim + AT["toilet_in"] + wr                    # колёсная база: в душе туалет за бортиком
            travel = WB - t_rim - wd
            xw_r0 = f0 - WB                                            # задние колёса (центр) — транспорт
            pfx0, pfx1 = xw_r0 - wr - AT["rear_over"], f0 + wr + AT["front_over"]
            # плита: от препятствий бака (брусок/бак/штуцеры по полосе платформы) до поддона
            band = Part.makeBox(4000.0, pfy1 - pfy0, z_pf1 - floor_top + 1.0, V(-500.0, ybase(ks, pfy1, pfy1 - pfy0),
                                                                              floor_top))
            obst = [o.Shape for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull()
                    and o.Name.startswith(("TankFloor_", "WaterTank_")) and o.Shape.BoundBox.XMax < xp0]
            x_obs = max([sh_.common(band).BoundBox.XMax for sh_ in obst if not sh_.common(band).isNull()
                         and sh_.common(band).Volume > 1.0] or [dx0])
            plx0, plx1 = x_obs, xp0 - 2.0
            put_t = lambda n_, l_, sh_, c_: (add_shape(doc, n_, l_, sh_, color=c_, group=fg_t), fsh_t.__setitem__(n_, sh_))
            fg_t = doc.getObject("TankFloor") or sg
            fsh_t = {}
            if plate_th > 1.0:
                put_t("Toilet_Plate", "Плита под туалет — %.1f″ (%.0f мм): верх = дно поддона у бортика; X %.0f..%.0f — "
                      "задние колёса по ней (ANCHORS)" % (plate_th / 25.4, plate_th, plx0, plx1),
                      Part.makeBox(plx1 - plx0, pfy1 - pfy0, plate_th, V(plx0, ybase(ks, pfy1, pfy1 - pfy0), floor_top)),
                      (0.55, 0.45, 0.35))
            f1 = f0 + travel                                           # передние колёса (центр) — в душе
            # передний край платформы скруглён по дуге (в душе — внутри линии шторки = вогнутого торца кухни)
            pf_box = Part.makeBox(pfx1 - pfx0, pfy1 - pfy0, AT["platform_th"], V(pfx0, ybase(ks, pfy1, pfy1 - pfy0), z_pf0))
            d_lim = max(AT.get("arc_gap", 5.0), K.get("curtain_in", 50.0) + 5.0)   # вогнутый торец кухни (по шторке)
            pf_box = pf_box.common(pshape(xp0 - travel, d_lim, z_pf0 - 100.0, 500.0))
            put_t("Toilet_Platform", "Платформа туалета — фанера %.2f″ %.1f×%.1f″ на 4 колёсах ⌀%.0f″, перед скруглён по "
                  "дуге поддона; передняя часть всегда в поддоне (за краем щита, внутри душа — согласованное исключение)" % (
                      AT["platform_th"] / 25.4, (pfx1 - pfx0) / 25.4, (pfy1 - pfy0) / 25.4, wd / 25.4),
                  pf_box, (0.80, 0.66, 0.46))
            # передние колёса: в душе — внутри дуги поддона → колесо к проходу смещено к борту (колея уже, чем у задних)
            d_w = max(t_curb + 3.0, d_lim)
            cxp, cyp, rc_w = xp0 + R_ - Rc, y_back_pan - (R_ - Rc), Rc - d_w
            xf_ = f1 + wr                                              # передний край переднего колеса в душе
            if xf_ <= cxp:
                y_need = y_back_pan - (R_ - d_w)
            else:
                q_ = rc_w ** 2 - (xf_ - cxp) ** 2
                y_need = (cyp - math.sqrt(q_)) if q_ > 0 else pfy1 - AT["wheel_inset"] - 2.0 * ww
            yF_a = max(pfy0 + AT["wheel_inset"] + ww / 2.0, y_need + ww / 2.0)
            yW = pfy1 - AT["wheel_inset"] - ww / 2.0
            for tag_, xc_ in (("F", f0), ("R", xw_r0)):
                for side_, yc_ in (("A", yF_a if tag_ == "F" else pfy0 + AT["wheel_inset"] + ww / 2.0), ("W", yW)):
                    yy = ks * yc_
                    wheel = Part.makeCylinder(wr, ww, V(xc_, yy - ww / 2.0, z_pl + wr), V(0, 1, 0)).fuse(
                        Part.makeBox(40.0, ww + 10.0, z_pf0 - (z_pl + wd), V(xc_ - 20.0, yy - ww / 2.0 - 5.0, z_pl + wd)))
                    put_t("Toilet_Wheel_%s%s" % (tag_, side_), "Колесо %s ⌀%.0f″ с креплением (%s)" % (
                        "переднее — всегда в поддоне" if tag_ == "F" else "заднее — всегда на плите", wd / 25.4,
                        "к проходу" if side_ == "A" else "к борту"), wheel, (0.15, 0.15, 0.15))
            xl1_ = xp0 + K["ledge_in"]                                 # линия нижней шторки (козырёк)
            put_t("Toilet_PlatformDam", "Порожек на платформе за нижней шторкой (в транспортном положении): вода с "
                  "передней части платформы стекает в поддон, а не по платформе под кровать",
                  Part.makeBox(10.0, pfy1 - pfy0, 10.0, V(xl1_ - 6.0 - 10.0, ybase(ks, pfy1, pfy1 - pfy0), z_pf1)),
                  (0.25, 0.25, 0.25))
            tsh_ = Part.makeBox(tlx, tly, tlz, V(xt0, ybase(ks, ty1, tly), z_pf1))
            try:
                tsh_ = tsh_.makeFillet(25.0, [e for e in tsh_.Edges if abs(e.tangentAt(0).z) > 0.9])
            except Exception:
                pass
            put_t("Toilet_Camco", "%s — на платформе с колёсами, транспортное положение (под щитом); выезжает в душ "
                  "на %.1f″" % (TT["title"], travel / 25.4), tsh_, (0.78, 0.78, 0.76))
            # ── проверки «в душе» — по формам (сдвиг на ход) ──
            mv = App.Vector(travel, 0, 0)
            t_sh = tsh_.translated(mv)
            wF = [fsh_t["Toilet_Wheel_F%s" % s_] for s_ in "AW"]
            wR = [fsh_t["Toilet_Wheel_R%s" % s_] for s_ in "AW"]
            pf_sh = fsh_t["Toilet_Platform"].translated(mv)
            def _in_arc(xx, yy):                                       # запас до внутренней кромки бортика (+ — внутри)
                cx_, cy_ = xp0 + R_ - Rc, y_back_pan - (R_ - Rc)
                m_ = min(xx - (xp0 + t_rim), (y_back_pan - t_rim) - yy, (xp0 + R_ - t_curb) - xx,
                         yy - (y_back_pan - R_ + t_curb))
                if xx > cx_ and yy < cy_:
                    m_ = min(m_, (Rc - t_curb) - math.hypot(xx - cx_, cy_ - yy))
                return m_
            tb1 = t_sh.BoundBox
            corners_t = [(x_, y_) for x_ in (tb1.XMin, tb1.XMax) for y_ in (ty0, ty1)]
            wf1 = [w_.translated(mv).BoundBox for w_ in wF]
            corners_w = [(x_, y_) for b_ in wf1 for x_ in (b_.XMin, b_.XMax) for y_ in (abs(b_.YMin), abs(b_.YMax))]
            wf0 = [w_.BoundBox for w_ in wF]
            corners_w0 = [(x_, y_) for b_ in wf0 for x_ in (b_.XMin, b_.XMax) for y_ in (abs(b_.YMin), abs(b_.YMax))]
            pfb = fsh_t["Toilet_Platform"].BoundBox
            fit = dict(
                toilet_in_arc=min(_in_arc(x_, y_) for x_, y_ in corners_t),
                front_wheels_in_pan_shower=min(_in_arc(x_, y_) for x_, y_ in corners_w),
                front_wheels_in_pan_transport=min(_in_arc(x_, y_) for x_, y_ in corners_w0),
                rear_wheels_out_shower=xp0 - max(w_.translated(mv).BoundBox.XMax for w_ in wR),
                rear_wheels_on_plate=min(w_.BoundBox.XMin for w_ in wR) - (plx0 + AT["rear_gap"]),
                toilet_under_deck=dx1 - tsh_.BoundBox.XMax,
                platform_over_rim=z_pf0 - z_pan - AT["rim_clear"],
                platform_front_in_pan_transport=min(_in_arc(pfb.XMax, y_) for y_ in (pfy0, pfy1)))
            chk_t = [("туалет в душе — внутри дуги поддона (запас)", fit["toilet_in_arc"]),
                     ("передние колёса в поддоне — в душе", fit["front_wheels_in_pan_shower"]),
                     ("передние колёса в поддоне — в транспорте", fit["front_wheels_in_pan_transport"]),
                     ("передний край платформы в поддоне — в транспорте", fit["platform_front_in_pan_transport"]),
                     ("задние колёса снаружи поддона — в душе", fit["rear_wheels_out_shower"]),
                     ("задние колёса на плите — в транспорте (до её заднего края)", fit["rear_wheels_on_plate"]),
                     ("туалет под щитом — в транспорте", fit["toilet_under_deck"]),
                     ("платформа над бортиком поддона (сверх %.0f мм)" % AT["rim_clear"], fit["platform_over_rim"])]
            moving0 = [tsh_, fsh_t["Toilet_Platform"]] + wF + wR
            moving1 = [t_sh, pf_sh] + [w_.translated(mv) for w_ in wF + wR]
            for lab, pref in (("бак/бруски/ремни/штуцеры", ("TankFloor_", "WaterTank_")), ("насос", ("Water_Pump",)),
                              ("арка", ("WheelArch_",)), ("стойки/пластины кровати", ("BedPost",)),
                              ("поперечины кровати", ("BedCross_",))):
                ss = [o.Shape for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull()
                      and o.Name.startswith(pref)]
                if ss:
                    chk_t.append(("туалет/платформа/колёса ↔ %s — в транспорте" % lab,
                                  min(m_.distToShape(s_)[0] for m_ in moving0 for s_ in ss)))
                    chk_t.append(("туалет/платформа/колёса ↔ %s — в душе" % lab,
                                  min(m_.distToShape(s_)[0] for m_ in moving1 for s_ in ss)))
            toilet_pf = dict(plate=(plx0, plx1, plate_th), z=(z_pl, z_pf0, z_pf1, z_tt1), x0=(xt0, xt0 + tlx),
                             x1=(xt0 + travel, xt0 + tlx + travel), y=(ty0, ty1), pf_x=(pfx0, pfx1), pf_y=(pfy0, pfy1),
                             WB=WB, travel=travel, wheels_x=(f0, xw_r0), checks=chk_t, fit=fit, x_obs=x_obs,
                             moving0=None, h_total=z_tt1 - floor_top, rim_t=t_rim, base_th=base_th)
            toilet_moving = (moving0, moving1)
            tfl_summary["toilet"] = dict(x=(xt0, xt0 + tlx), y=(ty0, ty1), z=(z_pf1, z_tt1), in_deck=dx1 - (xt0 + tlx),
                                         from_wall=(arch_ywall - ty1, arch_ywall - ty0), platform=toilet_pf)
            TANK_FLOOR["_summary"]["toilet"] = {k_: v_ for k_, v_ in tfl_summary["toilet"].items()}
        # задняя стенка (сверху) и козырёк под ней: вода со стенки стекает за бортик поддона
        put("Shower_WallRear", "Задняя стенка душа по краю щита кровати — только сверху: от уровня щита до потолка "
            "(внизу — проём: туалет выезжает в душ)", env_solid(x_rw, pt_, y_sf, z_rw0, z_ceil), COL_WALL, 10)
        xl1 = xp0 + K["ledge_in"]
        ledge = env_solid(x_rw + pt_, xl1 - (x_rw + pt_), y_sf + 60.0, z_rw0 - 12.0, z_rw0)
        put("Shower_DripLedge", "Козырёк под задней стенкой (FRP по фанере, уклон в поддон) — до %.0f мм внутрь поддона" %
            K["ledge_in"], ledge, COL_WALL, 10)
        cur_lo = Part.makeBox(4.0, (y_back_pan - 30.0) - (y_sf + 80.0), (z_rw0 - 14.0) - (z_pan + 25.0),
                              V(xl1 - 6.0, ks * (y_sf + 80.0) - (0 if ks > 0 else (y_back_pan - y_sf - 110.0)), z_pan + 25.0))
        if toilet_pf:                                                # ложится на платформу (перед порожком)
            pfy0_, pfy1_ = toilet_pf["pf_y"]
            cur_lo = cur_lo.cut(Part.makeBox(20.0, pfy1_ - pfy0_ + 2.0, toilet_pf["z"][2] - z_pan,
                                             V(xl1 - 16.0, ybase(ks, pfy1_ + 1.0, pfy1_ - pfy0_ + 2.0), z_pan)))
        put("Shower_CurtainLower", "Нижняя шторка с козырька до поддона — закрывает проём; ложится на платформу туалета "
            "перед порожком; сдвигается, когда туалет выезжает в душ", cur_lo, (0.55, 0.75, 0.85), 55)
        r_c = R_ - K.get("curtain_in", 50.0)                         # шторка (= вогнутый торец кухни)
        r_k = r_c + 0.5
        # панель по борту: над поддоном и (выше уровня щита) — от задней стенки до линии шторки (дальше — кухня)
        x_back1 = xp0 + r_c if K.get("kitchen_concave") else sx1
        back = env_solid(x_rw + pt_, x_back1 - (x_rw + pt_), y_sf, floor_top, z_ceil).cut(
            env_solid(x_rw + pt_ - 1, sx1 - x_rw + 2, y_sf - 5, floor_top - 1, z_ceil + 1, g_extra=12.0))
        back = back.cut(Part.makeBox(xp0 - x_rw, 2000.0, z_rw0 - floor_top + 1.0, V(x_rw, -1000.0, floor_top - 1.0)))
        put("Shower_WallBack", "Стенка душа по борту (фанера 1/2″ + FRP); над аркой — только выше уровня щита", back,
            COL_WALL, 10)
        # газовый проточный нагреватель на задней стенке, внутри душа (лицом к кабине), дымоход — вертикально вверх
        GH = K.get("gas_heater")
        flue = None
        if GH:
            ghx, ghy, ghz = GH["dims"][1], GH["dims"][0], GH["dims"][2]
            z_h0 = floor_top + GH["z0"]
            z_h1 = z_h0 + ghz
            y_h1 = yw(z_h1) - 12.0 - GH["side_gap"]                  # грань нагревателя к борту (|Y|)
            y_h0 = y_h1 - ghy
            x_h0 = x_rw + pt_
            heater = Part.makeBox(ghx, ghy, ghz, V(x_h0, ybase(ks, y_h1, ghy), z_h0))
            try:
                heater = heater.makeFillet(8.0, [e for e in heater.Edges if abs(e.tangentAt(0).z) > 0.9])
            except Exception:
                pass
            put("Shower_GasHeater", "Газовый проточный нагреватель Camplux 1.58 GPM 11.8×17.3×5.1″ на задней стенке "
                "(внутри душа); ⚠️ производитель: только на улице — дымоход, датчики CO/пропана, приток воздуха",
                heater, (0.97, 0.97, 0.97))
            for i_, (dy_, col_) in enumerate(((0.25, (0.85, 0.20, 0.15)), (0.5, (0.6, 0.6, 0.6)), (0.75, (0.15, 0.40, 0.85)))):
                put("Shower_GasHeater_Knob%d" % (i_ + 1), "Ручка нагревателя (%s)" % ("газ", "режим", "вода")[i_],
                    Part.makeCylinder(18.0, 15.0, V(x_h0 + ghx, ks * (y_h0 + dy_ * ghy), z_h0 + 120.0 + (40.0 if i_ == 1 else 0.0)),
                                      V(1, 0, 0)), col_)
            fx_c, fy_c = x_h0 + ghx / 2.0, ks * (y_h0 + ghy / 2.0)
            fr_ = GH["flue_d"] / 2.0
            z_fl1 = crown + GH["roof_out"]
            flue = Part.makeCylinder(fr_, z_fl1 - z_h1, V(fx_c, fy_c, z_h1))
            put("Shower_Flue", "Дымоход нагревателя ⌀%.0f″ нержавейка — вертикально вверх через потолок и крышу" %
                (GH["flue_d"] / 25.4), flue, (0.62, 0.64, 0.66))
            put("Shower_FlueCap", "Колпак дымохода на крыше (от дождя/ветра)",
                Part.makeCylinder(fr_ * 2.0, 60.0, V(fx_c, fy_c, z_fl1)), (0.35, 0.35, 0.35))
            put("Shower_FlueThimble", "Проходка дымохода через потолок/утеплитель (огнестойкая муфта)",
                Part.makeCylinder(fr_ + 25.0, 40.0, V(fx_c, fy_c, z_ceil - 20.0)).cut(
                    Part.makeCylinder(fr_ + 0.5, 50.0, V(fx_c, fy_c, z_ceil - 25.0))), (0.30, 0.30, 0.30))
        # потолок: от задней стенки до дуги шторки, по борту — до обшивки
        y_ceil_back = yw(z_ceil)
        ceil = pshape(xp0, K.get("curtain_in", 50.0) if K.get("kitchen_concave") else 0.0, z_ceil - 12.0, 12.0).fuse(
            Part.makeBox(xp0 - (x_rw + pt_), R_, 12.0, V(x_rw + pt_, ks * y_back_pan - (R_ if ks > 0 else 0.0),
                                                           z_ceil - 12.0)))
        ceil = ceil.common(Part.makeBox(3000.0, y_ceil_back, 40.0, V(x_rw, 0.0 if ks > 0 else -y_ceil_back,
                                                                    z_ceil - 20.0)))
        if flue is not None:
            ceil = ceil.cut(Part.makeCylinder(fr_ + 25.0, 60.0, V(fx_c, fy_c, z_ceil - 30.0)))
        put("Shower_Ceiling", "Потолок душа (фанера 1/2″ + FRP), Z=%.0f: сектор + полоса до задней стенки" % z_ceil, ceil,
            COL_WALL, 10)
        # шторка по дуге (внутри бортика) + прямой участок к задней стенке
        y_c = y_back_pan - r_c                                       # линия шторки у задней стенки
        z_c0, z_c1 = z_pan + 40.0, z_ceil - 60.0
        ci_ = K.get("curtain_in", 50.0)
        curt = pshape(xp0, ci_, z_c0, z_c1 - z_c0).cut(pshape(xp0, ci_ + 3.0, z_c0 - 1.0, z_c1 - z_c0 + 2.0)).fuse(
            Part.makeBox(xp0 - (x_rw + pt_ + 10.0), 3.0, z_c1 - z_c0,
                         V(x_rw + pt_ + 10.0, ks * y_c - (0 if ks > 0 else 3.0), z_c0)))
        put("Shower_Curtain", "Шторка душа по контуру поддона (прямые участки + дуга R22″) + прямой участок до задней стенки", curt,
            (0.55, 0.75, 0.85), 55)
        r_rod = r_c - 12.0                                           # карниз чуть внутри — шторка ложится на торец кухни
        rod = pshape(xp0, ci_ + 4.0, z_ceil - 48.0, 16.0).cut(pshape(xp0, ci_ + 20.0, z_ceil - 49.0, 18.0)).fuse(
            Part.makeCylinder(8.0, xp0 - (x_rw + pt_), V(x_rw + pt_, ks * (y_back_pan - r_rod), z_ceil - 40.0), V(1, 0, 0)))
        put("Shower_CurtainRod", "Карниз шторки — по контуру поддона, гнутый по дуге R22″ (под потолком)", rod, COL_STEEL)
        yb_h = yw(1650.0) - 12.0
        head = Part.makeCylinder(55.0, 25.0, V(xp0 + 300.0, ks * (yb_h - 25.0), 1650.0 + floor_top), V(0, ks, 0))
        put("Shower_Head", "Лейка душа на штанге / смеситель (на стенке по борту)", head, COL_STEEL)
        fan = Part.makeCylinder(60.0, 40.0, V(xp0 + 250.0, ks * (y_ceil_back - 120.0), z_ceil - 12.0), V(0, 0, 1))
        put("Shower_ExhaustFan", "Вытяжка 12V ~4″ в потолке душа → небольшое отверстие в стене", fan, COL_DARK)

        # — мини-кухня: 2 секции (у душа — мойка; у сиденья — шкафчик + холодильник); торец к душу — вогнутый по дуге шторки —
        def ccyl(d, z0, h):                                          # область внутри контура поддона, смещённого на d
            return pshape(xp0, d, z0, h)
        d_k = K.get("curtain_in", 50.0) - 0.5                        # торец кухни — по линии шторки
        kx1 = K["kitchen_end_x"]
        kx0 = xp0 if K.get("kitchen_concave") else max(K.get("kitchen_x0", 0.0), sx1 + 5.0)
        kl = kx1 - kx0
        z_ct = floor_top + K["counter_h"]
        z_cb = z_ct - K["counter_th"]
        y_kb = yw(z_cb)                                              # задняя плоскость у столешницы
        y_kf = yw(500.0) - K["kitchen_depth"]                        # фронт короба
        y_ctf = y_kf - 20.0                                          # передняя кромка столешницы (свес 20)
        ph, pr = K["plinth"]
        cut_hi = ccyl(d_k, -10.0, 3000.0) if K.get("kitchen_concave") else None     # всё внутри шторки — душ
        cut_lo = ccyl(-3.0, -10.0, 3000.0) if K.get("kitchen_concave") else None    # цоколь — снаружи бортика

        def kcut(sh, c=None):
            c = cut_hi if c is None else c
            return sh.cut(c) if c is not None else sh
        dvt = K.get("divider", pt_)
        fx, fy, fz = K["fridge"]
        fpad = K.get("fridge_pad", 10.0)
        x_div1 = kx1 - pt_ - fx - 2.0 * fpad                         # перегородка секций: грань к кабине
        x_div0 = x_div1 - dvt                                        # … грань к душу
        # мойка — в секции у душа: как можно ближе к перегородке не надо — к вогнутой кромке (с отступом)
        skx, sky, skz = K["sink"]
        m_arc, m_front = K.get("sink_margin", (40.0, 40.0))
        y_s0 = y_ctf + m_front
        y_s1 = y_s0 + sky
        if K.get("kitchen_concave"):
            sk_x0 = xline(d_k - m_arc, y_s1)                         # угол мойки у стены — ближе всего к контуру
        else:
            sk_x0 = kx0 + 60.0
        sink_fit = x_div0 - (sk_x0 + skx)
        z_b = floor_top + ph + pt_                                   # верх дна короба
        carc = kcut(env_solid(kx0, kl, y_kf, floor_top + ph, z_cb))
        cav1 = kcut(Part.makeBox(x_div0 - kx0, (y_kb - pt_) - (y_kf - 1.0), z_cb - z_b, V(kx0, ks * (y_kf - 1.0) -
                    (0 if ks > 0 else (y_kb - pt_) - (y_kf - 1.0)), z_b)),
                    ccyl(d_k - pt_, -10.0, 3000.0) if K.get("kitchen_concave") else None)
        z_f0 = z_b + 15.0                                            # ларь на салазках над дном короба
        z_sh = z_f0 + fz + 40.0                                      # полка над ларём (низ)
        cav_f = Part.makeBox(kx1 - pt_ - x_div1, fy + 40.0, z_sh - z_b, V(x_div1, y_kf - 1.0, z_b))
        cav_u = Part.makeBox(kx1 - pt_ - x_div1, (y_kb - pt_) - (y_kf - 1.0), z_cb - (z_sh + pt_),
                             V(x_div1, y_kf - 1.0, z_sh + pt_))
        carc = carc.cut(cav1).cut(cav_f).cut(cav_u)
        put("Kitchen_Carcass", "Короб кухни (фанера 3/4″), 2 секции: мойка | шкафчик + холодильник; торец к душу — "
            "вогнутый по дуге шторки (гнутая фанера/кант)", carc, COL_CAB)
        put("Kitchen_Plinth", "Цоколь кухни (у душа — по дуге поддона, снаружи бортика)",
            kcut(Part.makeBox(kl, (y_kb - y_kf) - pr, ph, V(kx0, y_kf + pr, floor_top)), cut_lo), (0.35, 0.30, 0.25))
        top = kcut(env_solid(kx0, kl, y_ctf, z_cb, z_ct)).cut(
            Part.makeBox(skx, sky, K["counter_th"] + 2, V(sk_x0, y_s0, z_cb - 1)))
        put("Kitchen_Countertop", "Столешница 1″ (мебельный щит), верх %.0f над полом (36″); кромка к душу вогнутая — "
            "шторка прилегает" % K["counter_h"], top, COL_TOP)
        sk_o = V(sk_x0, y_s0, z_ct - skz)
        sink = Part.makeBox(skx, sky, skz, sk_o).cut(Part.makeBox(skx - 4, sky - 4, skz, V(sk_o.x + 2, sk_o.y + 2, sk_o.z + 2)))
        put("Kitchen_Sink", "Барная мойка 10×10″ из нержавейки (секция у душа)", sink, COL_STEEL)
        fct = V(sk_o.x + skx / 2.0, y_s1 + 30.0, z_ct)
        faucet = Part.makeCylinder(12.0, 260.0, fct).fuse(
            Part.makeCylinder(10.0, 170.0, V(fct.x, fct.y, fct.z + 250.0), V(0, -1, 0)))
        put("Kitchen_Faucet", "Кран (насос 12V включается по давлению)", faucet, COL_STEEL)
        put("Kitchen_Kettle", "Электрочайник (от инвертора) или 12V-чайник",
            Part.makeCylinder(85.0, 230.0, V(kx1 - 150.0, (y_kf + y_kb) / 2.0, z_ct)), (0.85, 0.85, 0.88))
        put("Kitchen_Outlet", "Розетка 120V + USB над столешницей",
            Part.makeBox(70.0, 20.0, 115.0, V(kx1 - 150.0 - 35.0, yw(z_ct + 150.0) - 20.0, z_ct + 120.0)),
            (0.95, 0.95, 0.95))
        fridge_x0 = x_div1 + fpad
        put("Kitchen_Fridge", "Холодильник %s 23.7×12.6×13.8″ на салазках (выдвигается в проход на %.0f мм — "
            "крышка сверху)" % (K.get("fridge_title", "12V"), K["fridge_slide"]),
            Part.makeBox(fx, fy, fz, V(fridge_x0, y_kf + 8.0, z_f0)), COL_FRIDGE)
        put("Kitchen_FridgeSlide", "Салазки холодильника (полного выдвижения, под ~45 кг)",
            Part.makeBox(fx, fy, 15.0, V(fridge_x0, y_kf + 8.0, z_f0 - 15.0)), COL_STEEL)
        x_af = xline(d_k, y_kf) if K.get("kitchen_concave") else kx0
        put("Kitchen_DoorSink", "Дверца под мойкой (чашки, чай, фильтр, сифон)",
            kcut(Part.makeBox(x_div0 + dvt / 2.0 - 2.0 - (x_af + 3.0), 12.0, z_cb - z_b - 6.0,
                              V(x_af + 3.0, y_kf - 12.0, z_b + 3.0))), (0.86, 0.70, 0.48))
        put("Kitchen_DoorUpper", "Дверца шкафчика над холодильником",
            Part.makeBox(kx1 - 3.0 - (x_div0 + dvt / 2.0 + 2.0), 12.0, z_cb - (z_sh + pt_) - 6.0,
                         V(x_div0 + dvt / 2.0 + 2.0, y_kf - 12.0, z_sh + pt_ + 3.0)), (0.86, 0.70, 0.48))
        zu0 = floor_top + K["upper"][0]
        zu1 = z_ceil
        y_uf = yw(zu0) - K["upper"][1]
        put("Kitchen_UpperCabinet", "Верхний шкафчик (чашки/чай), по завалу борта; торец к душу — по дуге шторки",
            kcut(env_solid(kx0, kl, y_uf, zu0, zu1)), COL_CAB)
        # откидная часть столешницы — на торце кухни у сиденья: сложена (вниз) / разложена (призрак, сиденье на 180°)
        KF = KITCHEN_FLAP
        flap_summary = None
        if KF.get("enable"):
            fl_, fth = KF["len"], KF["th"]
            bt_, bw_, bl_ = KF["bracket"]
            fy0, fy1 = y_ctf, yw(z_ct) - 5.0
            yc_ = (fy0 + fy1) / 2.0
            for i_, yb_ in enumerate((yc_ - KF["spacing"] / 2.0, yc_ + KF["spacing"] / 2.0)):
                put("Kitchen_FlapBracket%d" % (i_ + 1), "Складной кронштейн %d (сложен) — на торце кухни, плечо %.0f″" % (
                    i_ + 1, bl_ / 25.4), Part.makeBox(bt_, bw_, bl_, V(kx1, ks * yb_ - bw_ / 2.0, z_ct - fth - bl_)), COL_STEEL)
                put("Kitchen_FlapBracketOpen%d" % (i_ + 1), "Кронштейн %d разложен (сиденье развёрнуто на 180°)" % (i_ + 1),
                    Part.makeBox(bl_, bw_, bt_, V(kx1, ks * yb_ - bw_ / 2.0, z_ct - fth - bt_)), COL_STEEL, 70)
            put("Kitchen_Flap", "Откидная столешница %.0f×%.0f″ (1/2″) — сложена, висит на торце кухни" % (
                fl_ / 25.4, (fy1 - fy0) / 25.4), Part.makeBox(fth, fy1 - fy0, fl_, V(kx1 + bt_, fy0, z_ct - fl_)), COL_TOP)
            put("Kitchen_FlapOpen", "Откидная столешница разложена — вровень со столешницей, над развёрнутым сиденьем",
                Part.makeBox(fl_, fy1 - fy0, fth, V(kx1, fy0, z_ct - fth)), COL_TOP, 65)
            flap_summary = dict(len=fl_, w=fy1 - fy0, x_open=(kx1, kx1 + fl_), to_seat=3190.0 - (kx1 + bt_ + fth),
                                z_fold_low=z_ct - fl_ - floor_top)

        # — пропан: баллон 30 lb в герметичном локере под щитом (перед баком, к проходу от туалета) + газ к нагревателю —
        PR = K.get("propane")
        prop_summary = None
        if PR and GH:
            wl, inn = PR["wall"], PR["inner"]
            inn_h = PR["inner_h"] or (PR["cyl_h"] - wl)               # баллон стоит на полу через отверстие в дне
            outer = inn + 2.0 * wl
            hL = inn_h + 2.0 * wl
            to_ = doc.getObject("Toilet_Camco")
            pu_ = doc.getObject("Water_Pump12V")
            AL = ANCHORS.get("propane_locker", {})
            ly1 = (to_.Shape.BoundBox.YMin - PR["toilet_gap"]) if (to_ is not None and ks > 0) else 364.0
            lx0 = (pu_.Shape.BoundBox.XMax + PR["pump_gap"]) if pu_ is not None else dx1 - outer - 1.0
            if AL.get("y1") is not None:                              # ANCHORS: замер после туалета
                ly1 = AL["y1"]
            if AL.get("x0") is not None:
                lx0 = AL["x0"]
            lx1 = lx0 + outer
            ly0 = ly1 - outer
            z_l0 = floor_top
            shell = Part.makeBox(outer, outer, hL, V(lx0, ly0, z_l0)).cut(
                Part.makeBox(inn, inn, inn_h, V(lx0 + wl, ly0 + wl, z_l0 + wl)))
            door_cut = Part.makeBox(outer, wl, hL - 2.0 * wl, V(lx0, ly0, z_l0 + wl))
            vx, vy = lx0 + wl + 20.0, ly1 - wl - 20.0                  # вент — в дальнем от дверцы углу (мимо баллона)
            foot_hole = Part.makeCylinder(PR.get("foot_d", 235.0) / 2.0 + 2.0, wl + 2.0,
                                          V(lx0 + outer / 2.0, ly0 + outer / 2.0, z_l0 - 1.0))
            vent_hole = Part.makeCylinder(PR["vent_d"] / 2.0, z_l0 + wl + 20.0, V(vx, vy, -20.0))
            put("Propane_Locker", "Локер пропана — герметичный ящик (фанера 1/2″ + герметик/FRP), внутр. %.1f×%.1f×%.1f″ "
                "(впритык); в дне — отверстие под опорное кольцо баллона; вент ⌀1″ в полу наружу" % (
                    inn / 25.4, inn / 25.4, inn_h / 25.4), shell.cut(door_cut).cut(vent_hole).cut(foot_hole),
                (0.93, 0.85, 0.55))
            put("Propane_LockerDoor", "Дверца локера к проходу (на уплотнителе, 2 замка-защёлки) — баллон вынимается в проход",
                shell.common(door_cut), (0.98, 0.75, 0.30))
            for fn in ("Floor_XPS", "Floor_Plywood"):
                fo = doc.getObject(fn)
                if fo is not None:
                    fo.Shape = fo.Shape.cut(vent_hole)
            put("Propane_Vent", "Вент-трубка локера ⌀1″ через пол вниз наружу (пропан тяжелее воздуха)",
                Part.makeCylinder(PR["vent_d"] / 2.0, z_l0 + wl + 40.0, V(vx, vy, -40.0)).cut(
                    Part.makeCylinder(PR["vent_d"] / 2.0 - 2.0, z_l0 + wl + 50.0, V(vx, vy, -45.0))), (0.25, 0.25, 0.25))
            cd, ch_ = PR["cyl_d"], PR["cyl_h"]
            ccx, ccy, cz0 = lx0 + outer / 2.0, ly0 + outer / 2.0, z_l0         # на полу фургона (через дно)
            cyl = Part.makeCylinder(PR.get("foot_d", cd * 0.76) / 2.0, 40.0, V(ccx, ccy, cz0)).cut(
                Part.makeCylinder(PR.get("foot_d", cd * 0.76) / 2.0 - 3.0, 50.0, V(ccx, ccy, cz0 - 5.0))).fuse(
                Part.makeCylinder(cd / 2.0, ch_ - 40.0 - 40.0 - 62.0, V(ccx, ccy, cz0 + 40.0))).fuse(
                Part.makeCone(cd / 2.0, cd * 0.28, 40.0, V(ccx, ccy, cz0 + ch_ - 102.0))).fuse(
                Part.makeCylinder(cd * 0.30, 62.0, V(ccx, ccy, cz0 + ch_ - 62.0)).cut(
                    Part.makeCylinder(cd * 0.27, 70.0, V(ccx, ccy, cz0 + ch_ - 64.0)))).fuse(
                Part.makeCylinder(22.0, 70.0, V(ccx, ccy, cz0 + ch_ - 102.0 + 40.0)))
            put("Propane_Cylinder", "Баллон пропана %s, вертикально, вентилем вверх" % PR.get("title", ""),
                cyl, (0.96, 0.96, 0.96))
            # хомута нет: баллон держат стенки (впритык), крышка (впритык) и кольцо в отверстии дна
            put("Propane_Regulator", "Редуктор (в комплекте Camplux) — внутри локера, на вентиле",
                Part.makeCylinder(45.0, 35.0, V(ccx + 60.0, ccy, cz0 + ch_ - 70.0), V(1, 0, 0)), (0.75, 0.75, 0.78))
            # газовая линия: из крышки локера (гермоввод) → вверх под поперечины → вдоль борта → вперёд за край щита →
            # вверх через козырёк к штуцеру газа нагревателя (слева снизу)
            z_lt = z_l0 + hL
            z_g = min(z_lt + 50.0, (z_rail_top - sw) - 25.0)
            if toilet_pf and toilet_pf["z"][3] + 25.0 > z_g:          # 2026-11-09: туалет на платформе выше — газ над
                z_g = (z_rail_top - sw) - 25.0                       # полкой 2-го этажа, под поперечинами кровати
            y_gas = y_h0 + 50.0
            x_gv = x_h0 + 14.0
            pts = [V(lx1 - 40.0, ly1 - 40.0, z_lt), V(lx1 - 40.0, ly1 - 40.0, z_g), V(lx1 - 40.0, y_gas, z_g),
                   V(x_gv, y_gas, z_g), V(x_gv, y_gas, z_h0)]
            gl = None
            for p0_, p1_ in zip(pts, pts[1:]):
                seg = Part.makeCylinder(5.0, (p1_ - p0_).Length, p0_, p1_ - p0_).fuse(Part.makeSphere(5.0, p1_))
                gl = seg if gl is None else gl.fuse(seg)
            put("Gas_Line", "Газ: шланг LP 3/8″ (RV, в оплётке) из гермоввода локера к нагревателю — без соединений в салоне",
                gl, (0.95, 0.75, 0.10))
            put("Gas_Bulkhead", "Гермоввод газа в крышке локера", Part.makeCylinder(15.0, 15.0, V(lx1 - 40.0, ly1 - 40.0, z_lt)),
                (0.45, 0.45, 0.45))
            # датчики: пропан/CO — низко у локера; CO — у изголовья (кровать)
            put("Safety_LPCO", "Датчик пропана + CO 12V (RV, низко — пропан стекает к полу), на передней грани локера",
                Part.makeBox(10.0, 120.0, 85.0, V(lx1, ly0 + 15.0, z_l0 + 110.0)), (0.95, 0.30, 0.25))
            mt_ = doc.getObject("BedMattress")
            z_co = (mt_.Shape.BoundBox.ZMax if mt_ is not None else z_rail_top + 200.0) + 250.0
            put("Safety_CO_Bed", "Датчик CO у изголовья (на задней стенке душа со стороны кровати)",
                Part.makeBox(30.0, 110.0, 110.0, V(x_rw - 30.0, ks * 450.0, z_co)), (0.95, 0.30, 0.25))
            K["_gas_pts"] = [[p_.x, p_.y, p_.z] for p_ in pts]          # для чертежей (export_drawing_data)
            prop_summary = dict(x=(lx0, lx1), y=(ly0, ly1), z_top=z_lt, outer=outer, inner=(inn, inn_h),
                                deck_over=lx1 - dx1, under_cross=(z_rail_top - sw) - z_lt,
                                to_toilet=(to_.Shape.BoundBox.YMin - ly1) if to_ is not None else None,
                                to_pump=(lx0 - pu_.Shape.BoundBox.XMax) if pu_ is not None else None,
                                gas_len=sum((p1_ - p0_).Length for p0_, p1_ in zip(pts, pts[1:])))
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
        pall = [s_ for n_, s_ in parts.items() if n_ != "Shower_WallRear"]   # задняя стенка — вплотную к щиту (так и надо)
        for lab, ss in (("кровать (стойки/рейки/настил/матрас)", no_plate("Bed")), ("бак", objs("WaterTank")),
                        ("подставка бака", objs("TankRiser")), ("стойки бака", objs("TankPost")),
                        ("этажерка бака", objs("TankRail") + objs("TankCross") + objs("TankShelf") + objs("TankStop")),
                        ("поддон бака", objs("TankFloor"))):
            if ss:
                checks.append((lab, min(_dd(p, s_) for p in pall for s_ in ss)))
        pl = doc.getObject("BedPostPlate_pY_front")
        if pl is not None and min(_dd(p, pl.Shape) for p in pall) < 0.5 and not plate_note:
            checks.append(("пластина передней стойки кровати (1.6 мм) — душ заходит на её край: подложить", 0.0))
        if toilet_pf and toilet_moving:                          # туалет на платформе: транспорт и «в душе» ↔ душ/газ/локер
            m0_, m1_ = toilet_moving
            pass_ = [n_ for n_ in parts if n_ not in ("Shower_CurtainLower", "Shower_Pan", "Shower_Drain")]
            for lab, nn in (("душ/кухня", [n_ for n_ in pass_ if not n_.startswith(("Gas_", "Propane_", "Safety_"))]),
                            ("газ/локер/датчики", [n_ for n_ in pass_ if n_.startswith(("Gas_", "Propane_", "Safety_"))])):
                for pos_, ms_ in (("в транспорте", m0_), ("в душе", m1_)):
                    if nn:
                        v_, n_min = min((_dd(m_, parts[n_]), n_) for m_ in ms_ for n_ in nn)
                        toilet_pf["checks"].append(("туалет/платформа ↔ %s — %s (ближе всего %s)" % (lab, pos_, n_min), v_))
            # поддон: платформа проходит над бортиком; колёса стоят на дне / на плите (0 — так задумано, не проверяем)
            toilet_pf["checks"].append(("платформа ↔ поддон — в транспорте", _dd(m0_[1], pan)))
            toilet_pf["checks"].append(("платформа ↔ поддон — в душе", _dd(m1_[1], pan)))
            checks += toilet_pf["checks"]
        if False and tfl_summary and tfl_summary.get("toilet") and doc.getObject("Toilet_Camco") is not None:
            tb_ = doc.getObject("Toilet_Camco").Shape.BoundBox     # путь туалета вперёд до задней стенки душа
            sweep = Part.makeBox(xp0 - tb_.XMax, tb_.YLength, tb_.ZLength, App.Vector(tb_.XMax, tb_.YMin, tb_.ZMin))
            path_ = [("бойлер", sweep.distToShape(parts["Water_Heater12V"])[0]) if "Water_Heater12V" in parts else None,
                     ("передняя стойка кровати", sweep.distToShape(doc.getObject("BedPost_pY_front").Shape)[0]),
                     ("пластина передней стойки", sweep.distToShape(doc.getObject("BedPostPlate_pY_front").Shape)[0]),
                     ("арка", sweep.distToShape(arch_shapes[ks])[0]),
                     ("до поддона душа, мм", xp0 - tb_.XMax)]
            tfl_summary["toilet"]["path"] = [p_ for p_ in path_ if p_]
            TANK_FLOOR["_summary"]["toilet"] = tfl_summary["toilet"]
        if plate_note:
            checks.append((plate_note, 0.0))
        checks.append(("поддон ↔ арка", pan.distToShape(arch_s)[0]))
        kpart = [parts[n_] for n_ in parts if n_.startswith("Kitchen_")]
        checks.append(("кухня ↔ поддон", min(_dd(k_, pan) for k_ in kpart)))
        checks.append(("кухня ↔ шторка (прилегает)", min(_dd(k_, parts["Shower_Curtain"]) for k_ in kpart)))
        checks.append(("кухня ↔ карниз", min(_dd(k_, parts["Shower_CurtainRod"]) for k_ in kpart)))
        checks.append(("мойка ↔ перегородка секций", sink_fit))
        gas = {}
        if GH:
            hsh = parts["Shower_GasHeater"]
            gas.update(heater_x=(x_h0, x_h0 + ghx), heater_y=(y_h0, y_h1), heater_z=(z_h0, z_h1),
                       over_pan=x_h0 + ghx - xp0, flue_c=(fx_c, abs(fy_c)), flue_top=z_fl1,
                       top_to_ceil=(z_ceil - 12.0) - z_h1)
            checks += [("нагреватель ↔ поддон (по высоте)", _dd(hsh, pan)), ("нагреватель ↔ лейка", _dd(hsh, parts["Shower_Head"])),
                       ("нагреватель ↔ шторка", _dd(hsh, parts["Shower_Curtain"])),
                       ("дымоход ↔ вытяжка", _dd(flue, parts["Shower_ExhaustFan"])),
                       ("дымоход ↔ карниз", _dd(flue, parts["Shower_CurtainRod"])),
                       ("дымоход ↔ ребро крыши", min(_dd(flue, s_) for s_ in objs("Rib")) if objs("Rib") else 999.0)]
        if prop_summary:
            lk = parts["Propane_Locker"]
            others = [("туалет", objs("Toilet")), ("насос", objs("Water_Pump")), ("бак", objs("WaterTank")),
                      ("бруски/анкеры бака", objs("TankFloor")), ("поперечины кровати", objs("BedCross")),
                      ("арка", [arch_s]), ("поддон душа", [pan])]
            for lab, ss in others:
                if ss:
                    checks.append(("локер ↔ " + lab, min(_dd(lk, s_) for s_ in ss)))
            gl_ = parts["Gas_Line"]
            if doc.getObject("Toilet_Camco") is not None and not toilet_pf:
                tb_ = doc.getObject("Toilet_Camco").Shape.BoundBox
                sweep = Part.makeBox(xp0 - tb_.XMin, tb_.YLength, tb_.ZLength, App.Vector(tb_.XMin, tb_.YMin, tb_.ZMin))
                checks.append(("газ ↔ путь туалета в душ", sweep.distToShape(gl_)[0]))
                checks.append(("локер ↔ путь туалета в душ", sweep.distToShape(lk)[0]))
            checks.append(("газ ↔ поперечины кровати", min(_dd(gl_, s_) for s_ in objs("BedCross"))))
            rail_ = doc.getObject("BankRail_Inner")
            if rail_ is not None:
                prop_summary["trunk"] = prop_summary["y"][0] - rail_.Shape.BoundBox.YMax
        aisle_sh = y_sf + y_at_z(half, 900.0)                       # от шторки до противоположной стены
        aisle_k = (y_kf - 20.0) + y_at_z(half, 900.0)
        # вход в душ: от задней стенки (по линии шторки) до угла столешницы
        x_ent = xline(d_k, y_ctf)
        entry = math.hypot(x_ent - (x_rw + pt_), y_ctf - y_c)
        galley_summary = dict(
            gas=gas, propane=prop_summary, entry=entry, flap=flap_summary, x_div=(x_div0, x_div1), sink_x=(sk_x0, sk_x0 + skx),
            sec1_front=(x_af, x_div0), sec2=(x_div1, kx1), fridge_title=K.get("fridge_title"), r_c=r_c,
            shower_x=(sx0, sx1), shower_in=(six, siy), y_sf=y_sf, z_pan=z_pan, z_ceil=z_ceil, pan_x0=xp0,
            pan_behind=xp0 - x_rw, rear_wall_z=z_rw0, y_pan_back=y_back_pan, pan_r=R_, pan_corner_r=Rc,
            headroom=(z_ceil - 12.0) - z_pan, kitchen_x=(kx0, kx1), kl=kl, y_kf=y_kf, counter=K["counter_h"],
            seat_gap=3190.0 - kx1, aisle_sh=aisle_sh, aisle_k=aisle_k, checks=checks,
            floor_top=floor_top, wall_y=y_at_z(half, 900.0), arch_ywall=arch_ywall,
            toilet_pf={k_: v_ for k_, v_ in toilet_pf.items() if k_ != "checks"} if toilet_pf else None,
            pan_in=dict(z_in=z_pin - floor_top, rim_t=t_rim, drain=(dr_x, abs(dr_y))))

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "galley_summary ph")
