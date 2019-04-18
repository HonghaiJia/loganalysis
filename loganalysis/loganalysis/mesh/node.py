# coding=utf-8
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from loganalysis.const import *
from loganalysis.mesh.tx import *
from loganalysis.mesh.rx import *
from loganalysis.mesh.nbr import *

class Node(object):
    '''小区实例'''

    def __init__(self, nodeid, log):
        '''初始化小区实例
            根据输入的信息，完成如下事情：
                a) 尝试推断上下行配比,有可能需要用户输入

            Args:
                cellid: 小区Id
        '''
        self._nodeid = nodeid
        self._log = log

        tx_log = log.get_schd_logfile(MESH_FILE_TX, nodeid=nodeid)
        if tx_log is not None:
            self._tx = TxNode(tx_log, self)

        rx_log = log.get_schd_logfile(MESH_FILE_RX, nodeid=nodeid)
        if rx_log is not None:
            self._rx = RxNode(rx_log, self)

        self._nbrs = {}
        self._nbrids = self._get_nbrids()

    @property
    def log(self):
        return self._log

    @property
    def nodeid(self):
        return self._nodeid

    @property
    def nbrids(self):
        return self._nbrids

    @property
    def tx(self):
        return getattr(self, '_tx', None)

    @property
    def rx(self):
        return getattr(self, '_rx', None)

    def _get_nbrids(self):
        '''获取本小区下的所有UEGID'''
        txnbrid = self._tx.log.nbrids if hasattr(self, '_tx') else set()
        rxnbrid = self._rx.log.nbrids if hasattr(self, '_rx') else set()
        return set.union(txnbrid, rxnbrid)

    def get_nbr(self, nbrid=None):
        '''获取小区实例
            Args：
                uegid：如果想查看Log中的所有uegid，那么不用赋值
            Returns:
                如果uegid不为None，返回对应的UE实例，否则返回Log中的所有uegid
        '''
        if nbrid is None:
            return '所有NBRID：{nbrids}. 请使用get_nbr(nbrid)获取对应的NBR实例'.format(nbrids=self._nbrids)

        if nbrid in self._nbrids:
            txlog = self.log.get_schd_logfile(MESH_FILE_TX, self.nodeid, nbrid)
            rxlog = self.log.get_schd_logfile(MESH_FILE_RX, self.nodeid, nbrid)
            self._nbrs[nbrid] = Nbr(txlog, rxlog, self, nbrid)
            return self._nbrs[nbrid]
        else:
            return '非法NbrId值，此邻节点不存在'