# -*- coding: utf-8 -*-
"""Два ящика под кроватью (вариант van_v1_rect_pan, 2026-11-12, Dimitri).

  • НИЖНИЙ — на маленьких колёсиках (лежат на полу), выкатывается ВПЕРЁД, в салон. Ширина — от стойки P3 батарей (пассажирский
    борт) до края поддона душа (водительский борт: поддон стоит в салоне на пути ящика).
  • ВЕРХНИЙ — выезжает НАЗАД, из багажника, на направляющих SLIDEWAY 44″ (как в прошлой модели). Ширина — проём задних
    дверей; идёт над туалетом (низ — над его верхом) и над аркой; направляющие висят на поперечинах кровати (подвесы strut).
Оба — «максимально широкие»: ради этого поддон и туалет сдвинуты к борту. Бак, баллон и полка 2-го этажа не строятся.
Размеры и зазоры считаются от уже построенных деталей (пассажирская стойка, поддон, туалет, задние стойки, поперечины)."""

import FreeCAD as App
import Part

from .common import COL_STRUT, add_shape
from .vslot import vslot_2020, vslot_x, vslot_y   # noqa: F401  (раньше были здесь)
from .params_rect import DRAWERS_RECT, SHELF_RECT, WATER_RECT

V = App.Vector
COL_PLY, COL_PLY2, COL_STEEL, COL_WHEEL = (0.80, 0.66, 0.42), (0.86, 0.74, 0.52), (0.80, 0.82, 0.86), (0.15, 0.15, 0.15)


def drawers(S):
    """Нижний ящик на колёсиках (вперёд) + верхний на направляющих (назад)."""
    doc, floor_top, sd, sw = S.doc, S.floor_top, S.sd, S.sw
    D = DRAWERS_RECT
    drawers_summary = None
    trunk_summary = None                                               # багажника (ящики на баке, полка) в этом варианте нет — общая сводка пропускает
    if not D.get("enable"):
        S.put(locals(), "drawers_summary trunk_summary")
        return
    gobj = lambda n: doc.getObject(n)
    bb = lambda n: gobj(n).Shape.BoundBox
    L, U = D["lower"], D["upper"]
    tw, tb = D["wall"], D["base"]
    g = doc.addObject("App::DocumentObjectGroup", "Drawers")
    g.Label = "Ящики под кроватью — нижний на колёсиках (вперёд), верхний на направляющих (назад) (проект 2026-11-12)"
    parts = {}

    def put(name, label, shape, color, tr=0):
        add_shape(doc, name, label, shape, color=color, transparency=tr, group=g)
        parts[name] = shape
        return shape

    def tray(x0, x1, y0, y1, z0, z1):
        """Ящик — фанера: дно tb и 4 стенки tw, сверху открыт."""
        outer = Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
        inner = Part.makeBox(x1 - x0 - 2 * tw, y1 - y0 - 2 * tw, z1 - z0 - tb + 1.0, V(x0 + tw, y0 + tw, z0 + tb))
        return outer.cut(inner)

    # ── ограничения из уже построенных деталей ──
    z_top_lim = bb("BedCross_1").ZMin                                  # низ поперечин кровати
    PS = S.propane_summary                                              # локер баллона на месте бывшего туалета: его верх задаёт низ верхнего ящика
    locker_top = PS["z_top"]
    locker_x0 = PS["x"][0]
    p3 = bb("BankPost_P3f")                                            # ножка батарей у пассажирского борта (край Y)
    pan = bb("Shower_PanRect")
    pil = bb("Pillar_Rear_pY")
    xb_end = S.dx1                                                      # край щита кровати

    # ═══════ ВЕРХНИЙ ящик: назад, на SLIDEWAY, над туалетом и аркой ═══════
    SL = U["slide"]
    zu0 = locker_top + U["above_locker"]                               # низ ящика — над акриловой крышкой локера
    zu1 = z_top_lim - U["top_gap"]                                     # верх ящика (под поперечинами кровати)
    y_out = pil.YMin - U["door_gap"]                                   # наружная плоскость направляющих (|Y|) — в проёме дверей
    y_box = y_out - SL["T"]                                            # наружная грань ящика (|Y|) пассажирской стороны: между направляющими
    y_box_d = min(U.get("driver_y_box", y_box), y_box)                 # водительская сторона сужена — колодец над аркой (люки в кровати)
    xu0, xu1 = U["x_rear"], xb_end - U["front_gap"]                    # 2026-11-12: ящик доведён вперёд до края щита кровати (направляющие короче — 44″)
    put("Drawer_Upper", "Верхний ящик (фанера 1/2″): X %.0f..%.0f, Y %.0f..%.0f, ширина %.0f мм (%.1f″) — пассажирская сторона на весь проём дверей, "
        "водительская сужена до Y %.0f (колодец над аркой), высота %.0f мм (%.1f″), низ %.0f мм над полом (над локером баллона: его верх %.0f); "
        "выезжает НАЗАД на SLIDEWAY" % (
            xu0, xu1, -y_box, y_box_d, y_box + y_box_d, (y_box + y_box_d) / 25.4, y_box_d, zu1 - zu0, (zu1 - zu0) / 25.4,
            zu0 - floor_top, locker_top - floor_top),
        tray(xu0, xu1, -y_box, y_box_d, zu0, zu1), COL_PLY)
    zs0 = zu0 + (zu1 - zu0 - SL["H"]) / 2.0                            # направляющие — на середине высоты стенки
    cb1, cb2 = bb("BedCross_1"), bb("BedCross_2")
    hang = []
    for sgn, side in ((1, "driver"), (-1, "passenger")):
        yo_ = y_box_d + SL["T"] if sgn > 0 else y_out                  # наружная плоскость направляющей (|Y|)
        ya, yb = (y_box_d, yo_) if sgn > 0 else (-y_out, -y_box)
        put("Drawer_Slide_%s" % side, "Направляющая %s (%s): рабочая часть на ящике, неподвижная — на подвесах" % (SL["title"], side),
            Part.makeBox(SL["L"], SL["T"], SL["H"], V(xu0, ya, zs0)), COL_STEEL)
        for k, cb in ((1, cb1), (2, cb2)):                             # стойки до пола (2026-11-12): вместо подвесов от поперечин
            lt = U["leg"]
            ya_h, yb_h = (yo_, yo_ + lt) if sgn > 0 else (-y_out - lt, -y_out)
            h = vslot_2020(cb.XMin + 4.0, ya_h, floor_top + 2.0, cb.ZMin)
            put("Drawer_Leg_%s_%d" % (side, k), "Стойка направляющей %d (%s): профиль V-Slot 2020, 20 × 20 мм (SeekLiny 10Pcs V Slot 2020 "
                "Aluminum Extrusion 2440 mm) от пола (над пластиной 2 мм) до поперечины кровати #%d; внизу и вверху — угольники 2020 с T-гайками; "
                "направляющая — болтами в паз стойки (держит и боковую нагрузку в повороте)" % (k, side, k), h, (0.78, 0.80, 0.84))
            hang.append(h)
    put("Drawer_Upper_Handle", "Ручка верхнего ящика (задний торец)",
        Part.makeCylinder(10.0, 300.0, V(xu0 - 25.0, (y_box_d - y_box) / 2.0 - 150.0, zu1 - 60.0), V(0, 1, 0)), COL_STEEL)

    # ═══════ НИЖНИЙ ящик: на колёсиках, вперёд в салон ═══════
    CA = L["caster"]
    y_pass = p3.YMax + L["side_gap"]                                   # пассажирская грань (|Y| макс. к борту)
    y_drv = pan.YMin - L["side_gap"]                                   # водительская грань — до края поддона
    WR = WATER_RECT
    arch_y = min(bb("WheelArch_pY").YMin, pil.YMin) - WR["gap_wall"]    # бак: поперёк до арки / задней стойки
    if WR.get("enable"):                                                # если бак не влезает — сужаем нижний ящик
        y_drv = min(y_drv, arch_y - WR["dims"][1] - WR["gap_drawer"])
    xl0, xl1 = L["x_rear"], xb_end - L["front_gap"]
    zl0 = floor_top + CA["h"]
    zl1 = zu0 - L["top_gap"]
    put("Drawer_Lower", "Нижний ящик на колёсиках (фанера 1/2″): X %.0f..%.0f, Y %.0f..%.0f — ширина %.0f мм (%.1f″), высота %.0f мм "
        "(%.1f″); от ножки батарей P3 до края поддона душа; катится ВПЕРЁД в салон" % (
            xl0, xl1, y_pass, y_drv, y_drv - y_pass, (y_drv - y_pass) / 25.4, zl1 - zl0, (zl1 - zl0) / 25.4),
        tray(xl0, xl1, y_pass, y_drv, zl0, zl1), COL_PLY2)
    wr, ww = CA["wheel_d"] / 2.0, CA["wheel_w"]
    mpx, mpy = CA["plate"]
    xs = [xl0 + CA["x_inset"], (xl0 + xl1) / 2.0, xl1 - CA["x_inset"]]
    for i, xc in enumerate(xs):
        for tag, yc in (("D", y_drv - CA["y_inset"]), ("P", y_pass + CA["y_inset"])):
            wh = Part.makeCylinder(wr, ww, V(xc, yc - ww / 2.0, floor_top + wr), V(0, 1, 0)).fuse(
                Part.makeBox(mpx, mpy, zl0 - (floor_top + 2 * wr), V(xc - mpx / 2.0, yc - mpy / 2.0, floor_top + 2 * wr)))
            put("Drawer_Wheel_%s%d" % (tag, i + 1), "Колёсико %s %d ⌀%.0f мм неповоротное (высота с креплением %.0f мм)" % (
                {"D": "водительское", "P": "пассажирское"}[tag], i + 1, CA["wheel_d"], CA["h"]), wh, COL_WHEEL)
    put("Drawer_Lower_Handle", "Ручка нижнего ящика (передний торец, к салону)",
        Part.makeCylinder(10.0, 300.0, V(xl1 + 25.0, (y_pass + y_drv) / 2.0 - 150.0, zl1 - 60.0), V(0, 1, 0)), COL_STEEL)

    # ═══════ ПРОВЕРКИ: в закрытом положении и по пути выдвижения ═══════
    skip = ("Scan_", "Opening_", "RearDoorLeaf", "Drawer", "Floor_")
    obst = [(o.Name, o.Shape) for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull() and o.Shape.Solids
            and not o.Name.startswith(skip)]

    def nearest(shape, extra_skip=()):
        best = (1e9, "")
        for n, s in obst:
            if n.startswith(extra_skip):
                continue
            dd = shape.distToShape(s)[0]
            if dd < best[0]:
                best = (dd, n)
        return best

    up = [parts[n] for n in parts if n.startswith(("Drawer_Upper", "Drawer_Slide")) or n.startswith("Drawer_Leg")]
    lo = [parts[n] for n in parts if n.startswith(("Drawer_Lower", "Drawer_Wheel"))]
    own_hang = ("Drawer_Hanger",)
    # путь верхнего ящика: объём ящика + направляющих, протянутый назад на ход (без стоек — они не движутся)
    tr_u, tr_l = U["travel"], L["travel"]
    ub = parts["Drawer_Upper"].BoundBox
    sw_u = Part.makeBox(ub.XLength + tr_u, ub.YLength, ub.ZLength, V(ub.XMin - tr_u, ub.YMin, ub.ZMin))
    lb = parts["Drawer_Lower"].BoundBox
    sw_l = Part.makeBox(lb.XLength + tr_l, lb.YLength, zl1 - floor_top, V(lb.XMin, lb.YMin, floor_top))
    checks = []
    # пластины 2 мм под ножки (BankPostPlate) колёсики переезжают; BedCross — подвесы к ним крепятся (касание задумано)
    for lab, sh, sk in (("верхний ящик — закрыт", Part.makeCompound([parts["Drawer_Upper"]]), ()),
                        ("верхний ящик — путь назад на %.0f мм" % tr_u, sw_u, ()),
                        ("нижний ящик — закрыт", Part.makeCompound([parts["Drawer_Lower"]]), ("BankPostPlate",)),
                        ("нижний ящик — путь вперёд на %.0f мм" % tr_l, sw_l, ("BankPostPlate",))):
        dd, nn = nearest(sh, sk)
        checks.append(("%s: ближе всего «%s»" % (lab, nn), dd))
    for s_ in hang + [parts["Drawer_Slide_driver"], parts["Drawer_Slide_passenger"]]:
        pass
    dd, nn = nearest(Part.makeCompound([parts[n] for n in parts if n.startswith(("Drawer_Slide", "Drawer_Leg"))]), ("BedCross", "BankPostPlate"))
    checks.append(("направляющие и стойки (кроме крепления к поперечинам и пластин 2 мм): ближе всего «%s»" % nn, dd))
    legs_c = Part.makeCompound([parts[n] for n in parts if n.startswith("Drawer_Leg")])
    checks.append(("стойки верхнего ящика ↔ путь нижнего ящика вперёд", sw_l.distToShape(legs_c)[0]))
    checks.append(("стойки верхнего ящика ↔ нижний ящик (закрыт)", parts["Drawer_Lower"].distToShape(legs_c)[0]))
    plates = [s_ for n_, s_ in obst if n_.startswith("BankPostPlate")]
    pw = Part.makeCompound([parts[n] for n in parts if n.startswith("Drawer_Wheel")])
    checks.append(("колёсики нижнего ящика переезжают пластины 2 мм под ножками батарей (P3 и P3f) — касание: %d шт" % len(plates),
                   min([pw.distToShape(p_)[0] for p_ in plates] or [0.0])))
    dd, nn = nearest(Part.makeCompound([parts[n] for n in parts if n.startswith("Drawer_Wheel")]), ())
    checks.append(("колёсики: ближе всего «%s»" % nn, dd))
    checks.append(("верхний ящик ↔ нижний ящик (зазор по высоте)", zu0 - zl1))
    checks.append(("верх верхнего ящика ↔ поперечины кровати", z_top_lim - zu1))
    checks.append(("нижний ящик: запас до края поддона / до ножки P3", min(pan.YMin - y_drv, y_pass - p3.YMax)))
    # ═══════ БАК ВОДЫ (Class A Customs): сзади от туалета, водительский борт, справа от нижнего ящика, под верхним ящиком ═══════
    water_summary = None
    if WR.get("enable"):
        tl, tw_, th_ = WR["dims"]
        tx1 = locker_x0 - WR["gap_toilet"]                              # бак — сзади от локера баллона
        ty0 = parts["Drawer_Lower"].BoundBox.YMax + WR["gap_drawer"]
        tx0 = tx1 - tl
        wg = doc.addObject("App::DocumentObjectGroup", "WaterTankRect")
        wg.Label = "Бак воды — Class A Customs %s %d gal (проект 2026-11-12)" % (WR["model"], WR["gal"])
        tank = Part.makeBox(tl, tw_, th_, V(tx0, ty0, floor_top))
        add_shape(doc, "WaterTank_Rect", "Бак воды Class A Customs %s, %d gal, %.1f×%.1f×%.1f″: сзади от локера баллона (X %.0f..%.0f), "
                  "справа от нижнего ящика (Y %.0f..%.0f), под верхним ящиком (верх %.0f мм над полом, зазор до ящика %.0f мм); "
                  "штуцеры 1.5″ NPT ×2 и 0.5″ ×2 — по месту" % (WR["model"], WR["gal"], tl / 25.4, tw_ / 25.4, th_ / 25.4, tx0, tx1,
                                                              ty0, ty0 + tw_, th_, zu0 - (floor_top + th_)),
                  tank, color=(0.70, 0.86, 0.98), transparency=25, group=wg)
        # штуцеры — все на ОДНОМ торце (по картинке T-1800): задний торец (к дверям) — залив; 2 × 1.5″ NPT по диагонали + 2 × 0.5″
        fz0, fz1 = floor_top + th_ * 0.28, floor_top + th_ * 0.72
        fy0, fy1 = ty0 + tw_ * 0.2, ty0 + tw_ * 0.8
        for k_, (yy, zz, dd_, ln_, lab) in enumerate(((fy0, fz1, 48.3, 22.0, "1.5″ NPT (залив)"), (fy1, fz0, 48.3, 22.0, "1.5″ NPT"),
                                                      (fy1, fz1, 21.3, 18.0, "0.5″ NPT"), (fy0, fz0, 21.3, 18.0, "0.5″ NPT"))):
            add_shape(doc, "WaterTank_Fitting_%d" % (k_ + 1), "Штуцер %s на заднем торце бака (смотрит к задним дверям)" % lab,
                      Part.makeCylinder(dd_ / 2.0, ln_, V(tx0 - ln_, yy, zz), V(1, 0, 0)), color=(0.15, 0.15, 0.15), group=wg)
        obst2 = [(n_, s_) for n_, s_ in obst if not n_.startswith(("Shower", "Kitchen", "Toilet_", "Gas_"))]
        dmin, nmin = min((tank.distToShape(s_)[0], n_) for n_, s_ in obst2 + [(n_, s_) for n_, s_ in parts.items()
                                                                           if n_.startswith("Drawer_") and "Wheel" not in n_ or "Wheel" in n_])
        checks.append(("бак воды: ближе всего «%s»" % nmin, dmin))
        water_summary = dict(model=WR["model"], gal=WR["gal"], x=(tx0, tx1), y=(ty0, ty0 + tw_), h=th_, dims=WR["dims"],
                             gap_up=zu0 - (floor_top + th_))
    drawers_summary = dict(
        upper=dict(x=(xu0, xu1), width=y_box + y_box_d, y_d=y_box_d, h=zu1 - zu0, z=(zu0 - floor_top, zu1 - floor_top), y_out=y_out, travel=tr_u,
                   vol=(xu1 - xu0 - 2 * tw) * (y_box + y_box_d - 2 * tw) * (zu1 - zu0 - tb) / 1e6, locker_top=locker_top - floor_top),
        lower=dict(x=(xl0, xl1), y=(y_pass, y_drv), width=y_drv - y_pass, h=zl1 - zl0, z=(zl0 - floor_top, zl1 - floor_top),
                   travel=tr_l, vol=(xl1 - xl0 - 2 * tw) * (y_drv - y_pass - 2 * tw) * (zl1 - zl0 - tb) / 1e6),
        checks=checks, floor_top=floor_top, water=water_summary)
    S.put(locals(), "drawers_summary trunk_summary")


def report(S):
    k = S.drawers_summary
    if not k:
        return
    u, l = k["upper"], k["lower"]
    print("=" * 70)
    print("[Ящики под кроватью — вариант van_v1_rect_pan, 2026-11-12]")
    print("  НИЖНИЙ (на колёсиках, катится ВПЕРЁД): X %.0f..%.0f (%.0f мм), Y %.0f..%.0f — ширина %.0f мм (%.1f″), высота %.0f мм "
          "(%.1f″), от %.0f до %.0f мм над полом; объём ≈ %.0f л; ход %.0f мм" % (
              l["x"][0], l["x"][1], l["x"][1] - l["x"][0], l["y"][0], l["y"][1], l["width"], l["width"] / 25.4, l["h"], l["h"] / 25.4,
              l["z"][0], l["z"][1], l["vol"], l["travel"]))
    print("  ВЕРХНИЙ (SLIDEWAY 44″, НАЗАД): X %.0f..%.0f, ширина %.0f мм (%.1f″) — пассажирская сторона на весь проём дверей (направляющие на |Y|=%.0f), водительская сужена до Y=%.0f; "
          "высота %.0f мм (%.1f″), от %.0f до %.0f мм над полом (верх локера баллона %.0f); объём ≈ %.0f л; ход %.0f мм" % (
              u["x"][0], u["x"][1], u["width"], u["width"] / 25.4, u["y_out"], u["y_d"], u["h"], u["h"] / 25.4, u["z"][0], u["z"][1],
              u["locker_top"], u["vol"], u["travel"]))
    sh = k.get("shelf")
    if sh:
        print("  ПОЛКА над левой аркой (2 яруса на водительских стойках 2020): X %.0f..%.0f, Y %.0f..%.0f (%.0f × %.0f мм); ярусы Z %.0f..%.0f и %.0f..%.0f; "
              "свободная высота нижнего яруса %.0f мм, верхнего %.0f мм; фанера на Z %.0f и %.0f; доступ от задних дверей и (при выдвинутом верхнем ящике) сбоку от салона" % (
                  sh["x"][0], sh["x"][1], sh["y"][0], sh["y"][1], sh["x"][1] - sh["x"][0], sh["y"][1] - sh["y"][0],
                  sh["z"][0][0], sh["z"][0][1], sh["z"][1][0], sh["z"][1][1], sh["gap_between"], sh["gap_top"], sh["board"][0][0], sh["board"][1][0]))
    w = k.get("water")
    if w:
        print("  БАК ВОДЫ Class A Customs %s (%d gal) %.1f×%.1f×%.1f″: X %.0f..%.0f (за локером баллона), Y %.0f..%.0f (справа от нижнего ящика), "
              "высота %.0f мм, до верхнего ящика %.0f мм" % (w["model"], w["gal"], w["dims"][0] / 25.4, w["dims"][1] / 25.4,
                                                         w["dims"][2] / 25.4, w["x"][0], w["x"][1], w["y"][0], w["y"][1], w["h"], w["gap_up"]))
    print("  Зазоры/запасы: " + "; ".join("%s %.1f" % (n_, v_) for n_, v_ in k["checks"]))
    print("=" * 70)



# ═══════════════════════════════════════════════════════════════════════════════════════════════════
# ПОЛКА НАД ЛЕВОЙ (водительской) АРКОЙ — 2026-11-12, Dimitri: два яруса на водительских стойках 2020, до задней стенки душа
# ═══════════════════════════════════════════════════════════════════════════════════════════════════
def shelf(S):
    doc = S.doc
    H = SHELF_RECT
    k = S.drawers_summary
    S.shelf_summary = None
    if not H.get("enable") or not k:
        S.put(locals(), "shelf_summary")
        return
    bb = lambda n: doc.getObject(n).Shape.BoundBox
    g = doc.addObject("App::DocumentObjectGroup", "ArchShelf")
    g.Label = "Полка над левой аркой — 2 яруса на водительских стойках 2020 (проект 2026-11-12)"
    parts = {}

    def put(name, label, shape, color):
        add_shape(doc, name, label, shape, color=color, group=g)
        parts[name] = shape

    PROF, PLY = (0.78, 0.80, 0.84), (0.80, 0.66, 0.42)
    legs = [bb("Drawer_Leg_driver_1"), bb("Drawer_Leg_driver_2")]
    y_leg = legs[0].YMax                                               # наружная грань стойки (Y)
    y_in = y_leg + H["gap_leg"]
    y_out = bb("BedSideRail_pY").YMin - H["gap_rail"]
    x0, bt, gu = H["x0"], H["board_t"], H["gusset"]
    x1 = H["x1"] if H["x1"] is not None else bb("Shower_WallRear").XMin - H["gap_wall"]
    locker_top = S.propane_summary["z_top"] if S.propane_summary else 0.0
    za_list = (max(H["tiers"][0], locker_top + H["gap_toilet"] - 20.0), H["tiers"][1])
    # колонна у переднего наружного угла: от арки (через резину) до низа фанеры верхнего яруса; под свес 460 мм до задней стенки душа
    yc0 = y_out - 22.0
    xc0 = x1 - 20.0
    arch = doc.getObject("WheelArch_pY").Shape
    z_arch = 0.0
    for dx_ in (0.0, 20.0):                                            # крона арки — в точке опоры, самая высокая по углам колонны
        for dy_ in (0.0, 20.0):
            try:
                z_arch = max(z_arch, arch.common(Part.makeLine(V(xc0 + dx_, yc0 + dy_, 900.0), V(xc0 + dx_, yc0 + dy_, 0.0))).BoundBox.ZMax)
            except Exception:
                z_arch = max(z_arch, bb("WheelArch_pY").ZMax)
    z_col0 = z_arch + H["col_pad"]
    z_col1 = za_list[1] + 20.0
    col = vslot_2020(xc0, yc0, z_col0, z_col1)
    colbox = Part.makeBox(22.0, 22.0, 2000.0, V(xc0 - 1.0, yc0 - 1.0, 0.0))
    tiers = []
    for t, za in enumerate(za_list, 1):
        zb = za + 20.0                                                 # верх плеч = низ фанеры
        for n, lg in enumerate(legs, 1):
            put("Shelf_Arm_%d_%d" % (t, n), "Плечо яруса %d у стойки %d: профиль 2020, от стойки к борту, к стойке — угольником в паз" % (t, n),
                vslot_y(lg.XMin, y_leg, y_out - 2.0, za), PROF)
            xc = (lg.XMin + lg.XMax) / 2.0
            tri = Part.Face(Part.makePolygon([V(xc - 2.0, y_leg, za - gu), V(xc - 2.0, y_leg, za), V(xc - 2.0, y_leg + gu, za),
                                              V(xc - 2.0, y_leg, za - gu)])).extrude(V(4.0, 0, 0))
            put("Shelf_Gusset_%d_%d" % (t, n), "Косынка %.0f мм под плечом яруса %d у стойки %d (2020 corner bracket / пластина 4 мм)" % (gu, t, n),
                tri, PROF)
        board = Part.makeBox(x1 - x0, y_out - y_in, bt, V(x0, y_in, zb))
        if t == 1:
            board = board.cut(colbox)                                  # колонна проходит через нижнюю фанеру
        put("Shelf_Board_%d" % t, "Фанера %.0f мм яруса %d: X %.0f..%.0f, Y %.0f..%.0f (%.0f × %.0f мм), на плечах, шурупами в T-гайки; "
            "переднее положение — до задней стенки душа" % (bt, t, x0, x1, y_in, y_out, x1 - x0, y_out - y_in), board, PLY)
        zl = zb + bt
        put("Shelf_Lip_Inner_%d" % t, "Бортик яруса %d со стороны салона (профиль 2020 вдоль X)" % t, vslot_x(x0, x1, y_in, zl), PROF)
        put("Shelf_Lip_Front_%d" % t, "Бортик яруса %d спереди, у стенки душа (профиль 2020 поперёк; к стенке — уголками)" % t,
            vslot_y(x1 - 20.0, y_in + 20.0, yc0 - 1.0, zl), PROF)
        put("Shelf_Lip_Rear_%d" % t, "Бортик яруса %d сзади, у дверей (профиль 2020 поперёк)" % t, vslot_y(x0, y_in + 20.0, y_out, zl), PROF)
        tiers.append((za, zl + 20.0, zb, zl))
    put("Shelf_Column_Front", "Колонна у переднего наружного угла: профиль 2020 от арки (резиновая прокладка %.0f мм) до низа фанеры верхнего яруса, "
        "болтами к плечам/угольникам; держит свес 460 мм до задней стенки душа" % H["col_pad"], col, PROF)
    # ── проверки ──
    skip = ("Scan_", "Opening_", "RearDoorLeaf", "Floor_", "Shelf_", "Drawer_Leg", "Drawer_Upper", "Drawer_Slide")
    obst = [(o.Name, o.Shape) for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull() and o.Shape.Solids
            and not o.Name.startswith(skip)]
    for t in (1, 2):
        comp = Part.makeCompound([sh for n_, sh in parts.items() if n_.endswith("_%d" % t) or n_.endswith("_%d_1" % t) or n_.endswith("_%d_2" % t)])
        dmin, nmin = min((comp.distToShape(s_)[0], n_) for n_, s_ in obst)
        k["checks"].append(("полка, ярус %d: ближе всего «%s»" % (t, nmin), dmin))
    dd = min(parts["Shelf_Board_1"].distToShape(doc.getObject("Drawer_Upper").Shape)[0], parts["Shelf_Board_2"].distToShape(doc.getObject("Drawer_Upper").Shape)[0])
    k["checks"].append(("полка ↔ верхний ящик", dd))
    k["checks"].append(("верх верхнего яруса (бортики) ↔ поперечины кровати", bb("BedCross_1").ZMin - tiers[1][1]))
    k["checks"].append(("нижний ярус над локером баллона (низ фанеры ↔ акрил)", tiers[0][2] - locker_top))
    k["shelf"] = dict(x=(x0, x1), y=(y_in, y_out), z=[(a_, b_) for a_, b_, _, _ in tiers],
                      gap_between=za_list[1] - tiers[0][3], gap_top=bb("BedCross_1").ZMin - tiers[1][1], z_arch=z_arch,
                      board=[(c_, d_) for _, _, c_, d_ in tiers])
    S.shelf_summary = k["shelf"]
    S.put(locals(), "shelf_summary")
