# coding=utf-8
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from loganalysis.const import *
from .dlschd import DlSchdCell
from .ue import Ue
from .ulschd import UlSchdCell


class Ni(object):
    def __init__(self, log, cell):
        self._cell = cell
        self._log = log

    def show(self, airtime_bin_size=1000):
        '''
        NI 图形化描述

            Args：
                rb: True:按照RB粒度，否则全带宽
                airtime_bin_size: 时间粒度，默认1000ms
            Return:
                两张图，NI_vs_RB, NI_vs_Time
        '''
        rb_data = None
        nicols = None
        for data in self._log.gen_of_cols():
            if nicols is None:
                nicols = [col for col in data.columns if col.startswith('RTL2_EI_CELL_NI')]
            data = data[nicols].dropna(how='any', axis=0)
            data = data[data < 0].dropna(how='any', axis=1).max()
            if rb_data is None:
                rb_data = data
            else:
                rb_data = pd.Series([max(rb_data[i], data[i]) for i in data.index])
            rb_data.index.name = 'RbIdx'
            rb_data.index = np.arange(len(rb_data.index))

        ax = plt.subplots(1, 1)[1]
        ax.set(xlabel='RbIdx', ylabel='NI', title='NI vs RB', xlim=[0, len(rb_data.index)])
        rb_data.plot(ax=ax, grid=True, kind='line', style='o--')

        time_data = None
        cols = [nicols[i] for i in [0, int(len(rb_data.index)/2), len(rb_data.index)-1]]
        for data in self._log.gen_of_cols(cols+['AirTime']):
            data = data[cols].groupby(data['AirTime'].map(self._log.dectime)//airtime_bin_size).max()
            if time_data is None:
                time_data = data
            else:
                time_data = [max(time_data[i], data[i]) for i in data.index]

        ax = plt.subplots(1, 1)[1]
        ax.set(xlabel='AirTime/{bin}ms'.format(bin=airtime_bin_size), ylabel='NI',
               title='NI vs Time', xlim=[0, len(time_data.columns)])
        cols = [col.split(r'.')[1] for col in time_data.columns]
        time_data.columns = cols
        time_data.plot(ax=ax, grid=True, kind='line', style='o--')
        return


class Cell(object):
    '''小区实例'''

    def __init__(self, cellid, log):
        '''初始化小区实例
            根据输入的信息，完成如下事情：
                a) 尝试推断上下行配比,有可能需要用户输入

            Args:
                cellid: 小区Id
        '''
        self._cellid = cellid
        self._log = log

        ni_log = log.get_schd_logfile(LTE_FILE_NI, cellid=cellid)
        if ni_log is not None:
            self._nilog = ni_log
            self._ni = Ni(self._nilog, self)

        dl_log = log.get_schd_logfile(LTE_FILE_DLSCHD, cellid=cellid)
        if dl_log is not None:
            self._dl = DlSchdCell(dl_log, self)

        ul_log = log.get_schd_logfile(LTE_FILE_ULSCHD, cellid=cellid)
        if ul_log is not None:
            self._ul = UlSchdCell(ul_log, self)

        dlphy_log = log.get_dlphy_logfile(cellid)
        if dlphy_log is not None:
            self._dlphylog = dlphy_log

        pucch_log = log.get_pucch_logfile(cellid)
        if pucch_log is not None:
            self._pucchlog = pucch_log

        pusch_log = log.get_pusch_logfile(cellid)
        if pusch_log is not None:
            self._puschlog = pusch_log

        self._uldlcfgidx = self._get_uldlcfgidx()
        self._next_dl_subfrm_offset = LTE_NEXT_DLSUBFRM_OFFSET[self._uldlcfgidx]
        self._dem_subfrm_offset = LTE_DEM_SUBFRM_OFFSET[self._uldlcfgidx]
        self._schd_subfrm_offset = LTE_SCHD_DLSUBFRM_OFFSET[self._uldlcfgidx]

        self._ues = {}
        self._uegids = self._get_uegids()

    @property
    def cellid(self):
        return self._cellid

    @property
    def log(self):
        return self._log

    @property
    def dl(self):
        return getattr(self, '_dl', None)

    @property
    def ul(self):
        return getattr(self, '_ul', None)

    @property
    def ni(self):
        return getattr(self, '_ni', None)

    @property
    def uldlcfgidx(self):
        return self._uldlcfgidx

    def _get_uegids(self):
        '''获取本小区下的所有UEGID'''
        dluegid = self._dl.log.uegids if hasattr(self, '_dl') else set()
        uluegid = self._ul.log.uegids if hasattr(self, '_ul') else set()
        return set.union(dluegid, uluegid)

    def _get_uldlcfgidx(self):
        '''用户输入uldlcfgidx'''

        uldlcfgidx = 255
        if hasattr(self, '_dl'):
            uldlcfgidx = self._dl.infer_uldlcfgidx()
        if uldlcfgidx == 255 and hasattr(self, '_ul'):
            uldlcfgidx = self._ul.infer_uldlcfgidx()
        if uldlcfgidx != 255:
            return uldlcfgidx

        while True:
            uldlcfgidx = input('Please input uldlcfgidx(0,1,2,7):')
            if int(uldlcfgidx) not in [0, 1, 2, 7]:
                print('Not support uldlcgfidx, input again:')
                continue
            return int(uldlcfgidx)

    def get_ue(self, uegid=None):
        '''获取小区实例
            Args：
                uegid：如果想查看Log中的所有uegid，那么不用赋值
            Returns:
                如果uegid不为None，返回对应的UE实例，否则返回Log中的所有uegid
        '''
        if uegid is None:
            return '所有UEGID：{uegids}. 请使用get_ue(uegid)获取对应的UE实例'.format(uegids=self._uegids)

        if uegid in self._uegids:
            dllog = self.log.get_schd_logfile(LTE_FILE_DLSCHD, self.cellid, uegid)
            ullog = self.log.get_schd_logfile(LTE_FILE_ULSCHD, self.cellid, uegid)
            self._ues[uegid] = Ue(ullog, dllog, self, uegid)
            return self._ues[uegid]
        else:
            return '非法CellId值，此小区不存在'

    def _mismatch_idx(self, schdcols, schddata, matchcols, matchlog):
        for matchdata in matchlog.gen_of_cols(matchcols):
            matchdata = matchdata.dropna(how='any')
            airtime_min = max(schddata[schdcols[0]].iat[0], matchdata[matchcols[0]].iat[0])
            airtime_max = min(schddata[schdcols[0]].iat[-1], matchdata[matchcols[0]].iat[-1])
            if airtime_min > airtime_max:
                return pd.Index([])
            schddata = schddata[(schddata[schdcols[0]] >= airtime_min) & (schddata[schdcols[0]] <= airtime_max)]
            matchdata = matchdata[(matchdata[matchcols[0]] >= airtime_min) & (matchdata[matchcols[0]] <= airtime_max)]
            merged = pd.merge(schddata, matchdata, left_on=schdcols, right_on=matchcols, how='left')
            merged.index = schddata.index
            return merged[merged[matchcols[2]].isnull()].index

    def find_pdsch_mismatch(self):
        '''查询L2和L1的PDSCH控制消息不匹配的情形，并输出相应的空口时间和UEGID

            Args：
                无

            return：
                result：不匹配的空口时间，UEGID列表
        '''

        if not hasattr(self, '_dl') or not hasattr(self, '_dlphylog'):
            return None

        schdcols = ['AirTime', 'UEGID', 'SCHD.u8TranScheme']
        dlphycols = ['DLPHY_UE_EI_INFO.u32AirTime', 'UEGID', 'DLPHY_UE_EI_INFO.u8PDSCH_TS']
        mis_match_data = pd.DataFrame(columns=schdcols)
        for schddata in self._dl.log.gen_of_cols(schdcols):
            schddata = schddata.dropna(how='any')
            mis_match_index = self._mismatch_idx(schdcols, schddata, dlphycols, self._dlphylog)
            mis_match_data = pd.concat([mis_match_data, schddata.reindex(index=mis_match_index)], axis=0, ignore_index=True)
        return mis_match_data.astype(np.uint32)

    def find_pdcch_mismatch(self):
        '''查询L2和L1的PDCCH控制消息不匹配的情形，并输出相应的空口时间和UEGID

            Args：
                无
            return：
                result：不匹配的空口时间，UEGID列表
        '''
        if not hasattr(self, '_dlphylog'):
            return None

        def mismatch(schdcols, schddata):
            dlphycols = ['DLPHY_UE_EI_INFO.u32AirTime', 'UEGID', 'DLPHY_UE_EI_INFO.u8PDCCH_CCEStartNo']
            mis_match_index = pd.Index([])
            for index in np.arange(4):
                dlphycols[2] = r'DLPHY_UE_EI_INFO.u8PDCCH_CCEStartNo' + str(index)
                mis_match_index = self._mismatch_idx(schdcols, schddata, dlphycols, self._dlphylog)
                schddata = schddata.reindex(index=mis_match_index)
                if 0 == len(mis_match_index):
                    break
            return schddata[['AirTime', 'UEGID']]

        rlt = pd.DataFrame(columns=['AirTime', 'UEGID'])
        if hasattr(self, '_dl'):
            schdcols = ['AirTime', 'UEGID', 'SCHD.u8CceStart']
            for schddata in self._dl._log.gen_of_cols(schdcols):
                schddata = schddata.dropna(how='any')
                dl_dismatch = mismatch(schdcols, schddata)
                rlt = pd.concat([rlt, dl_dismatch], axis=0, ignore_index=True)

        if hasattr(self, '_ul'):
            schdcols = ['AirTime', 'UEGID', 'GRANT.u8CceStart', 'GRANT.u8IsDciSchd']
            for schddata in self._ul.log.gen_of_cols(schdcols):
                schddata = schddata.dropna(how='any')
                if 7 == self._uldlcfgidx:
                    schddata['AirTime'] = schddata['AirTime'].map(lambda x: x+7 if (x%16 == 9) else x)
                schddata = schddata[schddata[schdcols[3]] == 1]
                ul_dismatch = mismatch(schdcols[:3], schddata)
                rlt = pd.concat([rlt, ul_dismatch], axis=0, ignore_index=True)
        return rlt.astype(np.uint32)

    def find_pucch_mismatch(self):
        '''查询L2和L1的PUCCH控制消息不匹配的情形，并输出相应的空口时间和UEGID

            Args：
                无
            return：
                result：不匹配的空口时间，UEGID列表
        '''
        if not hasattr(self, '_ul') or not hasattr(self, '_pucchlog'):
            return None

        schdcols = ['PHYMGR_INFO.u32DemTime', 'UEGID', 'PHYMGR_INFO.u8AckExist',
                    'PHYMGR_INFO.u8CqiExist', 'PHYMGR_INFO.u8SrExist']
        phycols = ['DSP1_PUCCH_UERUN_INFO.SystemSfn', 'UEGID', 'DSP1_PUCCH_UERUN_INFO.AckExist',
                     'DSP1_PUCCH_UERUN_INFO.CqiExist', 'DSP1_PUCCH_UERUN_INFO.SrExist']
        mis_match_data = pd.DataFrame(columns=schdcols)
        for schddata in self._ul.log.gen_of_cols(schdcols, val_filter={'PHYMGR_INFO.u8UlSchFlag': [0]}):
            if 0 == len(schddata.index):
                continue
            mis_match_index = self._mismatch_idx(schdcols, schddata, phycols, self._pucchlog)
            mis_match_data = pd.concat([mis_match_data, schddata.reindex(index=mis_match_index)], axis=0,
                                       ignore_index=True)
        return mis_match_data.astype(np.uint32)

    def find_pusch_mismatch(self):
        '''查询L2和L1的PUSCH控制消息不匹配的情形，并输出相应的空口时间和UEGID

            Args：
                无
            return：
                result：不匹配的空口时间，UEGID列表
        '''
        if not hasattr(self, '_ul') or not hasattr(self, '_puschlog'):
            return None

        schdcols = ['PHYMGR_INFO.u32DemTime', 'UEGID', 'PHYMGR_INFO.u8HarqProcID']
        phycols = ['DSP1_PUSCH_UE_RUN_INFO.SystemTime', 'UEGID', 'DSP1_PUSCH_UE_RUN_INFO.HarqProcID']
        mis_match_data = pd.DataFrame(columns=schdcols)
        for schddata in self._ul.log.gen_of_cols(schdcols, val_filter={'PHYMGR_INFO.u8UlSchFlag': [1]}):
            if 0 == len(schddata.index):
                continue
            mis_match_index = self._mismatch_idx(schdcols, schddata, phycols, self._puschlog)
            mis_match_data = pd.concat([mis_match_data, schddata.reindex(index=mis_match_index)], axis=0,
                                       ignore_index=True)
        return mis_match_data.astype(np.uint32)

    def find_dlackdem_mismatch(self):
        '''查询下行Ack解调消息不匹配的情形，并输出相应的空口时间和UEGID

            下行ACK解调需要下行调度先把调度信息告知PHY主控，PHY主控再下发解调，本函数的功能主要是检查
            下行调度器与PHY主控针对此消息的接口是否匹配
            Args：
                无
            return：
                result：不匹配的空口时间，UEGID列表
        '''
        if not hasattr(self, '_ul') or not hasattr(self, '_dl'):
            return None

        dlcols = ['ACK.u32DemTime', 'UEGID']
        ulcols = ['PHYMGR_INFO.u32DemTime', 'UEGID', 'PHYMGR_INFO.u8AckExist']
        mis_match_data = pd.DataFrame(columns=dlcols)
        for schddata in self._dl.log.gen_of_cols(dlcols, val_filter={'ACK.u8IsSelfMainTain': [1]}):
            if 0 == len(schddata.index):
                continue
            schddata = schddata.drop_duplicates()
            schddata.loc[:, 'AckExits'] = 1
            mis_match_index = self._mismatch_idx(dlcols+['AckExits'], schddata, ulcols, self._ul.log)
            mis_match_data = pd.concat([mis_match_data, schddata.reindex(index=mis_match_index)], axis=0,
                                       ignore_index=True)
        return mis_match_data.astype(np.uint32)

    def find_ulcrcdem_mismatch(self):
        '''上行CRC解调消息不匹配的情形，并输出相应的空口时间和UEGID

            上行CRC解调需要上行调度先把调度信息告知PHY主控，PHY主控再下发解调，本函数的功能主要是检查
            上行调度器与PHY主控针对此消息的接口是否匹配
            Args：
                无
            return：
                result：不匹配的空口时间，UEGID列表
        '''
        if not hasattr(self, '_ul'):
            return None

        schdcols = ['CRCI.u32DemTime', 'UEGID', 'CRCI.u8CrcHarqId']
        demcols = ['PHYMGR_INFO.u32DemTime', 'UEGID', 'PHYMGR_INFO.u8HarqProcID']
        mis_match_data = pd.DataFrame(columns=schdcols)
        for schddata in self._ul.log.gen_of_cols(schdcols, val_filter={'CRCI.b8IsSelfMainTain': [1]}):
            schddata = schddata.dropna(how='any').astype(np.uint32)
            if 0 == len(schddata.index):
                continue
            mis_match_index = self._mismatch_idx(schdcols, schddata, demcols, self._ul.log)
            mis_match_data = pd.concat([mis_match_data, schddata.reindex(index=mis_match_index)], axis=0,
                                       ignore_index=True)
        return mis_match_data.astype(np.uint32)

    def show_ue_livetime(self):
        cols = ['AirTime', 'UEGID']

        logs = []
        if hasattr(self, '_dl'):
            logs.append(self.dl.log)
        if hasattr(self, '_ul'):
            logs.append(self.ul.log)

        if 0 == len(logs):
            return

        rlt = pd.DataFrame()
        for log in logs:
            for data in self.dl.log.gen_of_cols(cols):
                data = data.groupby(cols[1])
                start = data[cols[0]].first()
                end = data[cols[0]].last()
                for uegid in start.index:
                    if uegid not in rlt.index:
                        rlt.at[uegid, 'start'] = start[uegid]
                        rlt.at[uegid, 'end'] = end[uegid]
                    else:
                        rlt.at[uegid, 'start'] = min(start[uegid], rlt.at[uegid, 'start'])
                        rlt.at[uegid, 'end'] = max(end[uegid], rlt.at[uegid, 'end'])

        temp = pd.DataFrame()
        for idx, uegid in enumerate(rlt.index):
            temp.at[rlt.at[uegid, 'start'], uegid] = 0
            temp.at[rlt.at[uegid, 'end'], uegid] = idx + 1

        def fill_na_val(uedata):
            maxidx = uedata.idxmax()
            minidx = uedata.idxmin()
            uedata[minidx:maxidx+1] = uedata.max()
            return uedata

        temp.columns.name = 'UEGID'
        temp = temp.reindex(np.sort(temp.index)).apply(fill_na_val)
        temp.index.name = 'AirTime'
        fig, ax = plt.subplots(1, 1)
        ax.set_ylim([0, len(rlt.index)+1])
        temp.plot(ax=ax, kind='line', title='Ue_Alive_time')

    def describle(self):
        '''小区整体信息描述'''
        rlt = pd.Series(name='小区整体信息描述')
        rlt['TotUeNum'] = len(self._uegids)
        rlt['dlschd_log_lines'] = self._dl.log.lines if hasattr(self, '_dl') else 0
        rlt['ulschd_log_lines'] = self._ul.log.lines if hasattr(self, '_ul') else 0
        rlt['dlphy_log_lines'] = self._dlphylog.lines if hasattr(self, '_dlphylog') else 0
        pdsch_mismatch = self.find_pdsch_mismatch()
        rlt['pdsch_mismatch_cnt'] = 0 if pdsch_mismatch is None else len(pdsch_mismatch.index)
        pdcch_mismatch = self.find_pdsch_mismatch()
        rlt['pdcch_mismatch_cnt'] = 0 if pdcch_mismatch is None else len(pdcch_mismatch.index)
        pucch_mismatch = self.find_pucch_mismatch()
        rlt['pucch_mismatch_cnt'] = 0 if pucch_mismatch is None else len(pucch_mismatch.index)
        pusch_mismatch = self.find_pusch_mismatch()
        rlt['pusch_mismatch_cnt'] = 0 if pusch_mismatch is None else len(pusch_mismatch.index)
        dlackdem_mismatch = self.find_dlackdem_mismatch()
        rlt['dlackdem_mismatch_cnt'] = 0 if dlackdem_mismatch is None else len(dlackdem_mismatch.index)
        ulcrcdem_mismatch = self.find_ulcrcdem_mismatch()
        rlt['ulcrcdem_mismatch_cnt'] = 0 if ulcrcdem_mismatch is None else len(ulcrcdem_mismatch.index)
        return rlt.astype(np.uint32)
