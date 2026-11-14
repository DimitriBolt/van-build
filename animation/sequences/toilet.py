# -*- coding: utf-8 -*-
# Анимация «toilet» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: написана Claude по модели van_v1_rect_pan (vanmodel/shower_rect.py, раздел туалета), 2026-11-14.
#
# Туалет SEAFLO 2.6 gal стоит на платформе на колёсиках под раковиной (секция мойки) и выкатывается НАЗАД (−X)
# в душевую кабину на 400 мм (15.7″): передние колёса едут по дну поддона, задние — по плите Toilet_Plate
# и в душе останавливаются у торца поддона. Едут вместе: платформа, порожек, туалет и 4 колёсика.
# Плита Toilet_Plate неподвижна. Колёсики не крутятся (в верстаке центр вращения неподвижен).
# ▶ — выкатить в душ, ◀ — закатить под раковину.
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.

SEQUENCE = 'toilet'

# Для каких моделей эта анимация (имя файла модели без .FCStd; 'van_v0' — это и van_v0_T4320 и т.д.).
MODELS = ['van_v1_rect_pan']

STEPS = [
    {   # 1
        'label': 'Туалет на платформе — выкатить в душ',
        'kind': 'simple',
        'distance': 400.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Toilet_Platform', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Toilet platform
            {'name': 'Toilet_PlatformDam', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Platform dam
            {'name': 'Toilet_Camco', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Toilet SEAFLO 2.6 gal
            {'name': 'Toilet_Wheel_FA', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Front wheel A
            {'name': 'Toilet_Wheel_FW', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Front wheel W
            {'name': 'Toilet_Wheel_RA', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rear wheel A
            {'name': 'Toilet_Wheel_RW', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rear wheel W
        ],
    },
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
]
