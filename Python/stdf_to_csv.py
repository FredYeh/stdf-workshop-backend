import stdfReader
import gzip, io, gc, time, json
from datetime import datetime, timezone


def read_stdf(filename: str) -> dict:

    def get_io(stdf_path: str):
        if stdf_path.lower().endswith('gz'):
            tmp = gzip.open(stdf_path, 'rb')
            content = tmp.read()
            fp = io.BytesIO(content)
            del content
            gc.collect()
            return fp
        else:
            return open(stdf_path, 'rb')

    def is_special_num(val: int|float) -> bool:
        return (val in [float('inf'),float('-inf')]) or (val != val)

    f = get_io(filename)
    f.read()
    eof = f.tell()
    f.seek(0)
    record, pos = '', 0
    headers = {}
    stdf_type = ''
    sBins, hBins = {}, {}
    test_items = {}
    tested_sites = []
    dies = {}
    progress_time = time.time()
    xs, ys = set(), set()
    try:
        while 'MRR' not in record:
            record, nextpos = stdfReader.readSTDF(f, pos)
            if time.time()-progress_time >= 5 or nextpos==eof:
                progress_time = time.time()
                print(json.dumps(
                        { 
                            'target': 'stdf2csv', 
                            'msg': {
                                'status':'parserProgress',
                                'number': '%d%s (%d/%d)' %(round((pos/eof)*90), '%', pos, eof)
                            }
                        }
                    )
                )
            if record == '!COM':
                raise EOFError('Incompleted record read, at %d' %pos)
            elif record[0] in ['MIR', 'SDR', 'WIR', 'WCR', 'WRR', 'MRR']:
                headers[record[0]] = record[1]
            elif record[0] == 'PIR':
                tested_sites.append(record[1]['SITE_NUM'])
            elif record[0] in ('PTR', 'MPR', 'FTR'):
                no = record[1]['TEST_NUM']
                name = record[1].get('TEST_TXT', '')
                site = record[1]['SITE_NUM']
                pf = record[1]['TEST_FLG'] < 128
                value = record[1].get('RESULT', 1 if pf else 0)
                patt = record[1].get('VECT_NAM', '')
                if is_special_num(value): value = 1
                # if not value:
                #     t_flat = record[1]['TEST_FLG']
                #     value = 'pass' if t_flat < 128 else 'fail'
                if (no, name, patt) not in test_items:
                    unit = record[1].get('UNITS', '')
                    l_limit = record[1].get('LO_LIMIT', '')
                    h_limit = record[1].get('HI_LIMIT', '')
                    res_scal = record[1].get('RES_SCAL', 0)
                    llm_scal = record[1].get('LLM_SCAL', 0)
                    hlm_scal = record[1].get('HLM_SCAL', 0)
                    if is_special_num(l_limit): l_limit = ''
                    if is_special_num(h_limit): h_limit = ''
                    if unit != '': unit = simplify_unit(res_scal) + unit
                    if l_limit != '': l_limit = l_limit * (10 ** llm_scal)
                    if h_limit != '': h_limit = h_limit * (10 ** hlm_scal)
                    test_items[(no, name, patt)] = {
                        'unit': unit, 'hi': h_limit, 'lo': l_limit, 'scal': res_scal,
                    }
                value = value * (10 ** test_items[(no, name, patt)]['scal'])
                test_items[(no, name, patt)][((tested_sites.index(site)+len(dies)))] = value
            elif record[0] == 'PRR':
                tested_sites = []
                xc = record[1]['X_COORD']
                yc = record[1]['Y_COORD']
                site = record[1]['SITE_NUM']
                sBin = record[1]['SOFT_BIN']
                hBin = record[1]['HARD_BIN']
                tTime = record[1]['TEST_T']
                pid = record[1].get('PART_ID', '')
                dies[len(dies)] = {'X':xc, 'Y':yc, 'pid': pid, 'sBin': sBin, 'hBin': hBin,'site':site,'time': tTime}
                xs.add(xc); ys.add(yc)
            elif record[0] == 'SBR':
                b = record[1]['SBIN_NUM']
                bName = record[1].get('SBIN_NAM','')
                if b not in sBins:
                    sBins[b] = bName
            elif record[0] == 'HBR':
                b = record[1]['HBIN_NUM']
                bName = record[1].get('HBIN_NAM','')
                if b not in hBins:
                    hBins[b] = bName
            pos = nextpos
    except:
        print(json.dumps(
                { 
                    'target': 'stdf2csv', 
                    'msg': {
                        'status':'parserProgress',
                        'number': '90% (incomplete STDF)',
                    }
                }
            )
        )
    stdf_type = 'FT' if len(xs) == 1 and len(ys) == 1 else 'FT'
    return {'header': headers, 'type': stdf_type,'dies': dies, 'sBins':sBins, 'hBins':hBins, 'items': test_items,}


def simplify_unit(res: int) -> str:
    return {
        15: 'f', 12: 'p', 9: 'n', 6: 'u', 3: 'm',
        2: '%', -3: 'K', -6: 'M', -9: 'G', -12: 'T'
    }.get(res, '')

def update_unit(unit: str, val: float) -> float:
    if unit.startswith('M'):
        return val / 1_000_000
    elif unit.startswith('K'):
        return val / 1_000
    elif unit.startswith('u'):
        return val * 1_000_000
    elif unit.startswith('m'):
        return val * 1_000
    else:
        return val

def translate_time(tStamp: float) -> str:
    tmp = datetime.fromtimestamp(tStamp, tz=timezone.utc)
    ans = tmp.strftime('%Y_%m_%d %H:%M:%S')
    return ans

def write_csv_CP(stdf_info: dict, output: str):
    fp = open(output, 'w')
    fp.write('# Semiconductor Yield Analysis is easy with Quantix!\n')
    fp.write('# Check latest news: www.mentor.com\n')
    fp.write('# Created by: Examinator-Pro - V7.7.30\n')
    fp.write('# Examinator Data File: Edit/Add/Remove any data you want!\n\n')
    fp.write('--- Csv version:\n')
    fp.write('Major,2\n')
    fp.write('Minor,1\n')
    fp.write('--- Global Info:\n')
    fp.write('Date,'); tmp = stdf_info['header'].get('MIR',{}).get('START_T',0)
    start_t = translate_time(tmp)
    fp.write('%s\n' %start_t)
    fp.write('SetupTime,'); tmp = stdf_info['header'].get('MIR',{}).get('SETUP_T',0)
    setup_t = translate_time(tmp)
    fp.write('%s\n' %setup_t)
    fp.write('StartTime,%s\n' %start_t)
    fp.write('FinishTime,'); tmp = stdf_info['header'].get('MRR',{}).get('FINISH_T',0)
    finish_t = translate_time(tmp)
    fp.write('%s\n' %finish_t)
    fp.write('ProgramName,%s\n' %stdf_info['header'].get('MIR',{}).get('JOB_NAM',''))
    fp.write('Lot,%s\n' %stdf_info['header'].get('MIR',{}).get('LOT_ID',''))
    fp.write('Wafer_Pos_X, \n')
    fp.write('Wafer_Pos_Y, \n')
    fp.write('TesterName,%s\n' %stdf_info['header'].get('MIR',{}).get('NODE_NAM',''))
    fp.write('TesterType,%s\n' %stdf_info['header'].get('MIR',{}).get('TSTR_TYP',''))
    fp.write('Operator,%s\n' %stdf_info['header'].get('MIR',{}).get('OPER_NAM',''))
    fp.write('ExecType,%s\n' %stdf_info['header'].get('MIR',{}).get('EXEC_TYP',''))
    fp.write('ExecRevision,%s\n' %stdf_info['header'].get('MIR',{}).get('EXEC_VER',''))
    fp.write('TestCode,%s\n' %stdf_info['header'].get('MIR',{}).get('TEST_COD',''))
    fp.write('ModeCode,%s\n' %stdf_info['header'].get('MIR',{}).get('MODE_COD',''))
    fp.write('PackageType,%s\n' %stdf_info['header'].get('MIR',{}).get('PKG_TYP',''))
    for b in sorted(stdf_info['sBins']):
        fp.write('SoftBinName,')
        fp.write('%d,' %b)
        fp.write('%s\n' %stdf_info['sBins'][b])
    for b in sorted(stdf_info['hBins']):
        fp.write('HardBinName,')
        fp.write('%d,' %b)
        fp.write('%s\n' %stdf_info['hBins'][b])
    fp.write('--- Site details:, Head #%s\n' %stdf_info['header'].get('SDR',{}).get('HEAD_NUM'))
    fp.write('Site group,%s\n' %stdf_info['header'].get('SDR',{}).get('SITE_GRP'))
    fp.write('Testing sites,')
    fp.write(','.join(str(x) for x in stdf_info['header'].get('SDR',{}).get('SITE_NUM')) + '\n')
    fp.write('--- Options:\n')
    fp.write('UnitsMode,scaling_factor\n\n')
    fp.write('Parameter,SBIN,HBIN,DIE_X,DIE_Y,SITE,TIME,TOTAL_TESTS,LOT_ID,WAFER_ID,')
    fp.write(','.join(key[1] for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Tests#,,,,,,,,,,')
    fp.write(','.join(str(key[0]) for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Patterns,,,,,,,,,,')
    fp.write(','.join(key[2] for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Unit,,,,,,sec.,,,,')
    fp.write(','.join(stdf_info['items'][no]['unit'] for no in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('HighL,,,,,,,,,,')
    fp.write(','.join(str(stdf_info['items'][no]['hi']) for no in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('LowL,,,,,,,,,,')
    fp.write(','.join(str(stdf_info['items'][no]['lo']) for no in sorted(stdf_info['items'])))
    fp.write('\n')
    for idx in range(len(stdf_info['dies'])):
        pid = 'PID-' + stdf_info["dies"][idx]["pid"]
        pid_items = [stdf_info['items'][key].get(idx, '') for key in sorted(stdf_info['items'])]
        fp.write(f'{pid},{stdf_info["dies"][idx]["sBin"]},{stdf_info["dies"][idx]["hBin"]},')
        fp.write(f'{stdf_info["dies"][idx]["X"]},{stdf_info["dies"][idx]["Y"]},')
        fp.write(f'{stdf_info["dies"][idx]["site"]},{stdf_info["dies"][idx]["time"]/1000},')
        fp.write(f'{len([x for x in pid_items if x != ""])}' + ',')
        fp.write(f'{stdf_info["header"].get("MIR",{}).get("LOT_ID","")},{stdf_info["header"].get("WIR",{}).get("WAFER_ID","")},')
        fp.write(','.join(map(str, pid_items)) + '\n')
    print(json.dumps(
            { 
                'target': 'stdf2csv', 
                'msg': {
                    'status':'parserProgress',
                    'number': '100% (---/---)',
                }
            }
        )
    )
    fp.close()


def write_csv_FT(stdf_info: dict, output: str):
    fp = open(output, 'w')
    fp.write('# Semiconductor Yield Analysis is easy with Galaxy! \n')
    fp.write('# Check latest news: www.galaxysemi.com \n')
    fp.write('# Created by: Examinator-Pro - V7.5.5\n')
    fp.write('# Examinator Data File: Edit/Add/Remove any data you want! \n\n')
    fp.write('--- Csv version:\n')
    fp.write('Major,2\n')
    fp.write('Minor,1\n')
    fp.write('--- Global Info:\n')
    fp.write('Date,'); tmp = stdf_info['header'].get('MIR',{}).get('START_T',0)
    start_t = translate_time(tmp)
    fp.write('%s\n' %start_t)
    fp.write('SetupTime,'); tmp = stdf_info['header'].get('MIR',{}).get('SETUP_T',0)
    setup_t = translate_time(tmp)
    fp.write('%s\n' %setup_t)
    fp.write('StartTime,%s\n' %start_t)
    fp.write('FinishTime,'); tmp = stdf_info['header'].get('MRR',{}).get('FINISH_T',0)
    finish_t = translate_time(tmp)
    fp.write('%s\n' %finish_t)
    fp.write('ProgramName,%s\n' %stdf_info['header'].get('MIR',{}).get('JOB_NAM',''))
    fp.write('ProgramRevision,%s\n' %stdf_info['header'].get('MIR',{}).get('JOB_REV',''))
    fp.write('Lot,%s\n' %stdf_info['header'].get('MIR',{}).get('LOT_ID',''))
    fp.write('SubLot,%s\n' %stdf_info['header'].get('MIR',{}).get('SBLOT_ID',''))
    fp.write('Wafer_Pos_X, \n')
    fp.write('Wafer_Pos_Y, \n')
    fp.write('TesterName,%s\n' %stdf_info['header'].get('MIR',{}).get('NODE_NAM',''))
    fp.write('TesterType,%s\n' %stdf_info['header'].get('MIR',{}).get('TSTR_TYP',''))
    fp.write('Product,%s\n' %stdf_info['header'].get('MIR',{}).get('PART_TYP',''))
    fp.write('Operator,%s\n' %stdf_info['header'].get('MIR',{}).get('OPER_NAM',''))
    fp.write('ExecType,%s\n' %stdf_info['header'].get('MIR',{}).get('EXEC_TYP',''))
    fp.write('ExecRevision,%s\n' %stdf_info['header'].get('MIR',{}).get('EXEC_VER',''))
    fp.write('ModeCode,%s\n' %stdf_info['header'].get('MIR',{}).get('MODE_COD',''))
    fp.write('RtstCode,%s\n' %stdf_info['header'].get('MIR',{}).get('RTST_COD',''))
    fp.write('BurnTime,%s\n' %stdf_info['header'].get('MIR',{}).get('BURN_TIM',''))
    fp.write('Temperature,%s\n' %stdf_info['header'].get('MIR',{}).get('TST_TEMP',''))
    fp.write('Facility,%s\n' %stdf_info['header'].get('MIR',{}).get('FACIL_ID',''))
    fp.write('EngineeringLotID,%s\n' %stdf_info['header'].get('MIR',{}).get('ENG_ID',''))
    fp.write('--- Site details:, Head #%s\n' %stdf_info['header'].get('SDR',{}).get('HEAD_NUM',''))
    fp.write('Site group,%s\n' %stdf_info['header'].get('SDR',{}).get('SITE_GRP',''))
    fp.write('Testing sites,')
    fp.write(' '.join(str(x) for x in stdf_info['header'].get('SDR',{}).get('SITE_NUM','')) + '\n')
    fp.write('Handler type,%s\n' %stdf_info['header'].get('SDR',{}).get('HAND_TYP',''))
    fp.write('Handler ID,%s\n' %stdf_info['header'].get('SDR',{}).get('HAND_ID',''))
    fp.write('Load board ID,%s\n' %stdf_info['header'].get('SDR',{}).get('LOAD_ID',''))
    fp.write('--- Options:\n')
    fp.write('UnitsMode,scaling_factor\n\n')
    fp.write('Parameter,SBIN,HBIN,DIE_X,DIE_Y,SITE,TIME,TOTAL_TESTS,LOT_ID,WAFER_ID,')
    fp.write(','.join(key[1] for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Tests#,,,,,,,,,,')
    fp.write(','.join(str(key[0]) for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Patterns,,,,,,,,,,')
    fp.write(','.join(key[2] for key in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('Unit,,,,,,sec.,,,,')
    fp.write(','.join(stdf_info['items'][no]['unit'] for no in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('HighL,,,,,,,,,,')
    fp.write(','.join(str(stdf_info['items'][no]['hi']) for no in sorted(stdf_info['items'])))
    fp.write('\n')
    fp.write('LowL,,,,,,,,,,')
    fp.write(','.join(str(stdf_info['items'][no]['lo']) for no in sorted(stdf_info['items'])))
    fp.write('\n')
    for idx in range(len(stdf_info['dies'])):
        pid = 'PID-' + stdf_info["dies"][idx]["pid"]
        pid_items = [stdf_info['items'][key].get(idx, '') for key in sorted(stdf_info['items'])]
        fp.write(f'{pid},{stdf_info["dies"][idx]["sBin"]},{stdf_info["dies"][idx]["hBin"]},')
        fp.write(f'{stdf_info["dies"][idx]["X"]},{stdf_info["dies"][idx]["Y"]},')
        fp.write(f'{stdf_info["dies"][idx]["site"]},{stdf_info["dies"][idx]["time"]/1000},')
        fp.write(f'{len([x for x in pid_items if x != ""])}' + ',')
        fp.write(f'{stdf_info["header"].get("MIR",{}).get("LOT_ID","")},{stdf_info["header"].get("WIR",{}).get("WAFER_ID","")},')
        fp.write(','.join(map(str, pid_items)) + '\n')
    print(json.dumps(
            { 
                'target': 'stdf2csv', 
                'msg': {
                    'status':'parserProgress',
                    'number': '100% (---/---)',
                }
            }
        )
    )
    fp.close()


if __name__ == '__main__':
    import sys
    file, output = sys.argv[1], sys.argv[2]
    output_filename = r'files\output' + f'\\{output}'
    info = read_stdf(file)
    {'CP': write_csv_CP, 'FT': write_csv_FT}[info['type']](info, output_filename)