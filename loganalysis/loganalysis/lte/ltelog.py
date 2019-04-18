# coding=utf-8
from loganalysis.log import Log
from loganalysis.log import LogFile
from loganalysis.const import *
from loganalysis.lte.cell import Cell


class LteLog(Log):
    ''' LTE调度模块Log分析接口类

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
               product_type: 产品类型['Macro', 'Micro']，默认为micro
        '''
        super(LteLog, self).__init__(directory, time_interval, product_type)
        self._cells = {}
        self._cellids = set()
        for filetype in LTE_FILE_TYPES:
            filenames = self._filenames_of_type(filetype, time_interval)
            if filenames:
                logfile = LteFile(filetype, directory, filenames)
                if logfile.lines == 0:
                    continue
                self._logfiles[filetype] = logfile
                if filetype == LTE_FILE_NI or filetype == LTE_FILE_DLSCHD or filetype == LTE_FILE_ULSCHD:
                    self._cellids = set.union(self._cellids, self._logfiles[filetype].cellids)

    def _get_phy_logfile(self, cellid, ftype):
        '''根据CellId以类型选择PHY文件
            Args：
                cellid: 小区ID
                ftype：
            Returns:
                文件名s(文件类型.csv）
        '''
        for filetype, logfile in self._logfiles.items():
            if -1 == filetype.find(ftype):
                continue

            if self.product_type == LTE_PRODUCT_MICRO:
                return logfile

            df = logfile.get_data_of_cols(cols=['CellId'], maxlines=2)
            if df['CellId'][0] == cellid:
                return logfile
        return None

    def get_dlphy_logfile(self, cellid):
        '''根据CellId选择DLPHY文件
            Args：
                cellid: 小区ID
            Returns:
                文件名(文件类型.csv）
        '''
        return self._get_phy_logfile(cellid, LTE_FILE_DLPHY)

    def get_pucch_logfile(self, cellid):
        '''根据CellId选择Pucch PHY文件
            Args：
                cellid: 小区ID
            Returns:
                文件名(文件类型.csv）
        '''
        return self._get_phy_logfile(cellid, LTE_FILE_PUCCH)

    def get_pusch_logfile(self, cellid):
        '''根据CellId选择Pusch PHY文件
            Args：
                cellid: 小区ID
            Returns:
                文件名(文件类型.csv）
        '''
        return self._get_phy_logfile(cellid, LTE_FILE_PUSCH)

    def get_cell(self, cellid=None):
        '''获取小区实例
            Args：
                cellid：如果想查看Log中的所有小区id，那么不用赋值
            Returns:
                如果cellid不为None，返回对应的小区实例，否则返回Log中的所有小区Id
        '''
        if cellid is None:
            return '所有CellId：{cellidlist}. 请使用get_cell(cellid)获取对应的Cell实例'.format(cellidlist=self._cellids)

        if cellid in self._cellids:
            if cellid not in self._cells.keys():
                self._cells[cellid] = Cell(cellid, self)
            return self._cells[cellid]
        else:
            return '非法CellId值，此小区不存在'

    def get_schd_logfile(self, filetype, cellid, uegid=None):
        '''获取Log文件实例'''

        if filetype not in self._logfiles:
            return None

        id_filter = {'CellId': [cellid]}
        if uegid is None:
            return LteFile(filetype, self._directory, self._filenames_of_type(filetype), id_filter=id_filter)

        id_filter = {'CellId': [cellid], 'UEGID': [uegid]}
        return LteFile(filetype, self._directory, self._filenames_of_type(filetype), id_filter=id_filter)


class LteFile(LogFile):
    '''Log文件接口类'''

    def __init__(self, filetype, directory, files, id_filter=None):
        '''初始化Log实例,把所有Log按照类型分类

           Args:
               file: 文件名
               filetype: log类型
        '''
        super(LteFile, self).__init__(filetype, directory, files, id_filter)
        self._cellids = set()
        self._uegids = set()
        cols = ['CellId', 'UEGID']
        for data in self.gen_of_cols(cols):
            if len(data.index) == 0:
                self._lines = 0
                return
            self._cellids = set.union(self._cellids, set(data[cols[0]]))
            self._uegids = set.union(self._uegids, set(data[cols[1]]))

    @property
    def cellids(self):
        '''获取所有小区ID'''
        return self._cellids

    @property
    def uegids(self):
        '''获取所有UEGID'''
        return self._uegids
