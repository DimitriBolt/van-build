# -*- coding: utf-8 -*-
"""Сборка модели: разделы выполняются по порядку и передают друг другу данные через контекст S (state.py).

Порядок здесь — порядок ПОСТРОЕНИЯ модели (что от чего считается), а не порядок монтажа в фургоне
(тот — в REQUIREMENTS.md §0а и animation/sequences/assembly.py).
"""
import sys

from . import body, bed, battery_bank, water_tank, shower_kitchen, trunk, wall_cabinets, finish, summary
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
]

LAST = None          # контекст последней сборки — посмотреть в консоли FreeCAD: vanmodel.build.LAST.<имя>


def build():
    """Собрать модель целиком; возвращает документ FreeCAD (сохранён в SAVE_PATH)."""
    global LAST
    S = LAST = State()
    for stage, title in STAGES:
        try:
            stage(S)
        except Exception as e:
            note = "van_v0: ошибка в разделе «%s» — vanmodel/%s.py, функция %s()" % (
                title, stage.__module__.rsplit(".", 1)[-1], stage.__name__)
            if hasattr(e, "add_note"):               # Python ≥ 3.11: строка попадёт в конец traceback
                e.add_note(note)
            else:
                sys.stderr.write(note + "\n")
            raise
    return S.doc
