# coding=utf-8
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loganalysis.const import *


class DlSchd():
    '''下行调度分析类'''

    def __init__(self, log, cell, uegid=None):
        self._type = LTE_FILE_DLSCHD
        self._log = log
        self._id_filter = {}
        self._cell = cell
        if cell:
            self._id_filter['CellId'] = [cell.cellid]
        if uegid:
            self._id_filter['UEGID'] = [uegid]

    @property
    def type(self):
        return self._type

    @property
    def log(self):
        return self._log

    def bler_of_subframe(self, airtime_bin_size=1, subframe = 255):
        '''计算指定时间粒度下特定子帧的bler,按照传输方案分别计算

            Args:
                airtime_bin_size：统计粒度，默认为1s
                subfrm: 255(不区分子帧), <10(特定subframe)
            Returns：
                bler， DataFrame格式，列为传输方案，行为时间
        '''
        ack_cols = ['ACK.u32DemTime', 'ACK.u8Tb0AckInfo', 'ACK.u8Tb1AckInfo']
        rlt = pd.DataFrame()
        for data in self._log.gen_of_cols(ack_cols):
            data = data.dropna(how='any').astype(np.uint32)
            if subframe < 10:
                data = data[data[ack_cols[0]]%16 == subframe]
            if 0 == data.size:
                continue
            ack_sum = data[ack_cols[1]] + data[ack_cols[2]]
            cnt = ack_sum.groupby(data[ack_cols[0]] // (airtime_bin_size*1600)).apply(
                lambda x: x.value_counts()).unstack(level=1)
            rlt = rlt.add(cnt, fill_value=0)

        def func(data):
            temp = pd.Series()
            temp.at['TxDiv'] = (data[255] + data[257]) / (data[255] + data[256] + data[257] + 1)
            temp.at['Cdd'] = (data[0] * 2 + data[4] * 2 + data[1]) / \
                             ((data[0] * 2 + data[1] + data[2] + data[4]) * 2 + 1)
            return temp

        return rlt.reindex(columns=[0, 1, 2, 4, 255, 256, 257]).fillna(0).apply(func, axis=1)

    def show_mimo(self, airtime_bin_size=1):
        '''图形化输出MIMO自适应信息

            Args:
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                趋势图：x轴为时间粒度，y轴为各传输方案比例
        '''

        cols = ['SCHD.u8TranScheme']
        ratio = self._log.hist_of_col(cols[0], airtime_bin_size=airtime_bin_size, ratio=True)
        ratio = ratio.reindex(columns=[0, 1, 2], fill_value=0)
        idxs = ['1_Port', 'Tx_div', 'Cdd']
        ratio.columns = ratio.columns.map(lambda x: idxs[x])

        ax = plt.subplots(1, 1)[1]
        xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Ratio')
        ratio.plot(ax=ax, kind='line', style='o--')

    def show_amc_txdiv(self, airtime_bin_size=1):
        '''画图描述指定粒度下的调度txdiv_Mcs

            Args:
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                趋势图：x轴为时间粒度，y轴为平均std_mcs，delta
        '''
        cols = ['AMC_DIV.s16TxDivDeltaMcs', 'AMC_DIV.u8TxDivStdMcs']
        data = self._log.mean_of_cols(cols, airtime_bin_size=airtime_bin_size, by='cnt', time_col='AirTime')
        if 0 == data.size:
            print('No Data to analysis of columns: [{0}, {1}]'.format(cols[0], cols[1]))
            return
        data[cols[0]] = data[cols[0]]/100
        #xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        data.plot(kind='line', style='o--', ylim=[-28,28])
            
    def show_amc_cdd(self, airtime_bin_size=1):
        '''画图描述指定粒度下的调度cdd_Mcs

            Args:
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                趋势图：x轴为时间粒度，y轴为平均std_mcs，delta
        '''
        cols = ['AMC_CDD.s16CddDeltaMcs', 'AMC_CDD.u8CddStdMcs']
        data = self._log.mean_of_cols(cols, airtime_bin_size=airtime_bin_size, by='cnt', time_col='AirTime')
        if 0 == data.size:
            print('No Data to analysis of columns: [{0}, {1}]'.format(cols[0], cols[1]))
            return
        data[cols[0]] = data[cols[0]]/100
        data.plot(kind='line', style='o--', ylim=[-28,28])

 
    def show_bler_of_subframe(self, airtime_bin_size=1, subframe = 255, ax=None):
        '''画图描述指定粒度下的子帧级bler

            Args:
                airtime_bin_size：统计粒度，默认为1s
                subfrm: 255(不区分子帧), <10(特定subframe)
            Returns：
                趋势图：x轴为时间粒度，y轴为bler(两种传输方案分别统计）
        '''
        if ax is None:
            fig, ax = plt.subplots(1, 1)
        ax.set_ylabel('Bler')
        ax.set_ylim([0, 1])
        xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        bler_data = self.bler_of_subframe(airtime_bin_size=airtime_bin_size, subframe = subframe)
        bler_data.index.name = xlabel
        bler_data.plot(ax=ax, kind='line', style='o--')

    def show_schd_uecnt(self, airtime_bin_size=1):
        '''画图描述指定粒度下的调度UE次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                直方图（kde）：x轴调度UE数，y轴为比例
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        col_name = r'SCHD.u8HarqId'
        self._log.show_trend(col_name, AGG_FUNC_CNT, airtime_bin_size)
        return

    def show_schd_rbnum(self, airtime_bin_size=1):
        '''画图描述指定粒度下的调度RB数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                直方图（kde）：x轴调度RB数，y轴为调度次数
                趋势图：x轴为时间粒度，y轴为平均RB数
        '''
        col_name = r'SCHD.u8RbNum'
        self._log.show_trend(col_name, AGG_FUNC_MEAN, airtime_bin_size, mean_by='time')
        self._log.show_hist(col_name, xlim=[0, 100])
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
        rlt.index.name='Fail_Rsn'
        return rlt

    def match_schd_and_ack(self, cols):
        ''' 匹配调度和Ack反馈信息

            根据调度时间，UEGID，HarqID匹配调度与ACK信息
            Args：
                cols: 匹配后输出的列名
            Yields:
                DataFrame, 生成器方式
        '''
        schdcols = ['FN', 'UEGID', 'SCHD.u8HarqId']
        demcols = ['ACK.u32DemTime', 'UEGID', 'ACK.u8HarqId']
        totcols = list(set(['AirTime'] + schdcols + demcols + cols))
        for data in self._log.gen_of_cols(cols=totcols):
            data['FN'] = data['AirTime'].map(self._get_demtime)
            addcols = [col for col in cols if col.startswith('ACK')]
            matchcols = np.union1d(addcols, demcols)
            matchdata = data[matchcols]
            data = data.drop(np.setdiff1d(matchcols, ['UEGID']), axis=1)
            merged = pd.merge(data, matchdata, how='left', left_on=schdcols, right_on=demcols)
            yield merged[cols]

    def _get_schdtime(self, demtime):
        '''给定解调时间，计算调度时间'''
        subfrm = demtime % 16
        offset = self._cell._schd_subfrm_offset[subfrm]
        return self._log.difftime(demtime, offset)

    def _get_demtime(self, schdtime):
        '''给定调度时间，计算解调时间'''
        subfrm = schdtime % 16
        offset = self._cell._dem_subfrm_offset[subfrm]
        return self._log.addtime(schdtime, offset)

    def is_valid_airtime(self, airtime):
        '''给定的airtime是否在当前log的时间范围'''
        return airtime in self._log.airtimes()

    def find_selfmaintain(self):
        '''查找是否存在自维护, 并输出相关信息'''

        cols = ['ACK.u32DemTime', 'UEGID', 'ACK.u8HarqId', 'ACK.u8IsSelfMainTain']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            data = data[data[cols[3]] == 1]
            rlt = rlt.append(data)
        return rlt

    def find_harqfail(self):
        '''查找是否存harqfail, 并输出相关信息'''

        cols = ['ACK.u32DemTime', 'UEGID', 'ACK.u8HarqId', 'ACK.u8Tb0IsHarqFail', 'ACK.u8Tb1IsHarqFail']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            data = data[(data[cols[3]] == 1) | (data[cols[4]] == 1)]
            rlt = rlt.append(data)
        return rlt

    def find_dtx(self):
        '''查找是否存dtx, 并输出相关信息'''

        cols = ['ACK.u32DemTime', 'UEGID', 'ACK.u8HarqId', 'ACK.u8Tb0AckInfo', 'ACK.u8Tb1AckInfo']
        rlt = pd.DataFrame(columns=cols)
        for data in self._log.gen_of_cols(cols):
            data = data[(data[cols[3]] == 2) | (data[cols[4]] == 2)]
            rlt = rlt.append(data)
        return rlt

    def find_bler_over(self, thresh, airtime_bin_size=1):
        '''查找bler超过一定门限的时间,时间粒度可以指定
            Args：
                thresh：门限，（0,1）之间
                airtime_bin_size：时间粒度，默认1s
            Returns：
                Series格式，{airtime：bler}
        '''
        bler_data = self.bler(airtime_bin_size=airtime_bin_size)
        bler_data = bler_data[bler_data > thresh].dropna().reindex(lambda x: x*airtime_bin_size for x in bler_data.index)
        bler_data.index.name = 'AirTime'
        return bler_data

    def why_selfmaintain(self):
        '''分析自维护原因

            Args：
                无
            return：
                demtime, uegid：reason 列表
        '''
        
        if self._cell is None:
            return 'cell is None, cant analysize '
        
        cols = ['ACK.u32DemTime', 'UEGID']
        selfdata = self.find_selfmaintain()[cols].drop_duplicates().astype(np.uint32)
        dlackdem_mismatch = self._cell.find_dlackdem_mismatch()
        pucch_mismatch = self._cell.find_pucch_mismatch()
        pusch_mismatch = self._cell.find_pusch_mismatch()

        for idx in selfdata.index:
            mismatchs = [dlackdem_mismatch, pucch_mismatch, pusch_mismatch]
            reasons = ['dlackdem_mismatch', 'pucch_mismatch', 'pusch_mismatch']
            for reason_idx, mismatch in enumerate(mismatchs):
                mismatch_cols = mismatch.columns  # 默认解调时间都在第一个位置
                mask = (mismatch[mismatch_cols[0]] == selfdata.at[idx, cols[0]])\
                       & (mismatch[cols[1]] == selfdata.at[idx, cols[1]])
                ack_filter = mismatch[mask]
                if len(ack_filter.index) != 0:
                    selfdata.loc[idx, 'Reason'] = reasons[reason_idx]
                    break

        return selfdata
    
    def show_throuput(self, airtime_bin_size=1):
        ''' 输出流量图

            根据时间粒度，输出流量图
            Args：
                airtime_bin_size: 时间粒度s
            Return:
                流量图
        '''
        assert(airtime_bin_size>=1)
        cols = [r'TB.u16TbSize', 'AirTime']
        rlt = pd.Series()
        for data in self.match_schd_and_ack(cols=cols):
            airtime = data[cols[1]] // (airtime_bin_size*1600)
            group_data = data[cols[0]].groupby(airtime)
            rlt = rlt.add(group_data.sum(), fill_value=0)
            
        ax = plt.subplots(1, 1)[1]
        xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        ax.set_ylabel('Throuput/Kbits')
        rlt = rlt * 8 / 1000
        rlt.index.name = xlabel
        rlt.plot(ax=ax, kind='line', style='ko--')
        return
    
    def show_dtx_cnt(self, airtime_bin_size=1):
        '''画图描述指定粒度下的dtx次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        assert(airtime_bin_size>=1)
        cols = ['ACK.u32DemTime','ACK.u8Tb0AckInfo', 'ACK.u8Tb1AckInfo']
        rlt = pd.DataFrame()
        for data in self._log.gen_of_cols(cols):
            data[cols[1]][data[cols[1]] != 2] = 0
            data[cols[2]][data[cols[2]] != 2] = 0            
            airtime = data[cols[0]] // (airtime_bin_size*1600)
            group_data = data[[cols[1], cols[2]]].groupby(airtime).sum()
            rlt = rlt.add(group_data, fill_value=0)
        
        ax = plt.subplots(1, 1)[1]
        xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        ax.set_ylabel('DtxCnt')
        rlt.index.name = xlabel
        if rlt.size:
            rlt.plot(ax=ax, kind='line', style='ko--')
        return
        
    def show_harqfail_cnt(self, airtime_bin_size=1):
        '''画图描述指定粒度下的harqfail次数

            Args:
                col_name: 待分析字段
                airtime_bin_size：统计粒度，默认为1s
            Returns：
                趋势图：x轴为时间粒度，y轴为调度UE次数
        '''
        assert(airtime_bin_size>=1)
        cols = ['ACK.u32DemTime','ACK.u8Tb0IsHarqFail', 'ACK.u8Tb1IsHarqFail']
        rlt = pd.DataFrame()
        for data in self._log.gen_of_cols(cols):
            data[cols[1]][data[cols[1]] != 1] = 0
            data[cols[1]][data[cols[2]] != 1] = 0            
            airtime = data[cols[0]] // (airtime_bin_size*1600)
            group_data = data[[cols[1], cols[2]]].groupby(airtime).sum()
            rlt = rlt.add(group_data,fill_value=0)
        
        ax = plt.subplots(1, 1)[1]
        xlabel = 'Airtime/{bin}s'.format(bin=airtime_bin_size)
        ax.set_ylabel('HarqFailCnt')
        rlt.index.name = xlabel
        rlt.plot(ax=ax, kind='line', style='ko--')
        return
    
class DlSchdCell(DlSchd):
    '''下行调度分析类'''

    def __init__(self, log, cell):
        super(DlSchdCell, self).__init__(log, cell)

    def infer_uldlcfgidx(self):
        '''推测上下行配比

        根据调度信息以及ACK反馈时序推测上下行配比，目前只支持0,1,2,7共4中配比推测。
        Args:
            无
        Return：
            255：推测失败
            其他：推测的配比
        '''

        schdcols = ['UEGID', 'AirTime', 'SCHD.u8HarqId']
        ackcols = ['UEGID', 'ACK.u32DemTime', 'ACK.u8HarqId']
        data = next(self._log.gen_of_cols(cols=schdcols + ackcols[1:]))[:400]
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
            if schddata.at[idx, 'SCHD.u8HarqId'] > 7:
                return 2

            ackidx = get_deminfo_idx(idx, *schddata.loc[idx, schdcols])
            if -1 == ackidx:
                continue

            airtime = ackdata.at[ackidx, 'ACK.u32DemTime']
            ackfrm = ackdata.at[ackidx, 'ACK.u32DemTime'] % 16
            subfrm = schddata.at[idx, 'AirTime'] % 16
            if 1 == ack_table[subfrm][ackfrm]:
                continue
            ack_table[subfrm][ackfrm] = 1
            if sum(ack_table[3]) != 0 or sum(ack_table[8]) != 0 or ack_table[4][2] != 0 or ack_table[9][7] != 0:
                return 2
            if ack_table[4][8] != 0 or ack_table[9][3] != 0:
                return 1
            if ack_table[5][9] != 0:
                return 0
            if ack_table[0][4] != 0 and ack_table[[1, 5, 6]].sum() != 0:
                return 0
            if ack_table[1][5] != 0:
                return 7
        return 255


class DlSchdUe(DlSchd):
    '''下行调度UE分析类'''

    def __init__(self, log, cell, uegid):
        super(DlSchdUe, self).__init__(log, cell, uegid)
        self._uegid = uegid

    def show_ta(self):
        '''画图显示TA变化以及TAC调整命令

            Args：
                无
            Yields：
                每个TTI文件画一张趋势图，通过next()来获取下一张趋势图
        '''
        cols = ['AirTime', 'SCHD.u8Tac', 'TA.as16Cp0RptTa', 'TA.as16Cp1RptTa']
        rlt = self._log.get_data_of_cols(cols)
        rlt[cols[0]] = rlt[cols[0]].map(self._log.dectime)
        rlt[cols[1]] = rlt[cols[1]].map(lambda x: (x-31)*16)
        rlt = rlt.set_index(cols[0])
        rlt[rlt==-32767] = None    
        ax = plt.subplots(3, 1, sharex=True)[1]
        rlt.index.name = 'Airtime/s'
        ax[0].set_ylabel('tac/ts')
        rlt[cols[1]].plot(ax=ax[0], kind='line', style='o--')
        
        ax[1].set_ylabel('cp0report ta/ts')
        rlt[cols[2]].plot(ax=ax[1], kind='line', style='o--')
        
        ax[2].set_ylabel('cp1report ta/ts')
        rlt[cols[3]].plot(ax=ax[2], kind='line', style='o--')
        
        return

    def is_bsr_enough(self):
        '''判断UE的bsr是否充足,schdbsr <= rlcbsr'''
        cols = ['LCH_SCHD.u16RlcRptBsr', 'LCH_SCHD.u16SchdBsr']
        for data in self._log.gen_of_cols(cols):
            if data(data[cols[1]] < data[cols[2]]).any():
                return False
        return True

    def get_idx_of_lastschd(self, curtime):
        '''距离当前时间往前的最近一次调度索引'''
        return self._log.get_idx_of_last_cols(curtime, ['SCHD.u8HarqId'], how='all')

    def _infer_schdfail_reason(self, airtime):
        '''分析指定时间UE没有得到调度的原因

            Args:
                airtime：指定时间
                max_tti_ue_num: 每TTI最大调度UE数，默认为4
            Returns：
                result: failrsn
        '''
        assert(airtime % 16 < 10)
        last_schd_idx = self._log.get_idx_of_last_cols(airtime, ['SCHD.u8HarqId'], how='any')
        if -1 == last_schd_idx:
            return 'AirTime:{airtime}不在Log空口时间范围内，没有相关Log'.format(airtime=airtime)
        if 0 == last_schd_idx:
            return 'AirTime:{airtime}已经被调度'.format(airtime=airtime)

        cols = ['AirTime', 'SCHD_FAIL_RSN.u32UeSchdFailRsn', 'BSRCHANGE.u8LchId', 'BSRCHANGE.b8LchHasBsr',
                'LCH_SCHD.u8LchId', 'LCH_SCHD.u16RlcRptBsr', 'LCH_SCHD.u16SchdBsr']
        last_bsr_idx = self._log.get_idx_of_last_cols(airtime, cols, how='all')
        if -1 == last_bsr_idx or last_bsr_idx < last_schd_idx:
            return 'Log中没有Airtime:{airtime}周围的调度数据，无法分析'.format(airtime=airtime)

        data = self._log.get_data_of_cols(cols)
        faildata = data[(data[cols[0]] == airtime) & data[cols[1]]]
        if faildata.size:
            return LTE_SCHD_FAIL_RSNS[int(faildata[cols[1]].iat[0])]

        data = data[data.index.isin(np.arange(last_schd_idx, last_bsr_idx+1, 1))]
        lch_cols = ['bsr_change', 'rlc_rpt_bsr', 'schd_bsr']
        lch_bsr = pd.DataFrame()
        for idx in data.index:
            if data.at[idx, cols[4]]:
                lch_bsr.at[data.at[idx, cols[4]], lch_cols[0]] = 1
                lch_bsr.at[data.at[idx, cols[4]], lch_cols[1]] = data.at[idx, cols[5]]
                lch_bsr.at[data.at[idx, cols[4]], lch_cols[2]] = data.at[idx, cols[6]]
            if data.at[idx, cols[2]]:
                lch_bsr.at[data.at[idx, cols[2]], lch_cols[0]] = data.at[idx, cols[3]]
        if 0 == lch_bsr[lch_cols[0]].sum():
            return '没有BSR'
        if data[data['AirTime'] == airtime][cols[2]].sum():
            return '调度结束才收到BSR'
        if (lch_bsr[lch_cols[1]] <= lch_bsr[lch_cols[2]]).all():
            return 'RLC上报的BSR为0'

        return '需要人工分析，上下文行索引范围：[{minidx}, {maxidx}]'.format(
            minidx=last_schd_idx, maxidx=last_bsr_idx)

