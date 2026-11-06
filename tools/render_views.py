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
VIEWS = [
    ("iso_with_skin.png", "viewIsometric", ()),
    ("iso_frame.png", "viewIsometric", ("Scan_Skin",)),
    ("top_frame.png", "viewTop", ("Scan_Skin",)),
    ("from_rear_doors.png", "viewLeft", ("Scan_Skin", "Opening_RearDoors", "RearDoorLeaf")),
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
        if vo is not None and vo.Visibility and any(o.Name.startswith(h) for h in hide):
            vo.Visibility = False
            hidden.append(o)
    v = Gui.ActiveDocument.ActiveView
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
