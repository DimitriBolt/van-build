# -*- coding: utf-8 -*-
"""Отделка готового документа: короткие подписи (Label / Label2), ссылки «где купить», скрытые по умолчанию
слои, начальный 3D-вид, сохранение .FCStd."""

import os

from .common import SAVE_PATH, _INTENDED
from .strut import apply_strut_profiles

# Начальный 3D-вид (Dimitri сохранил «приятный угол», коммит 52f931d) — ставится перед сохранением .FCStd
VIEW_CAMERA = """OrthographicCamera {
  viewportMapping ADJUST_CAMERA
  position 2703.6345 -179.83566 913.30084
  orientation 0.92288774 0.24093212 0.30038264  1.461176
  nearDistance -2261.1165
  farDistance 2575.0374
  aspectRatio 1
  focalDistance 1
  height 2919.8276

}
"""

# 2026-11-08 (Dimitri): по умолчанию скрыты — обшивка #2, каркас, проёмы дверей (сейчас с ними не работаем, мешают
# видеть остальное). Включаются глазиком в дереве. Рендеры (tools/render_views.py) это не трогает: VAN_HIDE_ON_SAVE=0.
HIDE_ON_SAVE = ["Scan_Skin_Body", "Frame", "Openings"]


def hide_default(doc):
    if os.environ.get("VAN_HIDE_ON_SAVE", "1") == "0":
        return

    def _hide(o):
        try:
            o.Visibility = False
        except Exception:
            pass
        vo = getattr(o, "ViewObject", None)
        if vo is not None:
            try:
                vo.Visibility = False
            except Exception:
                pass
        for c in getattr(o, "Group", []) or []:
            _hide(c)
    for n in HIDE_ON_SAVE:
        o = doc.getObject(n)
        if o is not None:
            _hide(o)


# Заметки Dimitri в Label2 (из его .FCStd) — сохраняются при пересборке, идут в начало Label2
USER_NOTES = {
    "BankRail_Wall": "Резать 1-ой!! Эта рейка задаёт высоту ножек этажерки. Поесле неё можно-нужно напрезать 2(а лучше 4) "
                     "ножки. Нужно учесть высоту всего, что стоит на 1-м этаже: Wheel arc, Water tank, Propan locker, туалет! "
                     "Рейка должна выдерживать Все !! батареи: 60-80 кг!",
}

# 2026-11-07 (Dimitri): в Label — только короткое название, описание — в Label2
_LABEL_SEPS = (" — ", ": ", " (", ", ", "; ")


# ─── Где купить (2026-11-11, Dimitri): у каждой детали — свойство BuyURL (группа «Покупка»), App::PropertyString ───
# Ключ — obj.Name, значение — ссылка на магазин. Пустое поле = ссылки пока нет (добавлять сюда).
BUY_URLS = {
    "Toilet_Camco": "https://a.co/d/0fEaEKEz",        # туалет SEAFLO 2.6 gal (Amazon B07ZPC4C9N)
}


def apply_buy_urls(doc):
    """Всем деталям — свойство BuyURL; заполняется из BUY_URLS."""
    for o in doc.Objects:
        if not o.isDerivedFrom("Part::Feature"):
            continue
        if "BuyURL" not in o.PropertiesList:
            o.addProperty("App::PropertyString", "BuyURL", "Покупка", "Где купить (ссылка на магазин)")
        o.BuyURL = BUY_URLS.get(o.Name, "")


def short_labels(doc, max_len=45):
    used = {}
    for o in doc.Objects:
        full = _INTENDED.get(o.Name, o.Label)
        cut = min([i for i in (full.find(sp) for sp in _LABEL_SEPS) if i > 0] or [len(full)])
        short = full[:cut].strip() or full
        if len(short) > max_len:                             # длинное без разделителей — по границе слова
            short = short[:max_len].rsplit(" ", 1)[0] + "…"
        base = short
        used[base] = used.get(base, 0) + 1
        if used[base] > 1:
            short = "%s #%d" % (base, used[base])
        note = USER_NOTES.get(o.Name)
        o.Label2 = (note + " | " if note else "") + full
        o.Label = short


# Каждая функция-раздел получает контекст сборки S (state.py). В начале она берёт из него то, что построили
# предыдущие разделы, в конце — кладёт то, что нужно следующим. Порядок разделов — в build.py.


def finalize(S):
    """Пересчёт, профили strut, короткие подписи, ссылки «где купить», скрытие слоёв, вид, сохранение .FCStd."""
    # ── из контекста сборки S: то, что построили предыдущие разделы ──
    doc = S.doc
    doc.recompute()
    apply_strut_profiles(doc)
    doc.recompute()
    short_labels(doc)
    apply_buy_urls(doc)
    hide_default(doc)
    try:                                                      # начальный вид — «приятный угол» Dimitri
        import FreeCADGui as Gui
        if Gui.activeDocument():
            Gui.activeDocument().activeView().setCamera(VIEW_CAMERA)
    except Exception:
        pass
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    doc.saveAs(SAVE_PATH)
