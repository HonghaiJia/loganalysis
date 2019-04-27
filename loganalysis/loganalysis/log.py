# coding=utf-8
import os
import os.path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loganalysis.const import *


class Log(object):
    ''' 调度模块Log分析接口类

        主要提供如下3类功能：
        a) 信息呈现
        b）问题发现
        c）问题定位
        要求所有文件命名符合EI命名格式：子系统_时间.csv
    '''

    def __init__(self, directory, time_interval=None, product_type='Micro'):
        '''初始化Log实例,把所有Log按照类型分类

           Args:
               directory: Log所在目录
               time_interval: 时间范围[start, end],格式为yyyymmddhhmmss
               product_type:产品类型['Macro', 'Micro']，默认为micro
        '''
        self._directory = directory
        self._product_type = product_type
        self._logfiles={}

    @property
    def product_type(self):
        return self._product_type

    @property
    def directory(self):
        return self._directory

    def _filenames_of_type(self, filetype, time_interval=None):
        '''获取指定文件类型的所有文件名
            Args：
                filetype：文件类型
                time_interval: 时间范围[start, end],格式为yyyymmddhhmmss
            Returns:
                文件名列表
        '''
        names_of_filetype = []
        for name in np.sort(os.listdir(self._directory)):
            if not name.endswith(r'.csv'):
                continue
            if -1 == name.find(filetype):
                continue
            if time_interval is not None:
                time = np.uint64(name.rsplit(r'.')[0].rsplit(r'_')[-1])
                if time < time_interval[0] or time > time_interval[1]:
                    continue
            names_of_filetype.append(name)
        return names_of_filetype

    def describle(self):
        '''当前目录下相关Log文件总体描述，每类Log文件合并为一个文件

           输出文件名，大小，行数，时间范围，airtime范围等，每个Log文件一列
        '''
        df = pd.DataFrame()
        for type, logfile in self._logfiles.items():
            df.at[type, 'size'] = logfile.size
            df.at[type, 'num_of_files'] = len(logfile.files)
            df.at[type, 'num_of_lines'] = logfile.lines
            df.at[type, 'pctime_start'] = logfile.pctimes[0]
            df.at[type, 'pctime_end'] = logfile.pctimes[1]
            df.at[type, 'airtime_start'] = logfile.airtimes[0]
            df.at[type, 'airtime_end'] = logfile.airtimes[1]
        df.index.name = 'filename'
        return df


class LogFile(object):
    '''Log文件接口类'''

    def __init__(self, type, directory, files, id_filter=None):
        '''初始化Log实例,把所有Log按照类型分类

           Args:
               file: 文件名
               type: log类型
        '''
        self._files = files
        self._type = type
        self._directory = directory
        self._id_filter = id_filter
        self._size = sum([os.path.getsize(os.path.join(directory, file)) for file in files])
        self._pctimes = [-1, -1]
        self._airtimes = [-1, -1]
        self._lines = 0
        cols = ['LocalTime', 'AirTime']
        for data in self.gen_of_cols(cols):
            if len(data.index) == 0:
                self._lines = 0
                return
            self._lines = self._lines + data.index.max()
            if self._pctimes[0] == -1:
                self._pctimes[0] = data.iat[0, 0]
            self._pctimes[1] = data.iat[-1, 0]
            if self._airtimes[0] == -1:
                self._airtimes[0] = data.iat[0, 1]
            self._airtimes[1] = data.iat[-1, 1]

    @property
    def type(self):
        return self._type

    @property
    def files(self):
        return self._files

    @property
    def size(self):
        return self._size

    @property
    def id_filter(self):
        return self._id_filter

    @property
    def lines(self):
        '''获取文件总行数'''
        return self._lines

    @property
    def pctimes(self):
        '''PC时间范围'''
        return tuple(self._pctimes)

    @property
    def airtimes(self):
        '''AirTime时间范围'''
        return tuple(self._airtimes)

    @staticmethod
    def addtime(time1, time2):
        time1 = np.uint32(time1)
        time2 = np.uint32(time2)
        frm = time1 // 16 + time2 // 16
        subfrm = time1 % 16 + time2 % 16
        if subfrm >= 10:
            subfrm -= 10
            frm += 1
        return frm % 0x10000000 * 16 + subfrm

    @staticmethod
    def difftime(time1, time2):
        time1 = np.uint32(time1)
        time2 = np.uint32(time2)
        subfrm1 = time1 % 16
        subfrm2 = time2 % 16
        frm = time1 // 16 + 0x10000000 - time2 // 16
        if subfrm1 >= subfrm2:
            subfrm = subfrm1 - subfrm2
        else:
            subfrm = subfrm1 + 10 - subfrm2
            frm = frm - 1
        frm = frm % 0x10000000
        return frm * 16 + subfrm

    @staticmethod
    def dectime(hextime):
        hextime = np.uint32(hextime)
        return hextime // 16 * 10 + hextime % 16

    @staticmethod
    def hextime(dectime):
        dectime = np.uint32(dectime)
        return dectime // 10 * 16 + dectime % 10

    def gen_of_cols(self, cols=None, val_filter=None):
        '''获取指定列的生成器
            Args：
                cols: 列名列表，如果为None，表示获取全部列
                col_val_filter: 过滤条件，字典格式{'colname': [val1,]}
            Yields:
                生成器格式
        '''

        filters = {}
        if val_filter:
            filters.update(val_filter)
        if self._id_filter:
            filters.update(self._id_filter)
        totcols = cols
        if cols is not None:
            totcols = list(set.union(set(filters), set(cols)))
        for file in self._files:
            filename = os.path.join(self._directory, file)
            data = pd.read_csv(filename, na_values='-', usecols=totcols)
            if not filters:
                yield data
                continue

            mask = data[list(filters.keys())].isin(filters).all(1)
            if cols is not None:
                yield data[mask][cols]
            else:
                yield data[mask]

    def get_filename_by_airtime(self, airtime):
        '''根据指定时间获取文件名
            Args：
                airtime：
            Returns:
                文件名
        '''
        col = ['AirTime']
        for file in self._files:
            filename = os.path.join(self._directory, file)
            data = pd.read_csv(filename, na_values='-', usecols=col)[col[0]]
            if airtime < data.iat[0] or airtime > data.iat[-1]:
                continue
            return file

    def get_data_between_airtimes(self, start_airtime, end_airtime, cols=None, val_filter=None):
        '''获取指定时间范围内的数据
            Args：
                start_airtime:起始时间
                end_airtime:截止时间
                cols: 列名列表，如果为None，表示获取全部列
                col_val_filter: 过滤条件，字典格式{'colname': [val1,]}
            Returns:
                数据，DataFrame格式
        '''
        assert(start_airtime <= end_airtime)
        rlt = pd.DataFrame()
        if cols is not None:
            totcols = list(set(cols + ['AirTime']))
        else:
            totcols = None
        for data in self.gen_of_cols(cols=totcols, val_filter=val_filter):
            airtime = data['AirTime'].astype(np.uint32)
            if start_airtime > airtime.iat[-1] or end_airtime < airtime.iat[0]:
                continue
            data = data[(airtime <= end_airtime) & (airtime >= start_airtime)]
            rlt = pd.concat([rlt, data], ignore_index=True)
        return rlt
        
    def get_data_of_cols(self, cols, val_filter=None):
        '''获取指定cols的数据
            Args：
                cols: 列名列表
                col_val_filter: 过滤条件，字典格式{'colname': [val1,]}
            Returns:
                数据，DataFrame格式
        '''
        rlt = pd.DataFrame()
        for data in self.gen_of_cols(cols=cols, val_filter=val_filter):
            rlt = pd.concat([rlt, data])
        return rlt

    def mean_of_cols(self, cols, airtime_bin_size, by, filters=None, time_col='AirTime'):
        '''按照时间粒度计算指定列的平均值

            Args:
                cols:待汇总的列名
                airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
                by: 'cnt'：按照次数平均，'time':
                filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
                time_col: 聚合的时间列名，默认‘AirTime’
        '''
        rlt = pd.DataFrame()
        cnt = pd.DataFrame()
        for data in self.gen_of_cols(cols+[time_col], val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[time_col].map(self.dectime) // airtime_bin_size
  
            group_data = data[cols].groupby(airtime)          
            rlt = rlt.add(group_data.sum(), fill_value=0)
            cnt = cnt.add(group_data.count(), fill_value=0) 
        return rlt.div(cnt).dropna()

    def sum_of_cols(self, cols, airtime_bin_size, filters=None, time_col='AirTime'):
        '''按照时间粒度计算指定列的总和

            Args:
                cols:待汇总的列名
                airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
                filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
                time_col: 聚合的时间列名，默认‘AirTime’
        '''
        rlt = pd.DataFrame()
        for data in self.gen_of_cols(cols+[time_col], val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[time_col].map(self.dectime) // airtime_bin_size
            group_data = data[cols].groupby(airtime)
            rlt = rlt.add(group_data.sum(), fill_value=0)
        return rlt.dropna()
        
    def min_of_cols(self, cols, airtime_bin_size, filters=None, time_col='AirTime'):
        '''按照时间粒度计算指定列的最小值

            Args:
                cols:待汇总的列名
                airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
                filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
                time_col: 聚合的时间列名，默认‘AirTime’
        '''
        rlt = pd.DataFrame()
        for data in self.gen_of_cols(cols+[time_col], val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[time_col].map(self.dectime) // airtime_bin_size
            group_data = data[cols].groupby(airtime)
            rlt = pd.concat([rlt, group_data.min().dropna()])
        return rlt.drop_duplicates(keep='first')
        
    def max_of_cols(self, cols, airtime_bin_size, filters=None, time_col='AirTime'):
        '''按照时间粒度计算指定列的最大值

            Args:
                cols:待汇总的列名
                airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
                filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
                time_col: 聚合的时间列名，默认‘AirTime’
        '''
        rlt = pd.DataFrame()
        for data in self.gen_of_cols(cols+[time_col], val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[time_col].map(self.dectime) // airtime_bin_size
            group_data = data[cols].groupby(airtime)
            rlt = pd.concat([rlt, group_data.max()])
        return rlt

    def cnt_of_cols(self, cols, airtime_bin_size, filters=None, time_col='AirTime'):
        '''按照时间粒度计算指定列的次数

            Args:
                airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
                filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
        '''
        cnt = pd.DataFrame()
        for data in self.gen_of_cols(cols+[time_col], val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[time_col].map(self.dectime) // airtime_bin_size
            group_data = data[cols].groupby(airtime)
            cnt = cnt.add(group_data.count(), fill_value=0)
        return cnt

    def hist_of_col(self, col, airtime_bin_size, ratio=True, filters=None):
        '''按照时间粒度计算指定列的直方图数据

            ratio: 是否计算比例, 默认Ratio为True
            airtime_bin_size：时间粒度（ms), 0表示不区分时间粒度
            filters：滤波条件，字典格式{‘列名0’：值， ‘列名1’：值...}
        '''
        cols = ['AirTime', col]
        rlt = pd.DataFrame()
        for data in self.gen_of_cols(cols, val_filter=filters):
            if airtime_bin_size == 0:
                airtime = np.zeros(len(data.index))
            else:
                airtime = data[cols[0]].map(self.dectime) // airtime_bin_size

            group_data = data[cols[1]].groupby(airtime).apply(lambda x: x.value_counts())
            if 0 == group_data.size:
                continue
            group_data = group_data.unstack(level=1, fill_value=0)
            rlt = rlt.add(group_data, fill_value=0)
            if ratio:
                rlt = rlt.apply(lambda x: x/x.sum(), axis=1)
        rlt.columns = rlt.columns.map(lambda x: np.uint32(x))
        rlt = rlt.reindex(columns=np.sort(rlt.columns))
        return rlt

    def show_trend(self, col, agg_func, airtime_bin_size, mean_by=None, ax=None, filters=None, y_label=None):
        '''指定列的时间趋势图

            Args：
                col：待分析列名
                agg_func:聚合函数{'sum', 'mean', 'cnt'}
                airtime_bin_size：时间粒度
                ylabel：y轴标签
                mean_by: 'cnt'
                ax：坐标，如果为none，在新的figure上画图
                filters:限定条件，字典格式{‘col_name’:value, ..}
        '''
        if agg_func == AGG_FUNC_SUM:
            data = self.sum_of_cols([col], airtime_bin_size, filters=filters)
        elif agg_func == AGG_FUNC_MEAN:
            data = self.mean_of_cols([col], airtime_bin_size, by=mean_by, filters=filters)
        elif agg_func == AGG_FUNC_CNT:
            data = self.cnt_of_cols([col], airtime_bin_size, filters=filters)
        elif agg_func == AGG_FUNC_MIN:
            data = self.min_of_cols([col], airtime_bin_size, filters=filters)
        elif agg_func == AGG_FUNC_MAX:
            data = self.max_of_cols([col], airtime_bin_size, filters=filters)
        else:
            return

        if ax is None:
            ax = plt.subplots(1, 1)[1]
        xlabel = 'Airtime/{bin}ms'.format(bin=airtime_bin_size)
        if y_label is None:
            ax.set_ylabel(col)
        else:
            ax.set_ylabel(y_label)
        data[col].index.name = xlabel
        data[col].plot(ax=ax, kind='line', style='ko--')

    def show_hist(self, col, xlim=None, ax=None, ratio=True):
        '''指定列的时间直方图

            Args：
                col： 待分析列
                xlim：x轴范围，如果为None,则自适应
                ax：坐标，如果为none，在新的figure上画图
                ratio：画比例，默认为True
        '''
        if ax is None:
            ax = plt.subplots(1, 1)[1]
        ax.set_xlabel(col)
        ylabel = 'Ratio' if ratio else 'Cnt'
        ax.set_ylabel(ylabel)
        hist = self.hist_of_col(col, airtime_bin_size=0, ratio=ratio)
        hist.loc[0, :].plot(kind='bar', xlim=xlim)
