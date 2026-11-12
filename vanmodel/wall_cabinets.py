# -*- coding: utf-8 -*-
"""Шкафчики под потолком по бортам."""

import FreeCAD as App
import Part

from .params import SHOWER_KITCHEN, WALL_CABINETS
from .common import add_shape
from .scan import y_at_z

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def wall_cabinets(S):
    """Шкафчики под потолком по обоим бортам."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    doc, dx1, floor_top, half, slider_x0 = S.doc, S.dx1, S.floor_top, S.half, S.slider_x0
    # ═══════ ШКАФЧИКИ ПОД ПОТОЛКОМ по бортам (проект 2026-11-07) ═══════
    cab_summary = []
    WC = WALL_CABINETS
    if WC.get("enable"):
        cg = doc.addObject("App::DocumentObjectGroup", "WallCabinets")
        cg.Label = "Шкафчики под потолком — пассажирский борт и над изголовьем (проект 2026-11-07)"
        crown_ = half[-1][1]
        z_cl = crown_ - SHOWER_KITCHEN.get("roof_clear", 55.0)
        pz_ = sorted(z for _, z in half if z < crown_)
        wg = WC["wall_gap"]
        ywc = lambda z: y_at_z(half, min(z, pz_[-1])) - wg
        mat_ = doc.getObject("BedMattress")
        for st_ in WC["sets"]:
            sg_ = st_["side"]
            cx_, cd_, ch_ = st_["dims"]
            z1 = z_cl - WC["ceil_gap"]
            for _ in range(80):                                     # верх — пока у задней стенки остаётся глубина
                z0 = z1 - ch_
                yf = ywc(z0) - cd_
                if ywc(z1) >= yf + 60.0:
                    break
                z1 -= 10.0
            rpn = doc.getObject("Pillar_Rear_%s" % ("pY" if sg_ > 0 else "nY"))
            xa = (rpn.Shape.BoundBox.XMax if rpn is not None else 80.0) + 5.0
            if st_["to"] == "slider":
                xb = slider_x0 - 5.0
            else:
                rw_ = doc.getObject("Shower_WallRear")
                xb = (rw_.Shape.BoundBox.XMin if rw_ is not None else dx1) - 5.0
            for rb_ in sorted((o.Shape.BoundBox for o in doc.Objects if o.Name.startswith("Rib_x")), key=lambda b: b.XMin):
                if rb_.XMin < xa + cx_ and rb_.XMax > xa - 1.0:       # гнутое ребро крыши у задней двери — за ним
                    xa = rb_.XMax + 5.0
            n_ = int((xb - xa + WC["between"]) // (cx_ + WC["between"]))
            zs_ = [z0] + [z for z in pz_ if z0 < z < z1] + [z1]
            pts_ = [(yf, z0), (yf, z1)] + [(ywc(z), z) for z in reversed(zs_)]
            boxes_ = []
            for i in range(n_):
                xi = xa + i * (cx_ + WC["between"])
                vec = [App.Vector(xi, sg_ * y, z) for y, z in pts_]
                sol = Part.Face(Part.makePolygon(vec + [vec[0]])).extrude(App.Vector(cx_, 0, 0))
                nm = "Cab%s_%d" % (st_["name"], i + 1)
                add_shape(doc, nm, "%s %d — %s; боковины вырезаны по профилю борта" % (st_["title"], i + 1, st_["desc"]),
                          sol, color=(0.86, 0.68, 0.40), group=cg)
                add_shape(doc, nm + "_Door", "Дверца шкафчика %s %d" % (st_["title"].split()[-1], i + 1),
                          Part.makeBox(cx_ - 6.0, 4.0, ch_ - 6.0, App.Vector(xi + 3.0, sg_ * yf - (4.0 if sg_ > 0 else 0.0),
                                                                           z0 + 3.0)), color=(0.93, 0.78, 0.50), group=cg)
                boxes_.append(sol)
            chk = []
            for lab, pref in (("рёбра кузова", "Rib_x"), ("продольные рейки кузова", "Rail_"), ("стойки кровати", "BedPost_"),
                              ("душ", "Shower_"), ("электрика", "Elec_")):
                ss = [o.Shape for o in doc.Objects if o.Name.startswith(pref) and o.isDerivedFrom("Part::Feature")
                      and not o.Shape.isNull() and o.Shape.Solids]
                if ss and boxes_:
                    chk.append((lab, min(b.distToShape(s_)[0] for b in boxes_ for s_ in ss)))
            cab_summary.append(dict(name=st_["title"], n=n_, x=(xa, xa + n_ * cx_ + (n_ - 1) * WC["between"]), free=xb - (
                xa + n_ * cx_ + (n_ - 1) * WC["between"]), z=(z0 - floor_top, z1 - floor_top), y_front=yf,
                over_mat=(z0 - mat_.Shape.BoundBox.ZMax) if mat_ is not None else None, depth_top=ywc(z1) - yf,
                from_wall=y_at_z(half, z0) - yf, checks=chk))

    # ── в контекст сборки S: то, что нужно следующим разделам ──
    S.put(locals(), "cab_summary")
