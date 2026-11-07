# Рисунки проекта (последние версии)

Все чертежи и виды строятся **из модели** `van_v0.py` — после любого изменения модели:

```bash
tools/make_docs.sh
# на M6800 (AppImage):
FREECADCMD="$HOME/Applications/FreeCAD.AppImage --console" FREECAD="$HOME/Applications/FreeCAD.AppImage" tools/make_docs.sh
```

Скрипт: `tools/photo_corners_2026-11-06.py` (точки с фото задних углов → `docs/rear_corners_points.json`) →
`tools/export_drawing_data.py` (FreeCAD → `docs/drawing_data.json`) → `tools/drawings/*.py`
(python3 + matplotlib → 2D-чертежи) → `tools/render_views.py` (FreeCAD GUI → `docs/renders/`,
и `van_v0.FCStd` с цветами). Размеры на чертежах — в дюймах, от чистового пола (верх фанеры).

## 2D-чертежи

| Файл | Что | Описание |
|---|---|---|
| `rear_corners_drawing.png` | задние углы у пола: арка ↔ D-стойка, оба борта — точки с 4 фото сверху + модель, таблица зазоров | §1f |
| `battery_rack_drawing.png` | задний блок батарей (пассажирский борт, D-стойка ↔ арка) | `FURNITURE_MEMORY.md` §1b |
| `battery_bank_drawing.png` | все 4 батареи: задний блок + полка НАД аркой (проект 2026-11-07) | §1g |
| `water_tank_drawing.png` | бак для воды TORVA 33 gal у водительской арки: вид на борт, сверху, разрез по колесу | §1d |
| `shower_kitchen_drawing.png` | душ 32×32″ + мини-кухня по водительскому борту: вид на борт, план, разрезы (высота в душе) | §1e |

## 3D-виды (`renders/`)

| Файл | Вид |
|---|---|
| `iso_with_skin.png`, `iso_frame.png` | весь фургон: со сканом кузова и только каркас |
| `top_frame.png`, `from_rear_doors.png` | сверху; от задних дверей |
| `bed_iso.png`, `bed_passenger_wall.png` | кровать крупно; пассажирский борт изнутри |
| `rack_with_cross.png`, `rack_3d.png`, `battery_bank_3d.png`, `rack_from_inside.png`, `rack_top.png` | батареи: задний блок, все 4 с полкой над аркой |
| `tank_3d.png`, `tank_wall_view.png`, `tank_top.png` | бак для воды |
| `galley_3d.png`, `galley_wall_view.png`, `galley_top.png` | душ + мини-кухня |

## Архив (`archive/`)

Аналитические рисунки, по которым принимались решения; **не обновляются** (числа — по модели на дату в имени).

| Файл | Что |
|---|---|
| `2026-11-05_battery_pocket_plan.png`, `…plan2.png` | влезет ли батарея между аркой и D-стойкой (варианты) |
| `2026-11-05_battery_option1.png` | выбранный вариант 1 — батарея внутрь от стойки кровати, задом в D-стойку |
| `2026-11-06_battery_rack_front_drawing.png` | передний блок у сдвижной двери (заменён полкой над аркой 2026-11-07) |

Скрипты архива — `tools/drawings/archive/`.
