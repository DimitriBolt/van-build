#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
van_v0.py — КАРКАСНАЯ модель RAM ProMaster 136" High Roof, повторяющая 3D-скан.

ИДЕЯ (по требованию заказчика):
  • CAD-модель = ТОЛЬКО КАРКАС (к нему крепится оборудование). Обшивки в CAD нет.
  • Обшивка — это сам 3D-скан кузова (Mesh), он лежит ПОВЕРХ каркаса.
  • Внутренний объём — НЕ «коробка», а сложная форма: гнутые борта + округлая крыша,
    снятая с реального скана. Рёбра каркаса — гнутые обручи по контуру скана.

СИСТЕМА КООРДИНАТ:
  ноль — пол у порога ЗАДНИХ дверей, на центральной оси.
  X = длина:  0 сзади, +X к кабине;  Y = ширина: 0 центр;  Z = высота: 0 пол.
  СК правая (как во FreeCAD): если смотреть вперёд на кабину (+X), то
    +Y = ЛЕВЫЙ борт  = сторона ВОДИТЕЛЯ (US),
    −Y = ПРАВЫЙ борт = сторона ПАССАЖИРА, там штатная сдвижная дверь US ProMaster.
  (До 2026-11-05 в подписях было наоборот, «+Y пассажир», — геометрия была верной,
   ошибочными были только подписи.)

ОТКУДА ГЕОМЕТРИЯ:
  Профиль сечения каркаса измеряется из Ducato_L2H2_body_reference.stl (наружная
  оболочка кузова, выровненная в СК модели через SCAN_ALIGN). По облаку точек в
  карго-зоне строится усреднённый ПОЛУ-ПРОФИЛЬ (полуширина борта в зависимости от Z),
  смещённый внутрь на frame_clearance (толщина обшивки/панели). Из него — гнутые рёбра.

СЛОИ (группы):
  Scan_Skin   — меш-обшивка (реальный кузов), полупрозрачная.
  Frame       — каркас:
      Ribs                — гнутые поперечные обручи (борт+крыша) по контуру скана
      Longitudinals       — продольные рейки вдоль X на заданных высотах
      CorrugatedFloor      — рефлёный пол: продольные рёбра жесткости, не отдельные поперечины
      Pillars             — стойки у проёмов
      HoleMarkers         — точки крепления на рёбрах (по реальной поверхности борта)
      FactoryThreadedMounts — заводские резьбовые точки на продольных рейках (M8/M10 — уточнить)
  Openings    — реф-рамки проёмов (сдвижная дверь, задние двери)

ГДЕ КОД (с 2026-11-11 модель разделена на модули — пакет vanmodel/, оглавление в vanmodel/__init__.py):
  этот файл — только точка входа: запускается как раньше, сам код модели лежит в vanmodel/:
      anchors.py — якорные размеры (правятся после замеров), params.py — остальные параметры,
      body.py, bed.py, battery_bank.py, water_tank.py, shower_kitchen.py, trunk.py, wall_cabinets.py — разделы модели,
      build.py — порядок разделов, summary.py — сводка.

ПЕРЕЗАПУСК: правишь vanmodel/anchors.py или vanmodel/params.py → запускаешь снова → документ van_v0
  пересобирается и пересохраняется в van_v0.FCStd.  ЗАПУСК: `python3 van_v0.py`, headless
  `FreeCAD.AppImage --console van_v0.py` или живьём через RPC execute_code(open(path).read()).
"""

import os
import sys

# Папка репозитория: рядом с этим файлом; при запуске текстом через RPC (без __file__) — ~/van-build.
_REAL_HOME = os.environ.get("SNAP_REAL_HOME") or os.path.expanduser("~")
_REPO_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
            else os.path.join(_REAL_HOME, "van-build")
if _REPO_DIR not in sys.path:
    sys.path.insert(0, _REPO_DIR)
# В уже открытом FreeCAD модули остаются в памяти с прошлого запуска — выгружаем, чтобы правки в vanmodel/
# и переменные окружения (VAN_WATER_VARIANT, VAN_SAVE_PATH) подхватывались при каждом запуске.
for _m in [m for m in sys.modules if m == "vanmodel" or m.startswith("vanmodel.")]:
    del sys.modules[_m]

# Имена модели — в пространство имён этого файла: их читают tools/*.py и консоль FreeCAD (как до разделения).
from vanmodel.anchors import *      # noqa: E402,F401,F403  ANCHORS, KERF
from vanmodel.params import *       # noqa: E402,F401,F403  PARAMS, BED, WHEEL_ARCH, WATER_VARIANT, …
from vanmodel.common import *       # noqa: E402,F401,F403  SAVE_PATH, цвета, add_box, add_shape, …
from vanmodel.scan import *         # noqa: E402,F401,F403  scan_points, measured_half_profile, y_at_z, …
from vanmodel.strut import *        # noqa: E402,F401,F403  STRUT, STRUT_BACK, …
from vanmodel.finish import *       # noqa: E402,F401,F403  short_labels, hide_default, …
from vanmodel.build import build    # noqa: E402

DOC = build()
