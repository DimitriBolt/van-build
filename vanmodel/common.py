# -*- coding: utf-8 -*-
"""Общее для всех разделов: имя документа и пути, выравнивание скана, цвета, создание объектов FreeCAD."""

import os

import FreeCAD as App

DOC_NAME    = os.environ.get("VAN_DOC_NAME") or "van_v0"   # env — для вариантов (van_v1_rect_pan.py)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # корень репозитория (на M6800 = ~/van-build)
SAVE_PATH   = os.path.join(PROJECT_DIR, "van_v0.FCStd")   # рядом с van_v0.py
if os.environ.get("VAN_SAVE_PATH"):                         # отдельный файл варианта (tools/save_variant.py)
    SAVE_PATH = os.path.abspath(os.environ["VAN_SAVE_PATH"])
BODY_STL_PATH = os.path.join(PROJECT_DIR, "Ducato_L2H2_body_reference.stl")

# ── Выравнивание скан → СК модели (измерено по body_reference) ──
SCAN_REAR_X   = -460.0
SCAN_CENTER_Y = 2380.0
SCAN_FLOOR_Z  = 41.0
SCAN_ALIGN = (-SCAN_REAR_X, -SCAN_CENTER_Y, -SCAN_FLOOR_Z)   # (+460, −2380, −41)

# Цвета
COL_SKIN   = (0.80, 0.83, 0.86)   # обшивка-скан — светло-серая
if os.environ.get("VAN_SKIN") == "bahama":   # цвет кузова: GMC Jimmy WA9656 Bahama Blue Metallic (вариант van_v1_rect_pan)
    COL_SKIN = (0.20, 0.40, 0.60)
COL_RIB    = (0.90, 0.10, 0.06)   # рёбра-обручи — красные
COL_RAIL   = (0.05, 0.38, 0.95)   # продольные рейки — синие
COL_FLOOR  = (0.34, 0.36, 0.38)   # рефлёный металлический пол
COL_PILLAR = (0.82, 0.15, 0.15)   # стойки — красные
COL_HOLE   = (1.00, 0.92, 0.10)   # маркеры — жёлтые
COL_FACTORY_THREAD = (0.00, 0.85, 1.00)  # заводские резьбовые точки — голубые
COL_SLIDER = (0.20, 0.70, 0.30)
COL_REAR   = (0.25, 0.45, 0.85)
COL_STRUT    = (0.55, 0.57, 0.62)   # strut channel — сталь/оцинковка
COL_PLY      = (0.80, 0.66, 0.42)   # фанерный настил
COL_WOOD     = (0.72, 0.52, 0.30)   # 2×4 деревянные лаги
COL_MATTRESS = (0.40, 0.55, 0.85)   # матрас (визуал)
COL_DECK     = (0.86, 0.80, 0.68)   # настил — плита MR (бежевая)
COL_XPS      = (0.95, 0.62, 0.72)   # XPS FOAMULAR — розовый
COL_ARCH     = (0.78, 0.78, 0.76)   # кожух колёсной арки
COL_BOLT     = (0.15, 0.80, 0.30)   # болт стойки в кузов (зелёная проставка)
COL_BATTERY  = (0.95, 0.42, 0.08)   # LiFePO4 Buknuwo (оранжевый)
COL_DPILLAR  = (0.55, 0.60, 0.65)   # передняя грань D-стойки (реф)


_INTENDED = {}           # имя объекта → полная подпись (до автопереименования FreeCAD дублей «…001»)


# ──────────────────────────── helpers ────────────────────────────
def _style(obj, color=None, transparency=None):
    vo = getattr(obj, "ViewObject", None)
    if vo is None:
        return
    try:
        if color is not None:
            vo.ShapeColor = color
        if transparency is not None:
            vo.Transparency = int(transparency)
    except Exception:
        pass


def add_box(doc, name, label, dims, base, color=None, transparency=None, group=None):
    o = doc.addObject("Part::Box", name)
    o.Length, o.Width, o.Height = (float(d) for d in dims)
    o.Placement.Base = App.Vector(*[float(v) for v in base])
    o.Label = label
    _INTENDED[name] = label
    _style(o, color, transparency)
    if group is not None:
        group.addObject(o)
    return o


def add_sphere(doc, name, label, radius, center, color=None, group=None):
    o = doc.addObject("Part::Sphere", name)
    o.Radius = float(radius)
    o.Placement.Base = App.Vector(*[float(v) for v in center])
    o.Label = label
    _INTENDED[name] = label
    _style(o, color)
    if group is not None:
        group.addObject(o)
    return o


def add_shape(doc, name, label, shape, color=None, transparency=None, group=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.Label = label
    _INTENDED[name] = label
    _style(o, color, transparency)
    if group is not None:
        group.addObject(o)
    return o


def overall_bbox(doc):
    bb = None
    for o in doc.Objects:
        sh = getattr(o, "Shape", None)
        me = getattr(o, "Mesh", None)
        b = None
        if me is not None and getattr(me, "CountFacets", 0) > 0:
            b = me.BoundBox
        elif sh is not None and not sh.isNull():
            b = sh.BoundBox
        if b is None:
            continue
        bb = b if bb is None else bb.united(b)
    return bb
