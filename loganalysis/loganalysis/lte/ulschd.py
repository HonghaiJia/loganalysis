# coding=utf-8
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loganalysis.const import *


class UlSchd():
    '''上行调度Log分析类'''

    def __init__(self, log, cell, uegid=None):
        self._type = LTE_FILE_ULSCHD
        self._log = log
        self._id_filter = {}
        self._cell = cell
        self._id_filter['CellId'] = [cell.cellid]
        if uegid is not None:
            self._id_filter['UEGID'] = [uegid]

    @property
    def type(self):
        return self._type

    @property
    def log(self):
        return self._log

    def show_bler(self, airtime_bin_size=1000, ax=None):
        ack_cols = ['CRCI.u32DemTime', 'CRCI.u8AckInfo']
        rlt = pd.DataFrame()
        for data in self._log.gen_of_cols(ack_cols):
            data = data.dropna(how='any')
            if 0 == data.size:
                continue
            cnt = data[ack_cols[1]].groupby(data[ack_cols[0]].map(self._log.dectime) // airtime_bin_size)\
                .apply(lambda x: x.value_counts()).unstack(level=1)
            rlt = rlt.add(cnt, fill_value=0, level=0)

        def func(data):
            return (data[0] + data[2]) / ((data[0]+data[1]+data[2])+1)
        bler_data = rlt.reindex(columns=[0, 1, 2], fill_value=0).apply(func, axis=1)

        if ax is None:
            ax = plt.subplots(1, 1)[1]
        ax.set_ylabel('Bler')
        ax.set_ylim([0, 1])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        bler_data.index.name = xlabel
        bler_data.plot(ax=ax, kind='line', style='o--')

    def show_amc(self, airtime_bin_size=1000):
        '''画图描述指定粒度下的调度RB数

            Args:
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                趋势图：x轴为时间粒度，y轴为平均1rb_sinr, pl, delta, bler
        '''
        cols = ['PUSCH_SINR.s16SingleRbSINR', 'AMC.s16DeltaMcs', 'AMC.u8StdMcs']
        mean_data = self._log.mean_of_cols(cols, airtime_bin_size=airtime_bin_size, by='cnt', time_col='AirTime')
        fig, ax = plt.subplots(4, 1, sharex=True)

        delta = mean_data[cols[1]] / 100
        ax[0].set_ylabel('Delta')
        ax[0].set_ylim([-28, 28])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[0].set_xlabel(xlabel)
        delta.plot(ax=ax[0], kind='line', style='o--')

        stdmcs = mean_data[cols[2]]
        ax[1].set_ylabel('Std_mcs')
        ax[1].set_ylim([0, 29])
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[1].set_xlabel(xlabel)
        stdmcs.plot(ax=ax[1], kind='line', style='o--')

        singlerb_sinr = mean_data[cols[0]]
        ax[2].set_ylabel('1Rb_Sinr')
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        ax[2].set_xlabel(xlabel)
        singlerb_sinr.plot(ax=ax[2], kind='line', style='o--')

        self.show_bler(airtime_bin_size=airtime_bin_size, ax=ax[3])
        return

    def show_schd_uecnt(self, airtime_bin_size=1000):
        '''画图描述指定粒度下的调度UE次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                直方图（kde）：x轴调度UE数，y轴为比例
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        col_name = r'GRANT.u8HarqId'
        self._log.show_trend(col_name, AGG_FUNC_CNT, airtime_bin_size)
        return

    def show_schd_rbnum(self, airtime_bin_size=1000):
        '''画图描述指定粒度下的调度RB数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                直方图（kde）：x轴调度RB数，y轴为调度次数
                趋势图：x轴为时间粒度，y轴为平均RB数
        '''
        col_name = r'GRANT.u8RbNum'
        self._log.show_trend(col_name, AGG_FUNC_MEAN, airtime_bin_size, mean_by='time')
        #self._log.show_hist(col_name, xlim=[0, 100])
        return
        
    def show_rpt_minbsr(self, lchgrp=3, airtime_bin_size=1000):
        '''画图描述指定粒度下的report bsr

            Args:
                lchgrp: 待分析字段
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                趋势图：x轴为时间粒度，y轴为平均RB数
        '''
        col_name = r'BSR.u32LchGrpBsr'
        filters = {r'BSR.u32LchGrpId': [lchgrp]}
        self._log.show_trend(col_name, AGG_FUNC_MIN, airtime_bin_size, filters=filters)
        return
        
    def show_rpt_maxbsr(self, lchgrp=3, airtime_bin_size=1000):
        '''画图描述指定粒度下的report bsr

            Args:
                lchgrp: 待分析lchgrpId
                airtime_bin_size：统计粒度，默认为1000ms
            Returns：
                趋势图：x轴为时间粒度，y轴为平均RB数
        '''
        col_name = r'BSR.u32LchGrpBsr'
        filters = {r'BSR.u32LchGrpId': [lchgrp]}
        self._log.show_trend(col_name, AGG_FUNC_MAX, airtime_bin_size, filters=filters)
        return
        
    def show_rpt_bsr(self, lchgrp=3):
        '''画图描述report bsr

            Args:
                lchgrp: 待分析lchgrpId
            Returns：
                趋势图：x轴为时间粒度，y轴为平均RB数
        '''
        col = ['AirTime', r'BSR.u32LchGrpId', r'BSR.u32LchGrpBsr']
        filters = {r'BSR.u32LchGrpId': [lchgrp]}
        rpt_bsr = self._log.get_data_of_cols(cols=col, val_filter=filters)
        rpt_bsr = rpt_bsr.set_index(col[0])[col[2]]
        rpt_bsr.plot()
        return

    def schdfail_reasons(self):
        '''汇总调度失败原因
        
            Args：
                无
            Returns：
                所有失败原因的总数以及所占比例
        '''
        col = ['SCHD_FAIL_RSN.u32UeSchdFailRsn']
        rlt = pd.Series(name='SchdFail_Cnt')
        for data in self._log.gen_of_cols(col):
            data = data[col[0]].dropna().astype(np.int32).value_counts()
            rlt = rlt.add(data, fill_value=0) if rlt is not None else data
        rlt.index = [LTE_SCHD_FAIL_RSNS[int(idx)] for idx in rlt.index]
        rlt.index.name = 'Fail_Rsn'
        return rlt

    def _get_schdtime(self, demtime):
        '''给定解调时间，获取下行调度时间'''
        return self._log.difftime(demtime, self._cell._schd_subfrm_offset[demtime % 16])

    def match_schd_and_ack(self, cols):
        '''
        根据UEGID，HarqId匹配调度和Ack反馈信息

        Args：
            无
        Yields:
            对齐后的数据，生成器
        '''
        demcols = ['FN', 'UEGID', 'CRCI.u8CrcHarqId']
        schdcols = ['AirTime', 'UEGID', 'GRANT.u8HarqId']
        totcols = list(set(['CRCI.u32DemTime']+demcols+schdcols+cols))
        for data in self._log.gen_of_cols(totcols):
            data['FN'] = data['CRCI.u32DemTime'].dropna().astype(np.uint32).map(self._get_schdtime)
            addcols = [col for col in cols if col.startswith('CRCI')]
            matchcols = np.union1d(addcols, demcols)
            ackdata = data[matchcols]
            data = data.drop(np.setdiff1d(matchcols, ['UEGID']), axis=1)
            merged = pd.merge(data, ackdata, how='left', left_on=schdcols, right_on=demcols)
            yield merged[cols]

    def bler_of_mcs(self):
        '''不同mcs下的bler'''
        cols = ['CRCI.u8AckInfo', 'TB.u8Mcs']
        ack_data = pd.DataFrame()
        for data in self.match_schd_and_ack(cols):
            data = data.dropna(how='any').astype(np.uint32)
            grouped = data[cols[0]].groupby(data[cols[1]]).apply(lambda x: x.value_counts()).unstack(0, fill_value=0)\
                .reindex(index=[0, 1, 2], fill_value=0)
            ack_data = ack_data.add(grouped, fill_value=0)
        bler = ack_data.apply(lambda x: (x[2]+x[0])/max(x.sum(), 1))
        bler.index.name = 'Mcs'
        bler.name = 'Bler_of_Mcs'
        return bler

    def bler_of_mu(self):
        '''sdma或者Mu统计

           a）正常调度bler
           b）配对bler
        '''
        cols = ['CRCI.u8AckInfo', 'GRANT.u8MatchType']
        ack_data = pd.DataFrame()
        for data in self.match_schd_and_ack(cols):
            grouped = data[cols[0]].groupby(data[cols[1]]).apply(lambda x: x.value_counts()).unstack(0, fill_value=0)\
                .reindex(index=[0, 1, 2], fill_value=0)
            ack_data = ack_data.add(grouped, fill_value=0)
        bler_data = ack_data.apply(lambda x: (x[0]+x[2])/max(x.sum(), 1))
        bler_data.index.name = 'IsMu'
        bler_data.name = 'Bler_of_Mu'
        return bler_data

    def bler_of_subfrm(self):
        '''不同子帧下的bler'''
        cols = ['CRCI.u8AckInfo', 'CRCI.u32DemTime']
        ack_data = pd.DataFrame()
        for data in self._log.gen_of_cols(cols):
            data = data.dropna(how='any').astype(np.uint32)
            grouped = data[cols[0]].groupby(data[cols[1]] % 16).apply(lambda x: x.value_counts())\
                .unstack(0, fill_value=0).reindex(index=np.arange(10), fill_value=0)
            ack_data = ack_data.add(grouped, fill_value=0)
        bler_data = ack_data.apply(lambda x: (x[0]+x[2])/max(x.sum(), 1))
        bler_data.index.name = 'Subfrm'
        bler_data.name = 'Bler_of_Subfrm'
        return bler_data

    def find_selfmaintain(self):
        '''查找是否存在自维护, 并输出相关信息'''

        cols = ['UEGID', 'CRCI.u32DemTime', 'CRCI.u8CrcHarqId', 'CRCI.b8IsSelfMainTain']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            rlt = rlt.append(data[data[cols[3]] == 1])
        return rlt

    def find_harqfail(self):
        '''查找是否存harqfail, 并输出相关信息'''

        cols = ['UEGID', 'CRCI.u32DemTime', 'CRCI.u8CrcHarqId', 'CRCI.b8IsHarqFail']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            rlt = rlt.append(data[data[cols[3]] == 1])
        return rlt

    def find_dci0lost(self):
        '''查找是否存dci0lost, 并输出相关信息'''

        cols = ['UEGID', 'CRCI.u32DemTime', 'CRCI.u8CrcHarqId', 'CRCI.u8DciLostFlag']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            data = data[data[cols[3]] == 1]
            rlt = rlt.append(data)
        return rlt

    def why_selfmaintain(self):
        '''分析自维护原因

            Args：
                无
            return：
                demtime, uegid：reason 列表
        '''
        cols = ['CRCI.u32DemTime', 'UEGID']
        selfdata = self.find_selfmaintain()[cols].drop_duplicates().astype(np.uint32)
        ulcrcdem_mismatch = self._cell.find_ulcrcdem_mismatch()
        pusch_mismatch = self._cell.find_pusch_mismatch()

        for idx in selfdata.index:
            mismatchs = [ulcrcdem_mismatch, pusch_mismatch]
            reasons = ['ulcrcdem_mismatch', 'pusch_mismatch']
            for reanson_idx, mismatch in enumerate(mismatchs):
                mismatch_cols = mismatch.columns  # 默认解调时间都在第一个位置
                mask = (mismatch[mismatch_cols[0]] == selfdata.at[idx, cols[0]])\
                       & (mismatch[cols[1]] == selfdata.at[idx, cols[1]])
                ack_filter = mismatch[mask]
                if len(ack_filter.index) != 0:
                    selfdata.loc[idx, 'Reason'] = reasons[reanson_idx]
                    break
        return selfdata


class UlSchdCell(UlSchd):
    '''上行调度Log分析类'''

    def __init__(self, log, cell):
        super(UlSchdCell, self).__init__(log, cell)

    def infer_uldlcfgidx(self):
        '''推测上下行配比

            根据调度信息以及ACK反馈时序推测上下行配比，目前只支持0,1,2,7共4中配比推测。

            Args:
                无
            Return：
                255：推测失败
                其他：推测的配比
        '''
        schdcols = ['UEGID', 'AirTime', 'GRANT.u8HarqId']
        ackcols = ['UEGID', 'CRCI.u32DemTime', 'CRCI.u8CrcHarqId']
        data = next(self._log.gen_of_cols(schdcols + ackcols[1:]))[:400]
        ackdata = data[ackcols].dropna(how='any').astype(np.uint32)
        schddata = data[schdcols].dropna(how='any').astype(np.uint32)

        def get_deminfo_idx(schdidx, uegid, airtime, harqid):
            for idx in ackdata.index:
                if idx <= schdidx:
                    continue
                if ackdata.at[idx, ackcols[0]] == uegid and ackdata.at[idx, ackcols[2]] == harqid:
                    demtime = ackdata.at[idx, ackcols[1]]
                    if self._log.difftime(demtime, airtime) < 32:
                        return idx
                    else:
                        return -1
            return -1

        ack_table = np.zeros((10, 10))
        for idx in schddata.index:
            if schddata.at[idx, 'GRANT.u8HarqId'] > 7:
                return 7

            ackidx = get_deminfo_idx(idx, *schddata.loc[idx, schdcols])
            if -1 == ackidx:
                continue

            ackfrm = ackdata.at[ackidx, 'CRCI.u32DemTime'] % 16
            subfrm = schddata.at[idx, 'AirTime'] % 16
            if ack_table[subfrm][ackfrm] == 1:
                continue
            ack_table[subfrm][ackfrm] += 1
            if ack_table[8][2] != 0 or ack_table[3][7]:  # 配比2
                return 2
            elif ack_table[9][4] != 0 or ack_table[4][9] != 0 or ack_table[5][2] != 0 \
                    or ack_table[9][4] != 0 or ack_table[6][3] != 0:
                return 0
            elif ack_table[1][7] != 0 or ack_table[6][2] != 0 or ack_table[4][8] != 0 \
                    or ack_table[9][3] != 0:
                return 1
            elif ack_table[0][4] != 0 or ack_table[0][5] != 0 or ack_table[0][6] != 0 \
                    or ack_table[1][9] != 0 or ack_table[1][2] != 0 or ack_table[1][3] != 0:
                return 7

            return 255

    def merge_with_pusch(self, ulschd_file, pusch_file):
        '''与PUSCH文件合并

            根据UEGID，PUSCH空口时间字段合并Pusch和ulschd log

            Args:
                 pusch_file：Ulphy pusch Log文件名

            Return：
                 result：合并后的数据，格式为DataFrame
        '''
        schddata = pd.read_csv(ulschd_file, na_values='-')
        puschdata = pd.read_csv(pusch_file, na_values='-')
        ulschdcol = ['UEGID', 'CRCI.u32DemTime']
        puschcol = ['UEGID', 'AirTime']
        merged = pd.merge(schddata, puschdata, left_on=ulschdcol, right_on=puschcol, how='left')
        return merged


class UlSchdUe(UlSchd):
    '''上行调度UE分析类'''

    def __init__(self, log, cell, uegid):
        super(UlSchdUe, self).__init__(log, cell, uegid)
        self._uegid = uegid
