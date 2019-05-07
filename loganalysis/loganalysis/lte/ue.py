# coding=utf-8
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
    
    def show_livetime(self):
        '''
            画出UE在各小区存在的时间
        '''
        logs = []
        if hasattr(self, '_dl'):
            logs.append(self.dl.log)
        if hasattr(self, '_ul'):
            logs.append(self.ul.log)

        if 0 == len(logs):
            return

        rlt = pd.DataFrame()
        cols = ['AirTime', 'CellId']
        for log in logs:
            for data in self.dl.log.gen_of_cols(cols):
                data[cols[0]] = data[cols[0]]//1600
                group_data = data[cols[1]].groupby(data[cols[0]]).apply(lambda x: x.value_counts())
                if 0 == group_data.size:
                    continue
                group_data = group_data.unstack(level=1, fill_value=0)
                rlt = rlt.add(group_data, fill_value=0)
        
        rlt[rlt==0]=None
        rlt.columns.name = 'CellId'
        rlt.index.name = 'AirTime'
        fig, ax = plt.subplots(1, 1)
        rlt.plot(ax=ax, kind='line', title='Ue_Alive_time')
        
        return
    
    def set_airtimes_interval(self, start, end):
        '''指定当前log的时间范围
            Args：
                start:起始时间
                end:截止时间
            Returns:
                无
        '''
        assert(start <= end)
        filters = {'AirTime': np.arange(start, end)}
        if self._dllog:
            self._dllog._id_filter.update(filters)
            
        if self._ullog:
            self._ullog._id_filter.update(filters)
        return
    
    def reset_airtimes_interval(self):
        '''重置当前log的时间范围
            Args：
                无
            Returns:
                无
        '''
    
        if self._dllog and 'AirTime' in self._dllog._id_filter:
            self._dllog._id_filter.pop('AirTime')
            
        if self._ullog and 'AirTime' in self._ullog._id_filter:
            self._ullog._id_filter.pop('AirTime')            
        return