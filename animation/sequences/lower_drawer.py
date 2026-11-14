# -*- coding: utf-8 -*-
# Анимация «lower_drawer» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: написана Claude по модели van_v1_rect_pan (vanmodel/drawers_rect.py), 2026-11-13.
#
# Нижний ящик на 6 колёсиках выкатывается ВПЕРЁД, в салон, на 900 мм (ход из проверок модели:
# DRAWERS_RECT["lower"]["travel"]); ящик, ручка и колёсики едут вместе. ▶ — выкатить, ◀ — закатить.
# Колёсики не вращаются: в ExplodedAssembly ось вращения стоит на месте, а у катящегося колеса она едет вместе с ним.
# Выкатывать — при закрытой двери душа (открытая дверь стоит на пути ящика), поэтому призраки открытых дверей
# душа в файле анимации скрыты (HIDDEN).
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком.

SEQUENCE = 'lower_drawer'

# Для каких моделей эта анимация (имя файла модели без .FCStd; 'van_v0' — это и van_v0_T4320 и т.д.).
MODELS = ['van_v1_rect_pan']

STEPS = [
    {   # 1
        'label': 'Нижний ящик — выкатить вперёд',
        'kind': 'simple',
        'distance': 900.0,
        'steps': 90,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Drawer_Lower', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Lower drawer (rolls forward)
            {'name': 'Drawer_Lower_Handle', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Lower drawer handle
            {'name': 'Drawer_Wheel_D1', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster D1
            {'name': 'Drawer_Wheel_P1', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster P1
            {'name': 'Drawer_Wheel_D2', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster D2
            {'name': 'Drawer_Wheel_P2', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster P2
            {'name': 'Drawer_Wheel_D3', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster D3
            {'name': 'Drawer_Wheel_P3', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Drawer caster P3
        ],
    },
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
    'Shower_Door_Open',  # Shower door open 90°
    'Shower_DoorEnd_Folded',  # Shower end panel folded
]
