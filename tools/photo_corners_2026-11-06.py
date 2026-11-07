"""Задние углы (арка ↔ D-стойка) по 4 фото сверху с рулеткой, 2026-11-06.

Пиксельные точки сняты вручную по увеличенным кадрам (сетка 20 px). Фото почти строго сверху:
масштаб на полу изотропный (проверено пластиной под стойкой кровати Simpson TP35 3-1/8×5″ и тем,
что рулетка пересекает её короткую сторону под нужным углом). Масштаб — по делениям рулетки
(двузначные числа читались на ~6 px позже — учтено).

Координаты пола: X — вперёд от передней грани короба D-стойки у стены, Y — от стены в салон
(стена = край фанеры у борта), дюймы.
    python3 tools/photo_corners_2026-11-06.py     → таблица + docs/rear_corners_points.json
"""
import json
import math
import os

PHOTOS = {
    # сторона, масштаб px/дюйм (рулетка), стена: ось и её положение в px, угол D-стойки у стены (px),
    # направление «вперёд» в кадре, точки
    "p1": dict(side="пассажир", scale=42.2, wall=("x", 625.0), origin=(625.0, 805.0), fwd=(0, -1), inb=(-1, 0),
               tape=dict(hook=(607.0, 805.0), dir=(-0.538, -0.843), read_at=None),
               dpillar=[(590, 805), (500, 825), (412, 845)], dp_inboard=[(400, 900), (380, 1000)],
               arch=[(620, 358), (600, 348), (550, 335), (500, 325), (450, 312), (400, 302), (350, 290),
                     (300, 275), (275, 262), (260, 245), (250, 225), (245, 200)],
               plate=[(420.7, 602.7), (631.7, 602.7), (631.7, 733.3), (420.7, 733.3)],
               post_center_y=668.0),
    "p2": dict(side="пассажир", scale=39.6, wall=("x", 595.0), origin=(595.0, 800.0), fwd=(0, -1), inb=(-1, 0),
               tape=dict(hook=(589.5, 385.0), read_corner=12.6),
               dpillar=[(580, 800), (500, 815), (420, 830), (385, 838)],
               arch=[(590, 380), (550, 365), (500, 350), (450, 337.5), (400, 322.5), (350, 302.5), (310, 280),
                     (280, 260), (260, 240), (250, 210), (247.5, 180)],
               plate=[(400, 612), (595, 612), (595, 733), (395, 733)],
               post_center_y=672.5),
    "p3": dict(side="водитель", scale=34.0, wall=("x", 618.0), origin=(618.0, 505.0), fwd=(0, 1), inb=(-1, 0),
               tape=dict(hook=(621.2, 860.8), read_corner=12.88),
               dpillar=[(610, 505), (560, 497.5), (510, 490), (470, 482.5), (435, 475), (430, 473)],
               dp_inboard=[(415, 440), (400, 400)],
               arch=[(610, 867.5), (550, 882.5), (500, 897.5), (450, 912.5), (400, 932.5), (375, 942.5),
                     (355, 955), (342.5, 970), (335, 990), (330, 1020), (327.5, 1070), (325, 1120)],
               plate=[(443, 582.5), (618, 582.5), (618, 695), (443, 695)],
               post_center_y=638.8),
    "p4": dict(side="водитель", scale=35.5, wall=("y", 579.0), origin=(765.0, 579.0), fwd=(-1, 0), inb=(0, -1),
               tape=dict(hook=(754.0, 577.0), read_corner=15.86),
               dpillar=[(765, 570), (780, 500), (795, 435), (800, 405)], dp_inboard=[(850, 400), (900, 398)],
               arch=[(395, 575), (380, 530), (365, 480), (345, 430), (330, 390), (320, 350), (305, 320),
                     (290, 295), (275, 280), (255, 272.5), (230, 270), (180, 270)],
               plate=[(567.5, 410), (680, 410), (680, 579), (567.5, 579)],
               post_center_x=623.8),
}


def to_floor(ph, p):
    """px → (X вперёд, Y от стены), дюймы."""
    ox, oy = ph["origin"]
    dx, dy = p[0] - ox, p[1] - oy
    fx, fy = ph["fwd"]
    ix, iy = ph["inb"]
    X = (dx * fx + dy * fy) / ph["scale"]
    Y = (dx * ix + dy * iy) / ph["scale"]
    if ph["wall"][0] == "x":                       # стена — вертикальная линия x=const
        Y = (ph["wall"][1] - p[0]) * (-ix) / ph["scale"] if ix else Y
    return X, Y


def arch_at(pts, Y):
    """X задней грани арки на расстоянии Y от стены (линейная интерполяция по точкам)."""
    pts = sorted(pts, key=lambda q: q[1])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 <= Y <= y1 and y1 > y0:
            return x0 + (x1 - x0) * (Y - y0) / (y1 - y0)
    return None


def main():
    out = {}
    print("%-4s %-9s %8s %8s %8s %8s %8s %8s" % ("фото", "борт", "у стены", "Y=1.1″", "Y=2.4″", "Y=5″",
                                                  "выступ", "глуб.D"))
    for k, ph in PHOTOS.items():
        arch = [to_floor(ph, p) for p in ph["arch"]]
        dp = [to_floor(ph, p) for p in ph["dpillar"]]
        dp_face = dp
        dpi = [to_floor(ph, p) for p in ph.get("dp_inboard", [])]
        dp_depth = max(q[1] for q in dp_face)
        res = dict(side=ph["side"], arch=arch, dpillar=dp, dp_inboard=dpi,
                   plate=[to_floor(ph, p) for p in ph["plate"]])

        def gap(Y):
            a = arch_at(arch, Y)
            d = arch_at(dp_face, min(Y, dp_depth))
            return None if a is None or d is None else a - d
        prot = max(q[1] for q in arch)
        res.update(gap_wall=arch[0][0], gap_1_1=gap(1.1), gap_2_4=gap(2.4), gap_5=gap(5.0), protrusion=prot,
                   dp_depth=dp_depth)
        if "post_center_y" in ph:
            res["post_center_X"] = to_floor(ph, (ph["origin"][0], ph["post_center_y"]))[0]
        else:
            res["post_center_X"] = to_floor(ph, (ph["post_center_x"], ph["origin"][1]))[0]
        # наклон задней грани арки (Y 0..6″) и передней грани короба D-стойки
        a6 = [q for q in arch if q[1] <= 6.6]
        n = len(a6)
        my = sum(q[1] for q in a6) / n
        mx = sum(q[0] for q in a6) / n
        res["arch_slope"] = sum((q[1] - my) * (q[0] - mx) for q in a6) / sum((q[1] - my) ** 2 for q in a6)
        res["arch_X0"] = mx - res["arch_slope"] * my
        res["dp_slope"] = (dp_face[-1][0] - dp_face[0][0]) / (dp_face[-1][1] - dp_face[0][1])
        # проверка рулеткой: от крючка до противоположного угла
        hk = to_floor(ph, ph["tape"]["hook"])
        if ph["tape"].get("read_corner"):
            if k in ("p2", "p3"):
                c = max(dp_face, key=lambda q: q[1])               # внутренний угол короба D-стойки
            else:
                c = min(arch, key=lambda q: math.hypot(q[0] - hk[0], q[1] - hk[1]) if q[1] > 8 else 1e9)
            res["tape_check"] = (math.hypot(c[0] - hk[0], c[1] - hk[1]), ph["tape"]["read_corner"])
        out[k] = res
        print("%-4s %-9s %7.2f″ %7.2f″ %7.2f″ %7.2f″ %7.2f″ %7.2f″   наклон арки %.2f, D %.2f, стойка %.2f″%s" % (
            k, ph["side"], res["gap_wall"], res["gap_1_1"], res["gap_2_4"], res["gap_5"], prot, dp_depth,
            res["arch_slope"], res["dp_slope"], res["post_center_X"],
            ("  рулетка: расчёт %.2f″ / по делениям %.2f″" % res["tape_check"]) if "tape_check" in res else ""))
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "rear_corners_points.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(path)


main()
