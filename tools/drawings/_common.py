"""Общее для чертежей: данные модели (docs/drawing_data.json), дюймы, форма арки."""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = os.path.join(REPO, "docs")
IN = 25.4


def load():
    path = os.path.join(DOCS, "drawing_data.json")
    if not os.path.exists(path):
        raise SystemExit("нет %s — сначала: freecadcmd tools/export_drawing_data.py" % path)
    d = json.load(open(path, encoding="utf-8"))
    if d.get("error"):
        raise SystemExit("ошибка экспорта:\n" + d["error"])
    return d


def arch_profile(d, which="wall", n_pts=120):
    """Контур арки сбоку в мм (X, Z от железного пола): which = 'wall' (у стены) или 'inner'
    (внутренняя грань, ниже на скругление верхней кромки). Как в van_v0.py: суперэллипс."""
    W = d["WHEEL_ARCH"]
    ff = d["geo"]["floor_top"]
    b_top = ff + W["height"]
    n = float(W.get("profile_n", 2.0))
    if which == "wall":
        a, b = W["len_x_wall"] / 2.0, b_top
    else:      # у внутренней грани углы в плане скруглены plan_round → короче на 2·R
        a, b = W["len_x"] / 2.0 - float(W.get("plan_round", 0.0)), b_top - float(W.get("top_round", 0.0))
    pts = []
    for i in range(n_pts + 1):
        t = math.pi * i / n_pts
        c, s = math.cos(t), math.sin(t)
        pts.append((W["center_x"] + a * math.copysign(abs(c) ** (2.0 / n), c), b * abs(s) ** (2.0 / n)))
    return pts


def box(d, name):
    return d["boxes"][name]


def save(fig, name):
    out = os.path.join(DOCS, name)
    fig.savefig(out, facecolor="white")
    print(out)
    return out
