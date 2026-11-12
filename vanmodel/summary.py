# -*- coding: utf-8 -*-
"""Сводка по модели — печатается после сборки (её конец читает tools/export_drawing_data.py)."""

from .anchors import ANCHORS
from .params import FLOOR, SHOWER_KITCHEN, TANK_RACK, WATER_TANK
from .common import SAVE_PATH, overall_bbox
from .scan import y_at_z

# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def print_summary(S):
    """Печать сводки по модели (размеры, зазоры, проверки)."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    DP, P, W, WA, arch_a_lin, bank_summary = S.DP, S.P, S.W, S.WA, S.arch_a_lin, S.bank_summary
    bed_summary, cab_summary, crown_z, deck_notes = S.bed_summary, S.cab_summary, S.crown_z, S.deck_notes
    doc, dp_box_x, floor_hw, galley_summary, half = S.doc, S.dp_box_x, S.floor_hw, S.galley_summary, S.half
    lower_rail_z, mesh_obj, n_factory_threads = S.lower_rail_z, S.mesh_obj, S.n_factory_threads
    n_floor_ribs, n_holes, n_rails = S.n_floor_ribs, S.n_holes, S.n_rails
    overarch_summary, ph, pitch, rack_summary = S.overarch_summary, S.ph, S.pitch, S.rack_summary
    rib_h, rib_xs, sec, tank_summary, tfl_summary = S.rib_h, S.rib_xs, S.sec, S.tank_summary, S.tfl_summary
    threaded_z, trk_summary, trunk_summary = S.threaded_z, S.trk_summary, S.trunk_summary
    wheel_x0, wheel_x1, x_dp, x_dp_s = S.wheel_x0, S.wheel_x1, S.x_dp, S.x_dp_s
    # ─── сводка ───
    bb = overall_bbox(doc)
    n_solid = len([o for o in doc.Objects if o.isDerivedFrom("Part::Feature")])
    print("=" * 70)
    print("VAN v0 — КАРКАС ProMaster 136 по 3D-скану  (обшивка = меш-скан)")
    print("Документ:", doc.Name, " Сохранён:", SAVE_PATH)
    print("-" * 70)
    print("Профиль борта (измерен по скану, внутр. поверхность, n=%d точек):" % len(half))
    print("  пол: полуширина %.0f → у свода %.0f;  свод Z=%.0f" % (floor_hw, half[-2][0], crown_z))
    print("  выборка: полуширина@Z500=%.0f  @Z1000=%.0f  @Z1500=%.0f  @Z1700=%.0f" % (
        y_at_z(half, 500), y_at_z(half, 1000), y_at_z(half, 1500), y_at_z(half, 1700)))
    print("-" * 70)
    print("[Каркас]")
    print("  Рёбра (гнутые обручи): %d @X=%s, %gx%g (ШxТ)" % (
        len(rib_xs), rib_xs, P["rib_width"], P["rib_depth"]))
    print("  Продольные рейки: %d сегм. @Z=%s, □%g" % (n_rails, P["wall_rail_z"], sec))
    print("    низовая рейка Z=%g прервана колёсными арками X=%g..%g и дверью" % (
        lower_rail_z, wheel_x0, wheel_x1))
    print("  Рефлёный пол: %d продольных гребней вдоль X, шаг %g, высота %g" % (
        n_floor_ribs, pitch, rib_h))
    print("  Стойки: 3 (B @X=%.0f + 2 задние @Y=±%.0f), %gx%g h=%g" % (
        P["slider_front_from_rear"], P["rear_w"] / 2.0,
        P["pillar_width"], P["pillar_depth"], ph))
    print("  Маркеры крепления: %d (на %d рёбрах × Z=%s × 2 борта)" % (
        n_holes, len(rib_xs), P["hole_marker_z"]))
    print("  Заводские резьбовые точки: %d на рейках Z=%g, резьба %s" % (
        n_factory_threads, threaded_z, P["factory_threaded_thread"]))
    print("  Обшивка-скан: %s" % ("загружена" if mesh_obj else "НЕТ"))
    print("-" * 70)
    print("[Задние углы у пола: D-стойка ↔ арка — фото сверху 2026-11-06]")
    print("  Передняя грань короба D-стойки у края фанеры: X=%.0f; уплотнитель задней двери X≈%.0f" % (
        x_dp, x_dp - DP["box_len"]))
    print("  Задняя грань арки у края фанеры: X=%.0f;  выступ арки от края фанеры %.0f мм (%.2f″)" % (
        W["center_x"] - arch_a_lin(DP["photo_wall"]), W["protrusion"] - DP["photo_wall"],
        (W["protrusion"] - DP["photo_wall"]) / 25.4))
    print("  Зазор короб ↔ арка по полу (от края фанеры): " + ";  ".join(
        "%.1f″ → %.2f″" % (yi, (W["center_x"] - arch_a_lin(DP["photo_wall"] + yi * 25.4)
                               - dp_box_x(min(DP["photo_wall"] + yi * 25.4, DP["photo_wall"] + DP["box_depth"]))) / 25.4)
        for yi in (0.0, 1.1, 2.4, 5.0)))
    if bed_summary:
        print("  Центр задней стойки кровати от грани короба: %.0f мм (%.2f″)" % (
            bed_summary["posts"][0] - x_dp, (bed_summary["posts"][0] - x_dp) / 25.4))
    if bed_summary:
        bs = bed_summary
        print("-" * 70)
        ff = bs["floor_top"]
        def _h(z):
            return "Z=%.0f (%.0f мм / %.1f″ над чистовым полом)" % (z, z - ff, (z - ff) / 25.4)
        print("[Кровать — как построена; strut SC14-10-EG; реконструкция по фото 2026-11-05]")
        print("  Чистовой пол (верх фанеры): Z=%.1f  (гребни %.0f + XPS %.1f + фанера %.1f)" % (
            ff, P["floor_corrugation_height"], FLOOR["xps_th"], FLOOR["ply_th"]))
        print("  Стойки: 4, X=%s, |Y|=%.0f; болт в кузов %s" % (
            [int(v) for v in bs["posts"]], bs["post_y"], _h(bs["z_bolt"])))
        print("  Верх реек/поперечин: %s;  верх настила: %s" % (_h(bs["z_rail_top"]), _h(bs["z_deck_top"])))
        print("  Настил X=%.0f..%.0f (%.0f мм = %.1f″ по центру), поперёк %.0f мм; перед — в %.0f мм (%.1f″) позади "
              "передних стоек, зад — до задних дверей (вырезы под D-стойки)" % (
            bs["deck"][0], bs["deck"][1], bs["deck"][1] - bs["deck"][0], (bs["deck"][1] - bs["deck"][0]) / 25.4,
            bs["deck_w"], bs["posts"][1] - 20.65 - bs["deck"][1], (bs["posts"][1] - 20.65 - bs["deck"][1]) / 25.4))
        print("  Поперечины: " + ", ".join("#%d X=%.0f" % (i + 1, x) for i, x in enumerate(bs["cross_x"])))
        print("  «Гараж» под кроватью: %.0f мм (%.1f″);  над аркой: %.0f мм" % (
            bs["garage"], bs["garage"] / 25.4, bs["z_rail_top"] - 41.3 - bs["arch_top"]))
        kinds = {}
        for what, Lp in bs["cutlist"]:
            kinds.setdefault(what, []).append(Lp)
        print("  Strut по деталям: " + "; ".join(
            "%s %d×%.0f" % (k, len(v), v[0]) for k, v in kinds.items()))
        print("  Strut всего: %.2f м" % (sum(Lp for _, Lp in bs["cutlist"]) / 1000.0))
        for note in deck_notes:
            print("  ⚠ " + note)
    for rs in rack_summary:
        f0 = rs["floor_top"]
        mm = lambda v: ("%.1f мм" % v) if v is not None else "—"
        print("[Этажерка, 2 батареи Buknuwo 150Ah — пассажирский борт, %s]" % (
            "арка ↔ сдвижная дверь" if rs["stack"] == "front" else "D-стойка ↔ арка"))
        print("  Батареи по X: %.0f..%.0f (%.2f″ вдоль борта); грань в салон — %.0f мм (%.1f″) от стены у пола" % (
            rs["X"][0], rs["X"][1], rs["bx"] / 25.4, rs["inner_from_wall"], rs["inner_from_wall"] / 25.4))
        print("  Нижняя до арки: %s%s" % (mm(rs["gap_arch"]),
            ("; до короба D-стойки: %s" % mm(rs["gap_dpillar"])) if rs["gap_dpillar"] is not None else ""))
        print("  Пластина P2 (TP15): до пластины P1 %s, до арки %s" % (mm(rs["plates_gap"]), mm(rs["p2_plate_arch"])))
        if rs["stack"] == "front":
            print("  До края сдвижной двери: %.0f мм (%.1f″); впереди края щита кровати на %.0f мм" % (
                rs["to_slider"], rs["to_slider"] / 25.4, rs["ahead_of_deck"]))
        print("  Нижняя: %.0f..%.0f мм над полом;  рейки полки: %.0f..%.0f;  верхняя: %.0f..%.0f" % (
            rs["z_b1"][0] - f0, rs["z_b1"][1] - f0, rs["z_rail"][0] - f0, rs["z_rail"][1] - f0,
            rs["z_b2"][0] - f0, rs["z_b2"][1] - f0))
        print("  От верхней батареи до низа поперечин/реек кровати: %.0f мм (%.1f″)" % (
            rs["above_b2"], rs["above_b2"] / 25.4))
        if rs["ties"] == "short":
            print("  Верхние стяжки: %.0f..%.0f над полом; до низа реек кровати: %.0f мм" % (
                rs["tie"][0] - f0, rs["tie"][1] - f0, rs["tie_to_bed"]))
        elif rs["ties"] == "bed":
            print("  Стяжки = поперечины кровати: существующая + новая L=%.0f" % rs["cross_len"])
        print("  Новая стойка P2 X=%.0f..%.0f, L=%.0f%s, до арки %s;  P3/P4 L=%.0f;  рейки полки 2×%.0f%s" % (
            rs["p2"][0], rs["p2"][1], rs["p2_len"], "" if rs["p2_on_rail"] else " (впереди рейки кровати)",
            mm(rs["p2_arch"]), rs["p34_len"], rs["rail_len"], ";  крышка — фанера 3/4″" if rs["lid"] else ""))
    if bank_summary:
        k = bank_summary
        f0 = k["floor_top"]
        print("[Этажерка на 4 батареи Buknuwo 150Ah — пассажирский борт — ПРОЕКТ 2026-11-07]")
        print("  B1 на полу X %.0f..%.0f; верх арки %.0f мм (%.2f″); лестница %.0f..%.0f над полом; полка (верх фанеры) "
              "%.0f мм (%.1f″)" % (k["X1"][0], k["X1"][1], k["z_arch"] - f0, (k["z_arch"] - f0) / 25.4,
                                  k["z_l"][0] - f0, k["z_l"][1] - f0, k["z_s1"] - f0, (k["z_s1"] - f0) / 25.4))
        print("  На полке: " + ", ".join("B%d X %.0f..%.0f" % (i + 2, x, x + k["bx"]) for i, x in enumerate(k["xs"])) +
              ";  верх %.0f мм (%.1f″);  до низа поперечин кровати %.0f мм" % (
                  k["top"] - f0, (k["top"] - f0) / 25.4, k["under_cross"]))
        print("  Грань батарей к проходу — %.0f мм (%.1f″) от стены у пола (арка — 239)" % (k["inner"], k["inner"] / 25.4))
        print("  Рейки L=%.0f / %.0f;  поперечины 2×%.0f;  стойки P3 L=%.0f, P3f L=%.0f;  свободно на полке перед "
              "B4 %.0f мм (%.1f″)" % (k["rails"][0], k["rails"][1], k["cross"], k["posts"][0], k["posts"][1],
                                     k["free"], k["free"] / 25.4))
        rf = k.get("rails_fit")
        if rf:
            (w0_, w1_), (i0_, i1_) = k["rails_x"]
            print("  Рейки из одного 10′ (%.0f мм с пропилом): у борта X %.0f..%.0f = %.0f мм (было %.0f), у прохода X %.0f..%.0f "
                  "= %.0f мм (было %.0f); перекрытие стойки nY front %.0f мм, P3f %.0f мм" % (
                      rf["stick"], w0_, w1_, rf["new"][0], rf["old"][0], i0_, i1_, rf["new"][1], rf["old"][1],
                      rf["wall_over_Pf"], rf["inner_over_P3f"]))
            print("  Полка — до X %.0f (было %.0f): полочка под бельё впереди Pf %.0f мм = %.1f″ (было %.0f = %.1f″); "
                  "резина/проставка на арке %.0f мм (рейка — на овале стоек: смещение по Z %.1f, по X P1 %.1f / Pf %.1f, "
                  "P3 %.1f / P3f %.1f; допуск ±%.1f)" % (
                      rf["shelf_front"][0], rf["shelf_front"][1], rf["linen"][0], rf["linen"][0] / 25.4, rf["linen"][1],
                      rf["linen"][1] / 25.4, rf["pad"], rf["hole_z"], rf["holes_x"]["P1"], rf["holes_x"]["Pf"],
                      rf["holes_x"]["P3"], rf["holes_x"]["P3f"], rf["tol"]))
        print("  Зазоры: " + "; ".join("%s %.1f" % (a_, v) for a_, v in k["checks"]))
        if k.get("elec"):
            e = k["elec"]
            print("  Электрика: панель на борту X %.0f..%.0f (%.0f мм), %.0f..%.0f над полом; до рейки кровати %.0f мм; "
                  "масса на C-стойке X=%.0f, %.0f над полом" % (e["board"][0], e["board"][1], e["free_x"], e["board"][2],
                                                              e["board"][3], e["clear_rail"], e["ground"][0], e["ground"][1]))
    if overarch_summary:
        o = overarch_summary
        f0 = o["floor_top"]
        print("[Полка НАД аркой — ещё 2 батареи Buknuwo 150Ah, пассажирский борт — ПРОЕКТ]")
        print("  Верх арки %.0f мм (%.1f″) над полом (⚠️ оценка Upfit — промерить); рейки %.0f..%.0f; полка (верх фанеры) "
              "%.0f мм (%.1f″)" % (o["z_arch"] - f0, (o["z_arch"] - f0) / 25.4, o["zr"][0] - f0, o["zr"][1] - f0,
                                  o["zs"][1] - f0, (o["zs"][1] - f0) / 25.4))
        print("  Батареи над аркой: X " + ", ".join("%.0f..%.0f" % (x, x + o["bx"]) for x in o["xs"]) +
              ";  верх %.0f мм (%.1f″) над полом" % (o["zb"][1] - f0, (o["zb"][1] - f0) / 25.4))
        print("  До низа настила %.0f мм (%.1f″), до низа продольной рейки кровати %.0f мм" % (
            o["deck_bottom"] - o["zb"][1], (o["deck_bottom"] - o["zb"][1]) / 25.4, o["rail_bottom"] - o["zb"][1]))
        print("  Рейки над аркой L=%.0f / %.0f (X %.0f..%.0f);  P3f L=%.0f;  свободно на полке перед батареями %.0f мм "
              "(%.1f″)" % (o["rails"][0], o["rails"][1], o["xa"], o["xb"], o["p3f"], o["free_front"], o["free_front"] / 25.4))
        if o["cross2"]:
            print("  Поперечина #2 кровати перенесена в промежуток между батареями: X=%.0f" % o["cross2"])
        print("  Зазоры: " + "; ".join("%s %.1f" % (k, v) for k, v in o["checks"]))
    if tank_summary:
        t = tank_summary
        f0 = t["floor_top"]
        print("[Бак для воды TORVA 33 gal — водительский борт, D-стойка ↔ арка]")
        if t["lift_min"] is not None:
            print("  Нужный подъём дна (зазор до арки ≥ %.0f мм): %.0f мм (%.1f″) → подставка %.0f мм (%.2f″): %s" % (
                WATER_TANK["arch_clear"], t["lift_min"], t["lift_min"] / 25.4, t["lift"], t["lift"] / 25.4, t["stack"]))
        else:
            print("  Подъём дна (задан): %.0f мм" % t["lift"])
        print("  X бака %.0f..%.0f; зад бака в %.0f мм от стены, грань в салон в %.0f мм от стены (у пола)" % (
            t["x"][0], t["x"][1], t["standoff"], t["standoff"] + WATER_TANK["size"][1]))
        print("  Верх бака %.0f мм над полом; до низа поперечин кровати %.0f мм" % (t["top"] - f0, t["under_cross"]))
        if t["over_box"] > 0:
            print("  Торец бака нависает над коробом D-стойки на %.0f мм: дно %.0f над полом, короб ~%.0f (оценка) → запас %.0f" % (
                t["over_box"], t["lift"], t["z_box"] - f0, t["lift"] - (t["z_box"] - f0)))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in t["checks"]))
        print("  Проставка задняя стойка кровати ↔ бак: %.0f мм;  P3/P4 L=%.0f;  объём тела в модели %.0f л" % (
            t["spacer"], t["p_len"], t["vol"]))
        for note in t.get("notes", []):
            print("  ⚠ " + note)
    if trk_summary:
        t = trk_summary
        f0 = t["floor_top"]
        print("[Бак T-3500 35 gal на полке над водительской аркой — ПРОЕКТ 2026-11-07]")
        print("  Верх арки %.0f мм (%.2f″); поперечины и рейка %.0f..%.0f над полом; полка (верх фанеры 3/4″) %.0f мм "
              "(%.1f″)" % (t["z_arch"] - f0, (t["z_arch"] - f0) / 25.4, t["z_c"][0] - f0, t["z_c"][1] - f0,
                          t["z"][0] - f0, (t["z"][0] - f0) / 25.4))
        print("  Бак X %.0f..%.0f, от стены (у пола) %.0f..%.0f мм (%.1f..%.1f″); верх %.0f мм (%.1f″); до низа поперечин "
              "кровати %.0f мм (%.1f″), с допуском +0.25″ — %.0f" % (
                  t["x"][0], t["x"][1], t["from_wall"][0], t["from_wall"][1], t["from_wall"][0] / 25.4,
                  t["from_wall"][1] / 25.4, t["z"][1] - f0, (t["z"][1] - f0) / 25.4, t["under_cross"],
                  t["under_cross"] / 25.4, t["under_cross"] - t["tol"]))
        print("  Полка %.0f×%.0f;  рейка L=%.0f;  поперечины 2×%.0f;  стойки P3/P3f 2×%.0f;  %s" % (
            t["shelf"][0], t["shelf"][1], t["rail"], t["cross"], t["post"],
            ("за баком на полке %.0f мм (%.1f″) — под штуцеры" % (t["free_rear"], t["free_rear"] / 25.4))
            if t["free_rear"] > 0 else ("полка сзади — консоль %.0f мм за P1/P3" % -t["free_rear"])))
        print("  Рейка в салон: доля бака %.0f%% → %.0f Н; σ ≈ %.0f МПа (×3g — %.0f) при текучести %.0f; прогиб ≈ %.1f мм" % (
            100 * t["share"], t["P_rail"], t["sigma"], t["sigma3"], TANK_RACK["yield_MPa"], t["defl"]))
        print("  Штуцеры: " + "; ".join("%.1f″ %s Z=%.0f" % (f_["d"], f_["what"], f_["z"] - f0) for f_ in t["fittings"]) +
              ";  насос X %.0f..%.0f на полу" % t["pump"])
        print("  Бак под щитом: передний торец в %.0f мм (%.1f″) позади края щита (X=%.0f); бобышки штуцеров — в %.0f мм; "
              "задний торец в %.0f мм от грани D-стойки (оценка), в %.0f мм (%.1f″) позади задней грани P1" % (
                  t["in_deck"], t["in_deck"] / 25.4, t["deck_front"], t["in_deck_fit"], t["to_dpillar"],
                  t["p1_rear"] - t["x"][0], (t["p1_rear"] - t["x"][0]) / 25.4))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in t["checks"]))
    if tfl_summary:
        t = tfl_summary
        f0 = t["floor_top"]
        print("[Бак %s на полу рядом с водительской аркой (%s) — ВАРИАНТ 2026-11-07]" % (
            t["title"], "поддон" if t["base_mode"] == "pallet" else "прямо на пол, коврик"))
        print("  Бак X %.0f..%.0f; от стены (у пола): грань к борту %.0f мм (%.1f″), к проходу %.0f (%.1f″), с бруском "
              "2×2 %.0f (%.1f″)" % (t["x"][0], t["x"][1], t["from_wall"][0], t["from_wall"][0] / 25.4,
                                        t["from_wall"][1], t["from_wall"][1] / 25.4, t["from_wall"][2],
                                        t["from_wall"][2] / 25.4))
        print("  Дно %.0f мм, верх %.0f мм (%.2f″) над полом%s;  до поперечин кровати %.0f мм" % (
            t["z"][0] - f0, t["z"][1] - f0, (t["z"][1] - f0) / 25.4,
            ("; полка батарей %.0f (%.2f″) → разница %+.0f мм" % (t["bank_top"] - f0, (t["bank_top"] - f0) / 25.4,
                                                              t["level"])) if t["level"] is not None else "",
            t["under_cross"]))
        print("  Под щитом: передний торец в %.0f мм (%.1f″) позади края щита; сзади до линии края щита %.0f мм (%.1f″) — "
              "под штуцеры;  багажник между рейкой батарей и поддоном бака %.0f мм (%.1f″)" % (
                  t["in_deck"], t["in_deck"] / 25.4, t["behind"], t["behind"] / 25.4, t["trunk"] or 0,
                  (t["trunk"] or 0) / 25.4))
        if t["base_mode"] == "pallet":
            print("  Поддон %.0f×%.0f: %d бруска 2×4 плашмя L=%.0f + фанера 1/2″; штуцеры на %s торце" % (
                t["base"][1] - t["base"][0], t["base"][3] - t["base"][2], t["n_runner"], t["runner_len"],
                "заднем" if t["fittings_end"] == "rear" else "переднем"))
        else:
            print("  Прямо на пол (коврик 1/8″), бруски 2×2 в пол, 2 ремня к 4 анкерам; штуцеры на %s торце; с фитингами "
                  "(~2″) до края щита %.0f мм (%.1f″)" % ("заднем" if t["fittings_end"] == "rear" else "переднем",
                                                       t["in_deck_fit"], t["in_deck_fit"] / 25.4))
        if t.get("toilet"):
            q = t["toilet"]
            print("  Туалет X %.0f..%.0f, от стены %.1f″…%.1f″, верх %.1f″; до края щита %.0f мм (%.1f″)%s" % (
                q["x"][0], q["x"][1], q["from_wall"][0] / 25.4, q["from_wall"][1] / 25.4, (q["z"][1] - f0) / 25.4,
                q["in_deck"], q["in_deck"] / 25.4, ("; путь в душ: " + "; ".join("%s %.0f" % (n_, v_) for n_, v_ in
                                                     q.get("path", []))) if q.get("path") else ""))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in t["checks"]))
    if galley_summary:
        k = galley_summary
        f0 = k["floor_top"]
        print("[Душ + мини-кухня — водительский борт, кровать ↔ кабина]")
        print("  Душ: задняя стенка X %.0f (край щита), сверху от %.0f мм (%.1f″) до потолка; поддон %.0f″ (угол R22″): X %.0f..%.0f — "
              "задний край в %.0f мм (%.1f″) впереди края щита (упёрся в арку); край поддона к проходу в %.0f мм (%.1f″) "
              "от стены" % (k["shower_x"][0], k["rear_wall_z"] - f0, (k["rear_wall_z"] - f0) / 25.4, k["pan_r"] / 25.4,
                            k["pan_x0"], k["shower_x"][1], k["pan_behind"], k["pan_behind"] / 25.4,
                            k["wall_y"] - k["y_sf"], (k["wall_y"] - k["y_sf"]) / 25.4))
        print("  В душе: верх поддона %.0f над полом, низ потолка %.0f → от поддона до потолка %.0f мм (%.1f″)" % (
            k["z_pan"] - f0, k["z_ceil"] - 12.0 - f0, k["headroom"], k["headroom"] / 25.4))
        print("  Кухня до X %.0f, торец к душу — по шторке (прямо у стены, дальше дуга R%.0f); у прохода от X %.0f (%.1f″ длины), у стены от X %.0f; "
              "глубина до %.0f мм от стены, столешница %.0f (36″); до спинок сидений %.0f мм" % (
            k["kitchen_x"][1], k["pan_corner_r"] - SHOWER_KITCHEN.get("curtain_in", 50.0), k["sec1_front"][0],
            (k["kitchen_x"][1] - k["sec1_front"][0]) / 25.4,
            k["pan_x0"] + k["r_c"], k["wall_y"] - k["y_kf"] + 20, k["counter"], k["seat_gap"]))
        print("  Секция 1 (мойка): по фасаду X %.0f..%.0f (%.1f″), мойка X %.0f..%.0f;  секция 2 (шкафчик + %s): X %.0f..%.0f "
              "(%.1f″);  перегородка 1/2″ X %.0f" % (
            k["sec1_front"][0], k["sec1_front"][1], (k["sec1_front"][1] - k["sec1_front"][0]) / 25.4, k["sink_x"][0],
            k["sink_x"][1], k["fridge_title"], k["sec2"][0], k["sec2"][1], (k["sec2"][1] - k["sec2"][0]) / 25.4, k["x_div"][0]))
        print("  Вход в душ (шторка открыта, от задней стенки до угла столешницы): %.0f мм (%.1f″)" % (k["entry"], k["entry"] / 25.4))
        if k.get("flap"):
            f_ = k["flap"]
            print("  Откидная столешница %.0f×%.0f″: разложена X %.0f..%.0f; сложена — до плоскости спинки %.0f мм, низ %.1f″ над полом" % (
                f_["len"] / 25.4, f_["w"] / 25.4, f_["x_open"][0], f_["x_open"][1], f_["to_seat"], f_["z_fold_low"] / 25.4))
        if k.get("gas"):
            g_ = k["gas"]
            print("  Нагреватель: X %.0f..%.0f (над поддоном %.0f мм), от стены %.1f″…%.1f″, низ/верх %.1f″/%.1f″ над полом; "
                  "до потолка %.0f мм; дымоход ⌀3″ X %.0f, %.1f″ от стены → до %.0f (над крышей)" % (
                g_["heater_x"][0], g_["heater_x"][1], g_["over_pan"], (k["wall_y"] - g_["heater_y"][1]) / 25.4,
                (k["wall_y"] - g_["heater_y"][0]) / 25.4, (g_["heater_z"][0] - f0) / 25.4, (g_["heater_z"][1] - f0) / 25.4,
                g_["top_to_ceil"], g_["flue_c"][0], (k["wall_y"] - g_["flue_c"][1]) / 25.4, g_["flue_top"]))
        if k.get("propane"):
            q_ = k["propane"]
            print("  Локер пропана: X %.0f..%.0f, Y %.0f..%.0f (%.1f″…%.1f″ от стены у пола), верх %.1f″; наружу %.0f×%.0f×%.0f; "
                  "за край щита %+.0f мм; до поперечин %.0f; до туалета %.0f; до насоса %.0f; багажник рядом %.0f мм (%.1f″); "
                  "газ ~%.1f м" % (
                q_["x"][0], q_["x"][1], q_["y"][0], q_["y"][1], (k["arch_ywall"] - q_["y"][1]) / 25.4,
                (k["arch_ywall"] - q_["y"][0]) / 25.4, (q_["z_top"] - f0) / 25.4, q_["outer"], q_["outer"],
                q_["z_top"] - f0, q_["deck_over"], q_["under_cross"], q_["to_toilet"] or -1, q_["to_pump"] or -1,
                q_.get("trunk") or -1, (q_.get("trunk") or 0) / 25.4, q_["gas_len"] / 1000.0))
        print("  Проход: у душа %.0f мм (%.1f″), у кухни %.0f мм (%.1f″)" % (
            k["aisle_sh"], k["aisle_sh"] / 25.4, k["aisle_k"], k["aisle_k"] / 25.4))
        tp_ = k.get("toilet_pf")
        if tp_:
            print("  Туалет на платформе: плита %.1f″ (X %.0f..%.0f; от препятствия бака X %.0f), колёса ⌀%.0f″, низ платформы "
                  "%.1f″, верх платформы %.1f″, ВЕРХ ТУАЛЕТА %.1f″ над полом" % (
                      tp_["plate"][2] / 25.4, tp_["plate"][0], tp_["plate"][1], tp_["x_obs"], ANCHORS["toilet"]["wheel_d"] / 25.4,
                      (tp_["z"][1] - f0) / 25.4, (tp_["z"][2] - f0) / 25.4, tp_["h_total"] / 25.4))
            print("  Колёсная база %.0f мм (%.1f″), ход %.0f мм (%.1f″) = база − бортик %.0f − длина колёсика с бруском; туалет: транспорт X %.0f..%.0f "
                  "(под щитом), в душе X %.0f..%.0f; платформа X %.0f..%.0f (транспорт), Y %.0f..%.0f" % (
                      tp_["WB"], tp_["WB"] / 25.4, tp_["travel"], tp_["travel"] / 25.4, tp_["rim_t"], tp_["x0"][0],
                      tp_["x0"][1], tp_["x1"][0], tp_["x1"][1], tp_["pf_x"][0], tp_["pf_x"][1], tp_["pf_y"][0], tp_["pf_y"][1]))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in k["checks"]))
    for c_ in cab_summary:
        print("[%s — проект 2026-11-07]" % c_["name"])
        print("  %d шт., X %.0f..%.0f (свободно %.0f мм); низ/верх %.1f″/%.1f″ над полом; над матрасом %.1f″; фасад %.1f″ от "
              "обшивки (внизу), глубина у верха %.0f мм" % (c_["n"], c_["x"][0], c_["x"][1], c_["free"], c_["z"][0] / 25.4,
              c_["z"][1] / 25.4, (c_["over_mat"] or 0) / 25.4, c_["from_wall"] / 25.4, c_["depth_top"]))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in c_["checks"]))
    if trunk_summary:
        t = trunk_summary
        f0 = t["floor_top"]
        print("[Багажник — 2 ящика на SLIDEWAY + полка над баком + хребет — ПРОЕКТ 2026-11-08]")
        for k_, ttl in (("fwd", "2-й этаж, передний (пасс.)"), ("floor1", "1-й этаж")):
            q = t["drawers"][k_]
            print("  %s: X %.0f..%.0f, Y %.0f..%.0f, низ/верх %.1f″/%.1f″; снаружи %.1f × %.1f × %.1f″, внутри %.1f × %.1f × "
                  "%.1f″; выдвигается %s на %.0f″" % (ttl, q["x"][0], q["x"][1], q["y"][0], q["y"][1], (q["z"][0] - f0) / 25.4,
                  (q["z"][1] - f0) / 25.4, (q["x"][1] - q["x"][0]) / 25.4, (q["y"][1] - q["y"][0]) / 25.4,
                  (q["z"][1] - q["z"][0]) / 25.4, q["inside"][0], q["inside"][1], q["inside"][2],
                  "вперёд" if q["out"] > 0 else "назад", abs(q["out"]) / 25.4))
        sh_ = t["shelf"]
        print("  Полка 2-го этажа (водит.): фанера %.2f″, X %.0f..%.0f, Y %.0f..%.0f (%.1f × %.1f″), низ/верх %.1f″/%.1f″; "
              "над ней до поперечин кровати %.1f″, до щита %.1f″; опоры — стойки хребта X %s и стойка кровати pY rear" % (
              sh_["th"] / 25.4, sh_["x"][0], sh_["x"][1], sh_["y"][0], sh_["y"][1], (sh_["x"][1] - sh_["x"][0]) / 25.4,
              (sh_["y"][1] - sh_["y"][0]) / 25.4, (sh_["z"][0] - f0) / 25.4, (sh_["z"][1] - f0) / 25.4,
              sh_["over_cross"] / 25.4, sh_["over_deck"] / 25.4, ", ".join("%.0f" % x_ for x_ in t["posts_x"])))
        print("  Направляющие 2-го этажа Z %.0f..%.0f, 1-го — Z %.0f..%.0f; P3m X %.0f" % (
              t["slide_z"][0], t["slide_z"][1], t["slide1_z"][0], t["slide1_z"][1], t["x_p3m"]))
        print("  Зазоры: " + "; ".join("%s %.1f" % (n, v) for n, v in t["checks"]))
    # ─── ANCHORS: якорные размеры — что сейчас в модели (None → посчитано моделью; подставить замер) ───
    print("[ANCHORS — якорные размеры: %s]" % ", ".join("%s: %s" % (k_, v_["status"]) for k_, v_ in ANCHORS.items()
                                                       if isinstance(v_, dict) and "status" in v_))
    if bed_summary:
        print("  Стойки кровати: X " + ", ".join("%s %.1f" % (k_, v_) for k_, v_ in ANCHORS["bed_posts"]["x"].items()) +
              "; нижний овал %.1f мм над полом; рейки кровати (верх) %.0f мм над полом" % (
                  ANCHORS["bed_posts"]["hole0_z"], bed_summary["z_rail_top"] - bed_summary["floor_top"]))
        print("  D-стойки: передняя грань короба X — nY %.0f, pY %.0f; арки: " % (x_dp_s[-1], x_dp_s[1]) + "; ".join(
            "%s центр X %.0f, верх %.0f, выступ %.0f" % (t_, WA[s_]["center_x"], WA[s_]["height"], WA[s_]["protrusion"])
            for s_, t_ in ((-1, "nY"), (1, "pY"))))
    if bank_summary and bank_summary.get("rails_fit"):
        f0 = bank_summary["floor_top"]
        (w0_, w1_), (i0_, i1_) = bank_summary["rails_x"]
        print("  Рейки этажерки: у борта X %.0f..%.0f, низ %.0f мм над полом (резина на арке %.0f мм); у прохода X %.0f..%.0f" % (
            w0_, w1_, bank_summary["z_l"][0] - f0, bank_summary["rails_fit"]["pad"], i0_, i1_))
        vf = bank_summary.get("valve")
        if vf:
            print("  Клапан сброса давления: X %.0f..%.0f; B1 X %.0f..%.0f закрывает решётку по X на %.0f из %.0f мм; "
                  "свободно перед решёткой %.0f мм (нужно ≥ %.0f → не хватает %.0f)" % (
                      vf["valve_x"][0], vf["valve_x"][1], vf["b1_x"][0], vf["b1_x"][1], vf["cover_x"], vf["w"], vf["gap"],
                      ANCHORS["relief_valve"]["free_min"], max(0.0, vf["need"])))
    if galley_summary:
        g_ = galley_summary
        f0 = g_["floor_top"]
        print("  Поддон: задний край X %.0f, край у борта |Y| %.0f, дно внутри %.0f мм над полом, бортик %.0f; слив X %.0f "
              "|Y| %.0f" % (g_["pan_x0"], g_["y_pan_back"], g_["pan_in"]["z_in"], g_["pan_in"]["rim_t"],
                            g_["pan_in"]["drain"][0], g_["pan_in"]["drain"][1]))
        if g_.get("propane"):
            q_ = g_["propane"]
            print("  Локер пропана: x0 %.0f, y1 %.0f (дверца — к проходу, грань |Y| %.0f)" % (q_["x"][0], q_["y"][1], q_["y"][0]))
    print("-" * 70)
    if bb:
        print("Bounding box (вкл. обшивку): %.0f x %.0f x %.0f мм" % (
            bb.XLength, bb.YLength, bb.ZLength))
    print("Объектов Part::Feature: %d" % n_solid)
    print("=" * 70)
    return doc
