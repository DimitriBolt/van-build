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
from .params_rect import DRAWERS_RECT, HATCH_RECT, WATER_RECT

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
    toilet_top = max(o.Shape.BoundBox.ZMax for o in doc.Objects if o.Name.startswith("Toilet_") and o.isDerivedFrom("Part::Feature")
                     and not o.Shape.isNull())
    p3 = bb("BankPost_P3")                                             # ножка батарей у пассажирского борта (край Y)
    pan = bb("Shower_PanRect")
    pil = bb("Pillar_Rear_pY")
    xb_end = S.dx1                                                      # край щита кровати

    # ═══════ ВЕРХНИЙ ящик: назад, на SLIDEWAY, над туалетом и аркой ═══════
    SL = U["slide"]
    zu0 = toilet_top + U["above_toilet"]                               # низ ящика
    zu1 = z_top_lim - U["top_gap"]                                     # верх ящика (под поперечинами кровати)
    y_out = pil.YMin - U["door_gap"]                                   # наружная плоскость направляющих (|Y|) — в проёме дверей
    y_box = y_out - SL["T"]                                            # наружная грань ящика (|Y|) пассажирской стороны: между направляющими
    y_box_d = min(U.get("driver_y_box", y_box), y_box)                 # водительская сторона сужена — колодец над аркой (люки в кровати)
    xu0, xu1 = U["x_rear"], U["x_rear"] + SL["L"]
    put("Drawer_Upper", "Верхний ящик (фанера 1/2″): X %.0f..%.0f, Y %.0f..%.0f, ширина %.0f мм (%.1f″) — пассажирская сторона на весь проём дверей, "
        "водительская сужена до Y %.0f (колодец над аркой), высота %.0f мм (%.1f″), низ %.0f мм над полом (над туалетом: его верх %.0f); "
        "выезжает НАЗАД на SLIDEWAY" % (
            xu0, xu1, -y_box, y_box_d, y_box + y_box_d, (y_box + y_box_d) / 25.4, y_box_d, zu1 - zu0, (zu1 - zu0) / 25.4,
            zu0 - floor_top, toilet_top - floor_top),
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
            h = Part.makeBox(lt, yb_h - ya_h, cb.ZMin - (floor_top + 2.0), V(cb.XMin + 4.0, ya_h, floor_top + 2.0))
            put("Drawer_Leg_%s_%d" % (side, k), "Стойка направляющей %d (%s): квадратная труба 1″ от пола (над пластиной 2 мм) до поперечины "
                "кровати #%d, к ней — крепление угольником; направляющая — болтами на грани стойки (держит и боковую нагрузку в повороте)"
                % (k, side, k), h, COL_STRUT)
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
        tx1 = min(o.Shape.BoundBox.XMin for o in doc.Objects if o.Name.startswith("Toilet_") and o.isDerivedFrom("Part::Feature")
                  and not o.Shape.isNull()) - WR["gap_toilet"]
        ty0 = parts["Drawer_Lower"].BoundBox.YMax + WR["gap_drawer"]
        tx0 = tx1 - tl
        wg = doc.addObject("App::DocumentObjectGroup", "WaterTankRect")
        wg.Label = "Бак воды — Class A Customs %s %d gal (проект 2026-11-12)" % (WR["model"], WR["gal"])
        tank = Part.makeBox(tl, tw_, th_, V(tx0, ty0, floor_top))
        add_shape(doc, "WaterTank_Rect", "Бак воды Class A Customs %s, %d gal, %.1f×%.1f×%.1f″: сзади от туалета (X %.0f..%.0f), "
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
        obst2 = [(n_, s_) for n_, s_ in obst if not n_.startswith(("Shower", "Kitchen", "Toilet_Plate"))]
        dmin, nmin = min((tank.distToShape(s_)[0], n_) for n_, s_ in obst2 + [(n_, s_) for n_, s_ in parts.items()
                                                                           if n_.startswith("Drawer_") and "Wheel" not in n_ or "Wheel" in n_])
        checks.append(("бак воды: ближе всего «%s»" % nmin, dmin))
        water_summary = dict(model=WR["model"], gal=WR["gal"], x=(tx0, tx1), y=(ty0, ty0 + tw_), h=th_, dims=WR["dims"],
                             gap_up=zu0 - (floor_top + th_))
    drawers_summary = dict(
        upper=dict(x=(xu0, xu1), width=y_box + y_box_d, y_d=y_box_d, h=zu1 - zu0, z=(zu0 - floor_top, zu1 - floor_top), y_out=y_out, travel=tr_u,
                   vol=(xu1 - xu0 - 2 * tw) * (y_box + y_box_d - 2 * tw) * (zu1 - zu0 - tb) / 1e6, toilet_top=toilet_top - floor_top),
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
          "высота %.0f мм (%.1f″), от %.0f до %.0f мм над полом (верх туалета %.0f); объём ≈ %.0f л; ход %.0f мм" % (
              u["x"][0], u["x"][1], u["width"], u["width"] / 25.4, u["y_out"], u["y_d"], u["h"], u["h"] / 25.4, u["z"][0], u["z"][1],
              u["toilet_top"], u["vol"], u["travel"]))
    h = k.get("hatch")
    if h:
        print("  ЛЮКИ в настиле кровати у борта (Y %.0f..%.0f): №1 X %.0f..%.0f — Г-образный контейнер ≈ %.0f л (над баком от Z %.0f, над аркой — ступенька); "
              "№2 X %.0f..%.0f — сервисная зона на арке: насос, фильтр, аккумулятор давления (габариты — заглушки)" % (
                  h["y"][0], h["y"][1], h["x1"][0], h["x1"][1], h["bin_vol"], h["z_wide"], h["x2"][0], h["x2"][1]))
    w = k.get("water")
    if w:
        print("  БАК ВОДЫ Class A Customs %s (%d gal) %.1f×%.1f×%.1f″: X %.0f..%.0f (за туалетом), Y %.0f..%.0f (справа от нижнего ящика), "
              "высота %.0f мм, до верхнего ящика %.0f мм" % (w["model"], w["gal"], w["dims"][0] / 25.4, w["dims"][1] / 25.4,
                                                         w["dims"][2] / 25.4, w["x"][0], w["x"][1], w["y"][0], w["y"][1], w["h"], w["gap_up"]))
    print("  Зазоры/запасы: " + "; ".join("%s %.1f" % (n_, v_) for n_, v_ in k["checks"]))
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════════════════════════
# ЛЮКИ В НАСТИЛЕ КРОВАТИ над левой (водительской) аркой — 2026-11-12, Dimitri
# ═══════════════════════════════════════════════════════════════════════════════════════════════════
def hatches(S):
    """Колодец над аркой: два люка в настиле у борта. Люк 1 — Г-образный контейнер; люк 2 — насос + фильтр + аккумулятор на полке над аркой."""
    doc = S.doc
    H = HATCH_RECT
    k = S.drawers_summary
    S.hatch_summary = None
    if not H.get("enable") or not k:
        S.put(locals(), "hatch_summary")
        return
    bb = lambda n: doc.getObject(n).Shape.BoundBox
    g = doc.addObject("App::DocumentObjectGroup", "BedHatches")
    g.Label = "Люки в настиле кровати над левой аркой: контейнер + сервисная зона (насос, фильтр) (проект 2026-11-12)"
    parts = {}

    def put(name, label, shape, color, tr=0):
        add_shape(doc, name, label, shape, color=color, transparency=tr, group=g)
        parts[name] = shape
        return shape

    deck, mat = doc.getObject("BedDeck"), doc.getObject("BedMattress")
    zd0, zd1, zm1 = deck.Shape.BoundBox.ZMin, deck.Shape.BoundBox.ZMax, mat.Shape.BoundBox.ZMax
    cb = [bb("BedCross_%d" % i) for i in (1, 2, 3)]
    y0 = bb("Drawer_Leg_driver_1").YMax + H["gap_leg"]                  # от стойки направляющей верхнего ящика
    y1 = bb("BedSideRail_pY").YMin - H["gap_rail"]                     # до боковой рейки кровати
    arch, tank = bb("WheelArch_pY"), bb("WaterTank_Rect")
    z_deck_under = cb[0].ZMax                                          # поперечины = 807..848; настил над ними
    try:
        mcol = tuple(mat.ViewObject.ShapeColor[:3])
    except Exception:
        mcol = (0.92, 0.92, 0.88)
    try:
        dcol = tuple(deck.ViewObject.ShapeColor[:3])
    except Exception:
        dcol = (0.80, 0.66, 0.42)
    hx = []
    for n, (ca, cbb) in enumerate(((cb[0], cb[1]), (cb[1], cb[2])), 1):
        hx.append((n, ca.XMax + H["gap_beam"], cbb.XMin - H["gap_beam"]))
    # ── вырезы в настиле и матрасе, крышки и откидные секции матраса ──
    cut_all = None
    for n, xa, xb in hx:
        hole = Part.makeBox(xb - xa, y1 - y0, zm1 - zd0 + 2.0, V(xa, y0, zd0 - 1.0))
        cut_all = hole if cut_all is None else cut_all.fuse(hole)
    deck.Shape = deck.Shape.cut(cut_all)
    mat.Shape = mat.Shape.cut(cut_all)
    gl = H["gap_lid"]
    for n, xa, xb in hx:
        put("BedHatch_%d_Lid" % n, "Крышка люка %d в настиле: %.0f × %.0f мм, на рояльной петле у борта; к ней приклеена откидная секция матраса"
            % (n, xb - xa - 2 * gl, y1 - y0 - 2 * gl), Part.makeBox(xb - xa - 2 * gl, y1 - y0 - 2 * gl, zd1 - zd0, V(xa + gl, y0 + gl, zd0)), dcol)
        put("BedHatch_%d_Mattress" % n, "Откидная секция матраса люка %d (вместе с крышкой)" % n,
            Part.makeBox(xb - xa - 2 * gl, y1 - y0 - 2 * gl, zm1 - zd1, V(xa + gl, y0 + gl, zd1)), mcol)
        put("BedHatch_%d_Hinge" % n, "Рояльная петля люка %d (вдоль X, со стороны борта)" % n,
            Part.makeBox(xb - xa - 40.0, 14.0, 3.0, V(xa + 20.0, y1 - 14.0, zd1 - 1.5)), COL_STEEL)
    # ── люк 1: Г-образный контейнер ──
    n, xa, xb = hx[0]
    bw, bm = H["bin_wall"], H["bin_margin"]
    z_wide0 = tank.ZMax + H["bin_gap_tank"]                            # широкая часть — над баком
    z_top = z_deck_under + (zd0 - z_deck_under) - H["bin_gap_deck"]    # = низ настила − зазор
    z_step0 = arch.ZMax + H["bin_gap_arch"]                            # ступенька — над аркой
    x0_, x1_ = xa + bm, xb - bm
    y_arch = arch.YMin + 8.0                                           # ступенька — только над аркой
    yb0, yb1 = y0 + bm, y1 - bm
    outer = Part.makeBox(x1_ - x0_, yb1 - yb0, z_top - z_wide0, V(x0_, yb0, z_wide0)).fuse(
        Part.makeBox(x1_ - x0_, yb1 - y_arch, z_wide0 - z_step0 + 1.0, V(x0_, y_arch, z_step0)))
    inner = Part.makeBox(x1_ - x0_ - 2 * bw, yb1 - yb0 - 2 * bw, z_top - z_wide0 - bw + 1.0, V(x0_ + bw, yb0 + bw, z_wide0 + bw)).fuse(
        Part.makeBox(x1_ - x0_ - 2 * bw, yb1 - y_arch - 2 * bw, z_wide0 - z_step0 + 2 * bw, V(x0_ + bw, y_arch + bw, z_step0 + bw)))
    bin_ = outer.cut(inner).removeSplitter()
    put("Hatch_Bin", "Контейнер Г-образный (пластик 4 мм) в люке 1: %.0f × %.0f мм, глубина %.0f мм, ступенька над аркой; вынимается вверх; "
        "≈ %.0f л" % (x1_ - x0_, yb1 - yb0, z_top - z_step0, (inner.Volume / 1e6)), bin_, (0.35, 0.55, 0.75), 30)
    # ── люк 2: сервисная зона на арке ──
    n, xa, xb = hx[1]
    zs = arch.ZMax + H["shelf_gap_arch"]
    ys0 = arch.YMin + H["shelf_gap_face"]
    put("Service_Shelf", "Полка сервисной зоны на арке (фанера %.0f мм): X %.0f..%.0f, Y %.0f..%.0f, на крон-пластине арки" % (
        H["shelf_t"], xa + 5, xb - 5, ys0, y1 - 5),
        Part.makeBox(xb - xa - 10.0, y1 - 5.0 - ys0, H["shelf_t"], V(xa + 5, ys0, zs)), (0.80, 0.66, 0.42))
    zt = zs + H["shelf_t"]
    px, py, pz = H["pump"]
    xp = xa + 12.0
    yp = ys0 + 8.0
    put("Service_Pump", "Насос воды 12 В (заглушка %.0f × %.0f × %.0f мм ≈ Shurflo 4008, проверить по купленному)" % (px, py, pz),
        Part.makeBox(px, py, pz, V(xp, yp, zt)), (0.25, 0.45, 0.80))
    fd, fh = H["filter"]
    ad, ah = H["accum"]
    xf = xp + px + 8.0 + fd / 2.0
    put("Service_Filter", "Проточный фильтр воды (заглушка ⌀%.0f × %.0f мм), вертикально" % (fd, fh),
        Part.makeCylinder(fd / 2.0, fh, V(xf, yp + fd / 2.0 + 10.0, zt)), (0.85, 0.85, 0.75))
    xa2 = xf + fd / 2.0 + 8.0 + ad / 2.0
    put("Service_Accumulator", "Аккумулятор давления 0.75 л (заглушка ⌀%.0f × %.0f мм), вертикально" % (ad, ah),
        Part.makeCylinder(ad / 2.0, ah, V(xa2, yp + ad / 2.0 + 10.0, zt)), (0.20, 0.55, 0.30))
    # ── проверки: ближайшие детали к контейнеру и к оборудованию ──
    chk = []
    obstacles = {n_: doc.getObject(n_).Shape for n_ in ("WheelArch_pY", "WaterTank_Rect", "Drawer_Upper", "Drawer_Slide_driver",
                                                          "Drawer_Leg_driver_1", "Drawer_Leg_driver_2", "BedCross_1", "BedCross_2",
                                                          "BedCross_3", "BedSideRail_pY", "Shower_WallRear", "BedWallPanel")
                 if doc.getObject(n_) is not None}
    for tag, nm in (("контейнер", "Hatch_Bin"), ("насос", "Service_Pump"), ("фильтр", "Service_Filter"), ("аккумулятор", "Service_Accumulator"),
                    ("полка", "Service_Shelf")):
        dmin, nmin = min((parts[nm].distToShape(s_)[0], n_) for n_, s_ in obstacles.items()
                         if not (nm in ("Service_Shelf", "Service_Pump", "Service_Filter", "Service_Accumulator") and n_ == "WheelArch_pY"))
        chk.append(("люки: %s — ближе всего «%s»" % (tag, nmin), dmin))
    chk.append(("люк 1/2: запас по Y до стойки / до рейки", min(y0 - bb("Drawer_Leg_driver_1").YMax, bb("BedSideRail_pY").YMin - y1)))
    k["checks"].extend(chk)
    k["hatch"] = dict(x1=(hx[0][1], hx[0][2]), x2=(hx[1][1], hx[1][2]), y=(y0, y1), bin_vol=inner.Volume / 1e6, bin_x=(x0_, x1_),
                      bin_z=(z_step0, z_top), z_wide=z_wide0)
    S.hatch_summary = k["hatch"]
    S.put(locals(), "hatch_summary")
