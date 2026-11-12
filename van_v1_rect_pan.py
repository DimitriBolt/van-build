#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
van_v1_rect_pan.py — вариант модели с ПРЯМОУГОЛЬНЫМ поддоном душа RecPro 36×24×5″ (2026-11-12).

Тот же пакет vanmodel/, что и у van_v0.py (кузов, кровать, этажерка батарей, шкафчики — без изменений), но:
  • «Душ + кухня» строит vanmodel/shower_rect.py: поддон 36×24″ вплотную к кровати (узкая грань — вровень с краем щита),
    угол у арки отпилен одной прямой, слив у кабины; туалет SEAFLO на платформе; кухонный блок шириной 24″;
  • бака воды, локера/баллона пропана, ящиков багажника и полки 2-го этажа НЕТ (WATER_VARIANT=none) — их положение
    Dimitri укажет следующим заданием;
  • результат — отдельный файл van_v1_rect_pan.FCStd (van_v0.FCStd не затрагивается).

ЗАПУСК: python3 van_v1_rect_pan.py    (или headless: FreeCAD --console tools/build_headless.py с VAN_ENTRY=van_v1_rect_pan.py)
После замеров правится vanmodel/anchors.py (ANCHORS["rect_pan"]: x_rear, drain_end, cut, зазоры), размеры поддона —
vanmodel/params_rect.py.
"""

import os
import sys

# Папка репозитория: рядом с этим файлом; при запуске текстом через RPC (без __file__) — ~/van-build.
_REAL_HOME = os.environ.get("SNAP_REAL_HOME") or os.path.expanduser("~")
_REPO_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
            else os.path.join(_REAL_HOME, "van-build")
if _REPO_DIR not in sys.path:
    sys.path.insert(0, _REPO_DIR)

# Вариант: без бака (и багажника на нём), свой документ и свой файл — задаём ДО импорта vanmodel.
os.environ["VAN_WATER_VARIANT"] = "none"
os.environ.setdefault("VAN_DOC_NAME", "van_v1_rect_pan")
os.environ.setdefault("VAN_SAVE_PATH", os.path.join(_REPO_DIR, "van_v1_rect_pan.FCStd"))

# В уже открытом FreeCAD модули остаются в памяти с прошлого запуска — выгружаем.
for _m in [m for m in sys.modules if m == "vanmodel" or m.startswith("vanmodel.")]:
    del sys.modules[_m]

from vanmodel.anchors import *      # noqa: E402,F401,F403  ANCHORS, KERF
from vanmodel.params import *       # noqa: E402,F401,F403  PARAMS, BED, WHEEL_ARCH, WATER_VARIANT, …
from vanmodel.params_rect import *  # noqa: E402,F401,F403  RECT_PAN, SHOWER_KITCHEN_RECT, TOILET_RECT
from vanmodel.common import *       # noqa: E402,F401,F403  SAVE_PATH, цвета, add_box, add_shape, …
from vanmodel.scan import *         # noqa: E402,F401,F403
from vanmodel.strut import *        # noqa: E402,F401,F403
from vanmodel.finish import *       # noqa: E402,F401,F403
from vanmodel.build import build, STAGES_RECT_PAN   # noqa: E402

DOC = build(STAGES_RECT_PAN)
