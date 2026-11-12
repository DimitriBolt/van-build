# -*- coding: utf-8 -*-
"""Модель ↔ анимации: все ли детали из animation/sequences/*.py есть в модели?  БЕЗ FreeCAD, ≈1 с.

    python3 tools/check_animation.py                       # модель — van_v0_T4320.FCStd (на ней строятся анимации)
    python3 tools/check_animation.py van_v0.FCStd          # или любой другой .FCStd

Анимация ссылается на детали по внутреннему имени (obj.Name). Скрипт читает имена объектов прямо из .FCStd
(это zip с Document.xml) и сверяет их с именами в STEPS и HIDDEN каждой последовательности.
Запускать после пересборки модели — до коммита. Код возврата 0 — все детали на месте.
"""
import ast
import glob
import os
import re
import sys
import zipfile

REPO = os.environ.get("VAN_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def model_names(fcstd):
    """Внутренние имена всех объектов документа .FCStd."""
    with zipfile.ZipFile(fcstd) as z:
        xml = z.read("Document.xml").decode("utf-8", "replace")
    block = xml[xml.find("<Objects "):xml.find("</Objects>")]
    return set(re.findall(r'<Object\s+type="[^"]*"\s+name="([^"]+)"', block))


def sequence_names(path):
    """(детали из STEPS: имя → подписи шагов, список HIDDEN) из файла последовательности — без его выполнения."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    data = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            try:
                data[n.targets[0].id] = ast.literal_eval(n.value)
            except ValueError:
                pass
    parts = {}
    for step in data.get("STEPS", []):
        for p in step.get("parts", []):
            parts.setdefault(p["name"], []).append(step.get("label", "?"))
    return parts, list(data.get("HIDDEN", []))


def check(names, repo=REPO, out=print):
    """Сверить все последовательности с набором имён модели; возвращает число пропавших деталей."""
    missing = 0
    files = sorted(glob.glob(os.path.join(repo, "animation", "sequences", "*.py")))
    for f in files:
        parts, hidden = sequence_names(f)
        lost = [(n, "шаг «%s»" % "», «".join(parts[n])) for n in parts if n not in names]
        lost += [(n, "список HIDDEN") for n in hidden if n not in names and n not in parts]
        out("  %-14s деталей в шагах %d, скрытых %d — %s" % (
            os.path.basename(f), len(parts), len(hidden), "все есть в модели" if not lost else "НЕТ В МОДЕЛИ: %d" % len(lost)))
        for n, where in lost:
            out("      нет детали %s (%s)" % (n, where))
        missing += len([1 for n, w in lost if w != "список HIDDEN"])
        # пропавшее из HIDDEN — не ошибка (ea_build просто пропустит), но сказать стоит
    if not files:
        out("  последовательностей нет (animation/sequences/*.py)")
    return missing


if __name__ == "__main__":
    fcstd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "van_v0_T4320.FCStd")
    names = model_names(fcstd)
    print("check_animation: %s — объектов %d" % (os.path.basename(fcstd), len(names)))
    bad = check(names)
    print("check_animation:", "OK" if not bad else "ПРОПАЛО ДЕТАЛЕЙ ИЗ ШАГОВ АНИМАЦИИ: %d — вернуть имя в модели или записать "
          "замену в CHANGELOG.md" % bad)
    sys.exit(1 if bad else 0)
