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
            "Hole_", "FactoryThread", "FloorCorrugation", "Floor_")
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
# этажерка под батареи: кровать и всё дальнее скрыто
_RACK_HIDE = _NOT_BED + ("_pY", "front", "BedSideRail", "BedCross", "BedDeck", "BedMattress",
                         "BedWall", "BedPostBodyBolt", "RackP2_RailBolt")
VIEWS += [
    # из салона, сверху-спереди (направление взгляда: назад, к борту −Y, вниз)
    ("rack_3d.png", (-0.55, -1.0, -0.55), _RACK_HIDE),
    ("rack_from_inside.png", "viewRear", _RACK_HIDE),
    ("rack_top.png", "viewTop", _RACK_HIDE),
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
        if vo is not None and vo.Visibility and any(h in o.Name for h in hide):
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
            g = {"__file__": SCRIPT, "__name__": "__main__"}
            exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), g)
            _maximize_view()
            for name, view, hide in VIEWS:
                _shot(log, name, view, hide)
            log.write("OK\n")
        except Exception:
            log.write(traceback.format_exc())
            rc = 1
    os._exit(rc)


main()
