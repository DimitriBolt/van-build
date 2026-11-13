# -*- coding: utf-8 -*-
"""Локер газового баллона 20 lb (вариант van_v1_rect_pan, 2026-11-12, Dimitri): на месте бывшего туалета под кроватью.

Баллон ⌀12.3″ × 17.8″ стоит на полу фургона через вырез в дне локера (толщину дна не учитываем); верх локера — акрил 1/8″;
дверца — на сторону прохода (−Y, к пассажирскому борту); вент ⌀1″ через пол вниз; газовая линия — через заднюю стенку душа
к нагревателю. Доступ к дверце: нижний ящик выкатывают НАЗАД (≈350 мм хватает; ход 900) — баллон меняют реже раза в год.
Порядок: после душа (нужны нагреватель и задняя стенка) и до ящиков (верх локера задаёт низ верхнего ящика, конец бака — его X)."""

import FreeCAD as App
import Part

from .common import add_shape
from .params_rect import PROPANE_RECT

V = App.Vector


def locker(S):
    """Локер баллона 20 lb + баллон + вент + газовая линия к нагревателю."""
    doc, floor_top, dx1 = S.doc, S.floor_top, S.dx1
    PR = PROPANE_RECT
    propane_summary = None
    if not PR.get("enable"):
        S.put(locals(), "propane_summary")
        return
    ks = 1
    gobj = lambda n: doc.getObject(n)
    bb = lambda n: gobj(n).Shape.BoundBox
    g = doc.addObject("App::DocumentObjectGroup", "Propane")
    g.Label = "Локер газового баллона 20 lb на месте туалета (проект 2026-11-12)"
    parts = {}

    def put(name, label, shape, color, tr=0):
        add_shape(doc, name, label, shape, color=color, transparency=tr, group=g)
        parts[name] = shape
        return shape

    wl = PR["wall"]
    cd, ch_ = PR["cyl_d"], PR["cyl_h"]
    inn = cd + 2.0 * PR["clear"]                                       # внутри — баллон с небольшим зазором
    outer = inn + 2.0 * wl
    z_l0 = floor_top
    z_wall1 = z_l0 + ch_                                               # стенки — до верха баллона (внутри его высота; дно не считаем)
    z_top = z_wall1 + PR["top_t"]                                      # верх акрила
    # X: вплотную к задней стенке душа / торцу поддона; Y: от арки к проходу (место бывшего туалета)
    lx1 = dx1 - PR["gap_wall"]
    lx0 = lx1 - outer
    arch = gobj("WheelArch_pY")
    ly1 = S.arch_ywall - (S.WA[ks]["protrusion"] + PR["gap_arch"])
    ly0 = ly1 - outer
    cx, cy = lx0 + outer / 2.0, ly0 + outer / 2.0
    # — ящик: 4 стенки + дно с вырезом под опорное кольцо (толщина дна над полом не учитывается: баллон стоит на полу) —
    shell = Part.makeBox(outer, outer, z_wall1 - z_l0, V(lx0, ly0, z_l0)).cut(
        Part.makeBox(inn, inn, z_wall1 - z_l0 - wl + 1.0, V(lx0 + wl, ly0 + wl, z_l0 + wl)))
    foot_hole = Part.makeCylinder(PR["foot_d"] / 2.0 + 2.0, wl + 2.0, V(cx, cy, z_l0 - 1.0))
    door_cut = Part.makeBox(outer, wl, (z_wall1 - z_l0) - wl, V(lx0, ly0, z_l0 + wl))          # дверца — грань к проходу (−Y)
    vx, vy = lx1 - wl - 20.0, ly1 - wl - 20.0                                                  # вент — в дальнем от дверцы углу
    vent_hole = Part.makeCylinder(PR["vent_d"] / 2.0, z_l0 + wl + 20.0, V(vx, vy, -20.0))
    box = shell.cut(door_cut).cut(foot_hole).cut(vent_hole)
    put("Propane_Locker", "Локер пропана — герметичный ящик (фанера 1/2″ + герметик/FRP), внутри %.1f×%.1f″, высота до акрила %.1f″ (впритык к "
        "баллону); в дне вырез под опорное кольцо (баллон стоит на полу); вент ⌀1″ через пол" % (inn / 25.4, inn / 25.4, ch_ / 25.4),
        box, (0.93, 0.85, 0.55))
    put("Propane_LockerDoor", "Дверца локера на сторону прохода (−Y): на уплотнителе, 2 замка-защёлки, открывается к пассажирскому борту; "
        "нижний ящик при этом выкатывают назад", shell.common(door_cut), (0.98, 0.75, 0.30))
    put("Propane_LockerLid", "Крышка локера — прозрачный акрил 1/8″ (3.2 мм) на уплотнителе: видно вентиль и редуктор; верх локера Z=%.1f мм" % z_top,
        Part.makeBox(outer, outer, PR["top_t"], V(lx0, ly0, z_wall1)), (0.75, 0.88, 0.95), 60)
    for fn in ("Floor_XPS", "Floor_Plywood"):
        fo = gobj(fn)
        if fo is not None:
            fo.Shape = fo.Shape.cut(vent_hole)
    put("Propane_Vent", "Вент-трубка локера ⌀1″ через пол вниз наружу (пропан тяжелее воздуха)",
        Part.makeCylinder(PR["vent_d"] / 2.0, z_l0 + wl + 40.0, V(vx, vy, -40.0)).cut(
            Part.makeCylinder(PR["vent_d"] / 2.0 - 2.0, z_l0 + wl + 50.0, V(vx, vy, -45.0))), (0.25, 0.25, 0.25))
    # — баллон: опорное кольцо + корпус + конус + воротник + вентиль —
    foot = PR["foot_d"]
    cyl = Part.makeCylinder(foot / 2.0, 40.0, V(cx, cy, z_l0)).cut(Part.makeCylinder(foot / 2.0 - 3.0, 50.0, V(cx, cy, z_l0 - 5.0))).fuse(
        Part.makeCylinder(cd / 2.0, ch_ - 40.0 - 40.0 - 62.0, V(cx, cy, z_l0 + 40.0))).fuse(
        Part.makeCone(cd / 2.0, cd * 0.28, 40.0, V(cx, cy, z_l0 + ch_ - 102.0))).fuse(
        Part.makeCylinder(cd * 0.30, 62.0, V(cx, cy, z_l0 + ch_ - 62.0)).cut(Part.makeCylinder(cd * 0.27, 70.0, V(cx, cy, z_l0 + ch_ - 64.0)))).fuse(
        Part.makeCylinder(22.0, 70.0, V(cx, cy, z_l0 + ch_ - 102.0 + 40.0)))
    put("Propane_Cylinder", "Баллон пропана %s, вертикально, вентилем вверх, стоит на полу фургона" % PR["title"], cyl, (0.96, 0.96, 0.96))
    put("Propane_Regulator", "Редуктор — внутри локера, на вентиле",
        Part.makeCylinder(45.0, 35.0, V(cx + 60.0, cy, z_l0 + ch_ - 70.0), V(1, 0, 0)), (0.75, 0.75, 0.78))
    # — газовая линия: из гермоввода в крышке → вверх под поперечины → вперёд через заднюю стенку душа (проходка) → вверх к нагревателю —
    rs = S.rect_summary
    pts = None
    if rs and rs.get("gas"):
        gas = rs["gas"]
        x_gv, y_gas, z_h0 = gas["heater_x"][0] + 14.0, gas["heater_y"][0] + 50.0, gas["heater_z"][0]
        z_g = bb("BedCross_3").ZMin - 25.0
        yb = min(max(y_gas, ly0 + 40.0), ly1 - 40.0)
        xb = lx1 - 7.0                      # у самой стенки душа: в щели между верхним ящиком и стенкой
        pts = [V(xb, yb, z_top), V(xb, yb, z_g), V(xb, y_gas, z_g), V(x_gv, y_gas, z_g), V(x_gv, y_gas, z_h0)]
        gl = None
        for p0_, p1_ in zip(pts, pts[1:]):
            if (p1_ - p0_).Length < 1.0:
                continue
            seg = Part.makeCylinder(5.0, (p1_ - p0_).Length, p0_, p1_ - p0_).fuse(Part.makeSphere(5.0, p1_))
            gl = seg if gl is None else gl.fuse(seg)
        put("Gas_Line", "Газ: шланг LP 3/8″ (RV, в оплётке) из гермоввода крышки локера → под поперечины → сквозь заднюю стенку душа "
            "(проходка) → к нагревателю; без соединений в салоне", gl, (0.95, 0.75, 0.10))
        put("Gas_Bulkhead", "Гермоввод газа в акриловой крышке локера", Part.makeCylinder(10.0, 15.0, V(xb, yb, z_top)), (0.45, 0.45, 0.45))
        put("Gas_WallGrommet", "Проходка газового шланга в задней стенке душа (резиновая, с гильзой)",
            Part.makeCylinder(14.0, 40.0, V(dx1 - 10.0, y_gas, z_g), V(1, 0, 0)), (0.25, 0.25, 0.25))
    # датчик пропана + CO — низко, на дверце (рядом с ящиком), на виду
    put("Safety_LPCO", "Датчик пропана + CO 12V (RV, низко — пропан стекает к полу), на дверце локера",
        Part.makeBox(120.0, 10.0, 85.0, V(cx - 60.0, ly0 - 10.0, z_l0 + 110.0)), (0.95, 0.30, 0.25))
    # — проверки —
    skip = ("Scan_", "Opening_", "RearDoorLeaf", "Floor_", "Propane_", "Gas_", "Safety_LPCO")
    obst = [(o.Name, o.Shape) for o in doc.Objects if o.isDerivedFrom("Part::Feature") and not o.Shape.isNull() and o.Shape.Solids
            and not o.Name.startswith(skip) and not o.Name.startswith("Drawer")]
    checks = []
    body = Part.makeCompound([parts["Propane_Locker"], parts["Propane_LockerDoor"], parts["Propane_LockerLid"], parts["Propane_Cylinder"]])
    dmin, nmin = min((body.distToShape(s_)[0], n_) for n_, s_ in obst)
    checks.append(("локер ↔ остальное (кроме ящиков и душа): ближе всего «%s»" % nmin, dmin))
    for nm_ in ("WheelArch_pY", "Shower_PanRect", "Shower_WallRear"):
        o_ = gobj(nm_)
        if o_ is not None:
            checks.append(("локер ↔ %s" % nm_, body.distToShape(o_.Shape)[0]))
    if pts is not None:
        glb = Part.makeCompound([parts["Gas_Line"]])
        dmin, nmin = min((glb.distToShape(s_)[0], n_) for n_, s_ in obst if n_ not in ("Shower_WallRear", "Shower_GasHeater") and not n_.startswith("Shower_GasHeater"))
        checks.append(("газовая линия ↔ остальное (кроме стенки душа и нагревателя): ближе всего «%s»" % nmin, dmin))
    propane_summary = dict(x=(lx0, lx1), y=(ly0, ly1), outer=outer, inner=inn, z_top=z_top, h=z_top - floor_top, door_y=ly0,
                           vent=(vx, vy), checks=checks, gas=[(p_.x, p_.y, p_.z) for p_ in pts] if pts else None)
    S.put(locals(), "propane_summary")


def report(S):
    k = S.propane_summary
    if not k:
        return
    print("=" * 70)
    print("[Локер баллона 20 lb на месте туалета — вариант van_v1_rect_pan, 2026-11-12]")
    print("  Локер: X %.0f..%.0f, Y %.0f..%.0f (%.0f × %.0f мм, внутри %.0f мм), верх (акрил 1/8″) %.0f мм над полом; дверца на −Y (к проходу), "
          "вент ⌀1″ в X %.0f, Y %.0f" % (k["x"][0], k["x"][1], k["y"][0], k["y"][1], k["outer"], k["outer"], k["inner"], k["h"], k["vent"][0], k["vent"][1]))
    print("  Зазоры: " + "; ".join("%s %.1f" % (n_, v_) for n_, v_ in k["checks"]))
    print("=" * 70)
