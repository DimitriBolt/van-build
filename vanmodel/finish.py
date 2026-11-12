# -*- coding: utf-8 -*-
"""Отделка готового документа: короткие подписи (Label / Label2), ссылки «где купить», скрытые по умолчанию
слои, начальный 3D-вид, сохранение .FCStd."""

import os
import re

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
    r"Toilet_Wheel_\w+": "https://a.co/d/02nt85Aa",   # колёсики 1″ неповоротные, высота 1.15″ (Amazon B0CHFSQHRP)
}


def apply_buy_urls(doc):
    """Всем деталям — свойство BuyURL; заполняется из BUY_URLS (ключ — obj.Name или регулярное выражение на всё имя)."""
    for o in doc.Objects:
        if not o.isDerivedFrom("Part::Feature"):
            continue
        if "BuyURL" not in o.PropertiesList:
            o.addProperty("App::PropertyString", "BuyURL", "Покупка", "Где купить (ссылка на магазин)")
        url = BUY_URLS.get(o.Name)
        if url is None:
            url = next((u for k, u in BUY_URLS.items() if re.fullmatch(k, o.Name)), "")
        o.BuyURL = url


# ─── 2026-11-11 (Dimitri): Label — по-английски (короткое название), Label2 — описание по-русски ───
# (регулярное выражение на всё obj.Name, английская подпись; {1}, {2}… — группы; числа — без ведущих нулей).
# Детали, которых здесь нет, получают подпись из obj.Name («BankRail_Wall» → «Bank Rail Wall»).
EN_LABELS = [
    (r"Scan_Skin", "Body skin (scan)"), (r"Scan_Skin_Body", "Body skin (scan) #2"),
    (r"Frame", "Body frame"), (r"Ribs", "Ribs"), (r"Rib_x(\d+)", "Rib X={1}"),
    (r"Longitudinals", "Body rails along X"), (r"Rail_(pY|nY)_z(\d+)_s(\d)", "Body rail {1} Z={2} #{3}"),
    (r"CorrugatedFloor", "Corrugated floor"), (r"FloorCorrugation_y_(\d+)", "Floor ridge"),
    (r"Pillars", "Door opening pillars"), (r"Pillar_B_slider", "B-pillar (sliding door)"),
    (r"Pillar_Rear_(pY|nY)", "Rear door pillar {1}"),
    (r"HoleMarkers", "Rib mounting points"), (r"Hole_(pY|nY)_x(\d+)_z(\d+)", "Mount point {1} X={2} Z={3}"),
    (r"FactoryThreadedMounts", "Factory threaded points"),
    (r"FactoryThread_(pY|nY)_([a-z]+)_x\d+_z\d+", "Factory thread {1} {2}"),
    (r"FloorBuildup", "Floor"), (r"Floor_XPS", "Floor XPS insulation"), (r"Floor_Plywood", "Floor plywood 1/2″"),
    (r"WheelArches", "Wheel arches"), (r"WheelArch_(pY|nY)", "Wheel arch {1}"),
    (r"DPillars", "D-pillars at floor"), (r"DPillarFace_(pY|nY)_ref", "D-pillar {1}"),
    (r"BodyReliefValves", "Body pressure relief valve"), (r"BodyReliefValve_(pY|nY)", "Pressure relief valve {1}"),
    # кровать
    (r"Bed_StrutFrame", "Bed"), (r"BedPostPlate_(pY|nY)_(rear|front)", "Bed post plate {1} {2}"),
    (r"BedPostBodyBolt_(pY|nY)_(rear|front)", "Bed post body bolt {1} {2}"),
    (r"BedPost_(pY|nY)_(rear|front)", "Bed post {1} {2}"), (r"BedSideRail_(pY|nY)", "Bed side rail {1}"),
    (r"BedCross_(\d)", "Bed crossbar #{1}"), (r"BedDeck", "Bed deck"), (r"BedMattress", "Mattress"),
    (r"BedWallLedger2x4", "Wall ledger 2x4"), (r"BedWallPanel", "Wall plywood above deck"),
    # этажерка батарей и электрика
    (r"BatteryBank", "Battery rack (4 x 150 Ah)"), (r"Battery_B(\d)", "Battery B{1}"),
    (r"BankPostPlate_(\w+)", "Rack post plate {1}"), (r"BankPost_(\w+)", "Rack post {1}"),
    (r"BankRailBolt_(\w+)", "Rail bolt 3/8″ {1}"), (r"BankRail_Wall", "Rack rail (wall side)"),
    (r"BankRail_Inner", "Rack rail (aisle side)"), (r"BankCross_(Rear|Front)", "Rack crossbar {1}"),
    (r"BankShelf", "Battery shelf"), (r"BankStop_ShelfRear", "Battery stop (rear)"),
    (r"BankStop_ShelfFront", "Battery stop (front)"), (r"BankWedge_B1Arch", "Wedge B1 / arch"),
    (r"BankArchPad_(\d)", "Arch pad {1}"), (r"BankHolddown_B1", "B1 hold-down"),
    (r"Electrical", "Electrical at batteries"), (r"Elec_Board", "Electrical board"),
    (r"Elec_MPPT", "MPPT solar controller"), (r"Elec_DCDC", "DC-DC charger 60 A"), (r"Elec_FuseBlock", "Fuse block"),
    (r"Elec_BusPos", "Busbar +"), (r"Elec_BusNeg", "Busbar −"), (r"Elec_GroundStud", "Ground stud"),
    (r"Cable_batteries", "Battery cable harness"), (r"Cable_alternator", "Alternator cable"),
    (r"Cable_solar", "Solar cable"), (r"Cable_ground", "Ground cable"),
    # бак воды
    (r"TankFloor", "Water tank"), (r"TankFloor_Mat", "Rubber mat under tank"), (r"WaterTank_(\w+)", "Water tank {1}"),
    (r"TankFloor_Fitting_(\d)", "Tank fitting {1}"), (r"TankFloor_Cleat_(\w+)", "Tank cleat 2x2 ({1})"),
    (r"TankFloor_ArchSpacer_(\d)", "Arch spacer {1}"), (r"TankFloor_Strap_(\d)", "Tank strap {1}"),
    (r"TankFloor_Anchor_(\w+)", "Strap anchor {1}"), (r"Water_Pump12V", "Water pump 12V + filter"),
    # душ, туалет
    (r"Shower", "Shower"), (r"Shower_Pan", "Shower pan 32x32x4″"), (r"Shower_Drain", "Shower drain"),
    (r"Shower_DrainTrap", "Drain trap 1-1/2″"), (r"Shower_WallRear", "Shower rear wall"),
    (r"Shower_DripLedge", "Drip ledge"), (r"Shower_CurtainLower", "Lower curtain"),
    (r"Shower_WallBack", "Shower side wall"), (r"Shower_GasHeater", "Gas water heater Camplux"),
    (r"Shower_GasHeater_Knob(\d)", "Heater knob {1}"), (r"Shower_Flue", "Heater flue 3″"),
    (r"Shower_FlueCap", "Flue roof cap"), (r"Shower_FlueThimble", "Flue ceiling thimble"),
    (r"Shower_Ceiling", "Shower ceiling"), (r"Shower_Curtain", "Shower curtain"), (r"Shower_CurtainRod", "Curtain rod"),
    (r"Shower_Head", "Shower head"), (r"Shower_ExhaustFan", "Exhaust fan 12V"),
    (r"Toilet_Plate", "Toilet floor plate"), (r"Toilet_Platform", "Toilet platform"),
    (r"Toilet_Wheel_F(\w)", "Front wheel {1}"), (r"Toilet_Wheel_R(\w)", "Rear wheel {1}"),
    (r"Toilet_PlatformDam", "Platform dam"), (r"Toilet_Camco", "Toilet SEAFLO 2.6 gal"),
    # кухня
    (r"Kitchen", "Kitchen"), (r"Kitchen_Carcass", "Kitchen carcass"), (r"Kitchen_Plinth", "Kitchen plinth"),
    (r"Kitchen_Countertop", "Countertop 1″"), (r"Kitchen_Sink", "Bar sink 10x10″"), (r"Kitchen_Faucet", "Faucet"),
    (r"Kitchen_Kettle", "Electric kettle"), (r"Kitchen_Outlet", "Outlet 120V + USB"),
    (r"Kitchen_Fridge", "Fridge BougeRV CRX3 23 qt"), (r"Kitchen_FridgeSlide", "Fridge slide"),
    (r"Kitchen_DoorSink", "Door under sink"), (r"Kitchen_DoorUpper", "Upper cabinet door"),
    (r"Kitchen_UpperCabinet", "Upper cabinet"), (r"Kitchen_FlapBracket(\d)", "Folding bracket {1}"),
    (r"Kitchen_FlapBracketOpen(\d)", "Folding bracket {1} (open)"), (r"Kitchen_Flap", "Fold-out countertop"),
    (r"Kitchen_FlapOpen", "Fold-out countertop (open)"),
    # пропан, газ, датчики
    (r"Propane_Locker", "Propane locker"), (r"Propane_LockerDoor", "Propane locker door"),
    (r"Propane_Vent", "Locker vent tube 1″"), (r"Propane_Cylinder", "Propane cylinder 20 lb"),
    (r"Propane_Regulator", "Propane regulator"), (r"Gas_Line", "Gas line"), (r"Gas_Bulkhead", "Gas bulkhead fitting"),
    (r"Safety_LPCO", "LP + CO detector"), (r"Safety_CO_Bed", "CO detector at bed"),
    # багажник
    (r"TrunkShelf", "Trunk"), (r"Trunk2_PlateP3m", "Post plate P3m"), (r"Trunk2_PostP3mBolt", "Bolt 3/8″ P3m"),
    (r"Trunk2_PostP3m", "Post P3m"), (r"Trunk2_SpinePlate_(\d)", "Spine post plate {1}"),
    (r"Trunk2_SpinePost_(\d)", "Spine post {1}"), (r"Trunk2_SlidePass", "Slide 44″ (passenger side)"),
    (r"Trunk2_SlideSpine", "Slide 44″ (spine side)"), (r"Trunk1_SlidePass", "Slide 36″ (passenger side)"),
    (r"Trunk1_SlideSpine", "Slide 36″ (spine side)"), (r"Trunk(\d)_P3Shim", "Slide shim 4 mm (level {1})"),
    (r"Trunk2_Shelf", "Upper trunk shelf"), (r"Trunk2_ShelfBolt_(\w+)", "Shelf cleat bolt {1}"),
    (r"Trunk2_ShelfCleat_(\w+)", "Shelf cleat {1}"), (r"Trunk2_TrayFwd", "Upper drawer (slides forward)"),
    (r"Trunk2_TrayFwd_Out", "Upper drawer (open)"), (r"Trunk1_Drawer", "Lower drawer (slides rearward)"),
    (r"Trunk1_Drawer_Out", "Lower drawer (open)"),
    # шкафчики, проёмы
    (r"WallCabinets", "Ceiling cabinets"), (r"CabPass_(\d)", "Cabinet passenger {1}"),
    (r"CabPass_(\d)_Door", "Cabinet passenger {1} door"), (r"CabDrv_(\d)", "Cabinet driver {1}"),
    (r"CabDrv_(\d)_Door", "Cabinet driver {1} door"),
    (r"Openings", "Door openings"), (r"Opening_SlidingDoor", "Sliding door opening"),
    (r"Opening_RearDoors", "Rear doors opening"), (r"RearDoorLeaf_Driver", "Rear door leaf (driver)"),
    (r"RearDoorLeaf_Passenger", "Rear door leaf (passenger)"),
]


def english_label(name):
    """Английская короткая подпись детали по её obj.Name."""
    for pat, fmt in EN_LABELS:
        m = re.fullmatch(pat, name)
        if m:
            gs = [(str(int(g)) if g.isdigit() else {"pY": "driver", "nY": "passenger"}.get(g, g)) for g in m.groups()]
            return fmt.format(None, *gs) if gs else fmt
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name.replace("_", " ")).strip()


def short_labels(doc, max_len=45):
    """Label — короткое название по-английски (EN_LABELS), Label2 — полное описание по-русски (+ заметки Dimitri)."""
    used = {}
    for o in doc.Objects:
        full = _INTENDED.get(o.Name, o.Label)
        short = english_label(o.Name)
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
