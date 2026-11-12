# -*- coding: utf-8 -*-
"""Быстрая проверка кода модели БЕЗ FreeCAD (≈1 с):  python3 tools/check_stages.py

Модель собирается по разделам (vanmodel/build.py → STAGES), которые передают друг другу данные через контекст
сборки S (vanmodel/state.py). Скрипт ничего не строит — он читает исходники и проверяет «проводку»:
  1) каждый модуль vanmodel/ компилируется;
  2) каждое имя, которое раздел берёт из контекста (S.имя), положил туда какой-то раздел, стоящий РАНЬШЕ;
  3) всё, что раздел кладёт в контекст (S.put(locals(), "…")), в нём действительно создаётся;
  4) в модулях нет обращений к именам, которых нигде нет (забыли взять из S или импортировать).
Запускать после любой правки vanmodel/ — до сборки во FreeCAD. Код возврата 0 — всё в порядке.
"""
import ast
import builtins
import os
import symtable
import sys

REPO = os.environ.get("VAN_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "vanmodel")
errors, notes = [], []


def read(name):
    with open(os.path.join(PKG, name + ".py"), encoding="utf-8") as f:
        return f.read()


# ── порядок разделов из build.py ──
stages = []
for node in ast.parse(read("build")).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "STAGES":
        for el in node.value.elts:
            fn, title = el.elts[0], el.elts[1]
            stages.append((fn.value.id, fn.attr, title.value))
if not stages:
    errors.append("build.py: не найден список STAGES")

# ── 1) компиляция и 4) неизвестные имена ──
modules = sorted(f[:-3] for f in os.listdir(PKG) if f.endswith(".py"))
trees = {}
for m in modules:
    src = read(m)
    try:
        trees[m] = ast.parse(src)
        compile(src, m + ".py", "exec")
    except SyntaxError as e:
        errors.append("%s.py: синтаксическая ошибка, строка %s: %s" % (m, e.lineno, e.msg))
        continue
    top = symtable.symtable(src, m + ".py", "exec")
    star = any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names) for n in trees[m].body)
    defined = set(s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace())
    known = defined | set(dir(builtins)) | {"__file__", "__name__", "__doc__"}

    def walk(tb, is_top, where):
        for s in tb.get_symbols():
            if not s.is_referenced() or s.get_name() in known:
                continue
            if (is_top and not s.is_assigned()) or (not is_top and s.is_global()):
                errors.append("%s.py, %s: имя «%s» нигде не определено (взять из S в начале раздела или "
                              "импортировать)" % (m, where, s.get_name()))
        for c in tb.get_children():
            walk(c, False, "%s()" % c.get_name() if is_top else where)
    if not star:
        walk(top, True, "уровень модуля")

# ── 2) и 3) проводка контекста ──
provided = {}            # имя → раздел, который положил его последним
readers = {}             # имя → разделы, которые его читают
for mod, func, title in stages:
    tree = trees.get(mod)
    fdef = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == func), None) if tree else None
    if fdef is None:
        errors.append("build.py: раздел %s.%s() не найден" % (mod, func))
        continue
    where = "%s.%s()" % (mod, func)
    local = set()
    for n in ast.walk(fdef):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            local.add(n.id)
        elif isinstance(n, ast.FunctionDef) and n is not fdef:
            local.add(n.name)
        elif isinstance(n, ast.alias):
            local.add((n.asname or n.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            local.add(n.name)
    reads, puts = [], []
    for n in ast.walk(fdef):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "S":
            if isinstance(n.ctx, ast.Load) and n.attr != "put":
                reads.append(n.attr)
            elif isinstance(n.ctx, ast.Store):
                puts.append(n.attr)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "put" and \
                isinstance(n.func.value, ast.Name) and n.func.value.id == "S":
            if len(n.args) == 2 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                for nm in n.args[1].value.split():
                    puts.append(nm)
                    if nm not in local:
                        errors.append("%s кладёт в контекст «%s», но такой переменной в разделе нет" % (where, nm))
            else:
                errors.append("%s: S.put(...) — ожидается S.put(locals(), \"имена через пробел\")" % where)
    for nm in reads:
        readers.setdefault(nm, []).append(where)
        if nm not in provided:
            errors.append("%s берёт из контекста «%s», но ни один раздел до него это не кладёт "
                          "(добавить в S.put(...) того раздела, где оно создаётся)" % (where, nm))
    for nm in puts:
        provided[nm] = where
last = "%s.%s()" % stages[-1][:2] if stages else None
for nm, where in sorted(provided.items()):
    if nm not in readers and where != last:      # последний раздел кладёт результаты для консоли
        notes.append("«%s» (кладёт %s) никто дальше не читает" % (nm, where))

print("vanmodel: модулей %d, разделов %d, имён в контексте сборки %d" % (len(modules), len(stages), len(provided)))
for n in notes:
    print("  заметка:", n)
for e in errors:
    print("  ОШИБКА:", e)
print("check_stages:", "OK" if not errors else "ОШИБОК: %d" % len(errors))
sys.exit(1 if errors else 0)
