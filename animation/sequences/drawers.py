# -*- coding: utf-8 -*-
# Анимация «drawers» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: van_v0_T4320_drawer.FCStd (ea_export, 2026-11-09 00:28).
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком.

SEQUENCE = 'drawers'

STEPS = [
    {   # 1
        'label': 'Ящик выдвинуть',
        'kind': 'simple',
        'distance': 914.4,
        'steps': 90,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Trunk1_Drawer', 'vec': (-1.0, 0.0, 0.0), 'rot_axis': (-1.0, 0.0, 0.0), 'rot_center': (30.0, -362.6133, 282.7)},  # Ящик 36.0×27.3×17.5″
        ],
    },
    {   # 2
        'label': 'Ящик 50.7 выдвинуть',
        'kind': 'simple',
        'distance': 1117.6,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Trunk2_TrayFwd', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (1317.9366, -362.6133, 655.85)},  # Ящик 50.7×27.3×10.7″
        ],
    },
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
    'CorrugatedFloor',  # Рефлёный пол
    'DPillarFace_nY_ref',  # D-стойка nY
    'DPillarFace_pY_ref',  # D-стойка pY
    'DPillars',  # D-стойки у пола
    'FactoryThread_nY_middle_x1618_z0980',  # Заводская резьбовая точка nY #2
    'FactoryThread_nY_rear_x0360_z0980',  # Заводская резьбовая точка nY
    'FactoryThread_pY_front_x2868_z0980',  # Заводская резьбовая точка pY #3
    'FactoryThread_pY_middle_x1618_z0980',  # Заводская резьбовая точка pY #2
    'FactoryThread_pY_rear_x0360_z0980',  # Заводская резьбовая точка pY
    'FactoryThreadedMounts',  # Заводские резьбовые точки на рейках
    'FloorBuildup',  # Пол
    'FloorCorrugation_y_0011',  # Продольный гребень пола Y=-11.3401
    'FloorCorrugation_y_0104',  # Продольный гребень пола Y=103.66
    'FloorCorrugation_y_0126',  # Продольный гребень пола Y=-126.34
    'FloorCorrugation_y_0219',  # Продольный гребень пола Y=218.66
    'FloorCorrugation_y_0241',  # Продольный гребень пола Y=-241.34
    'FloorCorrugation_y_0334',  # Продольный гребень пола Y=333.66
    'FloorCorrugation_y_0356',  # Продольный гребень пола Y=-356.34
    'FloorCorrugation_y_0449',  # Продольный гребень пола Y=448.66
    'FloorCorrugation_y_0471',  # Продольный гребень пола Y=-471.34
    'FloorCorrugation_y_0564',  # Продольный гребень пола Y=563.66
    'FloorCorrugation_y_0586',  # Продольный гребень пола Y=-586.34
    'FloorCorrugation_y_0679',  # Продольный гребень пола Y=678.66
    'FloorCorrugation_y_0701',  # Продольный гребень пола Y=-701.34
    'FloorCorrugation_y_0794',  # Продольный гребень пола Y=793.66
    'FloorCorrugation_y_0816',  # Продольный гребень пола Y=-816.34
    'FloorCorrugation_y_0909',  # Продольный гребень пола Y=908.66
    'FloorCorrugation_y_0931',  # Продольный гребень пола Y=-931.34
    'Floor_Plywood',  # Фанера пола 1/2″
    'Floor_XPS',  # XPS Owens Corning FOAMULAR NGX F-150
    'Frame',  # Каркас
    'HoleMarkers',  # Точки крепления на рёбрах
    'Hole_nY_x0160_z0350',  # Точка nY X=160 Z=350
    'Hole_nY_x0160_z0800',  # Точка nY X=160 Z=800
    'Hole_nY_x0160_z1250',  # Точка nY X=160 Z=1250
    'Hole_nY_x0160_z1650',  # Точка nY X=160 Z=1650
    'Hole_nY_x1818_z0350',  # Точка nY X=1818 Z=350
    'Hole_nY_x1818_z0800',  # Точка nY X=1818 Z=800
    'Hole_nY_x1818_z1250',  # Точка nY X=1818 Z=1250
    'Hole_nY_x1818_z1650',  # Точка nY X=1818 Z=1650
    'Hole_nY_x3068_z0350',  # Точка nY X=3068 Z=350
    'Hole_nY_x3068_z0800',  # Точка nY X=3068 Z=800
    'Hole_nY_x3068_z1250',  # Точка nY X=3068 Z=1250
    'Hole_nY_x3068_z1650',  # Точка nY X=3068 Z=1650
    'Hole_pY_x0160_z0350',  # Точка pY X=160 Z=350
    'Hole_pY_x0160_z0800',  # Точка pY X=160 Z=800
    'Hole_pY_x0160_z1250',  # Точка pY X=160 Z=1250
    'Hole_pY_x0160_z1650',  # Точка pY X=160 Z=1650
    'Hole_pY_x1818_z0350',  # Точка pY X=1818 Z=350
    'Hole_pY_x1818_z0800',  # Точка pY X=1818 Z=800
    'Hole_pY_x1818_z1250',  # Точка pY X=1818 Z=1250
    'Hole_pY_x1818_z1650',  # Точка pY X=1818 Z=1650
    'Hole_pY_x3068_z0350',  # Точка pY X=3068 Z=350
    'Hole_pY_x3068_z0800',  # Точка pY X=3068 Z=800
    'Hole_pY_x3068_z1250',  # Точка pY X=3068 Z=1250
    'Hole_pY_x3068_z1650',  # Точка pY X=3068 Z=1650
    'Longitudinals',  # Продольные рейки вдоль X
    'Opening_RearDoors',  # Проём задних дверей
    'Opening_SlidingDoor',  # Проём сдвижной двери
    'Openings',  # Проёмы дверей
    'Pillar_B_slider',  # B-стойка
    'Pillar_Rear_nY',  # Задняя стойка nY
    'Pillar_Rear_pY',  # Задняя стойка pY
    'Pillars',  # Стойки у проёмов
    'Rail_nY_z0020_s1',  # Рейка nY
    'Rail_nY_z0020_s2',  # Рейка nY #2
    'Rail_nY_z0980_s1',  # Рейка nY #3
    'Rail_nY_z1700_s1',  # Рейка nY #4
    'Rail_pY_z0020_s1',  # Рейка pY
    'Rail_pY_z0020_s2',  # Рейка pY #2
    'Rail_pY_z0980_s1',  # Рейка pY #3
    'Rail_pY_z1700_s1',  # Рейка pY #4
    'RearDoorLeaf_Driver',  # Створка задней двери со стороны водителя
    'RearDoorLeaf_Passenger',  # Створка задней двери со стороны пассажира
    'Rib_x0160',  # Ребро X=160
    'Rib_x1818',  # Ребро X=1818
    'Rib_x3068',  # Ребро X=3068
    'Ribs',  # Рёбра
    'Scan_Skin_Body',  # Обшивка #2
    'Trunk1_Drawer_Out',  # Ящик 36.0×27.3×17.5″ #2
    'Trunk2_TrayFwd_Out',  # Ящик 50.7×27.3×10.7″ #2
    'WheelArch_nY',  # Колёсная арка nY
    'WheelArch_pY',  # Колёсная арка pY
    'WheelArches',  # Колёсные арки
]
