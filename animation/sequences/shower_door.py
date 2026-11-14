# -*- coding: utf-8 -*-
# Анимация «shower_door» для ExplodedAssembly — это ДАННЫЕ, не программа.
# Источник: написана Claude по модели van_v1_rect_pan (vanmodel/shower_rect.py), 2026-11-13.
#
# Дверь душа вдоль прохода (акрил 1/4″) открывается НАРУЖУ, в проход, на 90° вокруг вертикальной оси петель —
# внутренней кромки задней стенки душа (Shower_WallRear.Edge4): X 1351.94, Y 334.19. Поворот −90° вокруг +Z
# (как у контрольного положения Shower_Door_Open в модели). ▶ — открыть, ◀ — закрыть.
# Поворот в ExplodedAssembly — это Bolt Group: revolutions = −0.25 оборота, distance = 0 (дверь не сдвигается).
# Петли Shower_DoorHinge_* стоят на оси — они не двигаются.
# Открытая дверь перекрывает проход: нижний ящик при этом должен быть закатан (в этом файле он закрыт).
# Призраки открытых дверей в файле анимации скрыты (HIDDEN) — вместо них настоящая дверь.
#
# STEPS идут в порядке РАЗБОРКИ — как группы в папке ExplodedAssembly:
#   ▶ Play Forward проигрывает их сверху вниз, ◀ Play Backwards («сборка») — снизу вверх.
# name       — внутреннее имя детали (obj.Name); справа в комментарии — её Label.
# vec        — направление движения; длина вектора масштабирует ход (0.5 = половина distance).
# distance   — мм; steps — число кадров; step_time — пауза между кадрами, с; revolutions — обороты (Bolt Group).
# rot_axis / rot_center — ось и центр вращения (нужны только при revolutions ≠ 0).
# Собрать файл анимации на свежей модели — макрос animation/ea_build.FCMacro.
# Если правите файл руками, учтите: повторный ea_export с тем же именем перезапишет его целиком.

SEQUENCE = 'shower_door'

# Для каких моделей эта анимация (имя файла модели без .FCStd; 'van_v0' — это и van_v0_T4320 и т.д.).
MODELS = ['van_v1_rect_pan']

STEPS = [
    {   # 1
        'label': 'Дверь душа — открыть на 90° наружу',
        'kind': 'bolt',
        'distance': 0.0,
        'steps': 90,
        'step_time': 0.01,
        'revolutions': -0.25,
        'parts': [
            {'name': 'Shower_Door', 'vec': (0.0, 0.0, 1.0), 'rot_axis': (0.0, 0.0, 1.0), 'rot_center': (1351.94, 334.1903, 0.0)},  # Shower door (acrylic, hinged on rear wall)
        ],
    },
]

# Объекты, скрытые в файле анимации на момент экспорта; ea_build скроет их снова.
HIDDEN = [
    'Shower_Door_Open',  # Shower door open 90°
    'Shower_DoorEnd_Folded',  # Shower end panel folded
]
