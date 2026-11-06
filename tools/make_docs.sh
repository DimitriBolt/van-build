#!/usr/bin/env bash
# Пересобрать ВСЕ рисунки в docs/ из текущей модели van_v0.py:
#   1) данные модели → docs/drawing_data.json        (FreeCAD headless)
#   2) 2D-чертежи → docs/*.png                         (python3 + matplotlib)
#   3) 3D-виды → docs/renders/*.png + van_v0.FCStd с цветами (FreeCAD GUI; без экрана — через xvfb-run)
#
#   tools/make_docs.sh
# На M6800 (AppImage):
#   FREECADCMD="$HOME/Applications/FreeCAD.AppImage --console" FREECAD="$HOME/Applications/FreeCAD.AppImage" tools/make_docs.sh
set -euo pipefail
cd "$(dirname "$0")/.."
FREECADCMD=${FREECADCMD:-freecadcmd}
FREECAD=${FREECAD:-freecad}
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8

$FREECADCMD tools/export_drawing_data.py
for s in tools/drawings/battery_rack_rear.py tools/drawings/battery_rack_front.py tools/drawings/water_tank.py; do
    (cd tools/drawings && python3 "$(basename "$s")")
done
if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null; then
    RENDER_OUT=docs/renders xvfb-run -a -s "-screen 0 1920x1200x24" $FREECAD tools/render_views.py
else
    RENDER_OUT=docs/renders $FREECAD tools/render_views.py
fi
cat docs/renders/render_log.txt | tail -1
