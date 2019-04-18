# coding=utf-8
from loganalysis.const import *
from loganalysis.mesh.tx import TxNbr
from loganalysis.mesh.rx import RxNbr

class Nbr(object):
    def __init__(self, txlog, rxlog, node, nbrid):
        self._nbrid = nbrid
        self._node = node
        if txlog:
            self._txlog = txlog
            self._tx = TxNbr(txlog, node, nbrid)
        if rxlog:
            self._rxlog = rxlog
            self._rx = RxNbr(rxlog, node, nbrid)

    @property
    def nbrid(self):
        return self._nbrid

    @property
    def tx(self):
        return getattr(self, '_tx', None)

    @property
    def rx(self):
        return getattr(self, '_rx', None)
