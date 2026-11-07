# -*- coding: utf-8 -*-
"""Собрать вариант модели в FreeCAD GUI (с цветами) и сохранить в ОТДЕЛЬНЫЙ .FCStd — чтобы открыть варианты
одновременно и сравнить (у каждого — своя вкладка и подпись «van_v0 — бак …» в дереве).

    VAN_WATER_VARIANT=T3500_shelf VAN_SAVE_PATH=van_v0_T3500.FCStd xvfb-run -a freecad tools/save_variant.py
    # на M6800: VAN_WATER_VARIANT=T4100_floor VAN_SAVE_PATH=~/van-build/van_v0_T4100.FCStd \\
    #           ~/Applications/FreeCAD.AppImage ~/van-build/tools/save_variant.py

Варианты бака — WATER_VARIANT в van_v0.py: T4100_floor, T3500_shelf, TORVA. Все варианты сразу — tools/make_docs.sh
(в конце собирает van_v0_T4100.FCStd и van_v0_T3500.FCStd). Выход через os._exit (не трогать user.cfg FreeCAD).
"""
import os
import traceback

import FreeCAD as App


def _repo_dir():
    if os.environ.get("VAN_REPO"):
        return os.environ["VAN_REPO"]
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.dirname(os.path.abspath(f)))
    return os.path.expanduser("~/van-build")


SCRIPT = os.path.join(_repo_dir(), "van_v0.py")
rc = 0
try:
    g = {"__file__": SCRIPT, "__name__": "__main__"}
    exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), g)
    print("save_variant: %s → %s" % (g.get("WATER_VARIANT"), g.get("SAVE_PATH")))
except Exception:
    traceback.print_exc()
    rc = 1
os._exit(rc)
