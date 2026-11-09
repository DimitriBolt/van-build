# -*- coding: utf-8 -*-
"""Собрать van_v0.py в FreeCAD GUI (с цветами) и сохранить PNG-виды.

Запуск (окно FreeCAD откроется, соберёт модель, снимет виды и закроется само):
    ~/Applications/FreeCAD.AppImage ~/van-build/tools/render_views.py
Без экрана (сервер/облако):
    xvfb-run -a -s "-screen 0 1920x1200x24" freecad tools/render_views.py

Результат:
    van_v0.FCStd  — пересохранён рядом со скриптом, С цветами (GuiDocument.xml)
    renders/*.png — изометрия со сканом и без, вид сверху, вид от задних дверей
Переменные окружения (необязательно): VAN_REPO, RENDER_OUT, RENDER_W, RENDER_H.

Выход через os._exit: FreeCAD не переписывает user.cfg при закрытии
(важно — там настройки кнопок SpaceExplorer) и не падает на закрытии Mesh-документа.
"""
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui


def _repo_dir():
    if os.environ.get("VAN_REPO"):
        return os.environ["VAN_REPO"]
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.dirname(os.path.abspath(f)))
    return os.path.expanduser("~/van-build")


REPO = _repo_dir()
SCRIPT = os.path.join(REPO, "van_v0.py")
OUT = os.environ.get("RENDER_OUT", os.path.join(REPO, "renders"))
W = int(os.environ.get("RENDER_W", 1800))
H = int(os.environ.get("RENDER_H", 1100))

# (файл, метод вида, префиксы скрываемых объектов)
# X = длина фургона, поэтому «от задних дверей в салон» = viewLeft (смотрим вдоль +X)
# Скрытие — по ПОДСТРОКЕ в имени объекта.
_NOT_BED = ("Scan_Skin", "Opening", "RearDoorLeaf", "Rib_x", "Rail_pY_z", "Rail_nY_z", "Pillar_",
            "Hole_", "FactoryThread", "FloorCorrugation", "Floor_XPS$", "Floor_Plywood$")
VIEWS = [
    ("iso_with_skin.png", "viewIsometric", ()),
    ("iso_frame.png", "viewIsometric", ("Scan_Skin",)),
    ("top_frame.png", "viewTop", ("Scan_Skin",)),
    ("from_rear_doors.png", "viewLeft", ("Scan_Skin", "Opening_RearDoors", "RearDoorLeaf")),
    # кровать крупно
    ("bed_iso.png", "viewIsometric", _NOT_BED),
    # пассажирский борт (−Y) изнутри, зад справа — как фото 2; водительские (_pY) детали скрыты
    ("bed_passenger_wall.png", "viewRear", _NOT_BED + ("_pY", "BedCross", "BedDeck", "BedMattress")),
]
# этажерки под батареи: кровать и всё дальнее скрыто. Элемент, оканчивающийся на "$", —
# ТОЧНОЕ имя объекта (иначе подстрока).
_RACK_HIDE = _NOT_BED + ("CabPass", "CabDrv", "_pY", "BedSideRail", "BedDeck", "BedMattress", "BedWall",
                         "BedPostBodyBolt", "RailBolt", "Tank", "Shower_", "Kitchen_", "Water_", "Toilet", "Propane_",
                         "Gas_", "Safety_")
_REAR_RACK = tuple(n + "$" for n in (
    "Battery_Lower", "Battery_Upper", "RackPostPlate_P2", "BedPost_nY_rackP2", "RackP2_BodyBolt",
    "RackShelfRail_Rear", "RackShelfRail_Front", "RackShelfPlate", "RackShelfFrontStop", "RackRubberBlock",
    "RackPostPlate_P3", "RackPost_P3", "RackPostPlate_P4", "RackPost_P4", "BedCross_RackFront",
    "RackLowerFrontStop", "DPillarFace_nY_ref", "BedPost_nY_rear", "BedPostPlate_nY_rear", "BedCross_1"))
VIEWS += [
    # этажерка на 4 батареи (пассажирский борт): из салона спереди-сверху, сзади-сверху, на борт, сверху
    ("bank_3d.png", (0.55, 1.0, -0.55), _RACK_HIDE + ("BedCross",)),          # из салона, сзади-сверху
    ("bank_wall_view.png", "viewRear", _RACK_HIDE + ("BedCross",)),
    ("bank_top.png", "viewTop", _RACK_HIDE + ("BedCross",)),
]
# бак T-3500 на полке над водительской аркой: пассажирский борт и всё с него скрыто
_TANK_HIDE = _NOT_BED + ("CabPass", "CabDrv", "_nY", "Battery_", "Bank", "RackShelf", "RackPost", "RackRubber", "RackLower", "RackP2",
                         "BedDeck", "BedMattress", "BedWall", "BedPostBodyBolt",
                         "Shower_", "Kitchen_", "Propane_", "Gas_", "Safety_", "Elec_", "Cable_")
VIEWS += [
    # из салона на водительский борт, сверху-сзади (взгляд вперёд-влево-вниз)
    ("tank_3d.png", (0.45, 1.0, -0.6), _TANK_HIDE),
    # прямо на водительский борт из салона: зад слева, перед справа
    ("tank_wall_view.png", "viewFront", _TANK_HIDE + ("BedCross", "BedSideRail")),
    ("tank_top.png", "viewTop", _TANK_HIDE + ("BedCross", "BedSideRail")),
]
# душ + мини-кухня (водительский борт, перед кроватью)
_GALLEY_HIDE = _NOT_BED + ("CabPass", "CabDrv", "_nY", "Battery_", "Bank", "Elec_", "Cable_", "RackShelf", "RackPost", "RackRubber", "RackLower", "RackP2",
                           "BedWall", "BedPostBodyBolt", "DPillar")
VIEWS += [
    # из прохода у сдвижной двери на водительский борт, сверху-сзади
    ("galley_3d.png", (0.55, 1.0, -0.5), _GALLEY_HIDE),
    # прямо на водительский борт (зад слева, кабина справа); шторка и дверца сняты, чтобы видеть внутри
    ("galley_wall_view.png", "viewFront", _GALLEY_HIDE + ("Shower_Curtain$", "Kitchen_DoorUpper$", "Kitchen_DoorSink$",
                                                         "BedMattress")),
    # 2026-11-07: из кабины назад — задняя стенка душа с газовым нагревателем, под щитом локер пропана и туалет
    ("shower_rear_wall.png", "viewRight", _GALLEY_HIDE + ("Kitchen_", "Shower_Curtain", "Shower_WallBack$",
                                                         "Propane_LockerDoor$")),
    # под кроватью: щит, матрас и поперечины сняты; дверца локера снята — виден баллон
    ("propane_3d.png", (0.55, 1.0, -0.5), _GALLEY_HIDE + ("BedDeck", "BedMattress", "BedCross", "Shower_Wall",
                                                         "Shower_Ceiling$", "Shower_Curtain", "Kitchen_UpperCabinet$",
                                                         "Propane_LockerDoor$")),
    # сверху: без потолка душа и верхнего шкафчика
    ("galley_top.png", "viewTop", _GALLEY_HIDE + ("Shower_Ceiling$", "Shower_ExhaustFan$", "Kitchen_UpperCabinet$",
                                                 "BedDeck", "BedMattress", "BedCross", "BedSideRail")),
]


# 2026-11-07: багажник с 2-м этажом (перфолист) — от задних дверей и сверху-сзади, щит/матрас сняты
_TRUNK_HIDE = ("CabPass", "CabDrv", "Scan_Skin", "Opening", "RearDoorLeaf", "Rib_x", "Rail_pY_z", "Rail_nY_z", "Pillar_", "Hole_",
               "FactoryThread", "BedMattress", "Shower_", "Kitchen_", "Elec_", "Cable_")
VIEWS += [
    # 2026-11-07: шкафчики под потолком (из кабины назад) и откидная столешница (из прохода к кабине)
    ("cabinets_3d.png", (-1.0, 0.0, -0.3), tuple(h for h in _TRUNK_HIDE if not h.startswith("Cab")) +
     ("Shower_", "Propane_", "Gas_", "Safety_")),
    ("kitchen_flap.png", (0.35, 1.0, -0.4), tuple(h for h in _TRUNK_HIDE if h != "Kitchen_") + (
        "Shower_", "Bed", "Bank", "Battery", "Trunk2", "Water", "Toilet", "Propane", "TankFloor", "Floor", "WheelArch",
        "Gas_", "Safety_", "DPillar", "Rail_", "FloorRib", "Thread", "Kitchen_FlapOpen", "Kitchen_FlapBracketOpen")),
    ("kitchen_flap_open.png", (0.35, 1.0, -0.4), tuple(h for h in _TRUNK_HIDE if h != "Kitchen_") + (
        "Shower_", "Bed", "Bank", "Battery", "Trunk2", "Water", "Toilet", "Propane", "TankFloor", "Floor", "WheelArch",
        "Gas_", "Safety_", "DPillar", "Rail_", "FloorRib", "Thread", "Kitchen_Flap$", "Kitchen_FlapBracket1$",
        "Kitchen_FlapBracket2$")),
    ("trunk_from_rear.png", "viewLeft", _TRUNK_HIDE),
    ("trunk_3d.png", (0.75, 0.55, -0.6), _TRUNK_HIDE + ("BedDeck", "BedWall")),
]


def _maximize_view():
    """Окно 3D-вида на весь экран, иначе fitAll считает камеру под маленькое
    окно, и saveImage обрезает модель."""
    mw = Gui.getMainWindow()
    mw.showMaximized()
    try:
        from PySide import QtGui
        mdi = mw.findChild(QtGui.QMdiArea)
        if mdi is not None:
            for sw in mdi.subWindowList():
                sw.showMaximized()
    except Exception as e:
        print("render_views: mdi:", e)
    for _ in range(5):
        Gui.updateGui()


def _shot(log, name, view, hide):
    doc = App.ActiveDocument
    hidden = []
    for o in doc.Objects:
        vo = getattr(o, "ViewObject", None)
        if vo is not None and vo.Visibility and any(
                (o.Name == h[:-1]) if h.endswith("$") else (h in o.Name) for h in hide):
            vo.Visibility = False
            hidden.append(o)
    v = Gui.ActiveDocument.ActiveView
    if isinstance(view, tuple):
        v.viewIsometric()
        v.setViewDirection(view)          # куда смотрит камера
    else:
        getattr(v, view)()
    for _ in range(3):
        Gui.updateGui()
        v.fitAll()
    Gui.updateGui()
    path = os.path.join(OUT, name)
    v.saveImage(path, W, H, "White")
    for o in hidden:
        o.ViewObject.Visibility = True
    log.write("saved %s\n" % path)


def main():
    os.makedirs(OUT, exist_ok=True)
    rc = 0
    with open(os.path.join(OUT, "render_log.txt"), "w", encoding="utf-8") as log:
        try:
            os.environ["VAN_HIDE_ON_SAVE"] = "0"                    # рендерам нужны все объекты видимыми
            g = {"__file__": SCRIPT, "__name__": "__main__"}
            exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), g)
            _maximize_view()
            var = str(g.get("WATER_VARIANT", "")).split("_")[0]          # T4100 / T3500 / TORVA
            for name, view, hide in VIEWS:
                if name.startswith("tank_") and var:
                    name = name.replace("tank_", "tank_%s_" % var, 1)
                _shot(log, name, view, hide)
            log.write("OK\n")
        except Exception:
            log.write(traceback.format_exc())
            rc = 1
    os._exit(rc)


main()
