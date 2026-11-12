# -*- coding: utf-8 -*-
"""3D-скан кузова: чтение STL, усреднённый профиль борта, меш-обшивка."""

import os
import struct

import FreeCAD as App
import Mesh

from .params import PARAMS
from .common import BODY_STL_PATH, COL_SKIN, SCAN_ALIGN, _style

try:
    import numpy as np
    _HAVE_NP = True
except Exception:
    _HAVE_NP = False

_SCAN_PTS = None   # кэш облака точек скана в СК модели


# ── чтение скана и снятие профиля ──
def _read_stl_points(path):
    """Бинарный STL → массив вершин Nx3 (numpy)."""
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    a = np.frombuffer(data[84:84 + 50 * n], dtype=np.uint8).reshape(n, 50)
    return a[:, 12:48].copy().view("<f4").reshape(n * 3, 3).astype(float)


def scan_points():
    global _SCAN_PTS
    if _SCAN_PTS is None:
        pts = _read_stl_points(BODY_STL_PATH)
        pts += np.array(SCAN_ALIGN)
        _SCAN_PTS = pts
    return _SCAN_PTS


def measured_half_profile(P):
    """Усреднённый полу-профиль борта по карго-зоне: список (y>=0, z), z по возрастанию.

    y — внутренняя поверхность борта (наруж. оболочка минус frame_clearance).
    Верх крыши делаем монотонным (убираем шум скана), завершаем точкой свода (0, крышаZ).
    """
    pp = PARAMS
    X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
    m = (X > pp["profile_x_lo"]) & (X < pp["profile_x_hi"]) & (Z > 15)
    y, z = np.abs(Y[m]), Z[m]
    dz = pp["profile_dz"]
    crown = pp["interior_height"] - 5.0
    hw_list, z_list = [], []
    for z0 in np.arange(0, crown, dz):
        b = (z >= z0 - dz / 2) & (z < z0 + dz / 2)
        if b.sum() < 5:
            continue
        hw_list.append(float(np.percentile(y[b], 93)) - pp["frame_clearance"])
        z_list.append(float(z0))
    if len(hw_list) < 6:
        raise RuntimeError("слишком мало точек скана для профиля")
    hw = np.array(hw_list)
    zz = np.array(z_list)
    # сглаживание полуширины (убираем шум скана), скользящее среднее окно 5,
    # концы сохраняем, чтобы не «утянуть» пол и плечо
    k = 5
    sm = np.convolve(hw, np.ones(k) / k, mode="same")
    sm[:2] = hw[:2]
    sm[-2:] = hw[-2:]
    # монотонность крыши: выше плеча полуширина не растёт с высотой
    shoulder = 1400.0
    for i in range(1, len(sm)):
        if zz[i] >= shoulder and sm[i] > sm[i - 1]:
            sm[i] = sm[i - 1]
    prof = [(max(float(w), 0.0), float(zv)) for w, zv in zip(sm, zz)]
    prof.append((0.0, crown))
    return prof


def full_hoop(half):
    """Полный обруч (борт+крыша) из полу-профиля: борт +Y (левый, водитель)→свод→борт −Y (правый, пассажир).
    Открыт снизу (U), пол не пересекает. Возвращает список (y, z)."""
    right = list(half)                       # (y, z) от пола до свода, y>=0
    left = [(-y, z) for (y, z) in reversed(right[:-1])]  # свод-1 … пол, y<=0
    return right + left


def y_at_z(half, z_query):
    """Линейная интерполяция полуширины борта на высоте z."""
    pts = sorted(half, key=lambda p: p[1])
    if z_query <= pts[0][1]:
        return pts[0][0]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z0 <= z_query <= z1:
            t = (z_query - z0) / (z1 - z0) if z1 > z0 else 0.0
            return y0 + (y1 - y0) * t
    return pts[-1][0]


def add_mesh_skin(doc, group):
    if not os.path.exists(BODY_STL_PATH):
        print("! STL обшивки не найден:", BODY_STL_PATH)
        return None
    mesh = Mesh.Mesh(BODY_STL_PATH)
    o = doc.addObject("Mesh::Feature", "Scan_Skin_Body")
    o.Mesh = mesh
    o.Placement.Base = App.Vector(*SCAN_ALIGN)
    o.Label = "Обшивка — 3D-скан кузова (выровнен на каркас)"
    _style(o, COL_SKIN, 60)
    group.addObject(o)
    return o
