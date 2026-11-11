# -*- coding: utf-8 -*-
"""Собрать van_v0.py (headless) и выгрузить данные для 2D-чертежей в docs/drawing_data.json.

    freecadcmd tools/export_drawing_data.py          # (на M6800: FreeCAD.AppImage --console …)

Что выгружается: параметры (WHEEL_ARCH, BED, BATTERY_RACK, WATER_TANK, FLOOR), габариты всех
деталей (Part::Feature → bbox), сечения бака/арки/подставки (для чертежа бака).
Чертежи строит tools/drawings/*.py (обычный python3 + matplotlib), всё вместе — tools/make_docs.sh.
"""
import io
import json
import os
import contextlib
import traceback


def _repo_dir():
    if os.environ.get("VAN_REPO"):
        return os.environ["VAN_REPO"]
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.dirname(os.path.abspath(f)))
    return os.path.expanduser("~/van-build")


REPO = _repo_dir()
SCRIPT = os.path.join(REPO, "van_v0.py")
OUT = os.path.join(REPO, "docs", "drawing_data.json")
rc = 0
res = {}
try:
    g = {"__file__": SCRIPT, "__name__": "__main__"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), g)
    import FreeCAD as App
    doc = App.ActiveDocument
    res["summary"] = buf.getvalue()[buf.getvalue().find("[Кровать"):] if "[Кровать" in buf.getvalue() else ""
    for k in ("WHEEL_ARCH", "DPILLAR", "BED", "BATTERY_RACK", "ELECTRICAL", "WATER_TANK", "TANK_RACK", "TANK_FLOOR",
              "WATER_VARIANT", "SHOWER_KITCHEN", "ANCHORS",
              "FLOOR", "PARAMS"):
        res[k] = json.loads(json.dumps(g[k], default=lambda o: list(o) if isinstance(o, tuple) else str(o)))
    boxes = {}
    for o in doc.Objects:
        sh = getattr(o, "Shape", None)
        if o.isDerivedFrom("Part::Feature") and sh is not None and not sh.isNull():
            b = sh.BoundBox
            boxes[o.Name] = [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]
    res["boxes"] = boxes
    half = g["measured_half_profile"](g["scan_points"]())
    yz = g["y_at_z"]
    B, P = g["BED"], g["PARAMS"]
    floor_top = P["floor_corrugation_height"] + g["FLOOR"]["xps_th"] + g["FLOOR"]["ply_th"]
    z_bolt = floor_top + B["body_bolt_h"]
    res["geo"] = dict(floor_top=floor_top, arch_ywall=yz(half, 0.0), yw_post=yz(half, z_bolt),
                      z_bolt=z_bolt, z_rail_top=floor_top + B["rail_top_h"] + B.get("rail_raise", 0.0))

    res["geo"]["half"] = [list(p) for p in half]
    # передняя грань короба D-стойки у края фанеры (как в van_v0.py)
    W_, DP_ = g["WHEEL_ARCH"], g["DPILLAR"]
    a_pw = (W_["len_x_wall"] - (W_["len_x_wall"] - W_["len_x"]) * DP_["photo_wall"] / W_["protrusion"]) / 2.0
    res["geo"]["x_dp"] = W_["center_x"] - a_pw - DP_["to_arch"]

    # — задние углы: сечения арки и D-стойки у пола (план) —
    corners = {}
    for tag in ("pY", "nY"):
        c = {}
        for nm, obj in (("arch", "WheelArch_%s" % tag), ("dpillar", "DPillarFace_%s_ref" % tag)):
            sh = doc.getObject(obj).Shape
            c[nm] = [[(p.x, p.y) for p in w.discretize(Distance=2.0)]
                     for w in sh.slice(App.Vector(0, 0, 1), floor_top + 2.0)]
        corners[tag] = c
    res["corners"] = corners

    def _slice(shape, normal, d):
        out = []
        for w in shape.slice(App.Vector(*normal), d):
            out.append([(p.x, p.y, p.z) for p in w.discretize(Distance=3.0)])
        return out

    # — душ + кухня: поперечные сечения (YZ) —
    if doc.getObject("Shower_Pan") is not None:
        sb, kb = boxes["Shower_Pan"], boxes["Kitchen_Carcass"]
        xs_sh = (sb[0] + sb[1]) / 2.0
        if "Shower_Drain" in boxes:                          # поддон-сектор: разрез через слив
            xs_sh = (boxes["Shower_Drain"][0] + boxes["Shower_Drain"][1]) / 2.0
        xs_k = (boxes["Kitchen_Sink"][0] + boxes["Kitchen_Sink"][1]) / 2.0
        sec = {"x_shower": xs_sh, "x_kitchen": xs_k, "shower": {}, "kitchen": {}}
        for o in doc.Objects:
            if o.Name.startswith("Shower_") and o.Name != "Shower_WallRear":
                sec["shower"][o.Name] = _slice(o.Shape, (1, 0, 0), xs_sh)
            elif o.Name.startswith("Kitchen_"):
                sec["kitchen"][o.Name] = _slice(o.Shape, (1, 0, 0), xs_k)
        sec["kitchen"]["Kitchen_Kettle"] = _slice(doc.getObject("Kitchen_Kettle").Shape, (1, 0, 0),
                                                  (boxes["Kitchen_Kettle"][0] + boxes["Kitchen_Kettle"][1]) / 2.0)
        # 2026-11-07: разрез по холодильнику (секция 2), план на разных высотах (вогнутый торец кухни),
        # разрез под кроватью по локеру пропана (взгляд к кабине)
        if "Kitchen_Fridge" in boxes:
            xs_f = (boxes["Kitchen_Fridge"][0] + boxes["Kitchen_Fridge"][1]) / 2.0
            sec["x_fridge"] = xs_f
            sec["fridge"] = {o.Name: _slice(o.Shape, (1, 0, 0), xs_f) for o in doc.Objects
                             if o.Name.startswith("Kitchen_") and o.isDerivedFrom("Part::Feature")}
        ct = boxes["Kitchen_Countertop"]
        plan = {}
        for nm, z in (("Kitchen_Countertop", (ct[4] + ct[5]) / 2.0), ("Kitchen_Carcass", 700.0),
                      ("Kitchen_Plinth", floor_top + 30.0), ("Kitchen_UpperCabinet", 1700.0),
                      ("Shower_Ceiling", boxes["Shower_Ceiling"][4] + 6.0)):
            if nm in boxes:
                plan[nm] = [[(p[0], p[1]) for p in w] for w in _slice(doc.getObject(nm).Shape, (0, 0, 1), z)]
        sec["plan"] = plan
        if "Propane_Locker" in boxes:
            lb = boxes["Propane_Locker"]
            xs_l = (lb[0] + lb[1]) / 2.0
            sec["x_locker"] = xs_l
            sec["locker"] = {}
            for o in doc.Objects:
                if o.isDerivedFrom("Part::Feature") and o.Name.startswith(
                        ("Propane_", "Toilet_", "BedDeck", "BedMattress", "BedCross", "BedSideRail_pY", "WaterTank_",
                         "BankShelf", "BankRail_Inner", "Water_Pump", "TankFloor_Cleat_Aisle", "Safety_")):
                    sl = _slice(o.Shape, (1, 0, 0), xs_l)
                    if sl:
                        sec["locker"][o.Name] = sl
        sec["gas_pts"] = g["SHOWER_KITCHEN"].get("_gas_pts")
        res["galley"] = sec

    # — багажник (3 ящика + хребет): разрезы по P3/стойке хребта 1 (X 395) и по подвесу/P3m/стойке хребта 2 (X 848) —
    if doc.getObject("Trunk2_TrayFwd") is not None:
        TSS = g["TRUNK_SHELF"]["_summary"]
        pref = ("Battery_B", "BankShelf", "BankRail", "BankPost", "BankCross", "WaterTank_", "TankFloor_", "Trunk2_",
                "Trunk1_", "BedDeck", "BedMattress", "BedSideRail", "WheelArch_", "BedPost_", "BedCross_", "Toilet_",
                "Propane_", "Water_Pump")
        for key, xs_ in (("trunk", 395.0), ("trunk3", 848.0)):
            tr = {"x": xs_}
            for o in doc.Objects:
                if o.isDerivedFrom("Part::Feature") and o.Name.startswith(pref) and not o.Name.endswith(("_Out", "_Front")):
                    sl = _slice(o.Shape, (1, 0, 0), xs_)
                    if sl:
                        tr[o.Name] = sl
            res[key] = tr
        res["TRUNK_SHELF"] = json.loads(json.dumps(g["TRUNK_SHELF"], default=lambda o: list(o) if isinstance(o, tuple) else str(o)))

    # — шкафчики под потолком: сечения первого шкафчика каждого ряда (профиль борта) —
    if doc.getObject("CabPass_1") is not None:
        cab = {}
        for nm in ("CabPass_1", "CabDrv_1"):
            o = doc.getObject(nm)
            if o is not None:
                xc = (o.Shape.BoundBox.XMin + o.Shape.BoundBox.XMax) / 2.0
                cab[nm] = _slice(o.Shape, (1, 0, 0), xc)
                for o2 in doc.Objects:
                    if o2.isDerivedFrom("Part::Feature") and o2.Name.startswith(("BedMattress", "BedDeck", "Battery_B2",
                                                                                "BankShelf")):
                        sl = _slice(o2.Shape, (1, 0, 0), xc)
                        if sl:
                            cab.setdefault("_ctx", {})[o2.Name + "@" + nm] = sl
        res["cabinets"] = cab
        res["WALL_CABINETS"] = json.loads(json.dumps(g["WALL_CABINETS"], default=str))

    # — strut: сечения, где видно спинку (с отверстиями) и паз — 2026-11-08 —
    pref = ("BedPost_", "BedSideRail", "BedCross_", "BankPost_P3", "BankRail_", "BankCross_", "BankHolddown",
            "Battery_B", "BankShelf", "BedDeck", "BankRailBolt", "Trunk2_")
    planes = {"yz600": ((1, 0, 0), 600.0), "yz377": ((1, 0, 0), 377.3), "xy300": ((0, 0, 1), 300.0),
              "xy466": ((0, 0, 1), 466.0), "xy1000": ((0, 0, 1), 1000.0), "xz0": ((0, 1, 0), 0.0),
              "xzm850": ((0, 1, 0), -850.0)}
    st = {}
    for key, (nv, val) in planes.items():
        st[key] = {}
        for o in doc.Objects:
            if o.isDerivedFrom("Part::Feature") and o.Name.startswith(pref):
                sl = _slice(o.Shape, nv, val)
                if sl:
                    st[key][o.Name] = sl
    res["strut"] = st
    res["STRUT_BACK"] = [[p, b] for p, b in g["STRUT_BACK"]]

    # — бак T-3500 на полке над аркой: поперечный разрез (YZ) по первому ремню —
    trk_o = doc.getObject("WaterTank_T3500")
    if trk_o is not None:
        TR = g["TANK_RACK"]
        tag = "pY" if TR["side"] > 0 else "nY"
        xs_ = min(TR["_summary"]["straps"], key=lambda x_: abs(x_ - g["WHEEL_ARCH"]["center_x"]))   # ремень над аркой
        sec = {"x": xs_}
        for nm in ("WaterTank_T3500", "TankStrap_1", "WheelArch_%s" % tag, "BedMattress", "BedDeck"):
            sec[nm] = _slice(doc.getObject(nm).Shape, (1, 0, 0), xs_)
        res["trk"] = sec

    # — бак T-4100 на полу: поперечный разрез (YZ) по ремню ближе к центру арки —
    tfl_o = doc.getObject(g["TANK_FLOOR"].get("_summary", {}).get("tank_name", "WaterTank_T4100")) \
        if g["TANK_FLOOR"].get("enable") else None
    if tfl_o is not None:
        TF = g["TANK_FLOOR"]
        tag = "pY" if TF["side"] > 0 else "nY"
        if TF.get("base") == "pallet":                  # по ремню ближе к центру арки
            xs_ = min(TF["_summary"]["straps"], key=lambda x_: abs(x_ - g["WHEEL_ARCH"]["center_x"]))
            strap_nm = "TankFloor_Strap_%d" % (1 + TF["_summary"]["straps"].index(xs_))
        else:                                           # ремни — за аркой; разрез — у проставки к арке
            sb = boxes["TankFloor_ArchSpacer_1"]
            xs_, strap_nm = (sb[0] + sb[1]) / 2.0, None
        sec = {"x": xs_}
        for key, nm in (("tank", TF["_summary"]["tank_name"]), ("strap", strap_nm),
                        ("arch", "WheelArch_%s" % tag), ("mattress", "BedMattress"), ("deck", "BedDeck")):
            if nm is None:
                continue
            sec[key] = _slice(doc.getObject(nm).Shape, (1, 0, 0), xs_)
        res["tfl"] = sec

    # — сечения бака (если он есть) —
    tank_o = doc.getObject("WaterTank_TORVA33")
    if tank_o is not None:
        T = g["WATER_TANK"]
        sgn = T["side"]
        tag = "pY" if sgn > 0 else "nY"
        tank, arch = tank_o.Shape, doc.getObject("WheelArch_%s" % tag).Shape
        risers = [o.Shape for o in doc.Objects if o.Name.startswith("TankRiser_")]
        ywall = res["geo"]["arch_ywall"]

        def slice_pts(shape, normal, d):
            out = []
            for w in shape.slice(App.Vector(*normal), d):
                out.append([(p.x, p.y, p.z) for p in w.discretize(Distance=4.0)])
            return out

        tbb = tank.BoundBox
        yb = tbb.YMax if sgn > 0 else -tbb.YMin                   # задняя (к стене) грань бака
        d, sol, _ = tank.distToShape(arch)
        tk = dict(y_back=yb, closest=[[sol[0][0].x, sol[0][0].y, sol[0][0].z],
                                      [sol[0][1].x, sol[0][1].y, sol[0][1].z], d])
        ye = sgn * (yb - 5.0)
        tk["elev_tank"] = slice_pts(tank, (0, 1, 0), ye)
        tk["elev_arch"] = slice_pts(arch, (0, 1, 0), ye)
        tk["elev_arch_wall"] = slice_pts(arch, (0, 1, 0), sgn * (ywall - 2.0))
        tk["elev_riser"] = sum((slice_pts(r, (0, 1, 0), sgn * (yb - 300.0)) for r in risers), [])
        tk["sec"] = {}
        for x in (1000.0,):
            tk["sec"][str(x)] = dict(tank=slice_pts(tank, (1, 0, 0), x), arch=slice_pts(arch, (1, 0, 0), x),
                                     riser=sum((slice_pts(r, (1, 0, 0), x) for r in risers), []))
        lift = boxes["TankRiser_Sleeper_Foot1"][5] - floor_top
        zt = floor_top + lift + 150.0
        tk["plan_z"] = zt
        tk["plan_tank"] = slice_pts(tank, (0, 0, 1), zt)
        tk["plan_arch"] = slice_pts(arch, (0, 0, 1), zt)
        tk["plan_arch0"] = slice_pts(arch, (0, 0, 1), 60.0)
        dp = doc.getObject("DPillarFace_%s_ref" % tag).Shape
        tk["dpillar_plan"] = [(v.X, v.Y) for v in dp.Vertexes if abs(v.Z) < 1e-6]
        tb = tank.BoundBox
        tk["lift"] = lift
        tk["tank_bb"] = [tb.XMin, tb.XMax, tb.YMin, tb.YMax, floor_top + lift, floor_top + lift + T["size"][2]]
        res["tank"] = tk
except Exception:
    res["error"] = traceback.format_exc()
    rc = 1
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)
print("export_drawing_data:", OUT, "OK" if rc == 0 else "ERROR")
if rc:
    print(res.get("error"))
os._exit(rc)
