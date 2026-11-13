# -*- coding: utf-8 -*-
"""Strut channel: настоящий C-профиль (спинка с овальными отверстиями + паз) и ориентация каждой детали."""

import FreeCAD as App
import Part

from .common import COL_STRUT, _INTENDED, add_shape

# ─────────── STRUT: настоящий профиль (спинка с отверстиями + паз) — 2026-11-08 ───────────
# Dimitri: «у strut рисуй на спинке заводские овальные отверстия — знать, какой стороной стоит channel, критично».
# Профиль shallow 1-5/8 × 13/16″, 14 ga; в спинке овалы 9/16 × 1-1/8″ с шагом 2″. Ориентация — по фото Dimitri
# (стойка кровати: отверстия видны из салона; рейка кровати — спинкой к спинке стойки, паз в салон; P3 ↔ рейка
# у прохода — спинка к спинке), остальное — предположение (Dimitri поправит).
STRUT = {"W": 41.3, "D": 20.6, "t": 1.9, "slot_open": 22.0, "lip_ret": 6.0,
         "hole": (28.6, 14.3), "pitch": 50.8, "hole0": 25.4}
# имя (regex) → куда смотрит СПИНКА: "aisle" (в проход), "wall" (к борту), "+X/-X/+Z/-Z" (мировые оси)
STRUT_BACK = [
    (r"BedPost_(pY|nY)_(rear|front)$", "aisle"),    # фото 2: отверстия видны из салона, паз к кузову
    (r"BedSideRail_(pY|nY)$", "wall"),              # фото: спинкой к спинке стойки, паз в салон
    (r"BedCross_\d$", "-X"),                       # ? стоит на ребре; спинка назад (к задним дверям)
    (r"BankRail_Wall$", "wall"),                    # ? как рейка кровати: спинкой к стойкам, паз в салон
    (r"BankPost_P3f?$", "wall"),                    # п. 4 Dimitri: P3 спинкой к рейке (к борту), паз в проход
    (r"BankRail_Inner$", "aisle"),                  # п. 4: спинкой к P3, паз к борту (под батареями)
    (r"BankCross_(Rear|Front)$", "-X"),             # ? на ребре между рейками
    (r"BankHolddown_B1$", "-X"),                    # ?
    (r"Trunk2_PostP3m$", "wall"),                   # как P3: спинка к рейке батарей, паз в проход (направляющая)
    (r"Trunk2_SpinePost_\d$", "-Y"),               # хребет (Dimitri: развернуть на 180°): спинка — к ящикам (направляющие), паз — к полке
    (r"Trunk2_ShelfCleat_S\d$", "-Y"),             # опора полки: спинкой к пазу стойки хребта (гайка-канал)
    (r"Trunk2_ShelfCleat_W$", "+Y"),                # опора полки: спинка к спинке со стойкой кровати pY rear
]


STRUT_HOLE0 = {}     # имя детали → от начала (меньшей координаты) до центра первого овала, мм (по умолчанию STRUT["hole0"])


def strut_shape(bb, back, side_sign, hole0=None):
    """C-профиль в габарите bb (BoundBox): длина — по наибольшему размеру, глубина — по оси нормали спинки."""
    W, D, t = STRUT["W"], STRUT["D"], STRUT["t"]
    ext = {"X": (bb.XMin, bb.XMax), "Y": (bb.YMin, bb.YMax), "Z": (bb.ZMin, bb.ZMax)}
    unit = {"X": App.Vector(1, 0, 0), "Y": App.Vector(0, 1, 0), "Z": App.Vector(0, 0, 1)}
    la = max(ext, key=lambda a: ext[a][1] - ext[a][0])
    if back in ("aisle", "wall"):
        nax, nsg = "Y", (-side_sign if back == "aisle" else side_sign)
    else:
        nax, nsg = back[1], (1 if back[0] == "+" else -1)
    if nax == la:
        return None
    wa = ({"X", "Y", "Z"} - {la, nax}).pop()
    if abs((ext[nax][1] - ext[nax][0]) - D) > 3.0 or abs((ext[wa][1] - ext[wa][0]) - W) > 3.0:
        return None
    L = ext[la][1] - ext[la][0]
    lip = (W - STRUT["slot_open"]) / 2.0 - t
    sh = Part.makeBox(L, W, t)                                          # спинка (local: x=длина, y=ширина, z=глубина)
    for y0 in (0.0, W - t):
        sh = sh.fuse(Part.makeBox(L, t, D, App.Vector(0, y0, 0)))
    for y0 in (t, W - t - lip):
        sh = sh.fuse(Part.makeBox(L, lip, t, App.Vector(0, y0, D - t)))
    for y0 in (t + lip - t, W - t - lip):
        sh = sh.fuse(Part.makeBox(L, t, STRUT["lip_ret"], App.Vector(0, y0, D - STRUT["lip_ret"])))
    hl, hw = STRUT["hole"]
    holes = []
    x = STRUT["hole0"] if hole0 is None else hole0
    while x - hl / 2.0 < 0:
        x += STRUT["pitch"]
    while x + hl / 2.0 < L:
        r_ = hw / 2.0
        hs = Part.makeBox(hl - hw, hw, 3 * t, App.Vector(x - (hl - hw) / 2.0, W / 2.0 - r_, -t)).fuse(
            Part.makeCylinder(r_, 3 * t, App.Vector(x - (hl - hw) / 2.0, W / 2.0, -t))).fuse(
            Part.makeCylinder(r_, 3 * t, App.Vector(x + (hl - hw) / 2.0, W / 2.0, -t)))
        holes.append(hs)
        x += STRUT["pitch"]
    if holes:
        sh = sh.cut(Part.makeCompound(holes))
    sh = sh.removeSplitter()
    el = unit[la]
    ed = unit[nax] * (-nsg)                                              # от спинки к пазу
    ew = ed.cross(el)
    org = App.Vector(0, 0, 0)
    for a in "XYZ":
        if a == la:
            v = ext[a][0]
        elif a == nax:
            v = ext[a][1] if nsg > 0 else ext[a][0]                     # плоскость спинки
        else:
            v = ext[a][0] if getattr(ew, a.lower()) > 0 else ext[a][1]
        setattr(org, a.lower(), v)
    m = App.Matrix(el.x, ew.x, ed.x, org.x, el.y, ew.y, ed.y, org.y, el.z, ew.z, ed.z, org.z, 0, 0, 0, 1)
    return sh.transformGeometry(m)


def apply_strut_profiles(doc):
    import re as _re
    done, skipped = [], []
    for o in list(doc.Objects):
        back = next((b for pat, b in STRUT_BACK if _re.match(pat, o.Name)), None)
        if back is None or not o.isDerivedFrom("Part::Feature"):
            continue
        if "V-Slot" in o.Label:                      # деталь из профиля V-Slot 2020, не strut
            continue
        bb = o.Shape.BoundBox
        side = 1 if (bb.YMin + bb.YMax) > 0 else -1
        try:
            shp = strut_shape(bb, back, side, STRUT_HOLE0.get(o.Name))
        except Exception as e:
            shp = None
        if shp is None:
            skipped.append(o.Name)
            continue
        name, label = o.Name, _INTENDED.get(o.Name, o.Label)
        grp = o.getParentGroup()
        doc.removeObject(name)
        add_shape(doc, name, label + "; спинка (отверстия 2″) → %s" % {"aisle": "в проход", "wall": "к борту",
                  "+X": "вперёд", "-X": "назад", "+Z": "вверх", "-Z": "вниз",
                  "+Y": "к водит. борту", "-Y": "к пасс. борту"}[back], shp,
                  color=(0.90, 0.25, 0.20) if "⚠️" in label else COL_STRUT, transparency=55 if "⚠️" in label else None,
                  group=grp)
        done.append(name)
    print("[STRUT] профиль со спинкой/пазом: %d деталей; пропущено: %s" % (len(done), ", ".join(skipped) or "—"))
