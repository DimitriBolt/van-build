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
| `battery_bank_drawing.png` | этажерка на 4 батареи (B1 на полу + полка над аркой на 3) и электрика рядом: MPPT, DC-DC, шины, трассы кабелей | `FURNITURE_MEMORY.md` §1h, §1i |
| `water_tank_drawing.png` | бак для воды T-3500 (35 gal) на полке над водительской аркой: сверху, вид на борт, разрез по ремню | §1j |
| `shower_kitchen_drawing.png` | душ 32×32″ + мини-кухня по водительскому борту: вид на борт, план, разрезы (высота в душе) | §1e |

## 3D-виды (`renders/`)

| Файл | Вид |
|---|---|
| `iso_with_skin.png`, `iso_frame.png` | весь фургон: со сканом кузова и только каркас |
| `top_frame.png`, `from_rear_doors.png` | сверху; от задних дверей |
| `bed_iso.png`, `bed_passenger_wall.png` | кровать крупно; пассажирский борт изнутри |
| `bank_3d.png`, `bank_wall_view.png`, `bank_top.png` | этажерка на 4 батареи |
| `tank_3d.png`, `tank_wall_view.png`, `tank_top.png` | бак T-3500 на полке над водительской аркой |
| `galley_3d.png`, `galley_wall_view.png`, `galley_top.png` | душ + мини-кухня |

## Архив (`archive/`)

Аналитические рисунки, по которым принимались решения; **не обновляются** (числа — по модели на дату в имени).

| Файл | Что |
|---|---|
| `2026-11-05_battery_pocket_plan.png`, `…plan2.png` | влезет ли батарея между аркой и D-стойкой (варианты) |
| `2026-11-05_battery_option1.png` | выбранный вариант 1 — батарея внутрь от стойки кровати, задом в D-стойку |
| `2026-11-06_battery_rack_front_drawing.png` | передний блок у сдвижной двери (заменён 2026-11-07) |
| `2026-11-07_battery_rack_drawing.png` | задний блок «2 батареи одна над другой» (заменён единой этажеркой 2026-11-07) |
| `2026-11-07_water_tank_torva_drawing.png`, `2026-11-07_tank_torva_*.png` | бак TORVA 33 gal у водительской арки на подставке (заменён T-3500 2026-11-07; модель — git-коммит `a2906da`) |

Скрипты архива — `tools/drawings/archive/`.
