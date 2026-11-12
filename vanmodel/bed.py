# -*- coding: utf-8 -*-
"""Кровать — как построена (strut SC14-10-EG): 4 стойки (база), продольные рейки, поперечины, щит, матрас.

Отдаёт остальным разделам базовые размеры: положение стоек (xr, xf, post_in, post_out), ширину/глубину strut
(sw, sd), высоты (z_rail_top, z_bolt), край щита (dx0, dx1), функцию ybase() и раскрой strut (cutlist).
"""

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .params import BED
from .common import (COL_BOLT, COL_DECK, COL_MATTRESS, COL_PLY, COL_STRUT, COL_WOOD, add_box, add_shape,
                     add_sphere)
from .scan import y_at_z
from .strut import STRUT_HOLE0

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def bed(S):
    """Кровать — как построена: стойки, рейки, поперечины, щит, матрас."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    DP, P, W, arch_ywall, doc, dp_body_x = S.DP, S.P, S.W, S.arch_ywall, S.doc, S.dp_body_x
    floor_top, half, x_dp_s = S.floor_top, S.half, S.x_dp_s
    # ═══════ КРОВАТЬ — как построена (strut SC14-10-EG), реконструкция по фото ═══════
    bed_summary = None
    B = BED
    if B.get("enable"):
        bed_g = doc.addObject("App::DocumentObjectGroup", "Bed_StrutFrame")
        bed_g.Label = "Кровать (построена) — strut SC14-10-EG, реконструкция по фото 2026-11-05/06"
        sw, sd = B["strut_w"], B["strut_d"]
        # 2026-11-09: 4 стойки кровати — база (ANCHORS["bed_posts"]), каждая со своим X; по бортам — свой зазор к ребру
        AP = ANCHORS["bed_posts"]
        xr_s = {+1: AP["x"]["pY_rear"], -1: AP["x"]["nY_rear"]}
        xf_s = {+1: AP["x"]["pY_front"], -1: AP["x"]["nY_front"]}
        xr, xf = xr_s[-1], xf_s[-1]                    # пассажирский борт (этажерка батарей и т.п.)
        z_bolt = floor_top + B["body_bolt_h"]
        z_rail_top = floor_top + B["rail_top_h"] + B.get("rail_raise", 0.0)
        z_deck_top = z_rail_top + B["deck_th"]
        z_deck_top_photo = floor_top + B["rail_top_h"] + B["deck_th"]   # брус 2×4 на стойках — не двигается
        yw_post = y_at_z(half, z_bolt)                 # стена (рёбра) на высоте болта
        post_out_s = {sg_: yw_post - AP["wall_gap"]["pY" if sg_ > 0 else "nY"] for sg_ in (1, -1)}
        post_in_s = {sg_: post_out_s[sg_] - sd for sg_ in (1, -1)}
        post_out = post_out_s[-1]                      # грань стойки к стене (|Y|) — пасс. борт
        post_in = post_out - sd                        # грань стойки в салон
        rail_in = min(post_in_s.values()) - sd         # грань продольной рейки в салон

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
        for xtag in ("rear", "front"):
            for sgn, tag in ((+1, "pY"), (-1, "nY")):
                x = (xr_s if xtag == "rear" else xf_s)[sgn]
                post_out = post_out_s[sgn]
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
                           9, (x, sgn * (post_out + AP["wall_gap"][tag] / 2.0), z_bolt),
                           color=COL_BOLT, group=bed_g)
                STRUT_HOLE0["BedPost_%s_%s" % (tag, xtag)] = AP["hole0_z"] - B["plate"][2]
        post_out = post_out_s[-1]

        # продольные рейки по бортам (1-5/8″ по вертикали, открытой стороной в салон)
        for sgn, tag in ((+1, "pY"), (-1, "nY")):
            rx0, rx1 = xr_s[sgn] - sw / 2.0, xf_s[sgn] + sw / 2.0
            post_in = post_in_s[sgn]
            strut("BedSideRail_%s" % tag,
                  "Продольная рейка %s X %.0f..%.0f, верх Z=%.0f" % (tag, rx0, rx1, z_rail_top),
                  (rx1 - rx0, sd, sw), (rx0, ybase(sgn, post_in, sd), z_rail_top - sw), "продольная")
        post_in = post_in_s[-1]

        # продольный размер щита: перед — в deck_front_gap позади передних стоек, зад — до задних дверей
        dx0 = (min(x_dp_s.values()) - DP["box_len"]) if B.get("deck_rear") == "doors" else max(xr_s.values()) - sw / 2.0
        if B.get("deck_front_gap") is not None:
            dx1 = min(xf_s.values()) - sw / 2.0 - B["deck_front_gap"]
        else:
            dx1 = max(xf_s.values()) + sw / 2.0 if not B.get("deck_len") else dx0 + B["deck_len"]

        # 3 съёмные поперечины между рейками: #1 у задних стоек, последняя — под передним краем щита
        nC = max(2, int(B["cross_n"]))
        cx0, cx1 = max(xr_s.values()) + sw / 2.0 + sd / 2.0, min(min(xf_s.values()) - sw / 2.0, dx1) - sd / 2.0
        for i in range(nC):
            cx = cx0 + (cx1 - cx0) * i / (nC - 1)
            strut("BedCross_%d" % (i + 1),
                  "Поперечина #%d X=%.0f (съёмная), L=%.0f" % (i + 1, cx, 2 * rail_in),
                  (sd, 2 * rail_in, sw), (cx - sd / 2.0, -rail_in, z_rail_top - sw), "поперечина")

        # настил (MR-плита) с вырезами под стойки и D-стойки + матрас
        dhw = y_at_z(half, z_rail_top) - 5.0
        deck = Part.makeBox(dx1 - dx0, 2 * dhw, B["deck_th"], App.Vector(dx0, -dhw, z_rail_top))
        mat = Part.makeBox(dx1 - dx0, 2 * post_in, B["mattress_th"], App.Vector(dx0, -post_in, z_deck_top))
        if B.get("deck_rear") == "doors":         # вырезы под D-стойки (грань стойки скошена назад к центру)
            y_dp_in = arch_ywall - DP["body_depth"]
            for sgn in (+1, -1):
                ya = dhw + 30.0
                pts = [(dx0 - 10.0, y_dp_in), (dp_body_x(DP["body_depth"], sgn), y_dp_in),
                       (dp_body_x(arch_ywall - ya, sgn), ya), (dx0 - 10.0, ya)]
                v = [App.Vector(x, sgn * y, z_rail_top - 5.0) for x, y in pts]
                nt = Part.Face(Part.makePolygon(v + [v[0]])).extrude(
                    App.Vector(0, 0, B["deck_th"] + B["mattress_th"] + 10.0))
                deck = deck.cut(nt)
                mat = mat.cut(nt)
        for s in post_solids:
            deck = deck.cut(s)
        add_shape(doc, "BedDeck", "Настил — плита MR Type II %g мм, %.0f×%.0f (вырезы под стойки)" % (
                      B["deck_th"], dx1 - dx0, 2 * dhw),
                  deck, color=COL_DECK, transparency=10, group=bed_g)
        add_shape(doc, "BedMattress", "Матрас ~%g мм" % B["mattress_th"], mat,
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
            posts=(xr, xf), posts_s={"pY": (xr_s[1], xf_s[1]), "nY": (xr_s[-1], xf_s[-1])},
            post_y=post_out - sd / 2.0, deck=(dx0, dx1), deck_w=2 * dhw,
            cross_x=[cx0 + (cx1 - cx0) * i / (nC - 1) for i in range(nC)],
            garage=z_rail_top - sw - floor_top, arch_top=floor_top + W["height"],
            cutlist=cutlist)

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "B bed_summary cutlist dx0 dx1 post_in post_in_s post_out post_out_s rail_in sd sw xf xr "
                     "ybase z_bolt z_rail_top")


def deck_cutouts(S):
    """Вырезы в щите кровати под стойки и головки болтов."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    B, doc, post_in_s = S.B, S.doc, S.post_in_s
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
                if bb.XMax < dsh.BoundBox.XMin or bb.XMin > dsh.BoundBox.XMax or bb.ZMax < dz0:
                    continue
                cut.append(Part.makeBox(bb.XLength + 6, bb.YLength + 6, bb.ZLength,
                                        App.Vector(bb.XMin - 3, bb.YMin - 3, bb.ZMin)))
        n_bolt = 0
        bh, bw_, bd = 14.0, 30.0, 12.0                                       # головка+шайба: ⌀~14, выступ ~12
        for o in doc.Objects:
            if o.Name.startswith("BedPostBodyBolt_") or o.Name.startswith("RackP2_BodyBolt"):
                c = o.Placement.Base                                 # Part::Sphere: центр (Shape — после recompute)
                if (c.z + bh / 2.0 > dz0 and c.z - bh / 2.0 < dz1
                        and dsh.BoundBox.XMin < c.x < dsh.BoundBox.XMax):
                    # вырез: от внутренней грани стойки (|Y|=post_in) на bd+3 в салон
                    pi_ = post_in_s[1 if c.y > 0 else -1]
                    y0 = (pi_ - bd - 3.0) if c.y > 0 else -pi_
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

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "deck_notes")
