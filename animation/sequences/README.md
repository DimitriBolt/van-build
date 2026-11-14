# animation/sequences/

Анимации — по файлу на последовательность; строка `MODELS` в файле говорит, для какой модели анимация:

| Файл | MODELS | Что показывает |
|---|---|---|
| `assembly.py` | любая | снять матрас → настил → поперечины → батареи B2–B4 |
| `drawers.py` | `van_v0` | два ящика багажника старой модели |
| `upper_drawer.py` | `van_v1_rect_pan` | верхний ящик выезжает назад на 1117.6 мм (SLIDEWAY 44″) |
| `lower_drawer.py` | `van_v1_rect_pan` | нижний ящик на колёсиках выкатывается вперёд на 900 мм |
| `shower_door.py` | `van_v1_rect_pan` | дверь душа открывается наружу на 90° вокруг петель |

Пишет их `animation/ea_export.FCMacro` (или руками — это данные на Python), собирает файл анимации на модели —
`animation/ea_build.FCMacro`. Формат и договор — `animation/README.md`.
