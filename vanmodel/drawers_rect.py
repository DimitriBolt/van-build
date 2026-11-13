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
from .params_rect import DRAWERS_RECT

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
    y_box = y_out - SL["T"]                                            # наружная грань ящика (|Y|): между направляющими
    xu0, xu1 = U["x_rear"], U["x_rear"] + SL["L"]
    put("Drawer_Upper", "Верхний ящик (фанера 1/2″): X %.0f..%.0f, ширина %.0f мм (%.1f″) — на всю ширину проёма задних дверей, "
        "высота %.0f мм (%.1f″), низ %.0f мм над полом (над туалетом: его верх %.0f); выезжает НАЗАД на SLIDEWAY" % (
            xu0, xu1, 2 * y_box, 2 * y_box / 25.4, zu1 - zu0, (zu1 - zu0) / 25.4, zu0 - floor_top, toilet_top - floor_top),
        tray(xu0, xu1, -y_box, y_box, zu0, zu1), COL_PLY)
    zs0 = zu0 + (zu1 - zu0 - SL["H"]) / 2.0                            # направляющие — на середине высоты стенки
    cb1, cb2 = bb("BedCross_1"), bb("BedCross_2")
    hang = []
    for sgn, side in ((1, "driver"), (-1, "passenger")):
        ya, yb = (y_box, y_out) if sgn > 0 else (-y_out, -y_box)
        put("Drawer_Slide_%s" % side, "Направляющая %s (%s): рабочая часть на ящике, неподвижная — на подвесах" % (SL["title"], side),
            Part.makeBox(SL["L"], SL["T"], SL["H"], V(xu0, ya, zs0)), COL_STEEL)
        for k, cb in ((1, cb1), (2, cb2)):                             # подвесы strut: от поперечины кровати вниз
            xc = (cb.XMin + cb.XMax) / 2.0
            ya_h, yb_h = (y_out, y_out + sd) if sgn > 0 else (-y_out - sd, -y_out)
            h = Part.makeBox(sw, sd, cb.ZMin - zs0, V(xc - sw / 2.0, ya_h, zs0))
            put("Drawer_Hanger_%s_%d" % (side, k), "Подвес направляющей %d (%s): strut от поперечины кровати #%d вниз, болтами "
                "через овалы; направляющая — на его грани" % (k, side, k), h, COL_STRUT)
            hang.append(h)
    put("Drawer_Upper_Handle", "Ручка верхнего ящика (задний торец)",
        Part.makeCylinder(10.0, 300.0, V(xu0 - 25.0, -150.0, zu1 - 60.0), V(0, 1, 0)), COL_STEEL)

    # ═══════ НИЖНИЙ ящик: на колёсиках, вперёд в салон ═══════
    CA = L["caster"]
    y_pass = p3.YMax + L["side_gap"]                                   # пассажирская грань (|Y| макс. к борту)
    y_drv = pan.YMin - L["side_gap"]                                   # водительская грань — до края поддона
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

    up = [parts[n] for n in parts if n.startswith(("Drawer_Upper", "Drawer_Slide")) or n.startswith("Drawer_Hanger")]
    lo = [parts[n] for n in parts if n.startswith(("Drawer_Lower", "Drawer_Wheel"))]
    own_hang = ("Drawer_Hanger",)
    # путь верхнего ящика: объём ящика + направляющих, протянутый назад на ход (без подвесов — они не движутся)
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
    dd, nn = nearest(Part.makeCompound([parts[n] for n in parts if n.startswith(("Drawer_Slide", "Drawer_Hanger"))]), ("BedCross",))
    checks.append(("направляющие и подвесы (кроме креплений к поперечинам): ближе всего «%s»" % nn, dd))
    plates = [s_ for n_, s_ in obst if n_.startswith("BankPostPlate")]
    pw = Part.makeCompound([parts[n] for n in parts if n.startswith("Drawer_Wheel")])
    checks.append(("колёсики нижнего ящика переезжают пластины 2 мм под ножками батарей (P3 и P3f) — касание: %d шт" % len(plates),
                   min([pw.distToShape(p_)[0] for p_ in plates] or [0.0])))
    dd, nn = nearest(Part.makeCompound([parts[n] for n in parts if n.startswith("Drawer_Wheel")]), ())
    checks.append(("колёсики: ближе всего «%s»" % nn, dd))
    checks.append(("верхний ящик ↔ нижний ящик (зазор по высоте)", zu0 - zl1))
    checks.append(("верх верхнего ящика ↔ поперечины кровати", z_top_lim - zu1))
    checks.append(("нижний ящик: запас до края поддона / до ножки P3", min(pan.YMin - y_drv, y_pass - p3.YMax)))
    drawers_summary = dict(
        upper=dict(x=(xu0, xu1), width=2 * y_box, h=zu1 - zu0, z=(zu0 - floor_top, zu1 - floor_top), y_out=y_out, travel=tr_u,
                   vol=(xu1 - xu0 - 2 * tw) * (2 * y_box - 2 * tw) * (zu1 - zu0 - tb) / 1e6, toilet_top=toilet_top - floor_top),
        lower=dict(x=(xl0, xl1), y=(y_pass, y_drv), width=y_drv - y_pass, h=zl1 - zl0, z=(zl0 - floor_top, zl1 - floor_top),
                   travel=tr_l, vol=(xl1 - xl0 - 2 * tw) * (y_drv - y_pass - 2 * tw) * (zl1 - zl0 - tb) / 1e6),
        checks=checks, floor_top=floor_top)
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
    print("  ВЕРХНИЙ (SLIDEWAY 44″, НАЗАД): X %.0f..%.0f, ширина %.0f мм (%.1f″) — на весь проём задних дверей (направляющие на |Y|=%.0f), "
          "высота %.0f мм (%.1f″), от %.0f до %.0f мм над полом (верх туалета %.0f); объём ≈ %.0f л; ход %.0f мм" % (
              u["x"][0], u["x"][1], u["width"], u["width"] / 25.4, u["y_out"], u["h"], u["h"] / 25.4, u["z"][0], u["z"][1],
              u["toilet_top"], u["vol"], u["travel"]))
    print("  Зазоры/запасы: " + "; ".join("%s %.1f" % (n_, v_) for n_, v_ in k["checks"]))
    print("=" * 70)
