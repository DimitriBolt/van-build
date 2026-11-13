# -*- coding: utf-8 -*-
"""Сборка модели: разделы выполняются по порядку и передают друг другу данные через контекст S (state.py).

Порядок здесь — порядок ПОСТРОЕНИЯ модели (что от чего считается), а не порядок монтажа в фургоне
(тот — в REQUIREMENTS.md §0а и animation/sequences/assembly.py).
"""
import sys

from . import body, bed, battery_bank, water_tank, shower_kitchen, shower_rect, propane_rect, drawers_rect, trunk, wall_cabinets, finish, summary, motion
from .state import State

# (функция раздела, название — для сообщения об ошибке)
STAGES = [
    (body.start,                    "Профиль борта по скану, документ FreeCAD"),
    (body.skin,                     "Обшивка (3D-скан)"),
    (body.frame,                    "Каркас кузова"),
    (body.floor,                    "Пол (XPS + фанера)"),
    (body.wheel_arches,             "Колёсные арки"),
    (body.dpillars,                 "D-стойки"),
    (body.relief_valve,             "Клапан сброса давления"),
    (bed.bed,                       "Кровать"),
    (battery_bank.racks,            "Этажерки под батареи (ранний вариант)"),
    (battery_bank.overarch_shelf,   "Полка над аркой (ранний вариант)"),
    (battery_bank.bank,             "Этажерка на 4 батареи + электрика"),
    (water_tank.torva,              "Бак TORVA (архивный вариант)"),
    (water_tank.t3500_shelf,        "Бак T-3500 на полке"),
    (water_tank.floor_tank,         "Бак на полу (T-4100 / T-4320)"),
    (shower_kitchen.shower_kitchen, "Душ + кухня"),
    (trunk.trunk,                   "Багажник под кроватью"),
    (wall_cabinets.wall_cabinets,   "Шкафчики под потолком"),
    (bed.deck_cutouts,              "Вырезы в щите кровати"),
    (body.openings,                 "Проёмы дверей"),
    (finish.finalize,               "Отделка и сохранение"),
    (summary.print_summary,         "Сводка"),
    (motion.report,                 "Анимации → проверки модели"),
]

# Вариант van_v1_rect_pan (2026-11-12): прямоугольный поддон RecPro 36×24×5″ вместо сектора 32″. Тот же порядок разделов,
# но «Душ + кухня» — shower_rect.shower_kitchen и после общей сводки — сводка по душу/туалету/кухне.
# Бака воды, локера/баллона и багажника в нём нет: точка входа van_v1_rect_pan.py ставит WATER_VARIANT=none.
STAGES_RECT_PAN = []
for _f, _t in STAGES:
    if _f is shower_kitchen.shower_kitchen:
        STAGES_RECT_PAN.append((shower_rect.shower_kitchen, "Душ (прямоугольный поддон RecPro) + туалет + кухня 24″"))
    elif _f is trunk.trunk:
        STAGES_RECT_PAN.append((propane_rect.locker, "Локер баллона 20 lb на месте туалета"))
        STAGES_RECT_PAN.append((drawers_rect.drawers, "Ящики под кроватью (нижний — вперёд на колёсиках, верхний — назад)"))
        STAGES_RECT_PAN.append((drawers_rect.shelf, "Полка над левой аркой (2 яруса на стойках 2020)"))
    else:
        STAGES_RECT_PAN.append((_f, _t))
    if _f is summary.print_summary:
        STAGES_RECT_PAN.append((shower_rect.report, "Сводка: поддон RecPro, туалет, кухня"))
        STAGES_RECT_PAN.append((drawers_rect.report, "Сводка: ящики под кроватью"))
        STAGES_RECT_PAN.append((propane_rect.report, "Сводка: локер баллона"))

LAST = None          # контекст последней сборки — посмотреть в консоли FreeCAD: vanmodel.build.LAST.<имя>


def build(stages=None):
    """Собрать модель целиком (stages — список разделов; по умолчанию STAGES); возвращает документ FreeCAD (сохранён в SAVE_PATH)."""
    global LAST
    S = LAST = State()
    import time as _t
    for stage, title in (STAGES if stages is None else stages):
        _t0 = _t.time()
        try:
            stage(S)
            sys.stderr.write("[build] %5.1f с — %s\n" % (_t.time() - _t0, title))
            sys.stderr.flush()
        except Exception as e:
            note = "van_v0: ошибка в разделе «%s» — vanmodel/%s.py, функция %s()" % (
                title, stage.__module__.rsplit(".", 1)[-1], stage.__name__)
            if hasattr(e, "add_note"):               # Python ≥ 3.11: строка попадёт в конец traceback
                e.add_note(note)
            else:
                sys.stderr.write(note + "\n")
            raise
    return S.doc
