# -*- coding: utf-8 -*-
# Анимация «upper_drawer» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: написана Claude по модели van_v1_rect_pan (vanmodel/drawers_rect.py), 2026-11-13.
#
# Верхний ящик (SLIDEWAY 44″) выдвигается НАЗАД, в задние двери, на полный ход направляющих — 1117.6 мм (44″).
# ▶ Play Forward — открыть, ◀ Play Backwards — закрыть.
# Направляющие Drawer_Slide_* в модели — по одному бруску на сторону (неподвижная + подвижная части вместе),
# поэтому они стоят на месте; когда в модели появятся секции, средняя поедет на половину хода (vec −0.5).
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком.

SEQUENCE = 'upper_drawer'

# Для каких моделей эта анимация (имя файла модели без .FCStd; 'van_v0' — это и van_v0_T4320 и т.д.).
MODELS = ['van_v1_rect_pan']

STEPS = [
    {   # 1
        'label': 'Верхний ящик — выдвинуть назад',
        'kind': 'simple',
        'distance': 1117.6,
        'steps': 110,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Drawer_Upper', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Upper drawer (slides rearward)
            {'name': 'Drawer_Upper_Handle', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Upper drawer handle
        ],
    },
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
]
