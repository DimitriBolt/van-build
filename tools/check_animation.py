# -*- coding: utf-8 -*-
"""Модель ↔ анимации: все ли детали из animation/sequences/*.py есть в модели?  БЕЗ FreeCAD, ≈1 с.

    python3 tools/check_animation.py                       # модель — van_v0_T4320.FCStd (на ней строятся анимации)
    python3 tools/check_animation.py van_v1_rect_pan.FCStd # или любой другой .FCStd

Проверяются только анимации этой модели: у кого в файле MODELS есть её имя (или MODELS пуст — «для любой»);
'van_v0' в MODELS подходит и к van_v0_T4320 и т.д. Остальные перечисляются как «для других моделей».

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


def applies(models, stem):
    """Подходит ли анимация к модели stem: MODELS пуст — к любой; 'van_v0' подходит и к van_v0_T4320."""
    return not models or any(stem == m or stem.startswith(m + "_") for m in models)


def sequence_models(path):
    """MODELS из файла последовательности — без его выполнения."""
    for n in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MODELS":
            try:
                return [str(m) for m in ast.literal_eval(n.value)]
            except ValueError:
                return []
    return []


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


def check(names, repo=REPO, out=print, model=None):
    """Сверить последовательности модели model (None — все) с набором её имён; возвращает число пропавших деталей."""
    missing = 0
    files = sorted(glob.glob(os.path.join(repo, "animation", "sequences", "*.py")))
    for f in files:
        models = sequence_models(f)
        if model and not applies(models, model):
            out("  %-16s для других моделей (%s) — пропущена" % (os.path.basename(f), ", ".join(models)))
            continue
        parts, hidden = sequence_names(f)
        lost = [(n, "шаг «%s»" % "», «".join(parts[n])) for n in parts if n not in names]
        lost += [(n, "список HIDDEN") for n in hidden if n not in names and n not in parts]
        out("  %-16s деталей в шагах %d, скрытых %d — %s" % (
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
    bad = check(names, model=os.path.splitext(os.path.basename(fcstd))[0])
    print("check_animation:", "OK" if not bad else "ПРОПАЛО ДЕТАЛЕЙ ИЗ ШАГОВ АНИМАЦИИ: %d — вернуть имя в модели или записать "
          "замену в CHANGELOG.md" % bad)
    sys.exit(1 if bad else 0)
