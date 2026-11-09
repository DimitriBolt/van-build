# -*- coding: utf-8 -*-
# Анимация «assembly» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: van_v0_T4320_anim.FCStd (ea_export, 2026-11-09 00:31).
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком.

SEQUENCE = 'assembly'

STEPS = [

    {   # 2
        'label': '1 Матрас',
        'kind': 'simple',
        'distance': 1500,
        'steps': 300,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedMattress', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (742.2213, 0.0, 966.9)},  # Матрас ~100 мм
        ],
    },
    {   # 3
        'label': '2 Настил',
        'kind': 'simple',
        'distance': 1000,
        'steps': 200,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedDeck', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (743.7884, 0.0, 866.9)},  # Настил
        ],
    },
    {   # 4
        'label': '3 Поперечины',
        'kind': 'simple',
        'distance': 150.0,
        'steps': 50,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedCross_1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (1623.4466, -55.8483, 45.3)},  # Поперечина #1 X=408
            {'name': 'BedCross_2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (1623.4466, -55.8483, 45.3)},  # Поперечина #2 X=865
            {'name': 'BedCross_3', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (1623.4466, -55.8483, 45.3)},  # Поперечина #3 X=1323
        ],
    },
    {   # Переставил на последнее место
        'label': '4 Батареи B2–B4',
        'kind': 'simple',
        'distance': 600.0,
        'steps': 200,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (968.5123, -859.0795, 498.6)},  # Батарея B2
            {'name': 'Battery_B3', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (968.5123, -859.0795, 498.6)},  # Батарея B3
            {'name': 'Battery_B4', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (968.5123, -859.0795, 498.6)},  # Батарея B4
        ],
    },    
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
    'Opening_RearDoors',  # Проём задних дверей
    'Opening_SlidingDoor',  # Проём сдвижной двери
    'Openings',  # Проёмы дверей
    'RearDoorLeaf_Driver',  # Створка задней двери со стороны водителя
    'RearDoorLeaf_Passenger',  # Створка задней двери со стороны пассажира
    'Scan_Skin',  # Обшивка
    'Scan_Skin_Body',  # Обшивка #2
]
