import sys
import struct
from stdf_spec import *
import time

def mkRecord(record, content):
    rectyp, recsub = list(info.keys())[list(info.values()).index(record)]
    bstring = struct.pack('BB',rectyp,recsub)
    for field, fstruct in RecordTypeMap[record]:
        if content.get(field,None)==None:
            continue
        bstring += writeField(fstruct, content[field])
    bstring = struct.pack('H',len(bstring)-2) +bstring
    return bstring

def writeField(stype, val):
    if stype.startswith('C'):
        res = b''
        if stype.endswith('n'):
            res += struct.pack('B',len(val))
        res += bytes(val,'utf-8')
    elif stype.endswith('k') or stype.endswith('j'):
        jkCount[stype[-1]] = val
        res = struct.pack(unpackFormatMap[stype.strip('k').strip('j')],val)
    elif stype.startswith('k') or stype.startswith('j'):
        res = b''
        for v in val:
            res += struct.pack(unpackFormatMap[stype.strip('k').strip('j')],v)
    elif stype == 'Bn':
        res = b''
        res += struct.pack('B',len(val))
        for v in val:
            res += struct.pack('B', v)
    elif stype == 'Dn':
        res = b''
        head_len = len(val) * 8
        res += struct.pack('H',len(head_len))
        for v in val:
            res += struct.pack('B', v)
    else:
        res = struct.pack(unpackFormatMap[stype],val)
    return res

if __name__ == '__main__':
    #mkRecord('FAR',{'CPU_TYPE':2,'STDF_VER':4})
    mkRecord('MIR',{'START_T': 1627380914, 'JOB_REV': 'TMLX55', 'FAMLY_ID': 'Beamer', 'SBLOT_ID': '15', 'USER_TXT': 'TSMC-U339', 'SPEC_NAM': None, 'EXEC_VER': '10.10.62_uflx', 'PROT_COD': ' ', 'PROC_ID': None, 'SPEC_VER': None, 'JOB_NAM': 'WS2U-PG660-12B-12_MX20', 'SUPR_NAM': None, 'TST_TEMP': '28.1', 'SETUP_T': 1627380588, 'STAT_NUM': 1, 'PART_TYP': 'CD90-PG660-12B', 'SETUP_ID': None, 'ROM_COD': None, 'LOT_ID': 'TBWG10.00', 'OPER_NAM': '91773', 'OPER_FRQ': None, 'DSGN_REV': None, 'FLOOR_ID': 'WS1040168.01.01', 'TSTR_TYP': 'Jaguar', 'AUX_FILE': '', 'BURN_TIM': 0, 'CMOD_COD': ' ', 'ENG_ID': None, 'PKG_TYP': '', 'NODE_NAM': 'TUF82', 'SERL_NUM': None, 'FACIL_ID': 'AMKT6-S', 'FLOW_ID': None, 'MODE_COD': 'P', 'TEST_COD': 'WS2', 'RTST_COD': '0', 'DATE_COD': '', 'EXEC_TYP': 'IG-XL'})
    
