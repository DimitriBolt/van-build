# -*- coding: utf-8 -*-
"""Багажник на крыше из профиля 2020 и солнечные панели (2026-11-20, Dimitri).

  • Опоры — 6 заводских штырей крыши (3 пары, Y = ±740): таблица Ram «2014 ProMaster Design Recommendations», L2H2
    (ANCHORS["roof_pins"]). На каждый штырь — кронштейн BSWAN (седло в углублении + Z-кронштейн, высота 58 мм).
  • Продольные рейки — 2 × 2020 друг на друге над линией штырей; палки 2440 мм, стык каждого яруса — в своём месте
    (нижний ярус — короткий кусок сзади, верхний — спереди), стык перекрыт целым соседним ярусом и 2 стяжными пластинами.
  • Поперечины 2020 — на рейках, ровно под отверстиями рам панелей (у каждой панели 2 поперечины); крепление поперечины
    к рейке — 2 литых уголка 2020 (по обе стороны поперечины, полка уголка — в верхнем пазу рейки).
  • Панели Rvpozwer 100W (1010.7 × 460 × 30) — 3 поперёк × 3 по длине, длинной стороной вдоль фургона; рама панели
    прикручена M5 через свои отверстия к T-гайке в верхнем пазу поперечины.
  • Дымоход нагревателя (Shower_FlueCap) — в разрыве между рядами панелей: ряды ставятся так, чтобы колпак был
    в ROOF_RACK["flue_clear"] от краёв панелей (если дымохода нет — ряды подряд от rear_limit).
Расчёт реек (неразрезная балка на 3 опорах), нагрузки на штыри, раскрой палок 2440 и спецификация крепежа — в сводке.
"""

import FreeCAD as App
import Part

from .anchors import ANCHORS
from .common import add_shape
from .params import ROOF_RACK
from .vslot import vslot_x, vslot_y

V = App.Vector
COL_ALU = (0.80, 0.81, 0.83)       # профиль 2020 (серебристый)
COL_STEEL = (0.62, 0.64, 0.68)     # нержавейка кронштейнов
COL_RUBBER = (0.08, 0.08, 0.08)
COL_PIN = (1.00, 0.85, 0.10)       # заводской штырь — жёлтый
COL_PANEL = (0.06, 0.09, 0.20)     # стекло/элементы панели
COL_PFRAME = (0.12, 0.12, 0.13)    # рама панели (чёрная анодированная)
COL_ZINC = (0.70, 0.72, 0.60)      # оцинкованные уголки/пластины


# ───────────── неразрезная балка (МКЭ, Эйлер–Бернулли): прогиб, моменты, реакции опор ─────────────
def _beam(xs_extra, supports, loads, EI, q):
    import numpy as np
    xs = np.array(sorted(set([round(x, 3) for x in list(xs_extra) + list(supports) + [x for x, _ in loads]])))
    n = len(xs)
    K = np.zeros((2 * n, 2 * n))
    F = np.zeros(2 * n)

    def ke(L):
        return EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                       [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
    for i in range(n - 1):
        L = xs[i + 1] - xs[i]
        idx = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
        K[np.ix_(idx, idx)] += ke(L)
        F[idx] += -q * L / 2.0 * np.array([1, L / 6.0, 1, -L / 6.0])
    ix = lambda x: int(np.argmin(abs(xs - x)))
    for x, P in loads:
        F[2 * ix(x)] += -P
    fixed = [2 * ix(s) for s in supports]
    free = [d for d in range(2 * n) if d not in fixed]
    u = np.zeros(2 * n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = K @ u - F
    m = 0.0
    for i in range(n - 1):
        L = xs[i + 1] - xs[i]
        idx = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
        fe = ke(L) @ u[idx] + q * L / 2.0 * np.array([1, L / 6.0, 1, -L / 6.0])
        m = max(m, abs(fe[1]), abs(fe[3]))
    return float(abs(u[0::2]).max()), m, [float(R[2 * ix(s)]) for s in supports]


def _pack(pieces, stock, kerf):
    """Раскрой: куски (имя, длина) по палкам stock (first-fit decreasing). → [[(имя, длина), …], …]"""
    sticks = []
    for name, L in sorted(pieces, key=lambda p: -p[1]):
        for s in sticks:
            used = sum(l for _, l in s) + kerf * len(s)
            if used + L <= stock + 1e-6:
                s.append((name, L))
                break
        else:
            sticks.append([(name, L)])
    return sticks


def roof_rack(S):
    """Багажник 2020 на 6 заводских штырях + 9 солнечных панелей (дымоход — в разрыве рядов)."""
    doc, half = S.doc, S.half
    R = ROOF_RACK
    roof_summary = None
    if not R.get("enable"):
        S.put(locals(), "roof_summary")
        return
    A = ANCHORS["roof_pins"]
    crown = half[-1][1]                                   # верх крыши (наружный) в СК модели
    z_pin = crown - A["z_pocket"]                         # дно углубления со штырём
    p1, p2, p3 = A["pitch"]
    if A.get("x_rear_pin") is not None:                   # промерено от порога — от него
        xr = float(A["x_rear_pin"])
        pins_x = [xr + p2 + p3, xr + p3, xr]
    else:
        xf = A["x_front_axle"]
        pins_x = [xf - p1, xf - p1 - p2, xf - p1 - p2 - p3]
    pins_x = sorted(pins_x)                               # сзади → вперёд
    yh = A["y_half"]
    MT = R["mount"]
    sx, sy, sz = MT["saddle"]
    t = MT["t"]
    z_m1 = z_pin + sz + MT["bracket_h"]                   # верх кронштейна = низ рейки
    nL = R["rail_layers"]
    z_r1 = z_m1 + 20.0 * nL                               # верх рейки
    low = R.get("cross_level", "top") == "lower"          # поперечины между нижними ярусами (2-я итерация)
    z_c0 = z_m1 if low else z_r1                          # низ поперечины
    z_c1 = z_c0 + 20.0                                    # верх поперечины = низ панели
    PN = R["panel"]
    PL, PW, PH = PN["L"], PN["W"], PN["H"]
    z_p1 = z_c1 + PH

    g = doc.addObject("App::DocumentObjectGroup", "RoofRack")
    g.Label = "Багажник на крыше 2020 + 9 солнечных панелей Rvpozwer 100W (проект 2026-11-20)"
    parts = {}

    def put(name, label, shape, color, tr=0):
        add_shape(doc, name, label, shape, color=color, transparency=tr, group=g)
        parts[name] = shape
        return shape

    # ── дымоход: где колпак ──
    cap = doc.getObject("Shower_FlueCap")
    flue = None
    if cap is not None:
        cb = cap.Shape.BoundBox
        flue = dict(x=(cb.XMin + cb.XMax) / 2.0, y=(cb.YMin + cb.YMax) / 2.0, r=(cb.XMax - cb.XMin) / 2.0,
                    z0=cb.ZMin, z1=cb.ZMax, bb=cb)

    # ── ряды панелей вдоль X ──
    nr, nc = R["rows"], R["cols"]
    gx, gy = R["gap_x"], R["gap_y"]
    em = R["end_margin"]
    rows = None
    gap_after = None
    FB = R.get("flue_board")
    if FB:                                                # дымоход — сквозь вставку на месте панели: ряды подряд
        rows = [R.get("x_start", R["rear_limit"] + em) + i * (PL + gx) for i in range(nr)]
    elif flue is not None:
        best = None
        for k in range(1, nr):                            # разрыв после k-го ряда (считая сзади)
            a = flue["x"] - flue["r"] - R["flue_clear"]   # конец k-го ряда
            b = flue["x"] + flue["r"] + R["flue_clear"]   # начало (k+1)-го
            s0 = a - k * PL - (k - 1) * gx
            st = [s0 + i * (PL + gx) for i in range(k)] + [b + i * (PL + gx) for i in range(nr - k)]
            x0, x1 = st[0] - em, st[-1] + PL + em
            if x0 < R["rear_limit"] or x1 > R["front_limit"]:
                continue
            over = max(pins_x[0] - x0, x1 - pins_x[-1])   # самый длинный свес за штыри
            if best is None or over < best[0]:
                best = (over, k, st)
        if best is not None:
            _, gap_after, rows = best
    if rows is None:                                      # без дымохода (или не влез) — подряд от заднего края
        rows = [R["rear_limit"] + em + i * (PL + gx) for i in range(nr)]
    x0, x1 = rows[0] - em, rows[-1] + PL + em
    field_w = nc * PW + (nc - 1) * gy
    cols = [-field_w / 2.0 + i * (PW + gy) for i in range(nc)]   # Y начала колонок

    # ── заводские штыри (маркер): ножка ⌀6.5, шляпка ⌀20 (форум: 0.255″ и 0.78″) ──
    for i, x in enumerate(pins_x):
        for side, ys in (("pY", 1), ("nY", -1)):
            pin = Part.makeCylinder(3.25, 3.2, V(x, ys * yh, z_pin)).fuse(Part.makeCylinder(10.0, 4.5, V(x, ys * yh, z_pin + 3.2)))
            put("RoofPin_%s_%d" % (side, i + 1),
                "Заводской штырь крыши %s #%d (X %.0f, Y %+.0f) — L2H2: от оси перед. колеса %s мм; ⌀ шляпки 0.78″, лимит 25 кг"
                % ({"pY": "водит.", "nY": "пасс."}[side], i + 1, x, ys * yh,
                   ("1392.8", "1392.8+1414.7", "1392.8+1414.7+1193.5")[2 - i]), pin, COL_PIN)

    # ── кронштейны BSWAN на штырях ──
    fw = MT["flange_w"]
    for i, x in enumerate(pins_x):
        for side, ys in (("pY", 1), ("nY", -1)):
            yc = ys * yh
            sad = Part.makeBox(sx, sy, sz - 6.0, V(x - sx / 2, yc - sy / 2, z_pin + 6.0)).cut(
                Part.makeBox(sx + 2, sy - 2 * t, sz - 6.0 - t, V(x - sx / 2 - 1, yc - sy / 2 + t, z_pin + 6.0)))
            rub = Part.makeBox(sx, sy + 4.0, 6.0, V(x - sx / 2, yc - sy / 2 - 2.0, z_pin))
            # Z-кронштейн: нижняя полка на седле (2 шпильки), стенка 30 мм с внешней стороны, верхняя полка под рейкой
            yo = ys * (sy / 2.0)                          # стенка — над наружной гранью седла
            low = Part.makeBox(sx, sy + 12.0, t, V(x - sx / 2, yc - (sy + 12.0) / 2, z_pin + sz))
            web = Part.makeBox(sx, t, MT["bracket_h"], V(x - sx / 2, yc + yo - (t if ys > 0 else 0.0), z_pin + sz))
            top = Part.makeBox(sx, fw, t, V(x - sx / 2, yc - fw / 2, z_m1 - t))
            put("RoofMount_%s_%d" % (side, i + 1),
                "Кронштейн BSWAN на штырь (нерж. 304, 2 мм): седло 70×28.5×28 + Z 30 мм, верх Z %.0f; к рейке — M5 + T-гайка в "
                "нижнем пазу" % z_m1, Part.makeCompound([sad, low, web, top]), COL_STEEL)
            put("RoofMountRubber_%s_%d" % (side, i + 1), "Резиновый U-профиль седла BSWAN (по углублению крыши)", rub, COL_RUBBER)

    # ── продольные рейки: nL ярусов, палки stock; стык нижнего яруса — сзади, верхнего — спереди ──
    Lr = x1 - x0
    stock = R["stock"]
    short = max(0.0, Lr - stock)
    rail_pieces = []
    splices = []
    for side, ys in (("pY", 1), ("nY", -1)):
        y0 = ys * yh - 10.0
        for k in range(nL):
            zk = z_m1 + 20.0 * k
            if short <= 0:
                segs = [(x0, x1)]
            elif k % 2 == 0:
                segs = [(x0, x0 + short), (x0 + short, x1)]
            else:
                segs = [(x0, x1 - short), (x1 - short, x1)]
            for j, (a, b) in enumerate(segs):
                nm = "RoofRail_%s_L%d%s" % (side, k + 1, "ab"[j] if len(segs) > 1 else "")
                put(nm, "Рейка багажника %s, ярус %d (снизу), кусок %d: X %.0f…%.0f = %.0f мм (2020, палка %.0f)"
                    % ({"pY": "водит.", "nY": "пасс."}[side], k + 1, j + 1, a, b, b - a, stock), vslot_x(a, b, y0, zk), COL_ALU)
                rail_pieces.append((nm, b - a))
            if len(segs) > 1:
                xs_ = segs[0][1]
                splices.append((side, k + 1, xs_))
                # 2 внутренних соединителя BLCCLOY 100 мм — в боковых пазах (наружном и внутреннем)
                for f, yy in (("o", ys * yh + ys * 10.0 - ys * 5.0), ("i", ys * yh - ys * 10.0 + ys * 5.0)):
                    put("RoofSplice_%s_L%d_%s" % (side, k + 1, f),
                        "Стык рейки %s ярус %d (X %.0f): внутренний соединитель BLCCLOY 100×10×5 мм в боковом пазу, 4 установочных M5×6"
                        % (side, k + 1, xs_), Part.makeBox(100.0, 5.0, 10.0, V(xs_ - 50.0, yy - 2.5, zk + 5.0)), COL_ZINC)

    hf = PN["hole_from_end"]
    cross_x = []
    for s_ in rows:
        cross_x += [s_ + hf, s_ + PL - hf]
    # ── стяжные пластины между ярусами (2-hole, шаг 20; 40×18×4) ──
    plates = []
    if nL >= 2:
        stations = []
        x = x0 + 60.0
        flip = 0
        while x < x1 - 60.0:
            stations.append((x, flip))
            x += R["plate_pitch"]
            flip ^= 1
        for side, k, xs_ in splices:                       # у стыков — по 2 с обеих сторон
            for dx in (-80.0, 80.0):
                stations += [(xs_ + dx, 0), (xs_ + dx, 1)]
        stations = [(x, f) for x, f in stations if min(abs(x - p) for p in pins_x) > sx / 2 + 25.0]
        n_pl = 0
        for side, ys in (("pY", 1), ("nY", -1)):
            for x, f in sorted(set(stations)):
                if low and f == 1 and min(abs(x - c) for c in cross_x) < 45.0:
                    f = 0                                  # у поперечины внутренняя грань занята торцом и уголком — пластина снаружи
                yface = ys * yh + (ys * 10.0 if f == 0 else -ys * 10.0)       # 0 — наружная грань, 1 — внутренняя
                ypl = yface if (ys * (1 if f == 0 else -1)) > 0 else yface - 4.0
                n_pl += 1
                plates.append("RoofTiePlate_%s_%02d" % (side, n_pl))
                put(plates[-1], "Стяжная пластина 2020, 2 отв. (шаг 20): ярусы рейки %s, X %.0f, %s грань; 2 × M5×8 + T-гайки"
                    % (side, x, ("наружная", "внутренняя")[f]), Part.makeBox(18.0, 4.0, 40.0, V(x - 9.0, ypl, z_m1)), COL_ZINC)

    # ── поперечины: под отверстиями рам (у каждого ряда 2) ──
    yc0, yc1 = (-(yh - 10.0), yh - 10.0) if low else (-(yh + 10.0), yh + 10.0)
    n_br = 0
    n_bolt = 0
    for i, cx in enumerate(cross_x):
        put("RoofCross_%d" % (i + 1), "Поперечина 2020 #%d: X %.0f (под отверстиями рам ряда %d), Y %.0f…%.0f = %.0f мм%s"
            % (i + 1, cx, i // 2 + 1, yc0, yc1, yc1 - yc0,
               "; между нижними ярусами реек, в торцах резьба M5 (центр. отверстие ⌀4.2)" if low else ""),
            vslot_y(cx - 10.0, yc0, yc1, z_c0), COL_ALU)
        if low:
            for side, ys in (("pY", 1), ("nY", -1)):
                # болт M5×35 ISO 7380 снаружи сквозь нижний ярус рейки в торец поперечины (головка — на наружной грани рейки)
                y_out = ys * (yh + 10.0)
                bolt = Part.makeCylinder(2.5, 35.0, V(cx, y_out, z_m1 + 10.0), V(0, -ys, 0)).fuse(
                    Part.makeCylinder(4.75, 2.75, V(cx, y_out, z_m1 + 10.0), V(0, ys, 0)))
                n_bolt += 1
                put("RoofCrossBolt_%d_%s" % (i + 1, side),
                    "Болт M5×35 ISO 7380 + шайба: сквозь нижний ярус рейки %s (отв. ⌀5.5 поперёк, по оси) в резьбу M5 торца "
                    "поперечины #%d; синий фиксатор" % (side, i + 1), bolt, COL_STEEL)
                # уголок сверху: полка на поперечине, стенка — на внутренней грани верхнего яруса
                lg, tb_ = 28.0, 4.0
                y_in = ys * (yh - 10.0)                   # внутренняя грань рейки
                hor = Part.makeBox(20.0, lg, tb_, V(cx - 10.0, y_in - (lg if ys > 0 else 0.0), z_c1))
                ver = Part.makeBox(20.0, tb_, lg, V(cx - 10.0, y_in - (tb_ if ys > 0 else 0.0), z_c1))
                n_br += 1
                put("RoofCrossBracket_%d_%s" % (i + 1, side),
                    "Уголок 2020 (литой 20×28×28): верх поперечины #%d ↔ внутренняя грань верхнего яруса рейки %s; 2 × M5×8 + "
                    "T-гайки (держит поперечину от проворота вокруг болта)" % (i + 1, side), hor.fuse(ver), COL_ZINC)
            continue
        for side, ys in (("pY", 1), ("nY", -1)):
            for f, dx in (("r", -1), ("f", 1)):
                lg, tb_ = 28.0, 4.0                      # стандартный литой уголок 2020: 20 × 28 × 28, стенка ~4
                xa = cx + dx * 10.0 + (0.0 if dx > 0 else -lg)
                hor = Part.makeBox(lg, 20.0, tb_, V(xa, ys * yh - 10.0, z_r1))
                ver = Part.makeBox(tb_, 20.0, lg, V(cx + dx * 10.0 - (tb_ if dx < 0 else 0.0), ys * yh - 10.0, z_r1))
                n_br += 1
                put("RoofCrossBracket_%d_%s_%s" % (i + 1, side, f),
                    "Уголок 2020 (литой 20×28×28): поперечина #%d ↔ верхний паз рейки %s, %s; 2 × M5×8 + T-гайки"
                    % (i + 1, side, {"r": "сзади", "f": "спереди"}[f]), hor.fuse(ver), COL_ZINC)

    # ── панели ──
    panels = []
    fwp = PN["frame_w"]
    board = None
    for r_, s in enumerate(rows):
        for c_, y0 in enumerate(cols):
            slot = "R%dC%d" % (r_ + 1, c_ + 1)
            if FB and slot == FB["slot"]:                  # вместо панели — фанерная вставка с отверстием под дымоход
                bt = FB["t"]
                b_ = Part.makeBox(PL, PW, bt, V(s, y0, z_c1))
                hole_r = None
                if flue is not None:
                    fl_ = doc.getObject("Shower_Flue")
                    fr_ = ((fl_.Shape.BoundBox.XMax - fl_.Shape.BoundBox.XMin) / 2.0) if fl_ is not None else 38.0
                    hole_r = fr_ + FB["hole_clear"]
                    b_ = b_.cut(Part.makeCylinder(hole_r, bt + 2.0, V(flue["x"], flue["y"], z_c1 - 1.0)))
                put("RoofFlueBoard", "Вставка на месте панели %s: %s, %.0f × %.0f × %.0f мм; отверстие ⌀%.0f под дымоход (зазор %.0f мм "
                    "до трубы — не горючее касание; кромку отверстия обшить жестью/алюминием); 4 × M5 к поперечинам, как панель"
                    % (slot, FB["title"], PL, PW, bt, 2 * hole_r if hole_r else 0, FB["hole_clear"]), b_, (0.72, 0.55, 0.33))
                board = dict(slot=slot, x=(s, s + PL), y=(y0, y0 + PW), z=(z_c1, z_c1 + bt), hole_r=hole_r)
                continue
            outer = Part.makeBox(PL, PW, PH, V(s, y0, z_c1))
            frame = outer.cut(Part.makeBox(PL - 2 * fwp, PW - 2 * fwp, PH + 2, V(s + fwp, y0 + fwp, z_c1 - 1)))
            glass = Part.makeBox(PL - 2 * fwp + 2.0, PW - 2 * fwp + 2.0, 4.0, V(s + fwp - 1.0, y0 + fwp - 1.0, z_p1 - 5.0))
            nm = "SolarPanel_R%dC%d" % (r_ + 1, c_ + 1)
            put(nm + "_Frame", "Рама панели %s (анод. алюминий, 30 мм); 4 отверстия крепления — %.0f мм от торцов" % (nm, hf),
                frame, COL_PFRAME)
            put(nm, "Солнечная панель %s — %s, 100 W; X %.0f…%.0f, Y %.0f…%.0f" % (nm, PN["title"], s, s + PL, y0, y0 + PW),
                glass, COL_PANEL)
            panels.append(nm)

    # ── проверки ──
    import math
    chk = []
    if flue is not None and board is not None and board["hole_r"]:
        hx0, hx1 = flue["x"] - board["hole_r"], flue["x"] + board["hole_r"]
        hy0, hy1 = flue["y"] - board["hole_r"], flue["y"] + board["hole_r"]
        chk.append(("отверстие вставки ↔ край вставки (мин.)", min(hx0 - board["x"][0], board["x"][1] - hx1,
                                                                  hy0 - board["y"][0], board["y"][1] - hy1)))
        chk.append(("низ колпака над верхом панелей", flue["z0"] - z_p1))
        others = [n_ for n_ in parts if n_.startswith("SolarPanel") and not n_.endswith("_Frame")]
        chk.append(("колпак ↔ ближайшая панель (3D)", min(cap.Shape.distToShape(parts[n_])[0] for n_ in others)))
        chk.append(("дымоход ↔ ближайшая поперечина (3D)",
                    min(doc.getObject("Shower_Flue").Shape.distToShape(parts[n_])[0] for n_ in parts if n_.startswith("RoofCross_"))))
    elif flue is not None:
        dx_ = min([abs(flue["x"] - (s + PL)) for s in rows] + [abs(s - flue["x"]) for s in rows])
        chk.append(("колпак дымохода ↔ край панели по X (до центра − r)", dx_ - flue["r"]))
        chk.append(("колпак дымохода ↔ рейка (по Y)", (yh - 10.0) - (abs(flue["y"]) + flue["r"])))
        chk.append(("низ колпака над верхом панелей", flue["z0"] - z_p1))
        sh_cap = cap.Shape
        chk.append(("колпак ↔ ближайшая деталь багажника (3D)",
                    min(sh_cap.distToShape(p)[0] for n_, p in parts.items() if not n_.startswith("RoofPin"))))
    chk.append(("поле панелей ↔ рейка (по Y, панели внутри багажника)", (yh + 10.0) - field_w / 2.0))
    # роль скана: высота крыши под передним/задним концом рейки
    roof_z = {}
    try:
        from .scan import scan_points
        import numpy as np
        P = scan_points()
        for nm_, xq in (("зад", x0), ("перед", x1)):
            m = (abs(P[:, 0] - xq) < 80) & (abs(P[:, 1]) < 600)
            roof_z[nm_] = float(P[m, 2].max()) if m.any() else float("nan")
    except Exception:
        pass

    # ── расчёт рейки ──
    E = 69000.0
    I1, A1 = 6982.0, 158.0                                # 2020: Ix ≈ 0.70 см⁴, площадь ≈ 1.58 см²
    kg_m = 0.45
    gg = 9.81
    P_cb = (nc * PN["kg"] / 2.0 + (yc1 - yc0) / 1000.0 * kg_m) * gg / 2.0   # на одну рейку от одной поперечины, Н
    q = nL * kg_m * gg / 1000.0
    xs_extra = [x0 + i * (x1 - x0) / 60.0 for i in range(61)]
    loads = [(x, P_cb) for x in cross_x]
    res = {}
    for nm_, EI in (("1 × 2020", E * I1), ("2 × 2020 без связи", nL * E * I1),
                    ("2 × 2020 стянуты (оценка 0.9·составного)", E * (2 * I1 + 2 * A1 * 10.0 ** 2) * 0.9)):
        w1, m1, r1 = _beam(xs_extra, pins_x, loads, EI, q)
        w3, m3, r3 = _beam(xs_extra, pins_x, [(x, 3 * P) for x, P in loads], EI, 3 * q)
        res[nm_] = (w1, w3, m3)
    w1, m1, reac = _beam(xs_extra, pins_x, loads, E * I1, q)
    W1 = I1 / 10.0
    Wc = (2 * I1 + 2 * A1 * 100.0) / 20.0
    m_cap1, m_capc = 110.0 * W1 / 1000.0, 110.0 * Wc / 1000.0       # Н·м при σ = 110 МПа (6063-T5, с запасом от σт ≈ 145)
    mass_alu = (sum(l for _, l in rail_pieces) + len(cross_x) * (yc1 - yc0)) / 1000.0 * kg_m
    mass_mounts = 6 * 0.35
    mass_pan = len(panels) * PN["kg"]
    mass_small = (n_br * 0.025 + len(plates) * 0.02 + 0.6)
    mass_total = mass_alu + mass_mounts + mass_pan + mass_small

    # ── раскрой и спецификация ──
    pieces = rail_pieces + [("RoofCross_%d" % (i + 1), yc1 - yc0) for i in range(len(cross_x))]
    sticks = _pack(pieces, stock, R["kerf"])
    n_cross = len(cross_x)
    tn_brackets = n_br * 2
    n_pan_bolts = (len(panels) + (1 if board else 0)) * 4
    tn_plates = len(plates) * 2
    tn_panels = n_pan_bolts
    tn_mounts = 12                                        # по 2 на кронштейн: штатное отверстие + 1 досверлить ⌀5.5
    bom = [
        ("Профиль 2020 V-slot 2440 мм (SeekLiny B0F83QJV1M, 10 шт.)", "%d палок" % len(sticks)),
        ("Кронштейны BSWAN на штыри (B0D9VN67HN, 6 шт.)", "6"),
        ("Внутренний прямой соединитель 2020, 100 мм (BLCCLOY B0CFVB9266, 10 шт. + винты M5×6)", "%d" % (2 * len(splices))),
        ("Уголок 2020 литой 20×28×28 (поперечина ↔ рейка)", "%d" % n_br),
    ] + ([("Болт M5×35 ISO 7380 + шайба M5 (сквозь нижний ярус рейки в торец поперечины; метчик M5 в торец)", "%d" % n_bolt)]
         if n_bolt else []) + ([("Фанера 3/4″ exterior/marine под вставку 1011 × 460 (+ лак/краска, жесть на кромку отверстия)", "1")]
                              if board else []) + [
        ("Пластина 2020 прямая 2 отв. 40×18×4, шаг 20 (ярусы реек)", "%d" % len(plates)),
        ("T-гайка M5 под паз 6 мм (hammer-head / drop-in — ставится сбоку в собранный профиль)",
         "%d (уголки %d + пластины %d + панели %d + кронштейны %d)" % (tn_brackets + tn_plates + tn_panels + tn_mounts,
                                                                     tn_brackets, tn_plates, tn_panels, tn_mounts)),
        ("Винт M5×8 (уголки, пластины)", "%d" % (tn_brackets + tn_plates)),
        ("Болт M5×12 + шайба M5 (рама панели → поперечина)", "%d" % (len(panels) * 4)),
    ] + ([("Болт M5×30 + шайба M5 (вставка → поперечина)", "4")] if board else []) + [
        ("Болт M5×12 + кузовная шайба M5×20 (кронштейн → нижний паз рейки)", "%d" % tn_mounts),
        ("Заглушка торца 2020", "%d" % (2 * 2 * nL + (0 if low else 2 * n_cross))),
        ("Синий фиксатор резьбы (есть)", "на все M5"),
    ]
    roof_summary = dict(pins_x=pins_x, yh=yh, z=(z_pin, z_m1, z_r1, z_c1, z_p1), rows=rows, cols=cols, gap_after=gap_after,
                        field=(rows[0], rows[-1] + PL, field_w), rack=(x0, x1, -(yh + 10.0), yh + 10.0), cross_x=cross_x, splices=splices,
                        flue=flue, chk=chk, roof_z=roof_z, res=res, reac=reac, m_cap=(m_cap1, m_capc),
                        mass=(mass_alu, mass_mounts, mass_pan, mass_small, mass_total), sticks=sticks, bom=bom,
                        n_panels=len(panels), short=short, n_plates=len(plates), n_br=n_br, board=board, low=low)
    S.put(locals(), "roof_summary")


def report(S):
    """Сводка: багажник на крыше и панели."""
    r = S.roof_summary
    if not r or not isinstance(r, dict):
        return
    print("=" * 70)
    print("[БАГАЖНИК НА КРЫШЕ] 2020 на 6 заводских штырях + %d панелей Rvpozwer 100W (%d W)%s" % (
        r["n_panels"], 100 * r["n_panels"], ("; вместо %s — фанерная вставка с отверстием под дымоход" % r["board"]["slot"]) if r["board"] else ""))
    px = r["pins_x"]
    print("  Штыри (таблица Ram L2H2): X %s (шаг %.1f и %.1f), Y ±%.0f (между 1480); X от порога — оценка ±25 мм"
          % (", ".join("%.0f" % x for x in px), px[1] - px[0], px[2] - px[1], r["yh"]))
    zp, zm, zr, zc, zt = r["z"]
    print("  Поперечины: %s" % ("между нижними ярусами реек (болт M5 в торец + уголок сверху)" if r["low"] else "сверху реек (2 уголка)"))
    print("  Высоты: дно углубления %.0f; верх кронштейна %.0f; верх реек %.0f; верх поперечин %.0f; верх панелей %.0f "
          "(над крышей +%.0f мм)" % (zp, zm, zr, zc, zt, zt - (zp + ANCHORS["roof_pins"]["z_pocket"])))
    x0, x1, y0, y1 = r["rack"]
    print("  Багажник: X %.0f…%.0f (%.0f мм), ширина %.0f мм (Y ±%.0f); свес за штыри: сзади %.0f, спереди %.0f"
          % (x0, x1, x1 - x0, y1 - y0, y1, px[0] - x0, x1 - px[-1]))
    import math
    for k_, v_ in r["roof_z"].items():
        if not math.isnan(v_) and v_ < zp:
            print("  Крыша (скан) под %s концом реек: Z≈%.0f — под рейкой %.0f мм (дальше крыша уходит вниз к кабине)"
                  % ({"зад": "задним", "перед": "передним"}[k_], v_, zm - v_))
    print("  Ряды панелей (X начала): %s; колонки (Y начала): %s; поле %.0f × %.0f мм%s"
          % (", ".join("%.0f" % s for s in r["rows"]), ", ".join("%.0f" % c for c in r["cols"]),
             r["field"][1] - r["field"][0], r["field"][2],
             ("; разрыв под дымоход — после ряда %d" % r["gap_after"]) if r["gap_after"] else ""))
    print("  Поперечины X: %s" % ", ".join("%.0f" % x for x in r["cross_x"]))
    if r["splices"]:
        print("  Стыки реек: %s" % "; ".join("%s ярус %d — X %.0f" % s for s in r["splices"]))
    if r["flue"]:
        f = r["flue"]
        print("  Дымоход: колпак ⌀%.0f в X %.0f, Y %+.0f, Z %.0f…%.0f" % (2 * f["r"], f["x"], f["y"], f["z0"], f["z1"]))
    print("  Зазоры: " + "; ".join("%s %.0f" % c for c in r["chk"]))
    print("  Рейка (неразрезная, 3 опоры), прогиб макс 1g / 3g, момент 3g:")
    for k, (w1, w3, m3) in r["res"].items():
        print("     %-40s %.1f / %.1f мм, %.0f Н·м" % (k, w1, w3, m3 / 1000.0))
    print("     допустимый момент (σ 110 МПа): 1 × 2020 — %.0f Н·м, 2 × 2020 стянуты — %.0f Н·м" % r["m_cap"])
    print("  Нагрузка на штырь (1g, одна сторона): сзади→вперёд %s Н (лимит Ram 245 Н = 25 кг)"
          % ", ".join("%.0f" % v for v in r["reac"]))
    ma, mm, mp, ms, mt = r["mass"]
    print("  Масса: профиль %.1f + кронштейны %.1f + панели %.0f + мелочь %.1f = %.0f кг (лимит Ram 150 кг)" % (ma, mm, mp, ms, mt))
    print("  Раскрой палок %.0f (пропил %.1f): %d палок" % (ROOF_RACK["stock"], ROOF_RACK["kerf"], len(r["sticks"])))
    for i, s in enumerate(r["sticks"]):
        used = sum(l for _, l in s) + ROOF_RACK["kerf"] * len(s)
        whole = len(s) == 1 and abs(s[0][1] - ROOF_RACK["stock"]) < 1.0
        print("     палка %2d: %s → %s" % (i + 1, " + ".join("%s %.0f" % (n, l) for n, l in s),
                                          "целиком, без реза" if whole else "остаток %.0f" % max(0.0, ROOF_RACK["stock"] - used)))
    print("  Спецификация:")
    for n, q in r["bom"]:
        print("     • %s — %s" % (n, q))
    print("=" * 70)
