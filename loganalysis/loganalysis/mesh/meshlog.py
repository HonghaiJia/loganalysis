# coding=utf-8
from loganalysis.log import Log
from loganalysis.log import LogFile
from loganalysis.const import *
from loganalysis.mesh.node import *

class MeshLog(Log):
    ''' MESH调度模块Log分析接口类

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
        super(MeshLog, self).__init__(directory, time_interval, product_type)
        self._nodes = {}
        self._nodeids = set()
        self._nbrids = set()
        for filetype in MESH_FILE_TYPES:
            filenames = self._filenames_of_type(filetype, time_interval)
            if filenames:
                logfile = MeshFile(filetype, directory, filenames)
                if logfile.lines == 0:
                    continue
                self._logfiles[filetype] = logfile
                if filetype == MESH_FILE_TX or filetype == MESH_FILE_RX or filetype == MESH_FILE_DEBUG:
                    self._nodeids = set.union(self._nodeids, self._logfiles[filetype].nodeids)
                    self._nbrids = set.union(self._nbrids, self._logfiles[filetype].nbrids)

    def get_node(self, nodeid=None):
        '''获取小区实例
            Args：
                cellid：如果想查看Log中的所有小区id，那么不用赋值
            Returns:
                如果cellid不为None，返回对应的小区实例，否则返回Log中的所有小区Id
        '''
        if nodeid is None:
            return '所有NodeId：{nodeidlist}. 请使用get_node(nodeid)获取对应的Node实例'.format(nodeidlist=self._nodeids)

        if nodeid in self._nodeids:
            if nodeid not in self._nodes.keys():
                self._nodes[nodeid] = Node(nodeid, self)
            return self._nodes[nodeid]
        else:
            return '非法NodeId值，此节点不存在'

    def get_schd_logfile(self, filetype, nodeid, nbrid=None):
        '''获取Log文件实例'''

        if filetype not in self._logfiles:
            return None

        id_filter = {'NodeID': [nodeid]}
        if nbrid is None:
            return MeshFile(filetype, self._directory, self._filenames_of_type(filetype), id_filter=id_filter)

        id_filter = {'NodeID': [nodeid], 'NBRID': [nbrid]}
        return MeshFile(filetype, self._directory, self._filenames_of_type(filetype), id_filter=id_filter)

    @property
    def nodeids(self):
        '''获取所有小区ID'''
        return self._nodeids

    @property
    def nbrids(self):
        '''获取所有小区ID'''
        return self._nbrids

class MeshFile(LogFile):
    '''Log文件接口类'''

    def __init__(self, filetype, directory, files, id_filter=None):
        '''初始化Log实例,把所有Log按照类型分类

           Args:
               file: 文件名
               filetype: log类型
        '''
        super(MeshFile, self).__init__(filetype, directory, files, id_filter)
        self._nodeids = set()
        self._nbrids = set()
        cols = ['NodeID', 'NBRID']
        for data in self.gen_of_cols(cols):
            if len(data.index) == 0:
                self._lines = 0
                return
            self._nodeids = set.union(self._nodeids, set(data[cols[0]]))
            self._nbrids = set.union(self._nbrids, set(data[cols[1]]))

    @property
    def nodeids(self):
        '''获取所有节点ID'''
        return self._nodeids

    @property
    def nbrids(self):
        '''获取所有邻节点ID'''
        return self._nbrids

if __name__ == '__main__':
    #main(['','E:\PycharmProjects\LogAnalysis\EI\RTL2_dlUeTtiInfo_20160818102737.csv'])
    log = MeshLog(r'E:\并网2_NBID3_0529_并网吞吐量下降')
    node = log.get_node(3)
    log_tx = node.tx
    log_tx.show_amc()
    log_tx.show_tx_cnt()
