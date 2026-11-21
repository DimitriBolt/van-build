# -*- coding: utf-8 -*-
"""Виды багажника на крыше и солнечных панелей (2026-11-20) из уже собранного .FCStd (с цветами).

    xvfb-run -a -s "-screen 0 1920x1200x24" freecad tools/render_roof.py      # VAN_FCSTD — файл (по умолч. van_v1_rect_pan.FCStd)
Результат — docs/renders/roof_*.png. Выход через os._exit (не трогать user.cfg FreeCAD).
"""
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui

REPO = os.environ.get("VAN_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(globals().get("__file__", "x/x"))))
FC = os.environ.get("VAN_FCSTD") or os.path.join(REPO, "van_v1_rect_pan.FCStd")
OUT = os.environ.get("RENDER_OUT") or os.path.join(REPO, "docs", "renders")
W, H = int(os.environ.get("RENDER_W", 1800)), int(os.environ.get("RENDER_H", 1100))

ROOF = ("RoofPin", "RoofMount", "RoofRail", "RoofSplice", "RoofTiePlate", "RoofCross", "RoofFlueBoard", "SolarPanel")
FLUE = ("Shower_Flue", "Shower_FlueCap")


def _vis(doc, show):
    for o in doc.Objects:
        vo = getattr(o, "ViewObject", None)
        if vo is None or o.isDerivedFrom("App::DocumentObjectGroup"):
            continue
        try:
            vo.Visibility = bool(show(o))
        except Exception:
            pass


def _maximize_view():
    mw = Gui.getMainWindow()
    mw.showMaximized()
    try:
        from PySide import QtGui
        mdi = mw.findChild(QtGui.QMdiArea)
        if mdi is not None:
            for sw in mdi.subWindowList():
                sw.showMaximized()
    except Exception as e:
        print("render_roof: mdi:", e)
    for _ in range(5):
        Gui.updateGui()


def _cam(d, up=(0, 0, 1)):
    """Ориентация камеры: смотрит вдоль d, «верх» кадра — up (под xvfb setViewDirection не работает)."""
    d = App.Vector(*d).normalize()
    zc = d * -1.0
    xc = App.Vector(*up).cross(zc).normalize()
    yc = zc.cross(xc)
    return App.Rotation(App.Matrix(xc.x, yc.x, zc.x, 0, xc.y, yc.y, zc.y, 0, xc.z, yc.z, zc.z, 0, 0, 0, 0, 1))


def _shot(doc, name, show, d, up=(0, 0, 1), focus=None):
    """focus=(центр (x, y, z), высота кадра мм) — крупный план вокруг точки (ортогональная камера)."""
    try:
        _shot1(doc, name, show, d, up, focus)
    except Exception:
        with open(os.path.join(OUT, "render_roof_error.txt"), "a") as f_:
            f_.write(name + "\n")
            traceback.print_exc(file=f_)


def _shot1(doc, name, show, d, up, focus):
    _vis(doc, show)
    v = Gui.activeDocument().activeView()
    v.setCameraOrientation(_cam(d, up))
    for _ in range(3):
        Gui.updateGui()
        v.fitAll()
    if focus is not None:                          # без pivy: камера строкой Inventor (как VIEW_CAMERA в finish.py)
        c, h = focus
        dv = App.Vector(*d).normalize()
        p = App.Vector(*c) - dv * 6000.0
        rot = _cam(d, up)
        ax, ang = rot.Axis, rot.Angle
        v.setCamera("#Inventor V2.1 ascii\nOrthographicCamera {\n viewportMapping ADJUST_CAMERA\n position %f %f %f\n"
                    " orientation %f %f %f %f\n nearDistance 10\n farDistance 20000\n aspectRatio 1\n focalDistance 6000\n"
                    " height %f\n}\n" % (p.x, p.y, p.z, ax.x, ax.y, ax.z, ang, h))
    Gui.updateGui()
    os.makedirs(OUT, exist_ok=True)
    v.saveImage(os.path.join(OUT, name), W, H, "White")
    print("render_roof:", name, flush=True)


rc = 0
if os.environ.get("_RENDER_ROOF_DONE"):              # FreeCAD GUI иногда выполняет файл второй раз — второй проход не нужен
    os._exit(0)
os.environ["_RENDER_ROOF_DONE"] = "1"
try:
    doc = App.openDocument(FC)
    _maximize_view()
    Gui.activeDocument().activeView().setCameraType("Orthographic")
    Gui.updateGui()
    roof = lambda o: o.Name.startswith(ROOF) or o.Name in FLUE
    skin = lambda o: roof(o) or o.Name.startswith("Scan_Skin")
    _shot(doc, "roof_iso_with_skin.png", skin, (-0.8, 1.0, -0.6))        # сзади-сверху со стороны пассажира (−Y)
    _shot(doc, "roof_iso_driver.png", skin, (-0.8, -1.0, -0.6))          # сзади-сверху со стороны водителя (+Y)
    _shot(doc, "roof_top.png", roof, (0, 0, -1), up=(0, 1, 0))            # сверху: X вправо (к кабине), +Y (водитель) вверх
    _shot(doc, "roof_side.png", skin, (0, -1, 0))                        # с водительского борта
    _shot(doc, "roof_iso.png", roof, (-0.8, -1.0, -0.7))
    _shot(doc, "roof_frame_iso.png", lambda o: roof(o) and not o.Name.startswith("SolarPanel"), (-0.8, -1.0, -0.7))
    # крупно: средний штырь пассажирского борта — кронштейн, 2 яруса рейки, уголки поперечин, пластины
    m = doc.getObject("RoofMount_nY_2").Shape.BoundBox
    _shot(doc, "roof_mount_detail.png", lambda o: o.Name.startswith(("RoofPin", "RoofMount", "RoofRail", "RoofCross", "RoofTiePlate",
                                                                     "RoofSplice")),
          (-0.6, 1.0, -0.45), focus=((m.Center.x, m.Center.y, m.ZMax + 30.0), 420.0))
    s_ = doc.getObject("RoofSplice_nY_L1_o").Shape.BoundBox
    _shot(doc, "roof_splice_detail.png", lambda o: o.Name.startswith(("RoofRail", "RoofSplice", "RoofTiePlate", "RoofCross")),
          (-0.6, 1.0, -0.45), focus=((s_.Center.x, s_.Center.y, s_.Center.z + 10.0), 380.0))
    f_ = doc.getObject("Shower_FlueCap").Shape.BoundBox
    _shot(doc, "roof_flue_detail.png", roof, (-0.5, -1.0, -0.5), focus=((f_.Center.x, f_.Center.y, f_.Center.z - 60.0), 1100.0))
except Exception:
            pass


def _maximize_view():
    mw = Gui.getMainWindow()
    mw.showMaximized()
    try:
        from PySide import QtGui
        mdi = mw.findChild(QtGui.QMdiArea)
        if mdi is not None:
            for sw in mdi.subWindowList():
                sw.showMaximized()
    except Exception as e:
        print("render_roof: mdi:", e)
    for _ in range(5):
        Gui.updateGui()


def _cam(d, up=(0, 0, 1)):
    """Ориентация камеры: смотрит вдоль d, «верх» кадра — up (под xvfb setViewDirection не работает)."""
    d = App.Vector(*d).normalize()
    zc = d * -1.0
    xc = App.Vector(*up).cross(zc).normalize()
    yc = zc.cross(xc)
    return App.Rotation(App.Matrix(xc.x, yc.x, zc.x, 0, xc.y, yc.y, zc.y, 0, xc.z, yc.z, zc.z, 0, 0, 0, 0, 1))


def _shot(doc, name, show, d, up=(0, 0, 1), focus=None):
    """focus=(центр (x, y, z), высота кадра мм) — крупный план вокруг точки (ортогональная камера)."""
    try:
        _shot1(doc, name, show, d, up, focus)
    except Exception:
        with open(os.path.join(OUT, "render_roof_error.txt"), "a") as f_:
            f_.write(name + "\n")
            traceback.print_exc(file=f_)


def _shot1(doc, name, show, d, up, focus):
    _vis(doc, show)
    v = Gui.activeDocument().activeView()
    v.setCameraOrientation(_cam(d, up))
    for _ in range(3):
        Gui.updateGui()
        v.fitAll()
    if focus is not None:
        c, h = focus
        cam = v.getCameraNode()
        dv = App.Vector(*d).normalize()
        p = App.Vector(*c) - dv * 6000.0
        cam.position.setValue(p.x, p.y, p.z)
        if hasattr(cam, "height"):
            cam.height.setValue(h)
        cam.focalDistance.setValue(6000.0)
    Gui.updateGui()
    os.makedirs(OUT, exist_ok=True)
    v.saveImage(os.path.join(OUT, name), W, H, "White")
    print("render_roof:", name, flush=True)


rc = 0
if os.environ.get("_RENDER_ROOF_DONE"):              # FreeCAD GUI иногда выполняет файл второй раз — второй проход не нужен
    os._exit(0)
os.environ["_RENDER_ROOF_DONE"] = "1"
try:
    doc = App.openDocument(FC)
    _maximize_view()
    Gui.activeDocument().activeView().setCameraType("Orthographic")
    Gui.updateGui()
    roof = lambda o: o.Name.startswith(ROOF) or o.Name in FLUE
    skin = lambda o: roof(o) or o.Name.startswith("Scan_Skin")
    _shot(doc, "roof_iso_with_skin.png", skin, (-0.8, 1.0, -0.6))        # сзади-сверху со стороны пассажира (−Y)
    _shot(doc, "roof_iso_driver.png", skin, (-0.8, -1.0, -0.6))          # сзади-сверху со стороны водителя (+Y)
    _shot(doc, "roof_top.png", roof, (0, 0, -1), up=(0, 1, 0))            # сверху: X вправо (к кабине), +Y (водитель) вверх
    _shot(doc, "roof_side.png", skin, (0, -1, 0))                        # с водительского борта
    _shot(doc, "roof_iso.png", roof, (-0.8, -1.0, -0.7))
    _shot(doc, "roof_frame_iso.png", lambda o: roof(o) and not o.Name.startswith("SolarPanel"), (-0.8, -1.0, -0.7))
    near = ("RoofPin_nY_2", "RoofMount_nY_2", "RoofMountRubber_nY_2", "RoofRail_nY", "RoofCross_3", "RoofCross_4",
            "RoofCrossBracket_3_nY", "RoofCrossBracket_4_nY", "RoofTiePlate_nY", "RoofSplice_nY")
    _shot(doc, "roof_mount_detail.png", lambda o: o.Name.startswith(near) and (
        not o.Name.startswith("RoofTiePlate") or 1300 < o.Shape.BoundBox.XMin < 2400) and (
        not o.Name.startswith("RoofRail") or True), (-0.6, 1.0, -0.45))
except Exception:
    with open(os.path.join(OUT, "render_roof_error.txt"), "w") as f_:
        traceback.print_exc(file=f_)
    rc = 1
os._exit(rc)
