# -*- coding: utf-8 -*-
"""Headless-сборка van_v0.py (без GUI, без цветов в .FCStd).

    ~/Applications/FreeCAD.AppImage --console ~/van-build/tools/build_headless.py

То же, что `--console van_v0.py`, но выходит через os._exit: FreeCAD 1.1.3
(conda-forge) падает с SIGSEGV, закрывая документ с Mesh, и при этом теряет
буферизованный вывод сводки. Для коммита .FCStd с цветами — tools/render_views.py.
"""
import os
import sys
import traceback


def _repo_dir():
    if os.environ.get("VAN_REPO"):
        return os.environ["VAN_REPO"]
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.dirname(os.path.abspath(f)))
    return os.path.expanduser("~/van-build")


SCRIPT = os.path.join(_repo_dir(), os.environ.get("VAN_ENTRY") or "van_v0.py")   # VAN_ENTRY=van_v1_rect_pan.py — вариант
rc = 0
try:
    g = {"__file__": SCRIPT, "__name__": "__main__"}
    exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), g)
except Exception:
    traceback.print_exc()
    rc = 1
finally:
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(rc)
