"""Профиль V-Slot 2020 (20 × 20 мм) для вариантов с профилем вместо strut: одиночный профиль, вдоль X / Y / Z, сдвоенный (2 друг на друге)."""
import FreeCAD as App
import Part

V = App.Vector


def vslot_2020(x0, y0, z0, z1):
    """Профиль V-Slot 2020 (20 × 20 мм, SeekLiny / европейский стандарт) от z0 до z1; (x0, y0) — угол в плане.
    Сечение приближённо по чертежу продавца: 4 паза (раскрытие 6.2, полость 11 мм, стенка 1.5), центральное отверстие ⌀4.2."""
    cx, cy = x0 + 10.0, y0 + 10.0
    ext = V(0, 0, z1 - z0)
    solid = Part.makeBox(20.0, 20.0, z1 - z0, V(x0, y0, z0))
    solid = solid.cut(Part.makeCylinder(2.1, z1 - z0, V(cx, cy, z0)))
    pts = [(-3.1, 0.0), (3.1, 0.0), (3.1, 1.8), (5.5, 1.8), (5.5, 3.2), (3.2, 5.9), (-3.2, 5.9), (-5.5, 3.2), (-5.5, 1.8), (-3.1, 1.8)]
    wire = Part.makePolygon([V(cx + u, y0 + v, z0 - 1.0) for u, v in pts] + [V(cx - 3.1, y0, z0 - 1.0)])
    slot = Part.Face(wire).extrude(V(0, 0, z1 - z0 + 2.0))
    for k in range(4):
        sl = slot.copy()
        sl.rotate(V(cx, cy, z0), V(0, 0, 1), 90.0 * k)
        solid = solid.cut(sl)
    return solid


def vslot_y(x0, y0, y1, z0):
    """Профиль 2020 вдоль Y: X — x0..x0+20, Y — y0..y1, Z — z0..z0+20."""
    sh = vslot_2020(0.0, 0.0, 0.0, y1 - y0)
    sh.rotate(V(0, 0, 0), V(1, 0, 0), -90.0)                          # Z → +Y, Y → −Z
    sh.translate(V(x0, y0, z0 + 20.0))
    return sh


def vslot_x(x0, x1, y0, z0):
    """Профиль 2020 вдоль X: X — x0..x1, Y — y0..y0+20, Z — z0..z0+20."""
    sh = vslot_2020(0.0, 0.0, 0.0, x1 - x0)
    sh.rotate(V(0, 0, 0), V(0, 1, 0), 90.0)                           # Z → +X, X → −Z
    sh.translate(V(x0, y0, z0 + 20.0))
    return sh


def vslot_z(x0, y0, z0, z1):
    """Профиль 2020 вертикально: (x0, y0) — угол в плане."""
    return vslot_2020(x0, y0, z0, z1)


def stack_x(x0, x1, y0, z0, n=2):
    """n профилей 2020 друг на друге вдоль X: общий габарит X x0..x1, Y y0..y0+20, Z z0..z0+20n; возвращает компаунд."""
    return Part.makeCompound([vslot_x(x0, x1, y0, z0 + 20.0 * k) for k in range(n)])


def stack_y(x0, y0, y1, z0, n=2):
    """n профилей 2020 друг на друге вдоль Y: X x0..x0+20, Y y0..y1, Z z0..z0+20n."""
    return Part.makeCompound([vslot_y(x0, y0, y1, z0 + 20.0 * k) for k in range(n)])


def drill_y(shape, x, z, y0, y1, d):
    """Отверстие ⌀d вдоль Y в точке (x, z), от y0 до y1."""
    return shape.cut(Part.makeCylinder(d / 2.0, y1 - y0, V(x, y0, z), V(0, 1, 0)))
