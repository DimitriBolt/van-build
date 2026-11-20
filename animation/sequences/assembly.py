# -*- coding: utf-8 -*-
# Анимация «assembly» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Сборка этажерки на 4 батареи (Battery rack 4 x 150 Ah) в модели van_v1_rect_pan — фактический порядок работ.
# Начало: Dimitri, van_v0_T4320_anim.FCStd (ea_export, 2026-11-09). Переработано Claude 2026-11-20 по указаниям Dimitri:
#   • перед ЛЮБОЙ работой снимаются матрас, настил и поперечины кровати #1–#3 (5 минут), в конце — ставятся обратно;
#   • в фургоне сейчас есть только кровать: 4 стойки с пластинами и 2 продольные рейки (стоят всегда, не двигаются),
#     матрас, настил, поперечины. Всё остальное — только в модели (список ABSENT: в файле анимации скрыто,
#     проверка модели не считает это препятствием).
#
# Как смотреть: ▶ (или ⏭) — до конца, затем ◀ Play Backwards — СБОРКА. В начале ◀ фургон такой, как сейчас
# (кровать собрана, этажерки нет); детали этажерки прилетают сверху «из-за кадра», через крышу.
# Подписи групп — по СБОРКЕ (◀): номер = шаг сборки, поэтому в дереве они идут снизу вверх (01 — внизу).
#
# Почему порядок именно такой (по геометрии модели):
#   • Рейка у борта — первая (якорь: задаёт высоту всей этажерки). Под продольной рейкой кровати её можно только
#     подать из прохода вбок (−Y), сверху не опустить. Затем болты M8 в овалы стоек P1/Pf, затем резина на арку.
#   • B1 — сразу после рейки у борта: потом её закроет ножка ящика #1 (до неё 8 мм) — B1 больше не вынуть,
#     пока стоит эта ножка.
#   • Опоры рейки прохода — ножки направляющих верхнего ящика #1, #2 (Drawer_Leg_passenger_1/2) сбоку, стойки P3f и передняя — под рейкой.
#   • Полку (фанера 214 мм) сверху прямо не опустить: щель между продольной рейкой кровати и ножками ящика —
#     181 мм. Опускается под наклоном 41° и ложится, поворачиваясь вокруг края у прохода.
#   • B2 и B4 с прохода прямо не поставить — мешают ножки #1 и #2. Все батареи заходят через «окно» — место B3
#     (между ножками 437 мм), затем B2 сдвигается назад к упору, B4 — вперёд к упору; B3 — последней.
#     Вверх с полки батарея идёт только на 57 мм (дальше продольная рейка кровати).
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения при ▶; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком
# (MODELS, ABSENT и SHOWN он сохраняет).

SEQUENCE = 'assembly'

# Для каких моделей эта анимация (имя файла модели без .FCStd).
# Детали этажерки из V-Slot 2020 (BankRailBolt_*, BankRailScrew_*, ножки ящика) есть только в van_v1_rect_pan.
MODELS = ['van_v1_rect_pan']

STEPS = [
    # ─────────── кровать: при ◀ это последние шаги — поставить всё обратно ───────────
    {   # 1
        'label': '28 Положить матрас',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 300,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedMattress', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Mattress
        ],
    },
    {   # 2
        'label': '27 Положить настил',
        'kind': 'simple',
        'distance': 1200.0,
        'steps': 240,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedDeck', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed deck
        ],
    },
    {   # 3
        'label': '26 Поставить поперечины кровати #1–#3',
        'kind': 'simple',
        'distance': 1200.0,
        'steps': 240,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedCross_1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #1
            {'name': 'BedCross_2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #2
            {'name': 'BedCross_3', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #3
        ],
    },
    # ─────────── батареи на полке: через «окно» B3 ───────────
    {   # 4
        'label': '25 B3 — с прохода на место',
        'kind': 'simple',
        'distance': 300.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B3', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B3
        ],
    },
    {   # 5  B4 едет 265.8 мм (место B3) за то же время, что B3 поднимается на 1500
        'label': '24 B4 — к переднему упору; B3 — сверху',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 150,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B3', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B3
            {'name': 'Battery_B4', 'vec': (-0.1772, 0.0, 0.0), 'rot_axis': (-0.1772, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B4
        ],
    },
    {   # 6
        'label': '23 B4 — с прохода в «окно» (место B3)',
        'kind': 'simple',
        'distance': 300.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B4', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B4
        ],
    },
    {   # 7
        'label': '22 B2 — к заднему упору; B4 — сверху',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 150,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B4', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B4
            {'name': 'Battery_B2', 'vec': (0.1772, 0.0, 0.0), 'rot_axis': (0.1772, 0.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B2
        ],
    },
    {   # 8
        'label': '21 B2 — с прохода в «окно» (место B3)',
        'kind': 'simple',
        'distance': 300.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B2', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B2
        ],
    },
    {   # 9
        'label': '20 B2 — сверху',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 150,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B2
        ],
    },
    # ─────────── упоры батарей ───────────
    {   # 10
        'label': '19 Упоры — на полку (за B2 и перед B4)',
        'kind': 'simple',
        'distance': 300.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankStop_ShelfRear', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery stop (rear)
            {'name': 'BankStop_ShelfFront', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery stop (front)
        ],
    },
    {   # 11
        'label': '18 Упоры батарей — сверху',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 150,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankStop_ShelfRear', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery stop (rear)
            {'name': 'BankStop_ShelfFront', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery stop (front)
        ],
    },
    # ─────────── полка: сверху под наклоном, потом лечь на рейки ───────────
    {   # 12  поворот вокруг верхнего края полки со стороны прохода (ось вдоль X): край у борта поднимается на 41°
        'label': '17 Полка — опустить на рейки',
        'kind': 'bolt',
        'distance': 0.0,
        'steps': 40,
        'step_time': 0.01,
        'revolutions': -0.113889,
        'parts': [
            {'name': 'BankShelf', 'vec': (1.0, 0.0, 0.0), 'rot_axis': (1.0, 0.0, 0.0), 'rot_center': (900.0, -745.0, 500.0)},  # Battery shelf
        ],
    },
    {   # 13
        'label': '16 Полка — сверху, под наклоном 41°',
        'kind': 'simple',
        'distance': 1550.0,
        'steps': 155,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankShelf', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery shelf
        ],
    },
    # ─────────── поперечины этажерки и L-пластины ───────────
    {   # 14
        'label': '15 L-пластины — под рейки и поперечины',
        'kind': 'simple',
        'distance': 300.0,
        'steps': 60,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankLPlate_Rear_Wall', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Rear_Wall
            {'name': 'BankLPlate_Rear_Inner', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Rear_Inner
            {'name': 'BankLPlate_Front_Wall', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Front_Wall
            {'name': 'BankLPlate_Front_Inner', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Front_Inner
        ],
    },
    {   # 15  чуть наклонно: поперечина у борта касается продольной рейки кровати (0.6 мм в модели)
        'label': '14 Поперечины этажерки и L-пластины — сверху',
        'kind': 'simple',
        'distance': 1550.0,
        'steps': 155,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankCross_Rear', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack crossbar Rear
            {'name': 'BankCross_Front', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack crossbar Front
            {'name': 'BankLPlate_Rear_Wall', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Rear_Wall
            {'name': 'BankLPlate_Rear_Inner', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Rear_Inner
            {'name': 'BankLPlate_Front_Wall', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Front_Wall
            {'name': 'BankLPlate_Front_Inner', 'vec': (0.0, 0.025, 1.0), 'rot_axis': (0.0, 0.025, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # L-plate Front_Inner
        ],
    },
    # ─────────── рейка со стороны прохода ───────────
    {   # 16  винты вставляются из щели между рейками (головка — со стороны борта)
        'label': '13 Винты M5: рейка прохода ↔ ножки #1, #2',
        'kind': 'simple',
        'distance': 100.0,
        'steps': 20,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankRailScrew_Leg1', 'vec': (0.0, -1.0, 0.0), 'rot_axis': (0.0, -1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 Leg1
            {'name': 'BankRailScrew_Leg2', 'vec': (0.0, -1.0, 0.0), 'rot_axis': (0.0, -1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 Leg2
        ],
    },
    {   # 17
        'label': '12 Рейка прохода — на стойки P3f и переднюю, вплотную к ножкам ящика; винты M5 — сверху',
        'kind': 'simple',
        'distance': 1550.0,
        'steps': 155,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankRail_Inner', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack rail (aisle side)
            {'name': 'BankRailScrew_Leg1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 Leg1
            {'name': 'BankRailScrew_Leg2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 Leg2
            {'name': 'BankRailScrew_P3f', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 P3f
            {'name': 'BankRailScrew_Front', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail screw M5 Front
        ],
    },
    # ─────────── опоры рейки прохода ───────────
    {   # 18
        'label': '11 Ножки ящика #1, #2 со скобами, стойки P3f и передняя с пластинами',
        'kind': 'simple',
        'distance': 2000.0,
        'steps': 200,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Drawer_Leg_passenger_1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Slide leg passenger 1
            {'name': 'Drawer_Leg_passenger_2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Slide leg passenger 2
            {'name': 'BankBracket_Leg1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Corner bracket Leg1
            {'name': 'BankBracket_Leg2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Corner bracket Leg2
            {'name': 'BankPostPlate_P3f', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack post plate P3f
            {'name': 'BankPost_P3f', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack post P3f
            {'name': 'BankPostPlate_Front', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack post plate Front
            {'name': 'BankPost_Front', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack post Front
        ],
    },
    # ─────────── B1 на полу — до ножки #1 ───────────
    {   # 19
        'label': '10 Клин B1 ↔ арка',
        'kind': 'simple',
        'distance': 350.0,
        'steps': 70,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankWedge_B1Arch', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Wedge B1 / arch
        ],
    },
    {   # 20
        'label': '09 B1 — на пол между D-стойкой и аркой',
        'kind': 'simple',
        'distance': 350.0,
        'steps': 70,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B1', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B1
        ],
    },
    {   # 21
        'label': '08 B1 и клин — сверху в проход',
        'kind': 'simple',
        'distance': 2000.0,
        'steps': 200,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'Battery_B1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Battery B1
            {'name': 'BankWedge_B1Arch', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Wedge B1 / arch
        ],
    },
    # ─────────── рейка у борта — первая (якорь) ───────────
    {   # 22
        'label': '07 Резина — между аркой и рейкой',
        'kind': 'simple',
        'distance': 250.0,
        'steps': 50,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankArchPad_1', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Arch pad 1
            {'name': 'BankArchPad_2', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Arch pad 2
        ],
    },
    {   # 23
        'label': '06 Болты M8: рейка ↔ стойки кровати P1, Pf',
        'kind': 'simple',
        'distance': 350.0,
        'steps': 70,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankRailBolt_P1', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail bolt M8 P1
            {'name': 'BankRailBolt_Pf', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail bolt M8 Pf
        ],
    },
    {   # 24
        'label': '05 Рейка у борта — к стойкам кровати P1, Pf',
        'kind': 'simple',
        'distance': 250.0,
        'steps': 50,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankRail_Wall', 'vec': (0.0, 1.0, 0.0), 'rot_axis': (0.0, 1.0, 0.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack rail (wall side)
        ],
    },
    {   # 25
        'label': '04 Рейка у борта, болты, резина — сверху в проход',
        'kind': 'simple',
        'distance': 1600.0,
        'steps': 160,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BankRail_Wall', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rack rail (wall side)
            {'name': 'BankRailBolt_P1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail bolt M8 P1
            {'name': 'BankRailBolt_Pf', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Rail bolt M8 Pf
            {'name': 'BankArchPad_1', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Arch pad 1
            {'name': 'BankArchPad_2', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Arch pad 2
        ],
    },
    # ─────────── кровать: при ◀ это первые шаги — снять ───────────
    {   # 26
        'label': '03 Снять поперечины кровати #1–#3',
        'kind': 'simple',
        'distance': 1200.0,
        'steps': 240,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedCross_1', 'vec': (0.0, 0.0, -1.0), 'rot_axis': (0.0, 0.0, -1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #1
            {'name': 'BedCross_2', 'vec': (0.0, 0.0, -1.0), 'rot_axis': (0.0, 0.0, -1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #2
            {'name': 'BedCross_3', 'vec': (0.0, 0.0, -1.0), 'rot_axis': (0.0, 0.0, -1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed crossbar #3
        ],
    },
    {   # 27
        'label': '02 Снять настил',
        'kind': 'simple',
        'distance': 1200.0,
        'steps': 240,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedDeck', 'vec': (0.0, 0.0, -1.0), 'rot_axis': (0.0, 0.0, -1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Bed deck
        ],
    },
    {   # 28
        'label': '01 Снять матрас',
        'kind': 'simple',
        'distance': 1500.0,
        'steps': 300,
        'step_time': 0.01,
        'revolutions': 0.0,
        'parts': [
            {'name': 'BedMattress', 'vec': (0.0, 0.0, -1.0), 'rot_axis': (0.0, 0.0, -1.0), 'rot_center': (0.0, 0.0, 0.0)},  # Mattress
        ],
    },
]

# Объекты, скрытые в файле анимации (только вид — проверка модели считает их препятствиями).
HIDDEN = [
    'Opening_RearDoors',  # Проём задних дверей
    'Opening_SlidingDoor',  # Проём сдвижной двери
    'Openings',  # Проёмы дверей
    'RearDoorLeaf_Driver',  # Створка задней двери со стороны водителя
    'RearDoorLeaf_Passenger',  # Створка задней двери со стороны пассажира
    'Scan_Skin',  # Обшивка
    'Scan_Skin_Body',  # Обшивка #2
]

# Чего в этом сценарии ещё НЕТ (есть только в модели): ea_build скрывает (группу — вместе с содержимым),
# проверка модели (vanmodel/motion.py) не считает препятствием.
ABSENT = [
    'BedWallLedger2x4',  # Wall ledger 2x4
    'BedWallPanel',  # Wall plywood above deck
    'Electrical',  # Electrical at batteries (вся группа)
    'Shower',  # Shower (вся группа: поддон, туалет, стенки, нагреватель…)
    'Kitchen',  # Kitchen (вся группа)
    'Propane',  # Propane (вся группа)
    'WaterTankRect',  # Water tank (вся группа)
    'ArchShelf',  # Arch shelf (вся группа)
    'WallCabinets',  # Ceiling cabinets (вся группа)
    # группа Drawers — всё, кроме ножек #1, #2 у пассажирского борта (они — опоры рейки прохода, ставятся в шаге 11)
    'Drawer_Upper',  # Upper drawer (slides rearward)
    'Drawer_Upper_Tailgate',  # Upper drawer tailgate (drop-down rear wall)
    'Drawer_Upper_TailgateHinge',  # Upper drawer tailgate hinge
    'Drawer_Upper_Bag',  # SUP bag Genreen (in upper drawer)
    'Drawer_Upper_BagPicture',  # SUP bag picture (top)
    'Drawer_Slide_driver',  # Drawer slide driver
    'Drawer_Slide_passenger',  # Drawer slide passenger
    'Drawer_Leg_driver_1',  # Slide leg driver 1
    'Drawer_Leg_driver_2',  # Slide leg driver 2
    'Drawer_Lower',  # Lower drawer (rolls forward)
    'Drawer_Wheel_D1',  # Drawer caster D1
    'Drawer_Wheel_D2',  # Drawer caster D2
    'Drawer_Wheel_D3',  # Drawer caster D3
    'Drawer_Wheel_P1',  # Drawer caster P1
    'Drawer_Wheel_P2',  # Drawer caster P2
    'Drawer_Wheel_P3',  # Drawer caster P3
]

# Что показать, хотя в модели оно скрыто по умолчанию (группа Frame): пол, арки, D-стойки — на них стоит этажерка.
SHOWN = [
    'Floor_Plywood',  # Floor plywood 1/2″
    'WheelArch_nY',  # Wheel arch passenger
    'WheelArch_pY',  # Wheel arch driver
    'DPillarFace_nY_ref',  # D-pillar passenger
    'DPillarFace_pY_ref',  # D-pillar driver
]
