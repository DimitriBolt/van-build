# -*- coding: utf-8 -*-
"""Контекст сборки S — то, что разделы модели передают друг другу.

Модель строится по разделам (vanmodel/build.py → STAGES). Раздел — обычная функция `раздел(S)`:
    • в начале берёт из S то, что построили предыдущие разделы:      doc, floor_top = S.doc, S.floor_top
    • в конце кладёт в S то, что понадобится следующим:               S.put(locals(), "bed_summary z_rail_top")
Так для каждого раздела явно видно, от чего он зависит и что отдаёт дальше.

После сборки контекст остаётся в vanmodel.build.LAST — удобно посмотреть в консоли FreeCAD:
    from vanmodel import build; build.LAST.floor_top
"""


class NotBuilt(object):
    """«Этого нет»: раздел, который создаёт значение, отключён в params.py или ещё не выполнялся.

    Само по себе не мешает (раздел, которому оно не нужно, его и не тронет), но любая попытка
    им воспользоваться — ошибка с понятным именем, а не тихо неверная геометрия."""
    __slots__ = ("_name",)

    def __init__(self, name):
        object.__setattr__(self, "_name", name)

    def _fail(self, *args, **kwargs):
        raise NameError("«%s» не построено: раздел, который его создаёт, отключён или ещё не выполнялся "
                        "(порядок разделов — vanmodel/build.py)" % object.__getattribute__(self, "_name"))

    def __getattr__(self, attr):
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        self._fail()

    __call__ = __getitem__ = __setitem__ = __iter__ = __len__ = __bool__ = __contains__ = _fail
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = _fail
    __neg__ = __abs__ = __float__ = __int__ = __index__ = __lt__ = __le__ = __gt__ = __ge__ = _fail

    def __repr__(self):
        return "<не построено: %s>" % object.__getattribute__(self, "_name")


class State(object):
    """Контекст одной сборки модели (создаётся в build.build())."""

    def __getattr__(self, name):                    # вызывается, только когда такого атрибута ещё нет
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return NotBuilt(name)

    def put(self, local_vars, names):
        """Положить в контекст перечисленные имена из locals() раздела (те, что реально появились)."""
        for n in names.split():
            if n in local_vars and not isinstance(local_vars[n], NotBuilt):
                setattr(self, n, local_vars[n])
