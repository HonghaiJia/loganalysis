# coding=utf-8
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loganalysis.const import *

class Tx():
    '''下行调度分析类'''

    def __init__(self, log, node, nbrid=None):
        self._type = MESH_FILE_TX
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

    def show_amc(self, airtime_bin_size=1000):
        '''画图描述指定粒度下的调度RB数

            Args:
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                趋势图：x轴为时间粒度，y轴为平均std_mcs，delta, bler
        '''
        cols = ['E_AMC_INFO.u8StdMcs', 'E_AMC_INFO.u8InnerMcs', 'E_AMC_INFO.s16DeltaMcs']

        mean_data = self._log.mean_of_cols(cols, airtime_bin_size=airtime_bin_size, by='cnt', time_col='AirTime')
        fig, ax = plt.subplots(3, 1, sharex=True)
        #data = mean_data.dropna(how='any', axis=1)
        stdmcs = mean_data[cols[0]]
        ax[0].set_ylim([0, 30])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[0].set_xlabel(xlabel)
        ax[0].set_ylabel('Std_Mcs')
        stdmcs.plot(ax=ax[0], kind='line', style='o--')

        innermcs = mean_data[cols[1]]
        ax[1].set_ylim([0, 30])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[1].set_xlabel(xlabel)
        ax[1].set_ylabel('Inner_Mcs')
        innermcs.plot(ax=ax[1], kind='line', style='o--')

        delta = mean_data[cols[2]] / 100
        ax[2].set_ylim([-30, 30])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[2].set_xlabel(xlabel)
        ax[2].set_ylabel('Delta')
        delta.plot(ax=ax[2], kind='line', style='o--')

        plt.show()

    def show_tx_cnt(self, airtime_bin_size=1000, filters=None):
        '''画图描述指定粒度下的调度UE次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                直方图（kde）：x轴调度UE数，y轴为比例
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        col_name = r'E_TX_HARQ_INFO.u8Pid'
        self._log.show_trend(col_name, AGG_FUNC_CNT, airtime_bin_size, filters=filters, y_label='TxCnt')
        return

class TxNode(Tx):
    '''下行调度分析类'''

    def __init__(self, log, node):
        super(TxNode, self).__init__(log, node)

class TxNbr(Tx):
    '''下行调度UE分析类'''

    def __init__(self, log, node, nbrid):
        super(TxNbr, self).__init__(log, node, nbrid)
        self._nbrid = nbrid

