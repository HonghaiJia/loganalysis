# coding=utf-8
from loganalysis.const import *
from .dlschd import DlSchdUe

from loganalysis.lte.ulschd import UlSchdUe


class Ue(object):
    def __init__(self, ullog, dllog, cell, uegid):
        self._uegid = uegid
        self._cell = cell
        if dllog:
            self._dllog = dllog
            self._dl = DlSchdUe(dllog, cell, uegid)
        if ullog:
            self._ullog = ullog
            self._ul = UlSchdUe(ullog, cell, uegid)

    @property
    def uegid(self):
        return self._uegid

    @property
    def dl(self):
        return getattr(self, '_dl', None)

    @property
    def ul(self):
        return getattr(self, '_ul', None)
