# coding=utf-8
########################################################################################################################
# 公共常量
########################################################################################################################

# 聚合函数
AGG_FUNC = ('sum', 'mean', 'max', 'min', 'count')
AGG_FUNC_SUM = AGG_FUNC[0]
AGG_FUNC_MEAN = AGG_FUNC[1]
AGG_FUNC_CNT = AGG_FUNC[4]
AGG_FUNC_MIN = AGG_FUNC[3]
AGG_FUNC_MAX = AGG_FUNC[2]


########################################################################################################################
# LTE常量
########################################################################################################################
# LTE调度失败原因
LTE_SCHD_FAIL_RSNS = ('cce_input_param', 'cce_not_enough', 'cce_position_collision', 'cce_pwr_limit',
                      'alloc_harqproc_fail', 'alloc_harqid_fail', 'alloc_rb_fail', 'retx_retx_rbnum_different',
                      'gap', 'dmrs_conflict', 'rbest_fail', 'has_schded', 'drx', 'pttsps_schded', 'sps_schded',
                      'retx_coderate_over', 'sr_request_time_over', 'sr_schded', 'err_state', 'schd_ue_num_over',
                      'pre_cnt_over', 'ccch_schd_timeover', 'fbd_schd', 'msg0_num_over', 'preamble_id_err',
                      'msg0_alloc_cce_fail', 'cce_alloc_fail', 'retx_occupy_rb_fail', 'pttgap', 'other')

# LTE文件类型
LTE_FILE_TYPES = ('RTL2_ulUeTtiInfo', 'RTL2_dlUeTtiInfo', 'RTL2_CellTtiInfo',
                  'Cell0DLPHYUERunInfo', 'Cell1DLPHYUERunInfo', 'Cell2DLPHYUERunInfo',
                  'Cell0PuschUERunInfo', 'Cell1PuschUERunInfo', 'Cell2PuschUERunInfo',
                  'Cell0PucchUERunInfo', 'Cell1PucchUERunInfo', 'Cell2PucchUERunInfo')
LTE_FILE_ULSCHD = LTE_FILE_TYPES[0]
LTE_FILE_DLSCHD = LTE_FILE_TYPES[1]
LTE_FILE_NI = LTE_FILE_TYPES[2]
LTE_FILE_DLPHY = 'DLPHYUERunInfo'
LTE_FILE_PUSCH = 'PuschUERunInfo'
LTE_FILE_PUCCH = 'PucchUERunInfo'

# LTE产品类型
LTE_PRODUCT_TYPES = ('Macro', 'Micro')
LTE_PRODUCT_MACRO = LTE_PRODUCT_TYPES[0]
LTE_PRODUCT_MICRO = LTE_PRODUCT_TYPES[1]

LTE_NEXT_DLSUBFRM_OFFSET = ((1, 4, 3, 2, 1, 1, 4, 3, 2, 1),
                            (1, 3, 2, 1, 1, 1, 3, 2, 1, 1),
                            (1, 2, 1, 1, 1, 1, 2, 1, 1, 1),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (1, 9, 8, 7, 6, 5, 4, 3, 2, 1))

LTE_NEXT_ULSUBFRM_OFFSET = ((2, 1, 1, 1, 3, 2, 1, 1, 1, 3),
                            (2, 1, 1, 4, 3, 2, 1, 1, 4, 3),
                            (2, 1, 5, 4, 3, 2, 1, 5, 4, 3),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (2, 1, 1, 1, 1, 1, 1, 1, 1, 3))

LTE_DEM_SUBFRM_OFFSET = ((4, 7, 0, 0, 0, 4, 7, 0, 0, 0),
                         (7, 6, 0, 0, 4, 7, 6, 0, 0, 4),
                         (7, 6, 0, 4, 8, 7, 6, 0, 4, 8),
                         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                         (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                         (4, 4, 0, 0, 0, 0, 0, 0, 0, 0))
LTE_SCHD_DLSUBFRM_OFFSET = ((0, 0, 7, 7, 5, 0, 0, 7, 7, 5),
                            (0, 0, 6, 4, 0, 0, 0, 6, 4, 0),
                            (0, 0, 4, 0, 0, 0, 0, 4, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            (0, 0, 11, 12, 4, 5, 6, 7, 7, 8))

########################################################################################################################
# MESH常量
########################################################################################################################
# LTE文件类型
MESH_FILE_TYPES = ('RTL2_TxInfo', 'RTL2_RxInfo', 'RTL2_DebugInfo')
MESH_FILE_TX = MESH_FILE_TYPES[0]
MESH_FILE_RX = MESH_FILE_TYPES[1]
MESH_FILE_DEBUG = MESH_FILE_TYPES[2]