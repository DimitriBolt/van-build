# -*- coding: utf-8 -*-
"""Анимации → модель: ходы деталей и порядок сборки берутся из анимаций Dimitri и проверяются на модели.

Откуда берутся анимации (сами они остаются отдельными — модель их только ЧИТАЕТ):
  1) animation/sequences/<имя>.py — то, что записано в репозиторий (ea_export);
  2) файлы анимации рядом с моделью: <модель>_anim_<имя>.FCStd (а также *_anim.FCStd, *_drawer.FCStd) — группы
     ExplodedAssembly читаются прямо из сохранённого файла, без шага ea_export. Если файл отличается от
     sequences/<имя>.py и не старее его — в модель идёт файл (и печатается напоминание про ea_export).

Что проверяется для каждого шага (шаги идут в порядке разборки, как в анимации):
  • деталь проходит свой ход (vec × distance), не задевая то, что в этот момент ещё стоит на месте;
    детали предыдущих шагов считаются уже сдвинутыми — так проверяется и порядок сборки;
  • если ход свободен — что оказывается рядом в конце хода (зазор меньше NEAR мм).
Результат печатается после сводки и пишется в docs/animation_report.md. Геометрию модели раздел не меняет;
любая ошибка здесь — только строка в отчёте, сборка модели от анимаций не зависит.
Отключить: переменная окружения VAN_MOTION=0.
"""
import ast
import base64
import glob
import json
import os
import re
import struct
import time
import xml.etree.ElementTree as ET
import zipfile

import FreeCAD as App

from .common import PROJECT_DIR, SAVE_PATH

SHELL_GROUPS = ("Ribs", "Longitudinals", "Pillars")      # оболочка кузова: упёрлись в неё — «выходит за кузов»
SKIP_GROUPS = ("Openings", "HoleMarkers", "FactoryThreadedMounts", "ExplodedAssembly")   # реф-объекты, не препятствия
SKIP_SUFFIX = ("_Out", "_ref", "_Open", "_Folded")      # иллюстративные копии (выдвинуто/открыто/сложено) и реф-грани
TOL_V = 200.0        # мм³ — пересечение меньше этого (сверх исходного) столкновением не считается
NEAR = 150.0         # мм — «рядом в конце хода» (соседи, которые были так же близко и до хода, не в счёт)
BUDGET = 240.0       # с — предел времени на все проверки (дальше шаги помечаются «не проверено»)

AXIS_WORDS = {(0, 1): "вперёд, к кабине", (0, -1): "назад, к задним дверям", (1, 1): "к борту водителя",
              (1, -1): "к борту пассажира", (2, 1): "вверх", (2, -1): "вниз"}


# ───────────────────────── чтение анимаций ─────────────────────────
def _py_data(path):
    """Переменные файла последовательности (SEQUENCE, MODELS, STEPS, HIDDEN) — без его выполнения."""
    data = {}
    for node in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                data[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    return data


def read_models_py(path):
    """MODELS — для каких моделей анимация (пусто — для любой)."""
    return [str(m) for m in _py_data(path).get("MODELS", [])]


def applies(models, stem):
    """Подходит ли анимация к модели stem: MODELS пуст — к любой; 'van_v0' подходит и к van_v0_T4320."""
    return not models or any(stem == m or stem.startswith(m + "_") for m in models)


def model_stem():
    """Имя модели, которая сейчас собирается: имя её файла без .FCStd (van_v0, van_v0_T4320, van_v1_rect_pan…)."""
    return os.path.splitext(os.path.basename(SAVE_PATH))[0]


def read_sequence_py(path):
    """animation/sequences/<имя>.py → список шагов. Файл — данные: читается без выполнения."""
    data = _py_data(path)
    steps = []
    for st in data.get("STEPS", []):
        steps.append(dict(label=str(st.get("label", "?")), kind=st.get("kind", "simple"),
                          distance=float(st.get("distance", 0.0)), revolutions=float(st.get("revolutions", 0.0)),
                          parts=[dict(name=p["name"], vec=tuple(float(c) for c in p["vec"]),
                                      rot_axis=tuple(float(c) for c in p.get("rot_axis", p["vec"])),
                                      rot_center=tuple(float(c) for c in p.get("rot_center", (0.0, 0.0, 0.0))))
                                 for p in st.get("parts", [])]))
    return steps


def _vector_list(blob):
    """Двоичный файл PropertyVectorList из .FCStd: uint32 n + n×3 чисел (double; в старых версиях — float)."""
    if len(blob) < 4:
        return []
    n = struct.unpack("<I", blob[:4])[0]
    if n and len(blob) >= 4 + 24 * n:
        v = struct.unpack("<%dd" % (3 * n), blob[4:4 + 24 * n])
    elif n and len(blob) >= 4 + 12 * n:
        v = struct.unpack("<%df" % (3 * n), blob[4:4 + 12 * n])
    else:
        return []
    return [tuple(v[3 * i:3 * i + 3]) for i in range(n)]


def read_anim_fcstd(path):
    """Группы ExplodedAssembly из сохранённого файла анимации (.FCStd — zip с Document.xml) → список шагов."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("Document.xml"))
        data = root.find("ObjectData")
        objs = {o.get("name"): o for o in (data.findall("Object") if data is not None else [])}

        def prop(obj, name):
            for p in obj.iter("Property"):
                if p.get("name") == name:
                    return p
            return None

        def value(obj, name, tag, default=None):
            p = prop(obj, name)
            el = p.find(tag) if p is not None else None
            return el.get("value") if el is not None else default

        folder = objs.get("ExplodedAssembly")
        if folder is None:
            return []
        links = prop(folder, "Group")
        order = [l.get("value") for l in links.iter("Link")] if links is not None else []
        steps = []
        for gname in order:
            g = objs.get(gname)
            if g is None or not gname.startswith(("SimpleGroup", "BoltGroup")):
                continue
            py = prop(g, "names")
            el = py.find("Python") if py is not None else None
            raw = el.get("value", "") if el is not None else ""
            if el is not None and el.get("encoded") == "yes":
                raw = base64.b64decode(raw).decode("utf-8")
            names = json.loads(raw) if raw else []
            dv = prop(g, "dir_vectors")
            vl = dv.find("VectorList") if dv is not None else None
            vecs = _vector_list(z.read(vl.get("file"))) if vl is not None and vl.get("file") else []

            def vlist(pname):
                pr = prop(g, pname)
                el_ = pr.find("VectorList") if pr is not None else None
                return _vector_list(z.read(el_.get("file"))) if el_ is not None and el_.get("file") else []
            rvs, rcs = vlist("rot_vectors"), vlist("rot_centers")
            n = min(len(names), len(vecs))
            steps.append(dict(label=value(g, "Label", "String", gname), kind="bolt" if gname.startswith("Bolt") else "simple",
                              distance=float(value(g, "Distance", "Float", 0.0)),
                              revolutions=float(value(g, "Revolutions", "Float", 0.0)),
                              parts=[dict(name=str(names[i]), vec=tuple(float(c) for c in vecs[i]),
                                          rot_axis=tuple(float(c) for c in (rvs[i] if i < len(rvs) else vecs[i])),
                                          rot_center=tuple(float(c) for c in (rcs[i] if i < len(rcs) else (0.0, 0.0, 0.0))))
                                     for i in range(n)]))
        return steps


def model_from_file(stem):
    """Модель по имени файла анимации: van_v1_rect_pan_anim_upper_drawer → van_v1_rect_pan."""
    m = re.search(r"^(.+?)_anim_[A-Za-z0-9_]+$", stem)
    if m:
        return m.group(1)
    for suf in ("_drawers", "_drawer", "_anim"):
        if stem.endswith(suf):
            return stem[:-len(suf)]
    return None


def seq_name_from_file(stem):
    """Имя последовательности по имени файла анимации — как в animation/ea_export.FCMacro."""
    m = re.search(r"_anim_([A-Za-z0-9_]+)$", stem)
    if m:
        return m.group(1)
    for suf, seq in (("_drawers", "drawers"), ("_drawer", "drawers"), ("_anim", "assembly")):
        if stem.endswith(suf):
            return seq
    return None


def _key(steps):
    return [(s["label"], s["kind"], round(s["distance"], 3),
             [(p["name"], tuple(round(c, 4) for c in p["vec"])) for p in s["parts"]]) for s in steps]


def load_sequences(repo=PROJECT_DIR, model=None, skipped=None):
    """Анимации модели model (None — все): [{name, source, steps, notes}] — из animation/sequences и из файлов
    анимации рядом с моделью. Анимации других моделей (MODELS) — в список skipped: (имя, модели)."""
    seqs = {}
    for f in sorted(glob.glob(os.path.join(repo, "animation", "sequences", "*.py"))):
        name = os.path.splitext(os.path.basename(f))[0]
        try:
            models = read_models_py(f)
        except Exception:
            models = []
        if model and not applies(models, model):
            if skipped is not None:
                skipped.append((name, models))
            continue
        try:
            seqs[name] = dict(name=name, source=os.path.relpath(f, repo), path=f, steps=read_sequence_py(f), notes=[])
        except Exception as e:
            seqs[name] = dict(name=name, source=os.path.relpath(f, repo), path=f, steps=[],
                              notes=["не прочитана: %s" % e])
    def same_model(stem):                      # файл анимации своей модели: van_v0 ↔ van_v0_T4320 — одна модель
        fm = model_from_file(stem)
        return not model or (fm is not None and (fm == model or fm.startswith(model + "_") or model.startswith(fm + "_")))

    skip_names = set(n for n, _ in (skipped or []))
    files = [f for f in glob.glob(os.path.join(repo, "*.FCStd"))
             if seq_name_from_file(os.path.splitext(os.path.basename(f))[0])
             and same_model(os.path.splitext(os.path.basename(f))[0])
             and seq_name_from_file(os.path.splitext(os.path.basename(f))[0]) not in skip_names]
    for f in sorted(files, key=os.path.getmtime):                       # самый свежий файл — последним
        name, base = seq_name_from_file(os.path.splitext(os.path.basename(f))[0]), os.path.basename(f)
        try:
            steps = read_anim_fcstd(f)
        except Exception as e:
            seqs.setdefault(name, dict(name=name, source=base, path=f, steps=[], notes=[]))["notes"].append(
                "файл анимации %s не прочитан: %s" % (base, e))
            continue
        if not steps:
            continue
        cur = seqs.get(name)
        if cur is None or not cur["path"].endswith(".py"):
            seqs[name] = dict(name=name, source=base, path=f, steps=steps,
                              notes=["взята из файла анимации — в репозиторий ещё не записана (ea_export)"])
        elif _key(steps) == _key(cur["steps"]):
            continue
        elif os.path.getmtime(f) >= os.path.getmtime(cur["path"]):
            seqs[name] = dict(name=name, source=base, path=f, steps=steps,
                              notes=["файл анимации отличается от %s и новее — в модель взят файл; "
                                     "записать в репозиторий: ea_export" % cur["source"]])
        else:
            cur["notes"].append("файл анимации %s отличается и старее — взят %s; пересоздать файл: ea_build"
                                % (base, cur["source"]))
    return [seqs[k] for k in sorted(seqs)]


# ───────────────────────── проверки на модели ─────────────────────────
def _bb(shape):
    b = shape.BoundBox
    return (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)


def _shift(bb, d):
    return (bb[0] + d[0], bb[1] + d[1], bb[2] + d[2], bb[3] + d[0], bb[4] + d[1], bb[5] + d[2])


def _overlap(a, b, m):
    """Габариты пересекаются с запасом m по каждой оси (m < 0 — «глубже, чем на |m|»)."""
    return (a[0] < b[3] + m and b[0] < a[3] + m and a[1] < b[4] + m and b[1] < a[4] + m and
            a[2] < b[5] + m and b[2] < a[5] + m)


def _moved(shape, d):
    s = shape.copy()
    s.translate(App.Vector(d[0], d[1], d[2]))
    return s


def _common(a, b):
    try:
        c = a.common(b)
        return 0.0 if c.isNull() else float(c.Volume)
    except Exception:
        return None


def _world(doc):
    """Твёрдые тела модели: имя → dict(shape, bb, shell)."""
    world = {}
    for o in doc.Objects:
        if not o.isDerivedFrom("Part::Feature") or o.Name.endswith(SKIP_SUFFIX):
            continue
        chain, g = [], o.getParentGroup()
        while g is not None:
            chain.append(g.Name)
            g = g.getParentGroup()
        if any(n in SKIP_GROUPS for n in chain) or o.Name.startswith("trajectory_line"):
            continue
        sh = o.Shape
        if sh.isNull() or not sh.Solids:
            continue
        world[o.Name] = dict(shape=sh, bb=_bb(sh), shell=any(n in SHELL_GROUPS for n in chain))
    return world


def _free_travel(shape, disp, world, skip, deadline):
    """Насколько деталь проходит по вектору disp (полный ход), пока не врежется. → (доля 0..1, имя препятствия)."""
    bb0 = _bb(shape)
    length = (disp[0] ** 2 + disp[1] ** 2 + disp[2] ** 2) ** 0.5
    if length < 1e-6:
        return 1.0, None, 0
    ext = (abs(disp[0]) * (bb0[3] - bb0[0]) + abs(disp[1]) * (bb0[4] - bb0[1]) + abs(disp[2]) * (bb0[5] - bb0[2])) / length
    step = min(25.0, max(5.0, ext / 2.0))
    base, unknown = {}, set()

    def hit(f):
        d = (disp[0] * f, disp[1] * f, disp[2] * f)
        bb, mv = _shift(bb0, d), None
        for name, ob in world.items():
            if name in skip or not _overlap(bb, ob["bb"], -0.2):
                continue
            if name not in base:
                v0 = _common(shape, ob["shape"]) if _overlap(bb0, ob["bb"], -0.2) else 0.0
                base[name] = v0
            if base[name] is None:
                unknown.add(name)
                continue
            if mv is None:
                mv = _moved(shape, d)
            v = _common(mv, ob["shape"])
            if v is None:
                unknown.add(name)
            elif v > base[name] + TOL_V:
                return name
        return None

    n = max(1, int(length / step + 0.999))
    prev = 0.0
    for i in range(1, n + 1):
        if time.time() > deadline:
            return None, None, len(unknown)
        f = min(1.0, i * step / length)
        ob = hit(f)
        if ob:
            lo, hi = prev, f
            for _ in range(7):
                mid = (lo + hi) / 2.0
                h = hit(mid)
                if h:
                    hi, ob = mid, h
                else:
                    lo = mid
            return lo, ob, len(unknown)
        prev = f
    return 1.0, None, len(unknown)


def _pose(shape, disp, rot):
    """f (0..1) → деталь в доле f хода: поворот rot = (центр, ось, градусы) · f вокруг неподвижной оси, затем сдвиг
    disp · f — как в ExplodedAssembly (Bolt Group: центр вращения не едет; сдвиг у болта идёт вдоль оси)."""
    def pose(f):
        s = shape.copy()
        if rot is not None and abs(rot[2]) > 1e-9:
            s.rotate(App.Vector(*rot[0]), App.Vector(*rot[1]), rot[2] * f)
        if any(abs(c) > 1e-12 for c in disp):
            s.translate(App.Vector(disp[0] * f, disp[1] * f, disp[2] * f))
        return s
    return pose


def _free_sweep(shape, pose, rot, disp, world, skip, deadline):
    """Как _free_travel, но для поворота (Bolt Group): деталь проходит дугу по кадрам — не больше ~20 мм на самом
    дальнем от оси углу за кадр. → (доля 0..1, имя препятствия, число неопределённых)."""
    import math
    bb0 = _bb(shape)
    c, a = rot[0], rot[1]
    an = (a[0] ** 2 + a[1] ** 2 + a[2] ** 2) ** 0.5 or 1.0
    a = (a[0] / an, a[1] / an, a[2] / an)
    rmax = 0.0
    for x in (bb0[0], bb0[3]):
        for y in (bb0[1], bb0[4]):
            for z in (bb0[2], bb0[5]):
                v = (x - c[0], y - c[1], z - c[2])
                t = v[0] * a[0] + v[1] * a[1] + v[2] * a[2]
                rmax = max(rmax, (max(0.0, v[0] ** 2 + v[1] ** 2 + v[2] ** 2 - t * t)) ** 0.5)
    arc = rmax * math.radians(abs(rot[2])) + (disp[0] ** 2 + disp[1] ** 2 + disp[2] ** 2) ** 0.5
    n = max(1, int(math.ceil(max(abs(rot[2]) / 3.0, arc / 20.0))))
    base, unknown = {}, set()

    def hit(f):
        mv = pose(f)
        bb = _bb(mv)
        for name, ob in world.items():
            if name in skip or not _overlap(bb, ob["bb"], -0.2):
                continue
            if name not in base:
                base[name] = _common(shape, ob["shape"]) if _overlap(bb0, ob["bb"], -0.2) else 0.0
            if base[name] is None:
                unknown.add(name)
                continue
            v = _common(mv, ob["shape"])
            if v is None:
                unknown.add(name)
            elif v > base[name] + TOL_V:
                return name
        return None

    prev = 0.0
    for i in range(1, n + 1):
        if time.time() > deadline:
            return None, None, len(unknown)
        f = float(i) / n
        ob = hit(f)
        if ob:
            lo, hi = prev, f
            for _ in range(7):
                mid = (lo + hi) / 2.0
                h = hit(mid)
                if h:
                    hi, ob = mid, h
                else:
                    lo = mid
            return lo, ob, len(unknown)
        prev = f
    return 1.0, None, len(unknown)


def _nearest(start, shape, world, skip):
    """Ближайшее к shape (деталь в конце хода) тело — из тех, к которым она ПРИБЛИЗИЛАСЬ (в начале, start, была дальше).
    → (имя, мм) или None, если ближе NEAR ничего нет."""
    bb, bb0, best = _bb(shape), _bb(start), None
    for name, ob in world.items():
        if name in skip or not _overlap(bb, ob["bb"], NEAR):
            continue
        try:
            d = float(shape.distToShape(ob["shape"])[0])
            if d >= NEAR or (best is not None and d >= best[1]):
                continue
            if _overlap(bb0, ob["bb"], d + 0.5) and float(start.distToShape(ob["shape"])[0]) <= d + 0.5:
                continue                                  # не приблизились: сосед был так же близко и до хода (опора, пол)
        except Exception:
            continue
        best = (name, d)
    return best


def direction_text(vec):
    ax = max(range(3), key=lambda i: abs(vec[i]))
    if abs(vec[ax]) < 1e-9:
        return "на месте"
    off = sum(abs(vec[i]) for i in range(3) if i != ax)
    word = AXIS_WORDS[(ax, 1 if vec[ax] > 0 else -1)]
    return word if off < 1e-6 * abs(vec[ax]) else "%s (наклонно: %.2f, %.2f, %.2f)" % ((word,) + tuple(vec))


def check_sequence(doc, seq, deadline):
    """Проверить одну анимацию на модели. → список шагов с результатами по каждой детали."""
    world = _world(doc)
    out = []
    for st in seq["steps"]:
        parts, res = [p for p in st["parts"]], []
        moving = set(p["name"] for p in parts)
        deg = float(st.get("revolutions") or 0.0) * 360.0
        for p in parts:
            disp = tuple(c * st["distance"] for c in p["vec"])
            rot = (p.get("rot_center", (0.0, 0.0, 0.0)), p.get("rot_axis", p["vec"]), deg) if abs(deg) > 1e-9 else None
            r = dict(name=p["name"], vec=p["vec"], travel=st["distance"] * (sum(c * c for c in p["vec"]) ** 0.5), unit=" мм")
            if rot is not None:
                r.update(travel=abs(deg), unit="°")         # поворот: ход и свободный ход — в градусах
            if doc.getObject(p["name"]) is None:
                r["status"] = "missing"
            elif p["name"] not in world:
                r["status"] = "nosolid"
            else:
                sh0 = world[p["name"]]["shape"]
                if rot is None:
                    f, ob, unk = _free_travel(sh0, disp, world, moving, deadline)
                    end = lambda: _moved(sh0, disp)
                else:
                    pose = _pose(sh0, disp, rot)
                    f, ob, unk = _free_sweep(sh0, pose, rot, disp, world, moving, deadline)
                    end = lambda: pose(1.0)
                r["unknown"] = unk
                if f is None:
                    r["status"] = "timeout"
                elif ob is None:
                    r["status"] = "free"
                    near = _nearest(sh0, end(), world, moving) if time.time() < deadline else None
                    if near:
                        r["near"] = near
                else:
                    r.update(status="shell" if world[ob]["shell"] else "blocked", free=f * r["travel"], obstacle=ob)
            res.append(r)
        for p in parts:                                   # после шага детали остаются в конце хода — как в анимации
            if p["name"] in world:
                disp = tuple(c * st["distance"] for c in p["vec"])
                w = world[p["name"]]
                if abs(deg) > 1e-9:
                    sh = _pose(w["shape"], disp, (p.get("rot_center", (0.0, 0.0, 0.0)), p.get("rot_axis", p["vec"]), deg))(1.0)
                    world[p["name"]] = dict(shape=sh, bb=_bb(sh), shell=w["shell"])
                else:
                    world[p["name"]] = dict(shape=_moved(w["shape"], disp), bb=_shift(w["bb"], disp), shell=w["shell"])
        out.append(dict(label=st["label"], kind=st["kind"], distance=st["distance"], revolutions=st["revolutions"],
                        parts=res))
    return out


# ───────────────────────── отчёт ─────────────────────────
def _lab(doc, name):
    o = doc.getObject(name)
    return "«%s» (%s)" % (o.Label, name) if o is not None and o.Label != name else name


def report_lines(doc, results):
    L = ["[Анимации → модель]  ходы и порядок — из анимаций; проверка: деталь проходит свой ход, не задевая то, что ещё стоит"]
    tot = dict(steps=0, free=0, blocked=0, shell=0, other=0)
    if not results:
        L.append("  анимаций нет (animation/sequences/*.py, файлы *_anim_*.FCStd рядом с моделью)")
    for seq, steps in results:
        n_parts = sum(len(s["parts"]) for s in steps)
        L.append("  %s — %s: шагов %d, деталей %d" % (seq["name"], seq["source"], len(steps), n_parts))
        for note in seq["notes"]:
            L.append("    ! %s" % note)
        if steps:
            L.append("    порядок сборки (обратный разборке): " +
                     " → ".join(re.sub(r"^\d+[.)]?\s+", "", s["label"]) for s in reversed(steps)))
        for i, s in enumerate(steps, 1):
            tot["steps"] += 1
            vecs = set(tuple(round(c, 4) for c in p["vec"]) for p in s["parts"])
            if s["revolutions"] and abs(s["distance"]) < 1e-9:
                head = "    ▶ %d «%s» — поворот %+.0f°" % (i, s["label"], s["revolutions"] * 360.0)
            else:
                head = "    ▶ %d «%s» — %s %.0f мм" % (i, s["label"], direction_text(s["parts"][0]["vec"]) if len(vecs) == 1
                                                       else "детали в разные стороны,", s["distance"])
                if s["revolutions"]:
                    head += " + поворот %+.0f°" % (s["revolutions"] * 360.0)
            bad = [p for p in s["parts"] if p["status"] != "free"]
            if not bad:
                tot["free"] += 1
                near = [p for p in s["parts"] if p.get("near")]
                tail = ""
                if near:
                    p = min(near, key=lambda q: q["near"][1])
                    tail = "; в конце хода ближе всего: %.0f мм — %s ↔ %s" % (p["near"][1], _lab(doc, p["name"]), _lab(doc, p["near"][0]))
                L.append("%s: свободно (%d дет.)%s" % (head, len(s["parts"]), tail))
                continue
            kinds = set(p["status"] for p in bad)
            tot["blocked" if "blocked" in kinds else "shell" if kinds == {"shell"} else "other"] += 1
            L.append(head + ":")
            for p in s["parts"]:
                nm = _lab(doc, p["name"])
                if p["status"] == "blocked" and p["free"] < 1.0:
                    L.append("        ⚠ %s: в эту сторону не идёт — сразу упирается в %s" % (nm, _lab(doc, p["obstacle"])))
                elif p["status"] == "blocked":
                    L.append("        ⚠ %s: свободный ход %.0f%s из %.0f — дальше %s" % (
                        nm, p["free"], p.get("unit", " мм"), p["travel"], _lab(doc, p["obstacle"])))
                elif p["status"] == "shell" and p["free"] < 1.0:
                    L.append("        ⓘ %s: уже в исходном положении задевает кузов — %s" % (nm, _lab(doc, p["obstacle"])))
                elif p["status"] == "shell":
                    L.append("        ⓘ %s: через %.0f%s из %.0f выходит за кузов (%s)" % (
                        nm, p["free"], p.get("unit", " мм"), p["travel"], _lab(doc, p["obstacle"])))
                elif p["status"] == "missing":
                    L.append("        ⚠ %s: такой детали в модели нет" % p["name"])
                elif p["status"] == "nosolid":
                    L.append("        · %s: не твёрдое тело — не проверяется" % nm)
                elif p["status"] == "timeout":
                    L.append("        · %s: не проверено (вышло время, VAN_MOTION_BUDGET)" % nm)
            ok = [p for p in s["parts"] if p["status"] == "free"]
            if ok:
                L.append("        остальные свободно: %s" % ", ".join(p["name"] for p in ok))
    if results:
        L.append("  Итого: шагов %d — свободно %d, ⚠ упирается %d, ⓘ выходит за кузов %d%s" % (
            tot["steps"], tot["free"], tot["blocked"], tot["shell"],
            ", прочее %d" % tot["other"] if tot["other"] else ""))
    return L


def report(S):
    """Анимации → проверки на модели. Ошибка здесь сборку модели не останавливает."""
    doc = S.doc
    if os.environ.get("VAN_MOTION", "1") == "0":
        return
    try:
        deadline = time.time() + float(os.environ.get("VAN_MOTION_BUDGET", BUDGET))
        stem, skipped = model_stem(), []
        results = [(seq, check_sequence(doc, seq, deadline)) for seq in load_sequences(model=stem, skipped=skipped)]
        lines = report_lines(doc, results)
        lines.insert(1, "  модель: %s" % stem)
        if skipped:
            lines.insert(2, "  для других моделей (не проверяются): " + ", ".join(
                "%s (%s)" % (n, ", ".join(m)) for n, m in skipped))
        motion = dict((seq["name"], steps) for seq, steps in results)
    except Exception as e:
        lines = ["[Анимации → модель]  проверка не выполнена: %s: %s" % (type(e).__name__, e)]
        motion = {}
    print("\n".join(lines))
    docs = os.path.join(PROJECT_DIR, "docs")
    if os.path.isdir(docs) and os.path.isdir(os.path.join(PROJECT_DIR, "animation")):
        try:
            stem = model_stem()
            fname = "animation_report.md" if stem.startswith("van_v0") else "animation_report_%s.md" % stem
            with open(os.path.join(docs, fname), "w", encoding="utf-8") as f:
                f.write("# Анимации → модель %s (последняя сборка)\n\n" % stem +
                        "Пишется при каждой сборке модели (`vanmodel/motion.py`): ходы и порядок шагов берутся из анимаций\n"
                        "(`animation/sequences/*.py` и файлы `*_anim_*.FCStd` рядом с моделью) и проверяются на модели.\n"
                        "⚠ — деталь упирается в другую деталь; ⓘ — выходит за кузов (приём «прилёт из-за кадра»).\n\n"
                        "```\n" + "\n".join(lines) + "\n```\n")
        except OSError:
            pass

    S.put(locals(), "motion")
