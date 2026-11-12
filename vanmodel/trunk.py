# -*- coding: utf-8 -*-
"""Багажник под кроватью: 2 выдвижных ящика на SLIDEWAY, полка 2-го этажа, стойки хребта."""

import FreeCAD as App
import Part

from .params import TRUNK_SHELF, WATER_VARIANT
from .common import COL_STRUT, add_shape

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def trunk(S):
    """Багажник под кроватью: 2 выдвижных ящика на SLIDEWAY, полка 2-го этажа, хребет."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, doc, dx0, dx1, floor_top, sd, sw = S.B, S.doc, S.dx0, S.dx1, S.floor_top, S.sd, S.sw
    # ═══════ БАГАЖНИК — 2 выдвижных ящика на SLIDEWAY + полка + хребет посередине (2026-11-08, Dimitri) ═══════
    trunk_summary = None
    trunk_boxes = {}
    TS = TRUNK_SHELF
    tank_o = doc.getObject("WaterTank_T4320") if WATER_VARIANT == "T4320_floor" else None
    if TS.get("enable") and doc.getObject("BankPost_P3") is not None and B.get("enable") and tank_o is not None:
        tg = doc.addObject("App::DocumentObjectGroup", "TrunkShelf")
        tg.Label = "Багажник — 2 выдвижных ящика на SLIDEWAY + полка над баком + хребет (проект 2026-11-08)"
        tparts = {}

        def tput(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr, group=tg)
            tparts[name] = shape
            return shape

        def mind(shapes, pref):
            ss = [o.Shape for o in doc.Objects if o.Name.startswith(pref) and o.isDerivedFrom("Part::Feature")
                  and not o.Shape.isNull() and o.Shape.Solids]
            return min(a.distToShape(b)[0] for a in shapes for b in ss) if ss else None
        SL, TR = TS["slide"], TS["tray"]
        tb = tank_o.Shape.BoundBox
        p3b_ = doc.getObject("BankPost_P3").Shape.BoundBox
        rbi = doc.getObject("BankRail_Inner").Shape.BoundBox
        ysh = TS.get("p3m_shim", 0.0)
        # ножка P3m (как P3) — X между передним бруском бака и туалетом (как раньше): держит направляющую, бортик у B4
        cfr = doc.getObject("TankFloor_Cleat_Front").Shape.BoundBox
        x3 = cfr.XMax + sw / 2.0
        tput("Trunk2_PlateP3m", "Пластина под P3m (как под P3)", Part.makeBox(127.0, 102.0, 3.0, App.Vector(
            x3 - 63.5, rbi.YMax + ysh, floor_top)), COL_STRUT)
        tput("Trunk2_PostP3m", "Ножка P3m (как P3): спинка к спинке с рейкой батарей (проставка %.0f мм — арка), "
             "бортик у B4; на её пазу — пассажирская направляющая поддона" % ysh,
             Part.makeBox(sw, sd, p3b_.ZMax - (floor_top + 3.0), App.Vector(x3 - sw / 2.0, rbi.YMax + ysh,
                                                                           floor_top + 3.0)), COL_STRUT)
        tput("Trunk2_PostP3mBolt", "Болт 3/8″: P3m ↔ рейка со стороны прохода (через овалы спинок + проставка)",
             Part.makeCylinder(4.75, 2 * sd + ysh + 16.0, App.Vector(x3, rbi.YMin - 8.0, (rbi.ZMin + rbi.ZMax) / 2.0),
                               App.Vector(0, 1, 0)), (0.85, 0.85, 0.20))
        # высоты: ящики 2-го этажа — над баком/туалетом/локером; верх — под поперечинами кровати
        lk_ = doc.getObject("Propane_Locker")
        to_ = doc.getObject("Toilet_Camco")
        lkb = lk_.Shape.BoundBox
        # 2026-11-09: ящики — над баком/локером (как были); туалет на платформе стал выше → над ним поднимаем только полку
        z_under = max([tb.ZMax] + [o.Shape.BoundBox.ZMax for o in (lk_,) if o is not None])
        z_under_shelf = max([z_under] + [o.Shape.BoundBox.ZMax for o in doc.Objects if o.Name.startswith("Toilet_")
                                         and o.isDerivedFrom("Part::Feature") and not o.Shape.isNull()])
        z_t0 = z_under + TR["z_gap"]                                 # низ ящиков 2-го этажа
        z_top = doc.getObject("BedCross_1").Shape.BoundBox.ZMin - TR["top_gap"]
        z_s0 = z_t0 + TR["base"] + 8.0                               # низ направляющей (на боковине ящика)
        z_s1 = z_s0 + SL["H"]
        zr0 = (z_s0 + z_s1) / 2.0 - sw / 2.0                         # рейки под направляющими 2-го этажа
        # плоскость пассажирских направляющих — паз P3m (P3 — с проставкой 4 мм); водительская — зеркально
        y_p = rbi.YMax + ysh + sd
        rp_ = doc.getObject("Pillar_Rear_pY").Shape.BoundBox
        xs0, xs1 = TS["x_rear"], TS["x_rear"] + SL["L"]
        assert -y_p <= rp_.YMin - TS["opening_gap"], "направляющие шире проёма задних дверей"
        # ── ХРЕБЕТ посередине: 2 стойки под поперечинами кровати #1 и #2 ──
        # Dimitri 2026-11-08: «ножку Post3W — справа от бака и справа от баллона + ещё одну такую же». Справа от
        # локера пропана — нельзя: его дверца смотрит в багажник (X 980..1310) и открывается туда; а впереди локера
        # стойка вылезла бы за край щита. Поэтому стойки — в X поперечин кровати #1 (справа от бака) и #2 (между баком
        # и локером), вверху упираются в поперечины (подпирают их посередине, как Post3W).
        # 2026-11-08 (ночь, Dimitri): задний ящик 2-го этажа и вся его обвязка (рейка над баком, поперечины, подвес,
        # направляющие #3/#4, рейки хребта 2-го этажа) — убраны: вместо них ПОЛКА из фанеры на уровне верха бака и
        # баллона на 3 опорах (стойки хребта 1, 2 и стойка кровати pY rear; 4-ю Dimitri решит на месте). Направляющая
        # переднего ящика — прямо на пазах стоек хребта, как на P3.
        SP, SH = TS["spine"], TS["shelf"]
        yc1 = lkb.YMin - SP["locker_gap"]                            # водительская грань стоек хребта (паз)
        yc0 = yc1 - sd                                               # пассажирская грань (спинка, к ящикам)
        y_scp = (yc0 - SL["T"], yc0)                                 # направляющая переднего ящика — на пазах стоек
        y_rp = (yc0 - sd, yc0)                                       # рейка хребта 1-го этажа — на пазах стоек
        posts_x = []
        for i_, cn in enumerate(("BedCross_1", "BedCross_2")):
            cb = doc.getObject(cn).Shape.BoundBox
            xc_ = (cb.XMin + cb.XMax) / 2.0
            posts_x.append(xc_)
            tput("Trunk2_SpinePlate_%d" % (i_ + 1), "Пластина под стойку хребта %d (как под P3), 4 болта в пол" % (i_ + 1),
                 Part.makeBox(76.0, 127.0, 3.0, App.Vector(xc_ - 38.0, (yc0 + yc1) / 2.0 - 63.5, floor_top)), COL_STRUT)
            tput("Trunk2_SpinePost_%d" % (i_ + 1), "Стойка хребта %d strut L=%.0f — посередине, от пола до поперечины "
                 "кровати #%d (упирается, подпирает её посередине); спинка (овалы) — к ящикам: направляющие на болтах через "
                 "овалы; паз — к полке (опора полки на гайке-канал)" % (i_ + 1, cb.ZMin - (floor_top + 3.0), i_ + 1),
                 Part.makeBox(sw, sd, cb.ZMin - (floor_top + 3.0), App.Vector(xc_ - sw / 2.0, yc0, floor_top + 3.0)),
                 COL_STRUT)
        # 1-й этаж: ящик на направляющих 36″ (44″ не влезают: впереди — дверца локера пропана)
        S1, BX = TS["slide1"], TS.get("boxes", {})
        b1 = BX["floor1"]
        z10, z11 = floor_top + b1["z_gap"], z_t0 - b1["top_gap"]
        z1s0 = z10 + b1["base"] + 8.0
        zr1 = z1s0 + S1["H"] / 2.0 - sw / 2.0
        x1s0, x1s1 = TS["x_rear"], TS["x_rear"] + S1["L"]
        y_s1 = y_scp                                                 # 2026-11-08 (Dimitri): рейка хребта 1-го этажа не нужна —
                                                                     # направляющая прямо на пазах стоек хребта, как на P3
        # направляющие
        for nm_, lab, x0_, ln_, y0_, z0_, ttl in (
                ("Trunk2_SlidePass", "переднего ящика (пасс.), на пазах P3 и P3m", xs0, SL["L"], y_p, z_s0, SL["title"]),
                ("Trunk2_SlideSpine", "переднего ящика, на спинке стоек хребта (болты через овалы)", xs0, SL["L"], y_scp[0], z_s0,
                 SL["title"]),
                ("Trunk1_SlidePass", "ящика 1-го этажа (пасс.), на пазах P3 и P3m", x1s0, S1["L"], y_p, z1s0, S1["title"]),
                ("Trunk1_SlideSpine", "ящика 1-го этажа, на спинке стоек хребта (болты через овалы)", x1s0, S1["L"], y_s1[0], z1s0,
                 S1["title"])):
            tput(nm_, "Направляющая %s — %s" % (ttl, lab),
                 Part.makeBox(ln_, SL["T"], SL["H"], App.Vector(x0_, y0_, z0_)), (0.80, 0.82, 0.86))
        for nm_, z0_ in (("Trunk2_P3Shim", z_s0), ("Trunk1_P3Shim", z1s0)):
            tput(nm_, "Проставка 4 мм под направляющую на P3 (P3 и P3m — в одной плоскости)",
                 Part.makeBox(p3b_.XLength, TS.get("p3_shim", 4.0), SL["H"], App.Vector(p3b_.XMin, p3b_.YMax, z0_)),
                 (0.25, 0.25, 0.25))
        x_fr = dx1 - TS["front_gap"]                                 # передний торец переднего ящика (закрыт)
        # ── ПОЛКА 2-го этажа (водит. половина): фанера на уровне верха бака и баллона ──
        bpr = doc.getObject("BedPost_pY_rear").Shape.BoundBox
        z_p0 = max(z_t0, z_under_shelf + TR["z_gap"])               # низ фанеры: над баком/локером/туалетом + 10 мм
        z_p1 = z_p0 + SH["th"]
        px0, px1, py0, py1 = rp_.XMax + SH["pillar_gap"], x_fr, yc1, bpr.YMin
        ply = Part.makeBox(px1 - px0, py1 - py0, SH["th"], App.Vector(px0, py0, z_p0))
        # 2026-11-08 (Dimitri): полку — вперёд за край щита до нижней шторки душа и до ребра стенки душа по борту
        cul = doc.getObject("Shower_CurtainLower")
        swb = doc.getObject("Shower_WallBack")
        outline = [(px0, py0), (px1, py0), (px1, py1), (px0, py1)]
        if cul is not None and swb is not None:
            cb_, wb_ = cul.Shape.BoundBox, swb.Shape.BoundBox
            px1 = cb_.XMin - SH["curtain_gap"]                       # до нижней шторки
            xw, yw = wb_.XMin, wb_.YMin                             # ребро стенки душа по борту
            # прямой участок основной шторки (вдоль X у прохода) — полка за ним, шторка висит мимо её кромки
            ye0 = py0
            scu = doc.getObject("Shower_Curtain")
            if scu is not None:
                cc_ = scu.Shape.common(Part.makeBox(px1 - xw, yw - py0, SH["th"], App.Vector(xw, py0, z_p0)))
                if not cc_.isNull() and cc_.Volume > 1.0:
                    ye0 = cc_.BoundBox.YMax + SH["curtain_gap"]
            ply = Part.makeBox(xw - px0, py1 - py0, SH["th"], App.Vector(px0, py0, z_p0)).fuse(
                Part.makeBox(px1 - xw, yw - ye0, SH["th"], App.Vector(xw, ye0, z_p0))).removeSplitter()
            outline = [(px0, py0), (xw, py0), (xw, ye0), (px1, ye0), (px1, yw), (xw, yw), (xw, py1), (px0, py1)]
        dpf = doc.getObject("DPillarFace_pY_ref")
        notch = None
        if dpf is not None:                                         # вырез под D-стойку
            db_ = dpf.Shape.BoundBox
            notch = (px0, db_.XMax + SH["pillar_gap"], db_.YMin - SH["pillar_gap"], py1)
            outline = outline[:-1] + [(notch[1], py1), (notch[1], notch[2]), (px0, notch[2])]
            ply = ply.cut(Part.makeBox(notch[1] - notch[0] + 1.0, notch[3] - notch[2] + 1.0, SH["th"] + 2.0,
                                       App.Vector(notch[0] - 1.0, notch[2], z_p0 - 1.0)))
        gas_hole = None
        slab = Part.makeBox(4000.0, 4000.0, SH["th"] + 2.0, App.Vector(-500.0, -2000.0, z_p0 - 1.0))
        gs_ = [doc.getObject(n_).Shape.common(slab) for n_ in ("Gas_Line", "Gas_Bulkhead") if doc.getObject(n_) is not None]
        gs_ = [s_ for s_ in gs_ if not s_.isNull() and s_.Volume > 1.0]
        if gs_:                                                     # отверстие под газовую трубку (с зазором)
            gb_ = gs_[0].BoundBox
            for s_ in gs_[1:]:
                gb_.add(s_.BoundBox)
            gg = SH["gas_gap"]
            gas_hole = (gb_.XMin - gg, gb_.XMax + gg, gb_.YMin - gg, gb_.YMax + gg)
            ply = ply.cut(Part.makeBox(gb_.XLength + 2 * gg, gb_.YLength + 2 * gg, SH["th"] + 2.0,
                                       App.Vector(gas_hole[0], gas_hole[2], z_p0 - 1.0)))
        tput("Trunk2_Shelf", "Полка 2-го этажа — фанера %.2f″ %.0f×%.0f мм над баком, туалетом и локером (водит. половина), "
             "вырез под D-стойку, отверстие под газовую трубку; опоры: стойки хребта 1, 2 и стойка кровати pY rear "
             "(4-й угол — по месту: арка или борт)" % (SH["th"] / 25.4, px1 - px0, py1 - py0), ply, (0.86, 0.72, 0.52))
        cl_L = SH["cleat_L"]
        for nm_, xc_, y0_, lab in (("Trunk2_ShelfCleat_S1", posts_x[0], yc1, "стойке хребта 1"),
                                   ("Trunk2_ShelfCleat_S2", posts_x[1], yc1, "стойке хребта 2"),
                                   ("Trunk2_ShelfCleat_W", (bpr.XMin + bpr.XMax) / 2.0, bpr.YMin - sd,
                                    "стойке кровати pY rear")):
            tput(nm_, "Опора полки strut L=%.0f (6″) — %s, болт 3/8″; полка на саморезах сверху" % (
                cl_L, ("спинкой к пазу: " + lab + " (гайка-канал, любая высота)") if nm_ != "Trunk2_ShelfCleat_W" else
                ("спинка к спинке к " + lab + " (овал — по месту/сверлить)")),
                 Part.makeBox(cl_L, sd, sw, App.Vector(xc_ - cl_L / 2.0, y0_, z_p0 - sw)), COL_STRUT)
            yb_ = (y0_ - sd - 8.0) if nm_ != "Trunk2_ShelfCleat_W" else (y0_ - 8.0)
            tput(nm_.replace("Cleat", "Bolt"), "Болт 3/8″: опора полки ↔ %s" % lab,
                 Part.makeCylinder(4.75, 2 * sd + 16.0, App.Vector(xc_, yb_, z_p0 - sw / 2.0), App.Vector(0, 1, 0)),
                 (0.85, 0.85, 0.20))
        shelf = dict(x=(px0, px1), y=(py0, py1), z=(z_p0, z_p1), th=SH["th"], notch=notch, gas_hole=gas_hole, outline=outline,
                     area_ft2=ply.Area / 2.0 / 92903.0,
                     over_cross=doc.getObject("BedCross_1").Shape.BoundBox.ZMin - z_p1,
                     over_deck=doc.getObject("BedDeck").Shape.BoundBox.ZMin - z_p1,
                     supports=[(posts_x[0], yc1), (posts_x[1], yc1), ((bpr.XMin + bpr.XMax) / 2.0, bpr.YMin)])

        def drawer(x0, y0, z0, lx, ly, lz, w, base):
            return Part.makeBox(lx, ly, lz, App.Vector(x0, y0, z0)).cut(
                Part.makeBox(lx - 2 * w, ly - 2 * w, lz, App.Vector(x0 + w, y0 + w, z0 + base)))
        dr = {}
        for key, nm_, x0_, x1_, y0_, y1_, za, zb, out, lab in (
                ("fwd", "Trunk2_TrayFwd", xs0, x_fr, y_p + SL["T"], y_scp[0], z_t0, z_top, SL["L"],
                 "2-й этаж, пасс. половина — выдвигается ВПЕРЁД, в салон"),
                ("floor1", "Trunk1_Drawer", x1s0, x1s1, y_p + SL["T"], y_s1[0], z10, z11, -S1["L"],
                 "1-й этаж — выдвигается НАЗАД, в задние двери")):
            dr[key] = dict(x=(x0_, x1_), y=(y0_, y1_), z=(za, zb), out=out,
                           inside=((x1_ - x0_ - 2 * TR["wall"]) / 25.4, (y1_ - y0_ - 2 * TR["wall"]) / 25.4,
                                   (zb - za - TR["base"]) / 25.4))
            for pos, dx_, tr_, lab2 in (("", 0.0, 0, "закрыт (по-походному)"),
                                        ("_Out", out, 80, "выдвинут целиком")):
                tput(nm_ + pos, "Ящик %.1f×%.1f×%.1f″ (фанера 1/2″) — %s; %s" % (
                    (x1_ - x0_) / 25.4, (y1_ - y0_) / 25.4, (zb - za) / 25.4, lab, lab2),
                     drawer(x0_ + dx_, y0_, za, x1_ - x0_, y1_ - y0_, zb - za, TR["wall"], TR["base"]),
                     (0.78, 0.60, 0.40) if key != "floor1" else (0.80, 0.66, 0.46), tr_)
        trunk_boxes = dr
        # проверки
        tch = []
        for nm_ in sorted(tparts):
            if nm_.endswith(("_Out", "_Front")) or "Caster" in nm_ or "Latch" in nm_ or "Bolt" in nm_:
                continue
            for lab, pref in (("бак", "WaterTank_"), ("ремни бака", "TankFloor_Strap"), ("батареи", "Battery_"),
                              ("поперечины кровати", "BedCross_"), ("туалет", "Toilet_"), ("локер", "Propane_Locker"),
                              ("газ", "Gas_"), ("насос", "Water_Pump"), ("штуцеры бака", "TankFloor_Fitting"),
                              ("арка", "WheelArch_"), ("стойки проёма", "Pillar_Rear"), ("D-стойка", "DPillarFace")):
                v = mind([tparts[nm_]], pref)
                if v is not None and v < 25:
                    tch.append(("%s ↔ %s" % (nm_.replace("Trunk2_", "").replace("Trunk1_", ""), lab), v))
        tch.append(("за край щита (макс X, закрыто; кроме полки — её Dimitri довёл до шторки душа)",
                    max(tparts[n_].BoundBox.XMax for n_ in tparts if not n_.endswith("_Out")
                        and not n_.startswith("Trunk2_Shelf")) - dx1))
        for lab, pref in (("душ", "Shower_"), ("стойки кровати", "BedPost_")):
            v = mind([tparts["Trunk2_Shelf"]], pref)
            if v is not None:
                tch.append(("полка ↔ %s" % lab, v))
        # дверца локера пропана (в багажник, X %.0f..%.0f) открывается на 90° — в зоне ничего неподвижного
        ldb = doc.getObject("Propane_LockerDoor").Shape.BoundBox
        swing = Part.makeBox(ldb.XLength, ldb.XLength, ldb.ZLength, App.Vector(ldb.XMin, ldb.YMin - ldb.XLength, ldb.ZMin))
        fixed = [tparts[n_] for n_ in tparts if not n_.startswith(("Trunk2_Tray", "Trunk1_Drawer"))]
        tch.append(("дверца локера (90°) ↔ неподвижное", min(swing.distToShape(f_)[0] for f_ in fixed)))
        # передний ящик, выдвинутый в салон — мимо душа, кухни, электрики
        fo_ = [tparts["Trunk2_TrayFwd_Out"]]
        for lab, pref in (("душ", "Shower_"), ("кухня", "Kitchen_"), ("P3f", "BankPost_P3f"), ("электрика", "Elec_"),
                          ("стойки кровати", "BedPost_"), ("поперечины кровати", "BedCross_")):
            v = mind(fo_, pref)
            if v is not None:
                tch.append(("передний ящик выдвинут ↔ %s" % lab, v))
        y_out = max(abs(tparts["Trunk1_Drawer_Out"].BoundBox.YMin), abs(tparts["Trunk1_Drawer_Out"].BoundBox.YMax))
        tch.append(("ящик 1-го этажа ↔ проём дверей (по Y)", rp_.YMin - y_out))
        trunk_summary = dict(floor_top=floor_top, checks=tch, h1_under=z_t0 - floor_top, x_rear=dx0, x_deck=dx1,
                             opening=rp_.YMin, x_p3m=x3, posts_x=posts_x, y_spine=(y_scp[0], yc1),
                             slide_z=(z_s0, z_s1), slide1_z=(z1s0, z1s0 + S1["H"]), drawers=trunk_boxes, shelf=shelf,
                             locker_door=(ldb.XMin, ldb.XMax, ldb.YMin), slide_L=SL["L"], slide1_L=S1["L"])
        TRUNK_SHELF["_summary"] = {k: v for k, v in trunk_summary.items() if k != "checks"}

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "trunk_summary")
