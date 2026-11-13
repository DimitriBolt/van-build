# -*- coding: utf-8 -*-
"""Батареи (пассажирский борт, −Y): этажерка на 4 батареи + электрика; ранние варианты этажерок сохранены."""

import math

import FreeCAD as App
import Part

from .anchors import ANCHORS, KERF
from .params import BATTERY_RACK, ELECTRICAL
from .common import COL_BATTERY, COL_BOLT, COL_PLY, COL_STRUT, COL_WOOD, add_box, add_shape, add_sphere
from .scan import y_at_z
from .strut import STRUT
from .vslot import vslot_2020, vslot_x, vslot_y, drill_y

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def racks(S):
    """Этажерки под батареи «rear» / «front» (ранний вариант; включается в BATTERY_RACK)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, P, W, arch_a_lin, arch_shapes, arch_ywall = S.B, S.P, S.W, S.arch_a_lin, S.arch_shapes, S.arch_ywall
    cutlist, doc, dp_box_x, dp_shapes, dx1 = S.cutlist, S.doc, S.dp_box_x, S.dp_shapes, S.dx1
    floor_top, post_in, post_out, rail_in, sd = S.floor_top, S.post_in, S.post_out, S.rail_in, S.sd
    slider_x0, sw, xf, xr, ybase, z_bolt = S.slider_x0, S.sw, S.xf, S.xr, S.ybase, S.z_bolt
    z_rail_top = S.z_rail_top
    # ═══════ ЭТАЖЕРКИ ПОД БАТАРЕИ (борт −Y): «rear» — D-стойка ↔ арка, «front» — арка ↔ сдвижная ═══════
    rack_summary = []
    rack_geo = {}
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
            ties = R.get("top_ties")
            if isinstance(ties, dict):
                ties = ties.get(stack)
            if ties == "bed":                          # стяжки = поперечины кровати (под настилом)
                z_tie0, z_tie1 = z_rail_top - sw, z_rail_top
            else:                                      # отдельные стяжки над верхней батареей
                z_tie0 = z_b2_top + R["gap_above_b2"]
                z_tie1 = z_tie0 + sw
            z_p34_top = z_tie1 if ties else z_b2_top + R["post_above_b2"]
            rk_g = doc.addObject("App::DocumentObjectGroup", "BatteryRack" + sfx)
            rk_g.Label = ("Этажерка: 2 батареи Buknuwo 150Ah, %s (пассажирский борт), %.2f″ вдоль борта"
                          % ("арка ↔ сдвижная дверь" if front else "D-стойка ↔ арка", bx / 25.4))
            shapes = {}

            def rk_box(name, label, dims, base, color, tr=0):
                add_box(doc, name + sfx, label, dims, base, color=color, transparency=tr, group=rk_g)
                shapes[name] = Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base))
                return shapes[name]

            # батареи: задний блок — задом в короб D-стойки (грань короба скошена назад к центру → ближе всего
            # она у грани батарей к борту), передний — задом в передний край арки
            if front:
                X0 = W["center_x"] + a_at_post + R["arch_gap"]
                p1x = xf                                   # существующая передняя стойка кровати
            else:
                X0 = dp_box_x(arch_ywall - post_in) + R["dpillar_gap"]
                p1x = xr                                   # существующая задняя стойка кровати
            X1 = X0 + bx
            # P2 — новая стойка у борта на том конце батарей, что дальше от P1 (центр батарей — между
            # P1 и P2); P3/P4 — со стороны салона напротив P1/P2: две поперечные рамы «стойка у борта —
            # рейка полки — стойка в салон — стяжка»
            if p1x <= (X0 + X1) / 2.0:
                p2x1 = X1 - R["p2_front_inset"]; p2x0 = p2x1 - sw
                p2_plate_x0 = p2x0 if front else p2x1 - p2px          # пластина P2 — от пластины P1 / от арки
            else:
                p2x0 = X0 + R["p2_front_inset"]; p2x1 = p2x0 + sw
                p2_plate_x0 = p2x0
            p3x0, p4x0 = p1x - sw / 2.0, p2x0
            frames = (("P1", p1x), ("P2", (p2x0 + p2x1) / 2.0))     # X центров рам

            # батареи
            bat1 = rk_box("Battery_Lower", "Батарея нижняя Buknuwo 12.8V 150Ah (%.2f″ вдоль борта)" % (bx / 25.4),
                          (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b1), COL_BATTERY)
            if R.get("upper"):
                rk_box("Battery_Upper", "Батарея верхняя Buknuwo 12.8V 150Ah (на полке)",
                       (bx, by, bz), (X0, ybase(ps, y_wall_side, by), z_b2), COL_BATTERY)

            # P2 — новая стойка у борта, как стойки кровати
            on_rail = p2x1 > xr - sw / 2.0 and p2x0 < xf + sw / 2.0         # в пределах продольной рейки
            p2_len = B["post_len"] if on_rail else (z_bolt + 50.0) - (floor_top + pt)
            rk_box("RackPostPlate_P2", "Пластина под новой стойкой P2 — Simpson TP15 1-13/16×5″",
                   (p2px, p2py, p2pt), (p2_plate_x0, ybase(ps, post_out, p2py), floor_top), COL_STRUT)
            rk_box("BedPost_nY_rackP2", "Стойка P2 (новая, как стойки кровати; L=%.0f) — %s" % (
                       p2_len, "болт к продольной рейке" if on_rail else "впереди рейки кровати: только в кузов"),
                   (sw, sd, p2_len), (p2x0, ybase(ps, post_out, sd), floor_top + pt), COL_STRUT)
            if on_rail:
                add_sphere(doc, "RackP2_RailBolt" + sfx, "Болт P2 ↔ продольная рейка кровати", 9,
                           ((p2x0 + p2x1) / 2.0, ps * post_in, z_rail_top - sw / 2.0), color=COL_BOLT, group=rk_g)
            if R.get("p2_body_bolt"):
                add_sphere(doc, "RackP2_BodyBolt" + sfx,
                           "Болт P2 в раму кузова M6 (новая резьба) на высоте болтов стоек кровати, Z=%.0f" % z_bolt,
                           9, ((p2x0 + p2x1) / 2.0, ps * (post_out + B["post_wall_gap"] / 2.0), z_bolt),
                           color=COL_BOLT, group=rk_g)

            # полка: 2 рейки поперёк фургона — по X стоек P1/P3 и P2/P4 (на болтах к ним) + фанера
            for nm, xc in (("Rear", min(f[1] for f in frames)), ("Front", max(f[1] for f in frames))):
                rk_box("RackShelfRail_%s" % nm, "Рейка полки %s strut, L=%.0f (между стойками у борта и в салон)" % (
                           nm, by + sd),
                       (sd, by + sd, sw), (xc - sd / 2.0, ybase(ps, y_wall_side, by + sd), z_rail0), COL_STRUT)
            rk_box("RackShelfPlate", "Полка — фанера 1/2″ %.0f×%.0f" % (bx, by),
                   (bx, by, R["shelf_th"]), (X0, ybase(ps, y_wall_side, by), z_rail1), COL_PLY, tr=10)
            # упор верхней батареи вперёд (по ходу машины, +X)
            if R.get("front_stop"):
                st, sh = R["front_stop"]
                rk_box("RackShelfFrontStop", "Упор-уголок по переднему краю полки (держит верхнюю батарею вперёд)",
                       (st, by, (z_b2 + sh) - z_rail0), (X1, ybase(ps, y_wall_side, by), z_rail0), COL_STRUT)
            # упор нижней батареи вперёд
            if R.get("lower_front_stop"):
                lh, lz = R["lower_front_stop"]
                gap_a = W["center_x"] - arch_a_lin(arch_ywall - post_in) - X1 if not front else slider_x0 - X1
                if gap_a >= sd + 5.0:          # strut поперёк
                    rk_box("RackLowerFrontStop", "Упор нижней батареи вперёд: strut поперёк, уголками к P2/P4",
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

            # P3/P4 — стойки со стороны салона напротив P1/P2
            for nm, x0 in (("P3", p3x0), ("P4", p4x0)):
                rk_box("RackPostPlate_%s" % nm, "Пластина под %s" % nm,
                       (qx, qy, qt), (x0 + sw / 2.0 - qx / 2.0, ybase(ps, y_in_side, qy), floor_top), COL_STRUT)
                rk_box("RackPost_%s" % nm, "Стойка %s (со стороны салона, напротив %s), L=%.0f" % (
                           nm, "P1" if nm == "P3" else "P2", z_p34_top - floor_top - qt),
                       (sw, sd, z_p34_top - floor_top - qt), (x0, ybase(ps, y_in_side, sd), floor_top + qt), COL_STRUT)

            # верхние стяжки
            cross_len = None
            if ties == "short":            # короткие стяжки поперёк над верхней батареей — по рамам P1/P3, P2/P4
                for nm, xc in (("Rear", min(f[1] for f in frames)), ("Front", max(f[1] for f in frames))):
                    rk_box("RackTopTie_%s" % nm, "Верхняя стяжка %s strut поперёк, L=%.0f (стойка у борта ↔ в салон)" % (
                               nm, by + sd),
                           (sd, by + sd, sw), (xc - sd / 2.0, ybase(ps, y_wall_side, by + sd), z_tie0), COL_STRUT)
                if R.get("top_lid"):       # крышка — фанера по стяжкам: полочка у кровати
                    lt = R["top_lid"]
                    rk_box("RackTopLid", "Крышка этажерки — фанера %.0f мм %.0f×%.0f по верхним стяжкам (полочка)" % (
                               lt, bx, by + sd),
                           (bx, by + sd, lt), (X0, ybase(ps, y_wall_side, by + sd), z_tie1), COL_PLY, tr=10)
            elif ties == "bed":
                # одна стяжка — существующая поперечина кровати у P1/P3, вторая — новая, у P2/P4
                if R.get("front_cross_full"):
                    cross_len, fy0 = 2 * rail_in, -rail_in
                else:
                    cross_len = rail_in - (y_in_side - sd)
                    fy0 = ybase(ps, rail_in, cross_len)
                cross_x0 = (p4x0 + sw) if p2x0 > p1x else (p4x0 - sd)
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
                ahead_of_deck=(X0 - dx1) if front else None,
                p2_len=p2_len, p2_on_rail=on_rail, lid=bool(ties == "short" and R.get("top_lid")),
                z_b1=(z_b1, z_b1_top), z_rail=(z_rail0, z_rail1), z_b2=(z_b2, z_b2_top),
                above_b2=(z_rail_top - sw) - z_b2_top, p34_len=z_p34_top - floor_top - qt,
                rail_len=by + sd, floor_top=floor_top, ties=ties, cross_len=cross_len,
                tie=(z_tie0, z_tie1) if ties else None,
                tie_to_bed=(z_rail_top - sw) - z_tie1 if ties == "short" else None))
            rack_geo[stack] = dict(X0=X0, X1=X1, p2=(p2x0, p2x1), p4x0=p4x0, y_in=y_in_side, by=by, bx=bx,
                                   cross_x1=(cross_x0 + sd) if ties == "bed" else None)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "R b_long b_short bz rack_geo rack_summary")


def overarch_shelf(S):
    """Полка над аркой на 2 батареи (ранний вариант)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, P, R, W, arch_shapes, b_long, b_short = S.B, S.P, S.R, S.W, S.arch_shapes, S.b_long, S.b_short
    bed_summary, bz, cutlist, doc, floor_top = S.bed_summary, S.bz, S.cutlist, S.doc, S.floor_top
    post_in, post_out, rack_geo, sd, sw, xf = S.post_in, S.post_out, S.rack_geo, S.sd, S.sw, S.xf
    ybase, z_rail_top = S.ybase, S.z_rail_top
    # ═══════ ПОЛКА НАД АРКОЙ (борт −Y): ещё 2 батареи над колёсной аркой — ПРОЕКТ 2026-11-07 ═══════
    overarch_summary = None
    OA = R.get("over_arch") if (B.get("enable") and R.get("enable")) else None   # (старый вариант; отключён)
    rg = rack_geo.get("rear")
    if OA and rg and W.get("enable"):
        ps = P["slider_side"]
        og = doc.addObject("App::DocumentObjectGroup", "BatteryRack_overArch")
        og.Label = "Полка НАД аркой: 2 батареи Buknuwo 150Ah (пассажирский борт) — ПРОЕКТ 2026-11-07"
        oshapes = {}

        def oa_box(name, label, dims, base, color, tr=0):
            add_box(doc, name, label, dims, base, color=color, transparency=tr, group=og)
            oshapes[name] = Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base))
            return oshapes[name]

        bxo, byo = b_long, b_short                       # длинной стороной вдоль борта
        y_i = post_in - byo                              # линия стоек P3/P4 со стороны салона
        z_arch = floor_top + W["height"]                 # верх арки (⚠️ 17″ по Upfit — промерить)
        zr0 = z_arch + OA["pad"]                         # низ продольных реек
        zr1 = zr0 + sw
        lw, lt = OA["ledger"]
        zs0 = zr0 + lt
        zs1 = zs0 + OA["shelf_th"]                       # верх фанеры полки = низ батарей
        zb1 = zs1 + bz
        xa = rg["p2"][1]                                 # передняя грань P2 заднего блока
        xa_in = rg["p4x0"] + sw                          # передняя грань P4
        xb = xf - sw / 2.0                               # задняя грань передней стойки кровати (и новой P3f)
        L_w, L_i = xb - xa, xb - xa_in
        oa_box("OverArchRail_Wall", "Продольная рейка над аркой у борта strut, L=%.0f: P2 ↔ передняя стойка "
               "кровати (уголки), на верх арки — через резину" % L_w,
               (L_w, sd, sw), (xa, ybase(ps, post_out, sd), zr0), COL_STRUT)
        oa_box("OverArchRail_Inner", "Продольная рейка над аркой со стороны салона strut, L=%.0f: P4 ↔ P3f" % L_i,
               (L_i, sd, sw), (xa_in, ybase(ps, y_i, sd), zr0), COL_STRUT)
        oa_box("OverArchLedger_Wall", "Уголок 1-1/2×1/8″ по низу рейки у борта — под фанеру полки, L=%.0f" % L_w,
               (L_w, lw, lt), (xa, ybase(ps, post_in, lw), zr0), COL_STRUT)
        oa_box("OverArchLedger_Inner", "Уголок 1-1/2×1/8″ по низу рейки в салон — под фанеру полки, L=%.0f" % L_i,
               (L_i, lw, lt), (xa_in, ybase(ps, y_i + lw, lw), zr0), COL_STRUT)
        oa_box("OverArchShelf", "Полка над аркой — фанера 1/2″ %.0f×%.0f на уголках" % (L_i, byo),
               (L_i, byo, OA["shelf_th"]), (xa_in, ybase(ps, post_in, byo), zs0), COL_PLY, tr=10)
        # батареи: первая — сразу за поперечиной-стяжкой заднего блока, между ними — промежуток под поперечину #2
        xb0 = (rg["cross_x1"] if rg.get("cross_x1") else xa) + OA["gap_rear"]
        xs_b = [xb0 + i * (bxo + OA["gap_between"]) for i in range(int(OA["n"]))]
        bats = []
        for i, x0 in enumerate(xs_b):
            bats.append(oa_box("Battery_OverArch_%d" % (i + 1),
                               "Батарея над аркой #%d Buknuwo 12.8V 150Ah (10.07″ вдоль борта)" % (i + 1),
                               (bxo, byo, bz), (x0, ybase(ps, post_in, byo), zs1), COL_BATTERY))
        st, sh = OA["stop"]
        oa_box("OverArchStop_Rear", "Упор-уголок за батареями (поперёк полки)",
               (st, byo, sh), (xs_b[0] - st, ybase(ps, post_in, byo), zs1), COL_STRUT)
        oa_box("OverArchStop_Front", "Упор-уголок перед батареями (поперёк полки)",
               (st, byo, sh), (xs_b[-1] + bxo, ybase(ps, post_in, byo), zs1), COL_STRUT)
        for i in range(len(xs_b) - 1):
            g0 = xs_b[i] + bxo
            oa_box("OverArchSpacer_%d" % (i + 1), "Брусок-распорка между батареями над аркой (%.0f мм)" % OA["gap_between"],
                   (OA["gap_between"], 120.0, 100.0), (g0, ybase(ps, post_in - (byo - 120.0) / 2.0, 120.0), zs1),
                   COL_WOOD)
        # опора рейки у борта на верх арки (резина) — над вершиной арки
        oa_box("OverArchPad", "Резина %.0f мм: рейка у борта ↔ верх арки" % OA["pad"],
               (120.0, sd, OA["pad"]), (W["center_x"] - 60.0, ybase(ps, post_out, sd), z_arch), (0.15, 0.15, 0.15))
        # передняя рама: передняя стойка кровати (у борта, есть) + новая P3f со стороны салона + поперечина
        qx, qy, qt = R["p34_plate"]
        p3f_len = zr1 - floor_top - qt
        oa_box("RackPostPlate_P3f", "Пластина под P3f", (qx, qy, qt),
               (xf - qx / 2.0, ybase(ps, y_i, qy), floor_top), COL_STRUT)
        oa_box("RackPost_P3f", "Стойка P3f (новая, со стороны салона напротив передней стойки кровати), L=%.0f" % p3f_len,
               (sw, sd, p3f_len), (xb, ybase(ps, y_i, sd), floor_top + qt), COL_STRUT)
        oa_box("OverArchCross_Front", "Поперечина strut у передней стойки кровати ↔ P3f, L=%.0f (концы реек — в неё)" % (
                   byo + sd), (sd, byo + sd, sw), (xb, ybase(ps, post_in, byo + sd), zr0), COL_STRUT)
        cutlist += [("рейка над аркой", float(L_w)), ("рейка над аркой", float(L_i)), ("стойка P3f", float(p3f_len)),
                    ("поперечина над аркой", float(byo + sd))]
        # поперечина #2 кровати — в промежуток между батареями (Dimitri: поперечины передвижные)
        cxs = bed_summary["cross_x"] if bed_summary else []
        c2 = doc.getObject("BedCross_2")
        if c2 is not None and len(xs_b) >= 2:
            cx_new = xs_b[0] + bxo + OA["gap_between"] / 2.0
            dxm = cx_new - c2.Shape.BoundBox.Center.x
            c2.Shape = c2.Shape.translated(App.Vector(dxm, 0, 0))
            c2.Label = "Поперечина #2 X=%.0f (съёмная) — между батареями над аркой, L=%.0f" % (
                cx_new, c2.Shape.BoundBox.YLength)
            if len(cxs) >= 2:
                cxs[1] = cx_new
        # проверки
        obj = lambda n: doc.getObject(n).Shape
        arch = arch_shapes.get(ps)
        bb_up = min(b.BoundBox.ZMax for b in bats)
        checks = [("батареи ↔ арка", min(b.distToShape(arch)[0] for b in bats)),
                  ("рейки ↔ арка (у борта — через резину)", min(oshapes[n].distToShape(arch)[0]
                                                               for n in ("OverArchRail_Wall", "OverArchRail_Inner"))),
                  ("батареи ↔ низ настила", min(b.distToShape(obj("BedDeck"))[0] for b in bats)),
                  ("батареи ↔ продольная рейка кровати", min(b.distToShape(obj("BedSideRail_nY"))[0] for b in bats)),
                  ("батареи ↔ поперечины кровати", min(b.distToShape(obj(n))[0] for b in bats
                                                     for n in ("BedCross_1", "BedCross_2", "BedCross_3",
                                                               "BedCross_RackFront") if doc.getObject(n))),
                  ("батареи ↔ задний блок", min(b.distToShape(obj("Battery_Upper"))[0] for b in bats))]
        overarch_summary = dict(z_arch=z_arch, zr=(zr0, zr1), zs=(zs0, zs1), zb=(zs1, zb1), xs=xs_b, bx=bxo,
                                rails=(L_w, L_i), xa=xa, xb=xb, p3f=p3f_len, checks=checks, floor_top=floor_top,
                                free_front=xb - (xs_b[-1] + bxo + st), cross2=cxs[1] if len(cxs) >= 2 else None,
                                deck_bottom=z_rail_top, rail_bottom=z_rail_top - sw)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "cutlist overarch_summary")


def bank(S):
    """Единая этажерка на 4 батареи (B1 на полу + полка над аркой) и электрика у батарей."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, P, R, RV, W, arch_a_lin, arch_shapes = S.B, S.P, S.R, S.RV, S.W, S.arch_a_lin, S.arch_shapes
    arch_ywall, cutlist, doc, dp_box_x, dp_shapes = S.arch_ywall, S.cutlist, S.doc, S.dp_box_x, S.dp_shapes
    dx1, floor_top, half, post_in, post_out = S.dx1, S.floor_top, S.half, S.post_in, S.post_out
    relief, sd, slider_x0, sw, xf, xr, ybase = S.relief, S.sd, S.slider_x0, S.sw, S.xf, S.xr, S.ybase
    z_rail_top = S.z_rail_top
    # ═══════ ЕДИНАЯ ЭТАЖЕРКА НА 4 БАТАРЕИ (борт −Y): B1 на полу + полка над аркой на 3 батареи ═══════
    bank_summary = None
    BK = R.get("bank") or {}
    if B.get("enable") and R.get("enable") and BK.get("enable") and W.get("enable"):
        ps = P["slider_side"]
        bg = doc.addObject("App::DocumentObjectGroup", "BatteryBank")
        bg.Label = "Этажерка на 4 батареи Buknuwo 150Ah (пассажирский борт): B1 на полу + полка над аркой; рейки/стойки/поперечины — V-Slot 2020 (2026-11-13)"
        bsh = {}

        def bk_box(name, label, dims, base, color, tr=0):
            add_box(doc, name, label, dims, base, color=color, transparency=tr, group=bg)
            bsh[name] = Part.makeBox(dims[0], dims[1], dims[2], App.Vector(*base))
            return bsh[name]

        def bk_shape(name, label, shape, color, tr=0):
            add_shape(doc, name, label, shape, color=color, transparency=tr, group=bg)
            bsh[name] = shape
            return shape

        VW, VH = 20.0, 20.0                              # V-Slot 2020: сечение 20×20; рейки — ОДИН профиль (расчёт 2026-11-13: стопка не нужна при опорах на ножки ящика)
        COL_VS = (0.72, 0.74, 0.78)                      # анодированный алюминий
        COL_HW = (0.30, 0.30, 0.32)                      # крепёж, пластины
        zb_off = BK.get("bolt_off", 10.0)                # болт M8 в стойку кровати — по центру НИЖНЕГО профиля рейки

        b_short, b_long, bz = R["battery"]
        bxl, byl = b_long, b_short                       # 10.07″ вдоль борта, 7.63″ поперёк
        y_w = post_in                                    # грань батарей к борту = внутр. грань стоек кровати
        y_i = post_in - byl                              # грань батарей к проходу (= линия стоек P3/P4/P3f)
        pt = B["plate"][2]
        qx, qy, qt = R["p34_plate"]
        p2px, p2py, p2pt = R["p2_plate"]
        # B1 — на полу, задом в короб D-стойки
        X0 = dp_box_x(arch_ywall - post_in) + R["dpillar_gap"]
        X1 = X0 + bxl
        z_b1 = floor_top + pt
        b1 = bk_box("Battery_B1", "Батарея B1 (нижняя, на полу) Buknuwo 12.8V 150Ah — 10.07″ вдоль борта",
                    (bxl, byl, bz), (X0, ybase(ps, y_w, byl), z_b1), COL_BATTERY)
        # уровень лестницы: низ реек — над верхом арки через резину
        # 2026-11-09 (ANCHORS): рейка у борта на сквозных болтах через овалы стоек P1/Pf → её центр — на овале стойки:
        # от «верх арки + резина (мин.)» вверх до ближайшего овала (резину/проставку добрать по месту)
        AR = ANCHORS["bank_rails"]
        z_arch = floor_top + W["height"]
        hz0 = floor_top + ANCHORS["bed_posts"]["hole0_z"]                # центр нижнего овала стоек кровати
        if AR.get("z_bottom") is not None:
            z_l0 = floor_top + AR["z_bottom"]
        else:
            k_ = math.ceil((z_arch + BK["pad"] + zb_off - hz0) / STRUT["pitch"] - 1e-9)
            z_l0 = hz0 + k_ * STRUT["pitch"] - zb_off
        pad_real = z_l0 - z_arch                                         # фактическая резина/проставка на арке
        z_l1 = z_l0 + VH
        z_s1 = z_l1 + BK["shelf_th"]                     # верх фанеры = низ батарей B2..B4
        # стойки: у борта — стойки кровати P1 (задняя) и Pf (передняя), они уже есть, с M8 в кузов;
        # со стороны прохода — 2 новые короткие: P3 (напротив P1) и P3f (напротив Pf), от пола до низа рейки.
        # (2026-11-07, вопрос Dimitri «зачем P2, P4, средняя поперечина?» — не нужны: рейка у борта лежит на арке,
        #  рейке в салон хватает пролёта P3 ↔ P3f; B1 спереди упирается в арку через клин)
        inb = (("P3f", xf - VW / 2.0, "напротив передней стойки кровати"),)      # P3 убрана: рейку держит ножка ящика #1 (см. ниже)
        z_p3t = z_l0 + VH + BK["shelf_th"] + BK.get("p3_guard", 0.0)      # верх P3: над полкой — бортик
        for nm, x0, note in inb:
            bk_box("BankPostPlate_%s" % nm, "Пластина под %s" % nm, (qx, qy, qt),
                   (x0 + VW / 2.0 - qx / 2.0, ybase(ps, y_i, qy), floor_top), COL_STRUT)
            bk_shape("BankPost_%s" % nm, "Стойка %s — V-Slot 2020 (со стороны прохода, %s), L=%.0f — к пластине снизу винтом "
                     "M5 в торец (резьба M5 в центральное отверстие), рейка — сбоку 2×M5 в T-гайки, верх на %.0f″ "
                     "выше полки (бортик у батарей)" % (nm, note, z_p3t - floor_top - qt, BK.get("p3_guard", 0.0) / 25.4),
                     vslot_2020(x0, ybase(ps, y_i, VW), floor_top + qt, z_p3t), COL_VS)
        # лестница
        # 2026-11-07 (Dimitri, фото): рейка у борта — как продольная рейка кровати: на всю длину X P1..Pf, по грани
        # стоек кровати со стороны салона, сквозной болт через стойку и рейку (без уголков) — просто и надёжно
        # 2026-11-07: обе рейки — назад до D-стойки (у борта) / задней рамы (у прохода), вперёд до проёма сдвижной двери
        eg_ = BK.get("ends_gap", 5.0)
        x_front = slider_x0 - eg_
        rp_ = doc.getObject("Pillar_Rear_%s" % ("nY" if ps < 0 else "pY"))
        x_rear_frame = (rp_.Shape.BoundBox.XMax if rp_ is not None else 80.0) + eg_ + 5.0

        def x_from_dp(y_out, yl, z0, zl, x_min):
            """Самый задний X торца бруса (|Y| y_out−yl..y_out), при котором до D-стойки ≥ ends_gap."""
            lo, hi = x_min, xr
            for _ in range(30):
                mid = (lo + hi) / 2.0
                bx_ = Part.makeBox(xr - mid, yl, zl, App.Vector(mid, ybase(ps, y_out, yl), z0))
                if bx_.distToShape(dp_shapes[ps])[0] >= eg_:
                    hi = mid
                else:
                    lo = mid
            return hi
        # 2026-11-09 (Dimitri): обе рейки — из одного 10′ strut: у борта 58″, у прохода 62″ − пропил; сзади — как было
        # (у борта — до D-стойки, у прохода — до задней двери), укорачиваются СПЕРЕДИ
        xw0 = AR["wall_x_rear"] if AR.get("wall_x_rear") is not None else x_from_dp(post_in, sd, z_l0, sw, x_rear_frame)
        xi0 = AR["inner_x_rear"] if AR.get("inner_x_rear") is not None else x_from_dp(y_i + sd, sd, z_l0, sw,
                                                                                      x_rear_frame)
        xw1, xi1 = xw0 + AR["wall_len"], xi0 + AR["inner_len"]
        xw1_old, xi1_old = x_front, x_front                                # было: обе — до проёма сдвижной двери
        yw0 = ybase(ps, post_in, VW)                      # Y-начало рейки у борта (грань стоек кровати со стороны салона)
        yi0 = ybase(ps, y_i + VW, VW)                     # … рейки со стороны прохода
        # рейка у борта: один профиль 2020; M8 (⌀8.5) насквозь по его центру в P1 и Pf (овалы стоек кровати)
        rw_ = vslot_x(xw0, xw1, yw0, z_l0)
        for xc_ in (xr, xf):
            rw_ = drill_y(rw_, xc_, z_l0 + zb_off, yw0 - 1.0, yw0 + VW + 1.0, 8.5)
        bk_shape("BankRail_Wall", "Продольная рейка у борта — V-Slot 2020 (20×20), L=%.0f: по грани стоек кровати P1 и Pf со "
                 "стороны салона, сквозной болт M8 (сверлить ⌀8.5) в овал стойки; посередине — на верх арки через резину/"
                 "подкладку %.0f мм (расчёт: на подушках арки прогиб 0.1 мм); назад — до D-стойки" % (xw1 - xw0, pad_real),
                 rw_, COL_VS)
        for nm, xc in (("P1", xr), ("Pf", xf)):
            bk_box("BankRailBolt_%s" % nm, "Болт M8×60 с шайбами и гайкой: рейка у борта ↔ стойка кровати %s (гайка — со стороны "
                   "прохода, в щели между рейками)" % nm,
                   (8.0, VW + (post_out - post_in) + 16.0, 8.0),
                   (xc - 4.0, ybase(ps, post_out + 8.0, VW + (post_out - post_in) + 16.0), z_l0 + zb_off - 4.0), COL_HW)
        # опоры рейки прохода: ножки направляющих верхнего ящика #1, #2 (X = BedCross_k.XMin + 4 + 10; их Y — на 8 мм ближе к проходу
        # грани рейки) и P3f. Расчёт: 3 опоры (ножка 1 ≈ X 412, ножка 2 ≈ X 869, P3f) — прогиб 0.1–0.2 мм, σ 4–8 МПа (P3 не нужна).
        legs_x = []
        for nm_ in ("BedCross_1", "BedCross_2"):
            o_ = doc.getObject(nm_)
            legs_x.append((o_.Shape.BoundBox.XMin + 4.0 + 10.0) if o_ is not None else None)
        legs_x = [x_ for x_ in legs_x if x_ is not None]
        sup_x = legs_x + [xf]                              # центры опор рейки прохода по X
        y_leg_face = y_i - 8.0                             # грань ножки ящика со стороны борта (|Y|): зазор 8 мм до рейки
        ri_ = vslot_x(xi0, xi1, yi0, z_l0)
        for xc_ in sup_x:
            ri_ = drill_y(ri_, xc_, z_l0 + 10.0, yi0 - 1.0, yi0 + VW + 1.0, 5.5)
        bk_shape("BankRail_Inner", "Продольная рейка со стороны прохода — V-Slot 2020 (20×20), L=%.0f: опоры — ножки направляющих "
                 "верхнего ящика #1 и #2 (винт M5×40 + проставка 8 мм + угловая скоба снизу) и P3f (винт M5×30); под гранью "
                 "батарей; назад — до задней рамы" % (xi1 - xi0), ri_, COL_VS)

        def screw_y(name, label, x, z, y_tip, y_head, d, head_d, head_h):
            """Винт вдоль Y: острие в |Y|=y_tip, головка (⌀head_d, высота head_h) на |Y|=y_head."""
            ya, yb_ = ps * y_tip, ps * y_head
            sg = 1.0 if yb_ > ya else -1.0
            lo = min(ya, yb_)
            sh_ = Part.makeCylinder(d / 2.0, abs(yb_ - ya), App.Vector(x, lo, z), App.Vector(0, 1, 0))
            hh_ = Part.makeCylinder(head_d / 2.0, head_h, App.Vector(x, yb_ if sg > 0 else yb_ - head_h, z), App.Vector(0, 1, 0))
            bk_shape(name, label, sh_.fuse(hh_), COL_HW)
        for i_, xc in enumerate(sup_x):
            is_leg = i_ < len(legs_x)
            tag = ("Leg%d" % (i_ + 1)) if is_leg else "P3f"
            y_tip = (y_leg_face - 8.0) if is_leg else (y_i - 8.0)         # острие — в T-гайке в пазу ножки/стойки
            screw_y("BankRailScrew_%s" % tag, "Винт M5×%d + T-гайка M5: рейка прохода ↔ %s (головка — со стороны щели между рейками)" % (
                    40 if is_leg else 30, "ножка направляющей ящика #%d" % (i_ + 1) if is_leg else "стойка P3f"),
                    xc, z_l0 + 10.0, y_tip, y_i + VW, 5.0, 8.5, 3.0)
            if is_leg:                                                    # проставка 8 мм между гранью ножки и рейкой
                sp_ = Part.makeBox(VW, 8.0, VW, App.Vector(xc - VW / 2.0, ybase(ps, y_i, 8.0), z_l0))
                bk_shape("BankLegSpacer_%d" % (i_ + 1), "Проставка 8 мм (алюминий/текстолит 20×8×20, отверстие ⌀5.5): рейка "
                         "прохода ↔ ножка направляющей #%d (ножка стоит на 8 мм ближе к проходу)" % (i_ + 1), sp_, (0.80, 0.70, 0.45))
            # угловая скоба 20×28 под рейкой: вертикальная полка — на грани ножки/стойки, горизонтальная — под рейкой
            ths = 4.0
            y_face = y_leg_face if is_leg else y_i                         # грань опоры со стороны борта (|Y|)
            hz = Part.makeBox(VW, y_i + VW - y_face, ths, App.Vector(xc - VW / 2.0, ybase(ps, y_i + VW, y_i + VW - y_face), z_l0 - ths))
            vt = Part.makeBox(VW, ths, 28.0, App.Vector(xc - VW / 2.0, ybase(ps, y_face + ths, ths), z_l0 - 28.0))
            bk_shape("BankBracket_%s" % tag, "Угловая скоба 2020 (20×28, T-гайки M5) под рейкой прохода у опоры %s — берёт "
                     "вертикальную нагрузку" % tag, hz.fuse(vt), COL_HW)
        # поперечины (один профиль 20×20 — это только распорки) — между рейками; сдвинуты от опор; к рейкам снизу L-пластинами
        cx_rear = BK.get("cross_rear_x", None)
        cx_rear = (max(legs_x) if False else (legs_x[0] + 43.0)) if cx_rear is None and legs_x else (xr + 78.0 if cx_rear is None else cx_rear)
        crosses = (("Rear", cx_rear, +1.0), ("Front", xf - BK.get("cross_off", 40.0), -1.0))
        yc0 = ybase(ps, post_in - VW, byl - 2 * VW)
        yc1 = yc0 + (byl - 2 * VW)
        for nm, xc, dx_ in crosses:
            bk_shape("BankCross_%s" % nm, "Поперечина лестницы %s — V-Slot 2020 (20×20), L=%.0f (распорка между рейками, сдвинута от "
                     "опоры); концы — на L-пластинах снизу" % (nm, byl - 2 * VW),
                     vslot_y(xc - VW / 2.0, yc0, yc1, z_l0), COL_VS)
            tp_ = 4.0
            for rl, c_abs, sg_ in (("Wall", post_in - VW / 2.0, -1.0), ("Inner", y_i + VW / 2.0, +1.0)):
                xa0, xa1 = (xc - VW / 2.0, xc + VW / 2.0 + 40.0) if dx_ > 0 else (xc - VW / 2.0 - 40.0, xc + VW / 2.0)
                ya0, ya1 = (c_abs - VW / 2.0 - 50.0, c_abs + VW / 2.0) if sg_ < 0 else (c_abs - VW / 2.0, c_abs + VW / 2.0 + 50.0)
                armx = Part.makeBox(xa1 - xa0, VW, tp_, App.Vector(xa0, ybase(ps, c_abs + VW / 2.0, VW), z_l0 - tp_))
                ya_t = sorted((ps * ya0, ps * ya1))
                army = Part.makeBox(VW, ya_t[1] - ya_t[0], tp_, App.Vector(xc - VW / 2.0, ya_t[0], z_l0 - tp_))
                bk_shape("BankLPlate_%s_%s" % (nm, rl), "L-пластина 2020 (5 отверстий, T-гайки M5) снизу: поперечина %s ↔ рейка %s" % (
                             nm, "у борта" if rl == "Wall" else "прохода"), armx.fuse(army), COL_HW)
        # фанера полки: поверх обеих реек, по грань батарей к проходу; 2026-11-07 — назад до D-стойки/задней рамы
        # (полочка за B2), вперёд до проёма сдвижной двери (полочка под бельё); вырезы под стойки кровати P1, Pf
        x_ply1 = xf - sw / 2.0                           # электрика на полке — до передней стойки кровати (как было)
        # 2026-11-09: полка спереди — до конца рейки у борта (длиннее); у прохода за концом своей рейки — свес
        xp0_, xp1_ = min(xw0, xi0), (xw1 if BK.get("shelf_front", "wall") == "wall" else min(xw1, xi1))
        ply = Part.makeBox(xp1_ - xp0_, post_out - y_i, BK["shelf_th"],
                           App.Vector(xp0_, ybase(ps, post_out, post_out - y_i), z_l1))
        for pn_ in ("BedPost_%s_rear" % ("nY" if ps < 0 else "pY"), "BedPost_%s_front" % ("nY" if ps < 0 else "pY")):
            pb = doc.getObject(pn_).Shape.BoundBox
            ply = ply.cut(Part.makeBox(pb.XLength + 4, pb.YLength + 4, BK["shelf_th"] + 2,
                                       App.Vector(pb.XMin - 2, pb.YMin - 2, z_l1 - 1)))
        dps_ = dp_shapes[ps]
        for dxo in (-eg_, 0.0, eg_):                         # зазор ends_gap вокруг D-стойки
            for dyo in (-eg_, 0.0, eg_):
                ply = ply.cut(dps_.translated(App.Vector(dxo, dyo, 0)))
        ply = Part.makeCompound([sl_ for sl_ in ply.Solids if sl_.Volume > 1e4]).Solids[0] if len(ply.Solids) > 1 else ply
        add_shape(doc, "BankShelf", "Полка — фанера 1/2″ %.0f×%.0f поверх лестницы: батареи + полочка за B2 (до D-стойки) "
                  "+ полочка под бельё (до проёма сдвижной двери); вырезы под стойки кровати" % (
                      xp1_ - xp0_, post_out - y_i), ply, color=COL_PLY, transparency=10, group=bg)
        bsh["BankShelf"] = ply
        # батареи на полке: B2 над B1, B3/B4 — над аркой
        xs = [X0 + i * (bxl + BK["gap"]) for i in range(int(BK["n_shelf"]))]
        bats = []
        for i, x0 in enumerate(xs):
            bats.append(bk_box("Battery_B%d" % (i + 2), "Батарея B%d (на полке%s) Buknuwo 12.8V 150Ah" % (
                i + 2, ", над B1" if i == 0 else ", над аркой"), (bxl, byl, bz), (x0, ybase(ps, y_w, byl), z_s1),
                COL_BATTERY))
        st, sh = BK["stop"]
        bk_box("BankStop_ShelfRear", "Упор-уголок за рядом батарей на полке", (st, byl, sh),
               (xs[0] - st, ybase(ps, y_w, byl), z_s1), COL_STRUT)
        bk_box("BankStop_ShelfFront", "Упор-уголок перед рядом батарей на полке", (st, byl, sh),
               (xs[-1] + bxl, ybase(ps, y_w, byl), z_s1), COL_STRUT)
        g_b1 = (W["center_x"] - arch_a_lin(arch_ywall - post_in)) - X1          # B1 ↔ арка у грани к борту
        bk_box("BankWedge_B1Arch", "Клин (дерево + резина) B1 ↔ задняя грань арки: %.0f мм у борта (грань арки скошена — "
               "к проходу шире)" % g_b1, (g_b1 - 0.5, 100.0, 120.0), (X1, ybase(ps, y_w, 100.0), floor_top + 60.0),
               COL_WOOD)
        zh0 = z_b1 + bz + BK["holddown_gap"]
        if BK.get("holddown_B1", True):                     # 2026-11-08 Dimitri: не нужна — батарея 20 кг не выпрыгнет
            bk_box("BankHolddown_B1", "Прижимная планка strut над B1 (между P1 и P3, резина %.0f мм)" % BK["holddown_gap"],
                   (sd, byl, sw), (xr - sd / 2.0, ybase(ps, y_w, byl), zh0), COL_STRUT)
        for i, dx in enumerate(BK["arch_pads_dx"]):
            bk_box("BankArchPad_%d" % (i + 1), "Резина/проставка %.0f мм: рейка у борта ↔ верх арки (рейка — на овалах "
                   "стоек кровати)" % pad_real,
                   (100.0, VW, pad_real), (W["center_x"] + dx - 50.0, ybase(ps, post_in, VW), z_arch), (0.15, 0.15, 0.15))
        L_p = z_p3t - floor_top - qt
        # раскрой V-Slot 2020 (профиль берём любой длины): каждая рейка/поперечина — 2 профиля; стойка — 1
        L_p = z_p3t - floor_top - qt
        vcut = [("рейка у борта", float(xw1 - xw0), 1), ("рейка прохода", float(xi1 - xi0), 1),
                ("поперечина", float(byl - 2 * VW), 2), ("стойка P3f", float(L_p), 1)]
        vcut_total = sum(L_ * n_ for _, L_, n_ in vcut)
        n_sup = len(sup_x)
        vhw = [("L-пластина 2020, 5 отв. (поперечины)", 4),
               ("угловая скоба 20×28 под рейкой прохода", n_sup),
               ("винт M5×40 + T-гайка (рейка↔ножка ящика) + проставка 8 мм", len(legs_x)),
               ("винт M5×30 + T-гайка (рейка↔P3f)", 1),
               ("болт M8×60 + гайка + 2 шайбы (рейка↔стойка кровати)", 2),
               ("винт M5×8 + T-гайка (L-пластины, скобы): ~", 4 * 5 + n_sup * 2),
               ("винт M5×10 в торец P3f + пластина снизу", 1)]
        # проверки
        obj = lambda n: doc.getObject(n).Shape
        arch = arch_shapes.get(ps)
        dpf = dp_shapes[ps]
        top = bats[0].BoundBox.ZMax
        near = lambda shs, n: min(sh_.distToShape(obj(n))[0] for sh_ in shs)
        checks = [("B1 ↔ арка", b1.distToShape(arch)[0]), ("B1 ↔ D-стойка", b1.distToShape(dpf)[0]),
                  ("B2–B4 ↔ арка", min(b.distToShape(arch)[0] for b in bats)),
                  ("B2 ↔ D-стойка", bats[0].distToShape(dpf)[0]),
                  ("лестница ↔ арка", min(bsh[n].distToShape(arch)[0] for n in (
                      "BankRail_Wall", "BankRail_Inner", "BankCross_Front", "BankCross_Rear", "BankLPlate_Front_Wall",
                      "BankLPlate_Rear_Wall", "BankLPlate_Front_Inner", "BankLPlate_Rear_Inner"))),
                  ("полка ↔ D-стойка", ply.distToShape(dpf)[0]),
                  ("батареи ↔ поперечины кровати", min(near(bats, n) for n in ("BedCross_1", "BedCross_2", "BedCross_3"))),
                  ("батареи ↔ продольная рейка кровати", near(bats, "BedSideRail_nY")),
                  ("батареи ↔ щит", near(bats, "BedDeck"))]
        # 2026-11-09: рейки 58″ / 62″ − пропил — что перекрывают и попадают ли болты в овалы (допуск овала ±9.5 мм)
        tol_ = (STRUT["hole"][0] - 9.5) / 2.0
        def _hoff(x_start, x_bolt):
            k_ = round((x_bolt - x_start - STRUT["hole0"]) / STRUT["pitch"])
            return abs(x_bolt - (x_start + STRUT["hole0"] + k_ * STRUT["pitch"]))
        zc_ = z_l0 + zb_off                               # ось болта M8 в стойки кровати P1/Pf
        z_off = abs(zc_ - (hz0 + round((zc_ - hz0) / STRUT["pitch"]) * STRUT["pitch"]))
        p3f_ = doc.getObject("BankPost_P3f").Shape.BoundBox
        rails_fit = dict(
            wall_over_Pf=xw1 - (xf + sw / 2.0),               # > 0 — рейка у борта перекрывает стойку nY front целиком
            inner_over_P3f=xi1 - p3f_.XMax,                   # > 0 — рейка прохода перекрывает P3f
            holes_x={"P1": 0.0, "Pf": 0.0, "P3": 0.0, "P3f": 0.0},     # V-Slot сверлим по месту — смещения нет
            hole_z=z_off, tol=tol_, pad=pad_real,
            old=(xw1_old - xw0, xi1_old - xi0), new=(xw1 - xw0, xi1 - xi0),
            shelf_front=(xp1_, x_front), linen=(xp1_ - (xf + sw / 2.0), x_front - (xf + sw / 2.0)),
            stick=vcut_total, vcut=vcut, vhw=vhw)
        checks += [("рейка у борта за стойку nY front (сквозной болт)", rails_fit["wall_over_Pf"]),
                   ("рейка прохода за P3f", rails_fit["inner_over_P3f"]),
                   ("ряд батарей на полке ↔ край полки", xp1_ - (xs[-1] + bxl + st)),
                   ("овал стойки кровати ↔ рейка у борта: запас по Z", tol_ - z_off)]
        # клапан сброса давления (ANCHORS) ↔ B1: свободное место перед решёткой
        valve_fit = None
        if relief is not None and RV["side"] == ps:
            rb_ = relief.BoundBox
            face_y = rb_.YMax if ps < 0 else rb_.YMin                      # лицевая плоскость решётки
            zone = Part.makeBox(rb_.XLength, RV["free_min"], rb_.ZLength,
                                App.Vector(rb_.XMin, face_y if ps < 0 else face_y - RV["free_min"], rb_.ZMin))
            g_ = relief.distToShape(b1)[0]
            ov_ = zone.common(b1)
            x_cov = max(0.0, min(rb_.XMax, X1) - max(rb_.XMin, X0))           # перекрытие по X решётки и B1
            valve_fit = dict(gap=g_, cover_x=x_cov, w=rb_.XLength, zone_vol=ov_.Volume if not ov_.isNull() else 0.0,
                             need=RV["free_min"] - g_, b1_x=(X0, X1), valve_x=(rb_.XMin, rb_.XMax),
                             b1_arch=g_b1)
            checks.append(("B1 ↔ клапан сброса давления (свободно перед решёткой)", g_))
        # ── электрика на полке перед B4 (раскладка) ──
        EL = ELECTRICAL
        elec = None
        if EL.get("enable"):
            eg = doc.addObject("App::DocumentObjectGroup", "Electrical")
            eg.Label = "Электрика у батарей: MPPT, DC-DC, шины, предохранители, трассы кабелей — ПРОЕКТ 2026-11-07"
            ft = floor_top
            bx0 = xs[-1] + bxl + st + 10.0                   # панель — от упора за B4
            bx1 = xf - sw / 2.0 - 6.0                        # … до передней стойки кровати
            z_rail_b = z_rail_top - sw                       # низ продольной рейки кровати
            bz0, bz1 = z_s1 + 2.0, z_rail_b - 6.0
            yw_b = y_at_z(half, (bz0 + bz1) / 2.0)           # борт на высоте панели
            yb_in = yw_b - EL["board_th"]                    # лицевая сторона панели
            eboxes = {}

            def el_box(name, label, dims, base, color, tr=0):
                add_box(doc, name, label, dims, base, color=color, transparency=tr, group=eg)
                eboxes[name] = (base[0], base[0] + dims[0], base[1], base[1] + dims[1], base[2], base[2] + dims[2])

            el_box("Elec_Board", "Панель на борту — фанера 1/2″ %.0f×%.0f (под MPPT, DC-DC, предохранители)" % (
                       bx1 - bx0, bz1 - bz0), (bx1 - bx0, EL["board_th"], bz1 - bz0),
                   (bx0, ybase(ps, yw_b, EL["board_th"]), bz0), COL_PLY, 0)
            mw, mh, md = EL["mppt"]
            el_box("Elec_MPPT", "Контроллер солнечных панелей IPANDEE MPPT 6.54×9.45×2.56″ (клеммы снизу)",
                   (mw, md, mh), (bx0 + 10.0, ybase(ps, yb_in, md), bz1 - 5.0 - mh), (0.12, 0.12, 0.14))
            dl, dh, dd = EL["dcdc"]
            el_box("Elec_DCDC", "Зарядник DC-DC VEVOR 60 A 9.45×5.7×3.3″ (вход — от стартерной АКБ)",
                   (dl, dd, dh), (bx1 - 5.0 - dl, ybase(ps, yb_in, dd), bz1 - 5.0 - dh), (0.20, 0.20, 0.22))
            fl, fw_, fh = EL["fuse_block"]
            el_box("Elec_FuseBlock", "Блок предохранителей потребителей (~6 позиций) — на панели под DC-DC",
                   (fl, fh, fw_), (bx1 - 5.0 - dl, ybase(ps, yb_in, fh), bz0 + 20.0), (0.85, 0.75, 0.15))
            bl, bw2, bh = EL["busbar"]
            ybus = y_i + 8.0 + bw2                           # шины — на полке у грани к проходу
            el_box("Elec_BusPos", "Шина + BB500 (красная): + всех 4 батарей (через клеммные предохранители), MPPT, DC-DC, "
                   "блок предохранителей", (bl, bw2, bh), (bx0 + 15.0, ybase(ps, ybus, bw2), z_s1), (0.80, 0.12, 0.10))
            el_box("Elec_BusNeg", "Шина − BB500 (чёрная): − всех батарей, MPPT, DC-DC, потребители; масса — на C-стойку",
                   (bl, bw2, bh), (bx1 - 5.0 - dl, ybase(ps, ybus, bw2), z_s1), (0.10, 0.10, 0.10))
            # точка массы на C-стойке (задний край проёма сдвижной двери)
            gx, gz = slider_x0 - EL["ground_back"], ft + EL["ground_h"]
            gy = y_at_z(half, gz)
            add_sphere(doc, "Elec_GroundStud", "Масса батарей на кузов: болт M8/M10 на C-стойке (задний край проёма "
                       "сдвижной двери), зачистить до металла", 10, (gx, ps * (gy - 6.0), gz), color=(0.1, 0.6, 0.1),
                       group=eg)
            # трассы кабелей (оси): вдоль борта
            dw = lambda d_: ps * (arch_ywall - d_)          # |Y| по расстоянию от стены у пола
            zh = ft + EL["harness_h"]
            routes = {
                "batteries": [(X0 + 20.0, dw(55.0), z_b1 + bz), (X0 + 20.0, dw(12.0), z_b1 + bz + 20.0),
                              (X0 + 20.0, dw(12.0), zh), (bx0 + 20.0, dw(12.0), zh)],
                "alternator": [(slider_x0 + 25.0, dw(8.0), ft + 10.0), (xf + sw / 2.0 + 12.0, dw(8.0), ft + 10.0),
                               (xf + sw / 2.0 + 12.0, dw(8.0), bz1 - 40.0), (bx1 - 5.0, dw(8.0), bz1 - 40.0)],
                "solar": [(dx1 + 60.0, dw(6.0), ft + 1650.0), (dx1 + 60.0, dw(6.0), bz0 + 25.0),
                          (bx0 + 10.0 + mw / 2.0, dw(6.0), bz0 + 25.0)],
                "ground": [(bx1 - 5.0, dw(arch_ywall - (ybus - bw2 / 2.0)), z_s1 + bh / 2.0),
                           (xf + sw / 2.0 + 12.0, dw(60.0), z_s1 + bh / 2.0), (gx, dw(10.0), gz)],
            }
            for nm, pts in routes.items():
                v = [App.Vector(*q) for q in pts]
                add_shape(doc, "Cable_%s" % nm, {"batteries": "Жгут от батарей вдоль борта (площадки для стяжек) к шинам",
                                                 "alternator": "Кабель от стартерной АКБ/генератора: по полу из-под порога "
                                                               "сдвижной двери, вверх у передней стойки кровати → DC-DC",
                                                 "solar": "Кабель от солнечных панелей: с крыши по борту → MPPT",
                                                 "ground": "Масса: шина − → C-стойка"}[nm],
                          Part.makePolygon(v), color={"batteries": (0.8, 0.1, 0.1), "alternator": (0.9, 0.5, 0.0),
                                                      "solar": (0.1, 0.4, 0.9), "ground": (0.1, 0.6, 0.1)}[nm], group=eg)
            EL["_routes"] = {k: [list(q) for q in v_] for k, v_ in routes.items()}
            EL["_ground"] = [gx, ps * gy, gz]
            obj = lambda n: doc.getObject(n).Shape
            checks.append(("шины электрики ↔ край полки", xp1_ - max(eboxes[n_][1] for n_ in ("Elec_BusPos", "Elec_BusNeg"))))
            checks.append(("шины электрики ↔ край рейки прохода (опора)", xi1 - max(eboxes[n_][1] for n_ in ("Elec_BusPos",
                                                                                                    "Elec_BusNeg"))))
            elec = dict(board=(bx0, bx1, bz0 - ft, bz1 - ft), boxes=eboxes,
                        clear_rail=z_rail_b - max(eboxes[n][5] for n in eboxes), ground=(gx, gz - ft),
                        free_x=bx1 - bx0)
        bank_summary = dict(X1=(X0, X1), xs=xs, bx=bxl, z_b1=(z_b1, z_b1 + bz), z_arch=z_arch, z_l=(z_l0, z_l1),
                            z_s1=z_s1, top=top, floor_top=floor_top, rails=(xw1 - xw0, xi1 - xi0), cross=byl - 2 * VW,
                            posts=(L_p, L_p), free=x_ply1 - (xs[-1] + bxl + st), checks=checks,
                            inner=arch_ywall - y_i, under_cross=(z_rail_top - sw) - top, elec=elec, rails_fit=rails_fit,
                            rails_x=((xw0, xw1), (xi0, xi1)), valve=valve_fit)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "bank_summary cutlist")
