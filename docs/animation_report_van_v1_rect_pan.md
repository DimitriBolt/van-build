# Анимации → модель van_v1_rect_pan (последняя сборка)

Пишется при каждой сборке модели (`vanmodel/motion.py`): ходы и порядок шагов берутся из анимаций
(`animation/sequences/*.py` и файлы `*_anim_*.FCStd` рядом с моделью) и проверяются на модели.
⚠ — деталь упирается в другую деталь; ⓘ — выходит за кузов (приём «прилёт из-за кадра»).

```
[Анимации → модель]  ходы и порядок — из анимаций; проверка: деталь проходит свой ход, не задевая то, что ещё стоит
  модель: van_v1_rect_pan
  assembly — animation/sequences/assembly.py: шагов 4, деталей 8
    порядок сборки (обратный разборке): Батареи B2–B4 → Поперечины → Настил → Матрас
    ▶ 1 «1 Матрас» — вверх 1500 мм:
        ⓘ «Mattress» (BedMattress): уже в исходном положении задевает кузов — «Body rail driver Z=980 #1» (Rail_pY_z0980_s1)
    ▶ 2 «2 Настил» — вверх 1000 мм:
        ⚠ «Bed deck» (BedDeck): в эту сторону не идёт — сразу упирается в «Wall plywood above deck» (BedWallPanel)
    ▶ 3 «3 Поперечины» — вверх 150 мм: свободно (3 дет.); в конце хода ближе всего: 15 мм — «Bed crossbar #1» (BedCross_1) ↔ «Body rail driver Z=980 #1» (Rail_pY_z0980_s1)
    ▶ 4 «4 Батареи B2–B4» — вверх 600 мм:
        ⚠ «Battery B2» (Battery_B2): свободный ход 57 мм из 600 — дальше «Bed side rail passenger» (BedSideRail_nY)
        ⚠ «Battery B3» (Battery_B3): свободный ход 57 мм из 600 — дальше «Bed side rail passenger» (BedSideRail_nY)
        ⚠ «Battery B4» (Battery_B4): свободный ход 57 мм из 600 — дальше «Bed side rail passenger» (BedSideRail_nY)
  fridge — animation/sequences/fridge.py: шагов 1, деталей 1
    порядок сборки (обратный разборке): Холодильник — выдвинуть в проход
    ▶ 1 «Холодильник — выдвинуть в проход» — к борту пассажира 400 мм: свободно (1 дет.)
  lower_drawer — animation/sequences/lower_drawer.py: шагов 1, деталей 8
    порядок сборки (обратный разборке): Нижний ящик — выкатить вперёд
    ▶ 1 «Нижний ящик — выкатить вперёд» — вперёд, к кабине 900 мм:
        ⚠ «Drawer caster P2» (Drawer_Wheel_P2): свободный ход 835 мм из 900 — дальше «Rack post plate P3f» (BankPostPlate_P3f)
        ⚠ «Drawer caster P3» (Drawer_Wheel_P3): свободный ход 286 мм из 900 — дальше «Rack post plate P3f» (BankPostPlate_P3f)
        остальные свободно: Drawer_Lower, Drawer_Lower_Handle, Drawer_Wheel_D1, Drawer_Wheel_P1, Drawer_Wheel_D2, Drawer_Wheel_D3
  shower_door — animation/sequences/shower_door.py: шагов 2, деталей 2
    порядок сборки (обратный разборке): Торцевая створка — сложить внутрь на 90° → Дверь душа — открыть на 90° наружу
    ▶ 1 «Дверь душа — открыть на 90° наружу» — поворот -90°:
        ⚠ «Shower door (acrylic, hinged on rear wall)» (Shower_Door): свободный ход 90° из 90 — дальше «Lower drawer handle» (Drawer_Lower_Handle)
    ▶ 2 «Торцевая створка — сложить внутрь на 90°» — поворот -90°: свободно (1 дет.); в конце хода ближе всего: 4 мм — «Shower end panel (acrylic, folds to side wall)» (Shower_DoorEnd) ↔ «Shower side wall» (Shower_WallBack)
  upper_drawer — animation/sequences/upper_drawer.py: шагов 2, деталей 6
    порядок сборки (обратный разборке): Откидной борт — откинуть назад на 90° → Верхний ящик — выдвинуть назад
    ▶ 1 «Верхний ящик — выдвинуть назад» — назад, к задним дверям 1118 мм: свободно (4 дет.)
    ▶ 2 «Откидной борт — откинуть назад на 90°» — поворот -90°: свободно (2 дет.)
  Итого: шагов 10 — свободно 5, ⚠ упирается 4, ⓘ выходит за кузов 1
```
