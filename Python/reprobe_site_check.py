import gzip, io, gc, time, json
from datetime import datetime
from os.path import basename
import xlsxwriter

import stdfReader

def write_report(wb: xlsxwriter.Workbook, stdf_path: str):
    # cell formats
    sc_title = wb.add_format({'font':'Arial','bg_color':'yellow','border':1,'font_size':10})
    sc_item = wb.add_format({'font':'Arial','border':1,'font_size':10})
    sc_item_percent = wb.add_format({'font':'Arial','border':1,'num_format':'0.00%','font_size':10})
    pass_green = wb.add_format({'font':'Arial','align':'center','bg_color':'lime','font_size':10})
    retest_pass_yellow = wb.add_format({'font':'Arial','align':'center','bg_color':'yellow','font_size':10})
    fail_red = wb.add_format({'font':'Arial','align':'center','bg_color':'red','font_size':10})
    green_front = wb.add_format({'font':'Arial','font_color':'lime','font_size':10})
    red_front = wb.add_format({'font':'Arial','font_color':'red','font_size':10})
    wb.formats[0].set_font_size(10)
    wb.formats[0].set_font('Arial')
    raw_sheet = wb.add_worksheet('Raw Data')
    raw_sheet.freeze_panes(6, 7)
    raw_sheet.set_column('A:A', 20)
    raw_sheet.set_column('B:B', 15)
    raw_sheet.set_column('C:E', 6.5)
    raw_sheet.set_column('F:F', 9)
    raw_sheet.set_column('G:G', 7)
    raw_sheet.write('A6', 'device no')
    raw_sheet.write('B6', 'touch down')
    raw_sheet.write('C6', 'sites')
    raw_sheet.write('D6', 'xCord')
    raw_sheet.write('E6', 'yCord')
    raw_sheet.write('F6', 'testTime')
    raw_sheet.write('G6', 'Bin')
    check_sheet = wb.add_worksheet('RC_check')
    check_sheet.freeze_panes(1,0)
    check_sheet.set_column('A:A', 20)
    check_sheet.set_column('B:B', 15)
    check_sheet.set_column('C:E', 6.5)
    check_sheet.set_column('F:F', 9)
    check_sheet.set_column('G:G', 7)
    check_sheet.set_column('L:L', 12)
    check_sheet.write('A1', 'No.')
    check_sheet.write('B1', 'touch down')
    check_sheet.write('C1', 'sites')
    check_sheet.write('D1', 'xCord')
    check_sheet.write('E1', 'yCord')
    check_sheet.write('F1', 'testTime')
    check_sheet.write('G1', 'Bin')
    check_sheet.write('H1', 'site')
    check_sheet.write('I1', '1 diff, 0 same')
    check_sheet.write('L2', '',sc_title)
    check_sheet.write('M2', 'Total',sc_title)
    check_sheet.write('N2', 'Re-test',sc_title)
    check_sheet.write('O2', 'same site',sc_title)
    check_sheet.write('P2', 'diff site',sc_title)
    check_sheet.write('L3', 'Count',sc_title)
    check_sheet.write('L4', 'Percentage',sc_title)

    def get_stdf_info() -> dict:
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
        record, pos = '', 0         # variable for stdfReader
        count, td_cnt = 0, 0
        record_info = {}            # all header information
        coords = {'x':[],'y':[]}    # x & y coords range
        pos_bin = {}                # all coords bins
        all_sb = {}                 # information for all soft bin
        last_site = 999
        reprobe_cnt = 1
        samesite_cnt = 0
        needed_records = ['MIR','SDR','PRR','MRR']
        stdf_fp = get_io(stdf_path)
        stdf_fp.read()
        eof = stdf_fp.tell()
        stdf_fp.seek(0)
        start_time = time.time()
        progress_time = time.time()
        try:
            while 'MRR' not in record:
                record, pos = stdfReader.readSTDFspecifyRecs(stdf_fp, pos, needed_records)
                if time.time()-progress_time >= 3 or pos==eof:
                    progress_time = time.time()
                    print(json.dumps(
                            { 
                                'target': 'recipeBuyoff', 
                                'msg': {
                                    'status':'parserProgress',
                                    'number': '%d%s (%d/%d)' %(round((pos/eof)*100), '%', pos, eof)
                                }
                            }
                        )
                    )
                    # print('\rPercentage: %3.6f%s (%d/%d)' %((pos/eof)*100, '%', pos, eof), end='')
                if '!COM' in record:
                    raise EOFError('Incompleted record read, at %d' %pos)
                if record[0] in ['MIR','SDR','WIR','WRR','MRR']:
                    record_info[record[0]] = record[1]
                elif 'PRR' in record:
                    count += 1
                    sn = record[1]['SITE_NUM']
                    xc = record[1]['X_COORD']
                    yc = record[1]['Y_COORD']
                    test_time = record[1]['TEST_T'] / 1000
                    sb = record[1]['SOFT_BIN']
                    pf = False if ('%4s' %(bin(record[1]['PART_FLG'])))[-4] == '1' else True
                    if sn <= last_site:
                        td_cnt += 1
                    if sb not in all_sb:
                        all_sb[sb] = {
                            'pass': pf,
                        }
                    coords['x'].append(xc), coords['y'].append(yc)
                    if (xc,yc) not in pos_bin:
                        pos_bin[(xc,yc)] = [[sb], [sn], count, test_time, td_cnt]
                    else:
                        pos_bin[(xc,yc)][0].append(sb)
                        pos_bin[(xc,yc)][1].append(sn)
                        is_same = pos_bin[(xc,yc)][1][0] == sn
                        if is_same:
                            samesite_cnt += 1
                        fmt = red_front if is_same else green_front
                        check_sheet.write(reprobe_cnt, 0, pos_bin[(xc,yc)][2], fmt)
                        check_sheet.write(reprobe_cnt, 1, pos_bin[(xc,yc)][4], fmt)
                        check_sheet.write(reprobe_cnt, 2, pos_bin[(xc,yc)][1][0], fmt)
                        check_sheet.write(reprobe_cnt, 3, xc, fmt)
                        check_sheet.write(reprobe_cnt, 4, yc, fmt)
                        check_sheet.write(reprobe_cnt, 5, pos_bin[(xc,yc)][3], fmt)
                        check_sheet.write(reprobe_cnt, 6, pos_bin[(xc,yc)][0][0], fmt)
                        check_sheet.write(reprobe_cnt, 7, 'same' if is_same else 'diff', fmt)
                        check_sheet.write(reprobe_cnt, 8, 1 if is_same else 0, fmt)
                        check_sheet.write(reprobe_cnt+1, 0, count, fmt)
                        check_sheet.write(reprobe_cnt+1, 1, td_cnt, fmt)
                        check_sheet.write(reprobe_cnt+1, 2, sn, fmt)
                        check_sheet.write(reprobe_cnt+1, 3, xc, fmt)
                        check_sheet.write(reprobe_cnt+1, 4, yc, fmt)
                        check_sheet.write(reprobe_cnt+1, 5, test_time, fmt)
                        check_sheet.write(reprobe_cnt+1, 6, sb, fmt)
                        check_sheet.write(reprobe_cnt+1, 7, 'same' if is_same else 'diff', fmt)
                        check_sheet.write(reprobe_cnt+1, 8, 1 if is_same else 0, fmt)
                        reprobe_cnt += 2
                    raw_sheet.write(count+5, 0, count)
                    raw_sheet.write(count+5, 1, td_cnt)
                    raw_sheet.write(count+5, 2, sn)
                    raw_sheet.write(count+5, 3, xc)
                    raw_sheet.write(count+5, 4, yc)
                    raw_sheet.write(count+5, 5, test_time)
                    raw_sheet.write(count+5, 6, sb)
                    last_site = sn
        except:
            print(json.dumps(
                    { 
                        'target': 'recipeBuyoff', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '100% (incomplete STDF)',
                        }
                    }
                )
            )
        # print("\n--- %.3f seconds ---" % (time.time() - start_time))
        info = {
            'records':record_info,
            'coords': pos_bin,
            'soft_bins': all_sb,
            'reprobe':{'total':reprobe_cnt // 2, 'same_site':samesite_cnt},
            'x':{'max':max(coords['x']),'min':min(coords['x'])},
            'y':{'max':max(coords['y']),'min':min(coords['y'])},
        }
        return info

    stdf_values = get_stdf_info()
    gross_die = len(stdf_values['coords'])
    
    def bin_map_color(bins: list):
        if stdf_values['soft_bins'][bins[-1]]['pass'] == True:
            if len(bins) > 1:
                return retest_pass_yellow
            else:
                return pass_green
        else:
            return fail_red
    
    def site_map_color(site_list: list):
        if len(site_list) > 1:
            if site_list[0] == site_list[-1]:
                return fail_red
            else:
                return pass_green
        else:
            return retest_pass_yellow

    raw_sheet.write('A1','Tester Name: %s' %stdf_values['records'].get('MIR', {}).get('NODE_NAM', ''))
    raw_sheet.write('A2','Job Name: %s' %stdf_values['records'].get('MIR', {}).get('JOB_NAM', ''))
    raw_sheet.write('A3','Start Time: %s' %datetime.fromtimestamp(stdf_values['records'].get('MIR', {}).get('START_T', '')))
    raw_sheet.write('A4','Finish Time: %s' %datetime.fromtimestamp(stdf_values['records'].get('MRR', {}).get('FINISH_T', '')))
    raw_sheet.write('A5','Lot ID: %s' %stdf_values['records'].get('MIR', {}).get('LOT_ID', ''))
    raw_sheet.write('B1','Cust: %s' %stdf_values['records'].get('MIR', {}).get('USER_TXT', ''))
    raw_sheet.write('B2','Device: %s' %stdf_values['records'].get('MIR', {}).get('PART_TYP', ''))
    raw_sheet.write('B3','Stage: %s' %stdf_values['records'].get('MIR', {}).get('FLOW_ID', ''))
    raw_sheet.write('B4','P/C ID: %s' %stdf_values['records'].get('SDR', {}).get('CARD_ID', ''))
    raw_sheet.write('B5','Prober ID: %s' %stdf_values['records'].get('SDR', {}).get('HAND_ID', ''))
    raw_sheet.write('C1','Test Head: %s' %stdf_values['records'].get('SDR', {}).get('HEAD_NUM', ''))
    raw_sheet.write('C2','Gross Die: %d' %gross_die)
    raw_sheet.write('C3','OP ID: %s' %stdf_values['records'].get('MIR', {}).get('OPER_NAM', ''))
    check_sheet.write('M3',gross_die,sc_item)
    check_sheet.write('M4',1,sc_item_percent)
    check_sheet.write('N3',stdf_values['reprobe']['total'],sc_item)
    check_sheet.write('N4',stdf_values['reprobe']['total']/gross_die,sc_item_percent)
    check_sheet.write('O3',stdf_values['reprobe']['same_site'],sc_item)
    check_sheet.write('O4',stdf_values['reprobe']['same_site']/stdf_values['reprobe']['total'],sc_item_percent)
    check_sheet.write('P3',stdf_values['reprobe']['total']-stdf_values['reprobe']['same_site'],sc_item)
    check_sheet.write('P4',(stdf_values['reprobe']['total']-stdf_values['reprobe']['same_site'])/stdf_values['reprobe']['total'],sc_item_percent)
    # ============= draw maps =============
    bin_map_sheet = wb.add_worksheet('Bin Map')
    bin_map_sheet.freeze_panes(1, 1)
    bin_map_sheet.set_column('A:ZZ',2.14)
    site_map_sheet = wb.add_worksheet('Site Map')
    site_map_sheet.freeze_panes(1, 1)
    site_map_sheet.set_column('A:ZZ',2.14)
    for i, num in enumerate(range(stdf_values['x']['min'],stdf_values['x']['max']+1)):
        bin_map_sheet.write(0,i+1,num)
        site_map_sheet.write(0,i+1,num)
    for i, num in enumerate(range(stdf_values['y']['min'],stdf_values['y']['max']+1)):
        bin_map_sheet.write(i+1,0,num)
        site_map_sheet.write(i+1,0,num)
    print_bin = lambda l: l[0] if len(l)==1 else '/'.join(str(x) for x in l)
    for x, y in stdf_values['coords'].keys():
        bin_map_sheet.write(y-stdf_values['y']['min']+1, x-stdf_values['x']['min']+1, 
                        print_bin(stdf_values['coords'][(x,y)][0]), bin_map_color(stdf_values['coords'][(x,y)][0]))
        site_map_sheet.write(y-stdf_values['y']['min']+1, x-stdf_values['x']['min']+1, 
                        print_bin(stdf_values['coords'][(x,y)][1]), site_map_color(stdf_values['coords'][(x,y)][1]))
        
def stdf_to_excel(stdf_path: str, excel_name: str):
    excel_name = r'files\output' + f'\\{excel_name}'
    workbook = xlsxwriter.Workbook(excel_name)
    write_report(workbook, stdf_path)
    workbook.close()
    # return basename(excel_name)

import sys
file_path, file_name = sys.argv[1], sys.argv[2]
stdf_to_excel(file_path, file_name)