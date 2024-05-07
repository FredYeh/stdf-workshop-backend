# =============================
# Author : Fred Yeh
# E-mail : b0093069@gmail.com
# Python : 3.9.0
# Version: 1
# Last Update : 2022/1/6
# =============================

# All records' type & subtype informations
info = {
    (0,10):'FAR',(0,20):'ATR',(1,10):'MIR',(1,20):'MRR',(1,30):'PCR',
    (1,40):'HBR',(1,50):'SBR',(1,60):'PMR',(1,62):'PGR',(1,63):'PLR',
    (1,70):'RDR',(1,80):'SDR',(2,10):'WIR',(2,20):'WRR',(2,30):'WCR',
    (5,10):'PIR',(5,20):'PRR',(10,30):'TSR',(15,10):'PTR',(15,15):'MPR',
    (15,20):'FTR',(20,10):'BPS',(20,20):'EPS',(50,10):'GDR',(50,30):'DTR',
}

# For struct unpack function
# Comparsion of STDF spec(*num) & struct format
unpackFormatMap = {
    "B1": "B",
    "U1": "B",
    "U2": "H",
    "U4": "I",
    "U8": "Q",
    "I1": "b",
    "I2": "h",
    "I4": "i",
    "I8": "q",
    "R4": "f",
    "R8": "B",
}
# For j, k type count j, k
jkCount = {
    'j': 0, 'k': 0
}
# All records' informations
RecordTypeMap = {
    'FAR':(
        ('CPU_TYP','U1'),('STDF_VER','U1')),
    'MIR':(
        ('SETUP_T', 'U4'),('START_T', 'U4'),('STAT_NUM', 'U1'),
        ('MODE_COD', 'C1'),('RTST_COD', 'C1'),('PROT_COD', 'C1'),
        ('BURN_TIM', 'U2'),('CMOD_COD', 'C1'),('LOT_ID', 'Cn'),
        ('PART_TYP', 'Cn'),('NODE_NAM', 'Cn'),('TSTR_TYP', 'Cn'),
        ('JOB_NAM', 'Cn'),('JOB_REV', 'Cn'),('SBLOT_ID', 'Cn'),
        ('OPER_NAM', 'Cn'),('EXEC_TYP', 'Cn'),('EXEC_VER', 'Cn'),
        ('TEST_COD', 'Cn'),('TST_TEMP', 'Cn'),('USER_TXT', 'Cn'),
        ('AUX_FILE', 'Cn'),('PKG_TYP', 'Cn'),('FAMLY_ID', 'Cn'),
        ('DATE_COD', 'Cn'),('FACIL_ID', 'Cn'),('FLOOR_ID', 'Cn'),
        ('PROC_ID', 'Cn'),('OPER_FRQ', 'Cn'),('SPEC_NAM', 'Cn'),
        ('SPEC_VER', 'Cn'),('FLOW_ID', 'Cn'),('SETUP_ID', 'Cn'),
        ('DSGN_REV', 'Cn'),('ENG_ID', 'Cn'),('ROM_COD', 'Cn'),
        ('SERL_NUM', 'Cn'),('SUPR_NAM', 'Cn')),
    'MRR':(
        ('FINISH_T','U4'),('DISP_COD','C1'),('USR_DESC','Cn'),
        ('EXC_DESC','Cn')),
    'SDR':(
        ('HEAD_NUM','U1'),('SITE_GRP','U1'),('SITE_CNT','U1k'),
        ('SITE_NUM','kU1'),('HAND_TYP','Cn'),('HAND_ID','Cn'),
        ('CARD_TYP','Cn'),('CARD_ID','Cn'),('LOAD_TYP','Cn'),
        ('LOAD_ID','Cn'),('DIB_TYP','Cn'),('DIB_ID','Cn'),
        ('CABL_TYP','Cn'),('CABL_ID','Cn'),('CONT_TYP','Cn'),
        ('CONT_ID','Cn'),('LASR_TYP','Cn'),('LASR_ID','Cn'),
        ('EXTR_TYP','Cn'),('EXTR_ID','Cn')),
    'WIR':(
        ('HEAD_NUM','U1'),('SITE_GRP','U1'),
        ('START_T','U4'),('WAFER_ID','Cn')),
    'PRR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1'),('PART_FLG','B1'),
        ('NUM_TEST','U2'),('HARD_BIN','U2'),('SOFT_BIN','U2'),
        ('X_COORD','I2'),('Y_COORD','I2'),('TEST_T','U4'),
        ('PART_ID','Cn'),('PART_TXT','Cn'),('PART_FIX','Bn')),
    #===========================================================
    'ATR':(
        ('MOD_TIM','U4'),('CMD_LINE','Cn')),
    'MRR':(
        ('FINISH_T','U4'),('DISP_COD','C1'),('USR_DES','Cn'),
        ('EXC_DESC','Cn')),
    'PCR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1'),('PART_CNT','U4'),
        ('RSTS_CNT','U4'),('ABRT_CNT','U4'),('GOOD_CNT','U4'),
        ('FUNC_CNT','U4')),
    'HBR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1'),('HBIN_NUM','U2'),
        ('HBIN_CNT','U4'),('HBIN_PF','C1'),('HBIN_NAM','Cn')),
    'SBR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1'),('SBIN_NUM','U2'),
        ('SBIN_CNT','U4'),('SBIN_PF','C1'),('SBIN_NAM','Cn')),
    'PMR':(
        ('PMR_INDX','U2'),('CHAN_TYP','U2'),('CHAN_NAM','Cn'),
        ('PHY_NAM','Cn'),('LOG_NAM','Cn'),('HEAD_NUM','U1'),
        ('SITE_NUM','U1')),
    'PGR':(
        ('GRP_INDX','U2'),('GRP_NAM','Cn'),('INDX_CNT','U2k'),
        ('PMR_INDX','kU2')),
    'PLR':(
        ('GRP_CNT','U2k'),('GRP_INDX','kU2'),('GRP_MODE','kU2'),
        ('GRP_RADX','kU1'),('PGM_CHAR','kCn'),('RTN_CHAR','kCn'),
        ('PGM_CHAL','kCn'),('RTN_CHAL','kCn')),
    'RDR':(
        ('NUM_BINS','U2k'),('RSTS_BIN','kU2')),
    'WRR':(
        ('HEAD_NUM','U1'),('SITE_GRP','U1'),('FINISH_T','U4'),
        ('PART_CNT','U4'),('RSTS_CNT','U4'),('ABRT_CNT','U4'),
        ('GOOD_CNT','U4'),('FUNC_CNT','U4'),('WAFER_ID','Cn'),
        ('FABWF_ID','Cn'),('FRAME_ID','Cn'),('MASK_ID','Cn'),
        ('USR_DESC','Cn'),('EXC_DESC','Cn')),
    'WCR':(
        ('WAFR_SIZ','R4'),('DIE_HT','R4'),('DIE_WID','R4'),
        ('WF_UNITS','U1'),('WF_FLAT','C1'),('CENTER_X','I2'),
        ('CENTER_Y','I2'),('POS_X','C1'),('POS_Y','C1')),
    'PIR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1')),
    'TSR':(
        ('HEAD_NUM','U1'),('SITE_NUM','U1'),('TEST_TYP','C1'),
        ('TEST_NUM','U4'),('EXEC_CNT','U4'),('FAIL_CNT','U4'),
        ('ALRM_CNT','U4'),('TEST_NAM','Cn'),('SEQ_NAME','Cn'),
        ('TEST_LBL','Cn'),('OPT_FLAG','B1'),('TEST_TIM','R4'),
        ('TEST_MIN','R4'),('TEST_MAX','R4'),('TST_SUMS','R4'),
        ('TST_SQRS','R4')),
    'PTR':(
        ('TEST_NUM','U4'),('HEAD_NUM','U1'),('SITE_NUM','U1'),
        ('TEST_FLG','B1'),('PARM_FLG','B1'),('RESULT','R4'),
        ('TEST_TXT','Cn'),('ALARM_ID','Cn'),
        ('OPT_FLAG','B1'),('RES_SCAL','I1'),('LLM_SCAL','I1'),
        ('HLM_SCAL','I1'),('LO_LIMIT','R4'),('HI_LIMIT','R4'),
        ('UNITS','Cn'),('C_RESFMT','Cn'),('C_LLMFMT','Cn'),
        ('C_HLMFMR','Cn'),('LO_SPEC','R4'),('HI_SPEC','R4')),
    'MPR':(
        ('TEST_NUM','U4'),('HEAD_NUM','U1'),('SITE_NUM','U1'),
        ('TEST_FLG','B1'),('PARM_FLG','B1'),('RTN_ICNT','U2j'),
        ('RSLT_CNT','U2k'),('RTN_STAT','jN1'),('RTN_RSLT','kR4'),
        ('TEST_TXT','Cn'),('ALARM_ID','Cn'),('OPT_FLAG','B1'),
        ('RES_SCAL','I1'),('LLM_SCAL','I1'),('HLM_SCAL','I1'),
        ('LO_LIMIT','R4'),('HI_LIMIT','R4'),('START_IN','R4'),
        ('INCR_IN','R4'),('RTN_INDX','jU2'),('UNITS','Cn'),
        ('UNITS_IN','Cn'),('C_RESFMT','Cn'),('C_LLMFMT','Cn'),
        ('C_HLMFMT','Cn'),('LO_SPEC','R4'),('HI_SPEC','R4')),
    'FTR':(
        ('TEST_NUM','U4'),('HEAD_NUM','U1'),('SITE_NUM','U1'),
        ('TEST_FLG','B1'),('OPT_FLG','B1'),('CYCL_CNT','U4'),
        ('REL_VADR','U4'),('REPT_CNT','U4'),('NUM_FAIL','U4'),
        ('XFAIL_AD','I4'),('YFAIL_AD','I4'),('VECT_OFF','I2'),
        ('RTN_ICNT','U2j'),('PGM_ICNT','U2k'),('RTN_INDX','jU2'),
        ('RTN_STAT','jN1'),('PGM_INDX','kU2'),('PGM_STAT','kN1'),
        ('FAIL_PIN','Dn'),('VECT_NAM','Cn'),('TIME_SET','Cn'),
        ('OP_CODE','Cn'),('TEST_TXT','Cn'),('ALARM_ID','Cn'),
        ('PROG_TXT','Cn'),('RSLT_TXT','Cn'),('PATG_NUM','U1'),
        ('SPIN_MAP','Dn')),
    # Change data type tuple to list for only 1 field records, BPS & DTR, 
    # because of python would auto parse tuple (()) to () if only 1 item
    # The program will run error when try to get first tuple in tuple
    'BPS':[
        ('SEQ_NAME','Cn')],
    'EPS':(),
    'GDR':(
        ('FLD_CNT','U2'),('GEN_DATA','Vn')),
    'DTR':[
        ('TEXT_DAT','Cn')],
}