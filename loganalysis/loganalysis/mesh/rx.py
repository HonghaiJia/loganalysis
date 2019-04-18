# coding=utf-8
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loganalysis.const import *

class Rx():
    '''下行调度分析类'''

    def __init__(self, log, node, nbrid=None):
        self._type = MESH_FILE_RX
        self._log = log
        self._id_filter = {}
        self._node = node
        self._id_filter['NodeId'] = [node.nodeid]
        if nbrid is not None:
            self._id_filter['NbrId'] = [nbrid]

    @property
    def type(self):
        return self._type

    @property
    def log(self):
        return self._log

    def show_rx_cnt(self, airtime_bin_size=1000, filters=None):
        '''画图描述指定粒度下的调度UE次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                直方图（kde）：x轴调度UE数，y轴为比例
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        col_name = r'E_PCCH.u8NodeId'
        self._log.show_trend(col_name, AGG_FUNC_CNT, airtime_bin_size, filters=filters, y_label='RxCnt')
        return

class RxNode(Rx):
    '''下行调度分析类'''

    def __init__(self, log, node):
        super(RxNode, self).__init__(log, node)

class RxNbr(Rx):
    '''下行调度UE分析类'''

    def __init__(self, log, node, nbrid):
        super(RxNbr, self).__init__(log, node, nbrid)
        self._nbrid = nbrid
