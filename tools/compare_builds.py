# -*- coding: utf-8 -*-
"""Изменилась ли модель? Собирает модель из двух версий кода и сравнивает деталь в деталь.

    python3 tools/compare_builds.py              # рабочая папка ↔ последний коммит (HEAD)
    python3 tools/compare_builds.py 96b8666      # рабочая папка ↔ указанный коммит

Для каждой версии — отдельный запуск FreeCAD (сборка van_v0.py в консольном режиме); сравниваются все объекты
(имя, тип, подпись, группа, габариты, объём, площадь, число граней/рёбер) и текст сводки. Готовые .FCStd в
репозитории НЕ трогаются: модель сохраняется во временную папку.

Зачем: после правки кода, которая НЕ должна менять геометрию (переименование, перестановка, разделение на модули),
ответ должен быть «модели совпадают»; после правки размеров — видно, какие именно детали изменились.

Чем запускать FreeCAD — переменная FREECADCMD (как в tools/make_docs.sh), например:
    FREECADCMD="$HOME/Applications/FreeCAD.AppImage --console" python3 tools/compare_builds.py
Если её нет: тот же python3, которым запущен скрипт (если в нём есть модуль FreeCAD), иначе freecadcmd.
"""
import json
import os
import shlex
import subprocess
import sys
import tempfile

TOL = 1e-6          # мм / мм² / мм³ — допуск сравнения чисел


def _repo_dir():
    if os.environ.get("VAN_REPO"):
        return os.environ["VAN_REPO"]
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.dirname(os.path.abspath(f)))
    return os.path.expanduser("~/van-build")


# ══════════════ режим «снимок»: выполняется ВНУТРИ FreeCAD (его запускает основной режим) ══════════════
def snapshot_mode(out_path):
    import contextlib
    import io
    import traceback
    res, rc = {}, 0
    try:
        script = os.path.join(_repo_dir(), "van_v0.py")
        g = {"__file__": script, "__name__": "__main__"}
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(open(script, encoding="utf-8").read(), script, "exec"), g)
        finally:
            res["output"] = buf.getvalue()
        import FreeCAD as App
        doc = App.ActiveDocument
        objs = []
        for o in doc.Objects:
            grp = o.getParentGroup()
            e = {"Name": o.Name, "TypeId": o.TypeId, "Label": o.Label, "Label2": getattr(o, "Label2", ""),
                 "Group": grp.Name if grp is not None else None}
            sh = getattr(o, "Shape", None)
            if o.isDerivedFrom("Part::Feature") and sh is not None:
                if sh.isNull():
                    e["null"] = True
                else:
                    b = sh.BoundBox
                    e["bbox"] = [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]
                    e["volume"], e["area"] = sh.Volume, sh.Area
                    e["faces"], e["edges"] = len(sh.Faces), len(sh.Edges)
            objs.append(e)
        res["objects"] = objs
        res["doc_label"] = doc.Label
    except Exception:
        res["error"] = traceback.format_exc()
        rc = 1
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    sys.stdout.flush()
    os._exit(rc)        # как в остальных tools/: без «тихого» падения FreeCAD при закрытии документа с мешем


if os.environ.get("VAN_SNAPSHOT_OUT"):
    snapshot_mode(os.environ["VAN_SNAPSHOT_OUT"])


# ══════════════ основной режим: обычный python3 ══════════════
def freecad_cmd():
    if os.environ.get("FREECADCMD"):
        return shlex.split(os.environ["FREECADCMD"])
    try:
        import FreeCAD  # noqa: F401
        return [sys.executable]
    except Exception:
        return ["freecadcmd"]


def build_snapshot(tree, label, tmp):
    out = os.path.join(tmp, label + ".json")
    save_dir = os.path.join(tmp, "save_" + label)        # имя файла одинаковое: FreeCAD берёт из него подпись документа
    os.makedirs(save_dir)
    env = dict(os.environ, VAN_REPO=tree, VAN_SNAPSHOT_OUT=out, VAN_SAVE_PATH=os.path.join(save_dir, "van_v0.FCStd"),
               PYTHONIOENCODING="utf-8")
    print("  сборка: %s …" % label)
    sys.stdout.flush()
    p = subprocess.run(freecad_cmd() + [os.path.abspath(__file__)], env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    if not os.path.exists(out):
        print(p.stdout.decode("utf-8", "replace")[-3000:])
        sys.exit("compare_builds: сборка «%s» не дала результата (команда: %s)" % (label, " ".join(freecad_cmd())))
    with open(out, encoding="utf-8") as f:
        res = json.load(f)
    if res.get("error"):
        print(res.get("output", "")[-1500:])
        print(res["error"])
        sys.exit("compare_builds: сборка «%s» завершилась ошибкой" % label)
    return res


def export_ref(repo, ref, tmp):
    """Код модели из коммита ref — во временную папку (van_v0.py + vanmodel/, если он там есть)."""
    tree = os.path.join(tmp, "ref")
    os.makedirs(tree)
    names = ["van_v0.py"]
    for extra in ("vanmodel", "animation/sequences"):
        if subprocess.run(["git", "-C", repo, "cat-file", "-e", ref + ":" + extra], stderr=subprocess.DEVNULL).returncode == 0:
            names.append(extra)
    ar = subprocess.run(["git", "-C", repo, "archive", ref] + names, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ar.returncode != 0:
        sys.exit("compare_builds: нет такого коммита или в нём нет van_v0.py: %s\n%s" % (
            ref, ar.stderr.decode("utf-8", "replace")))
    import io
    import tarfile
    tf = tarfile.open(fileobj=io.BytesIO(ar.stdout))
    try:
        tf.extractall(tree, filter="data")
    except TypeError:                                            # Python < 3.12 без параметра filter
        tf.extractall(tree)
    stl = "Ducato_L2H2_body_reference.stl"                       # скан — один и тот же, берём из рабочей папки
    try:
        os.symlink(os.path.join(repo, stl), os.path.join(tree, stl))
    except OSError:
        import shutil
        shutil.copy(os.path.join(repo, stl), os.path.join(tree, stl))
    return tree


def differs(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(a - b) > TOL * max(1.0, abs(a), abs(b))
        except TypeError:
            return True
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return any(differs(x, y) for x, y in zip(a, b))
    return a != b


def main():
    repo = _repo_dir()
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    print("compare_builds: рабочая папка %s ↔ коммит %s" % (repo, ref))
    with tempfile.TemporaryDirectory(prefix="van_compare_") as tmp:
        old = build_snapshot(export_ref(repo, ref, tmp), "коммит " + ref, tmp)
        new = build_snapshot(repo, "рабочая папка", tmp)
    oa = {o["Name"]: o for o in old["objects"]}
    ob = {o["Name"]: o for o in new["objects"]}
    n_diff = 0
    gone, added = [n for n in oa if n not in ob], [n for n in ob if n not in oa]
    if gone:
        n_diff += len(gone)
        print("Исчезли (%d): %s" % (len(gone), ", ".join(gone[:30]) + (" …" if len(gone) > 30 else "")))
    if added:
        n_diff += len(added)
        print("Появились (%d): %s" % (len(added), ", ".join(added[:30]) + (" …" if len(added) > 30 else "")))
    if not gone and not added and list(oa) != list(ob):
        n_diff += 1
        print("Порядок объектов в дереве изменился")
    changed = 0
    for n, a in oa.items():
        b = ob.get(n)
        if b is None:
            continue
        keys = [k for k in sorted(set(a) | set(b)) if differs(a.get(k), b.get(k))]
        if not keys:
            continue
        changed += 1
        if changed <= 40:
            parts = []
            for k in keys:
                if k == "bbox" and a.get(k) and b.get(k):
                    d = [y - x for x, y in zip(a[k], b[k])]
                    parts.append("габариты: ΔX %+.3f…%+.3f, ΔY %+.3f…%+.3f, ΔZ %+.3f…%+.3f мм" % tuple(d))
                elif k in ("volume", "area") and a.get(k) is not None and b.get(k) is not None:
                    parts.append("%s %.6g → %.6g" % ({"volume": "объём", "area": "площадь"}[k], a[k], b[k]))
                else:
                    parts.append("%s: %r → %r" % (k, a.get(k), b.get(k)))
            print("Изменён %s — %s" % (n, "; ".join(parts)))
    if changed > 40:
        print("… и ещё %d изменённых объектов" % (changed - 40))
    n_diff += changed

    def clean(t):                       # путь сохранения у двух сборок разный по построению
        return [l for l in t.split("\n") if "Сохранён:" not in l]
    la, lb = clean(old.get("output", "")), clean(new.get("output", ""))
    if la != lb:
        import difflib
        d = [l for l in difflib.unified_diff(la, lb, "коммит " + ref, "рабочая папка", lineterm="", n=0)
             if not l.startswith("@@")]
        n_diff += 1
        print("Сводка отличается:")
        for l in d[:60]:
            print("   ", l)
    if old.get("doc_label") != new.get("doc_label"):
        n_diff += 1
        print("Подпись документа: %r → %r" % (old.get("doc_label"), new.get("doc_label")))
    n_shape = sum(1 for o in new["objects"] if "bbox" in o)
    print("-" * 70)
    if n_diff:
        print("РАЗЛИЧИЯ ЕСТЬ: объектов %d ↔ %d, изменённых %d" % (len(oa), len(ob), changed))
        sys.exit(1)
    print("МОДЕЛИ СОВПАДАЮТ: %d объектов (из них с геометрией %d), %d строк сводки — без отличий" % (
        len(ob), n_shape, len(lb)))


if __name__ == "__main__":
    main()
