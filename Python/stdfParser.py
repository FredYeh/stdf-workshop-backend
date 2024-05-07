import gzip, io, gc, time, json
from datetime import datetime
from os.path import basename
import xlsxwriter

import stdfReader

def write_report(wb: xlsxwriter.Workbook, stdf_path: str):
    raw_sheet = wb.add_worksheet('Raw Data')
    raw_sheet.freeze_panes(6, 6)
    raw_sheet.set_column('A:A', 20)
    raw_sheet.set_column('B:B', 15)
    raw_sheet.set_column('C:D', 6.5)
    raw_sheet.set_column('E:E', 9)
    raw_sheet.set_column('F:F', 7)
    raw_sheet.write('A6', 'device no')
    raw_sheet.write('B6', 'sites')
    raw_sheet.write('C6', 'xCord')
    raw_sheet.write('D6', 'yCord')
    raw_sheet.write('E6', 'testTime')
    raw_sheet.write('F6', 'Bin')
    items_sheets = [raw_sheet]
    # cell formats
    pass_green = wb.add_format({'align':'center','bg_color':'lime'})
    retest_pass_yellow = wb.add_format({'align':'center','bg_color':'yellow'})
    fail_red = wb.add_format({'align':'center','bg_color':'red'})
    percent = wb.add_format({'num_format': '0.00%'})
    underline = wb.add_format({'bottom':True})
    green_front = wb.add_format({'font_color':'lime'})
    red_front = wb.add_format({'font_color':'red'})
    all_pass = wb.add_format({'num_format': '0.00%','bg_color':'lime'})
    warning = wb.add_format({'num_format': '0.00%','bg_color':'yellow'})
    bad = wb.add_format({'num_format': '0.00%','bg_color':'red'})

    def is_special_num(val: int|float) -> bool:
        return (val in [float('inf'),float('-inf')]) or (val != val)

    def get_item_sheet(item: dict) -> xlsxwriter.Workbook.worksheet_class:
        if item['#'] < 16000:
            return raw_sheet
        else:
            sheet_num = item['#'] // 16000
            sheet_name = 'Test items %d' %sheet_num
            sheet = wb.get_worksheet_by_name(sheet_name)
            if sheet == None:
                sheet = wb.add_worksheet(sheet_name)
                sheet.freeze_panes(6, 6)
                sheet.set_column('A:A', 20)
                sheet.set_column('B:B', 15)
                sheet.set_column('C:D', 6.5)
                sheet.set_column('E:E', 9)
                sheet.set_column('F:F', 7)
                sheet.write('A6', 'device no')
                sheet.write('B6', 'sites')
                sheet.write('C6', 'xCord')
                sheet.write('D6', 'yCord')
                sheet.write('E6', 'testTime')
                sheet.write('F6', 'Bin')
                items_sheets.append(sheet)
            return sheet

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
        count = 0
        record_info = {}            # all header information
        coords = {'x':[],'y':[]}    # x & y coords range
        pos_bin = {}                # all coords bins
        all_sb = {}                 # information for all soft bin
        all_items = {}              # all test items
        testing_sites = []          # testing sites for test item index
        test_item_row_cnt = 6       # row of test item start
        needed_records = ['MIR','SDR','PRR','WIR','WRR','SBR','MRR','PTR']
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
                                'target': 'parser', 
                                'msg': {
                                    'status':'parserProgress',
                                    'number': '%d%s (%d/%d)' %(round((pos/eof)*100), '%', pos, eof)
                                }
                            }
                        )
                    )
                    # print('%3.6f%s (%d/%d)' %((pos/eof)*100, '%', pos, eof), end='')
                if '!COM' in record:
                    raise EOFError('Incompleted record read, at %d' %pos)
                if record[0] in ['MIR','SDR','WIR','WRR','MRR']:
                    record_info[record[0]] = record[1]
                elif 'PTR' in record:
                    item_name = record[1]['TEST_TXT']
                    site = record[1]['SITE_NUM']
                    if site not in testing_sites:
                        testing_sites.append(site)
                    item_pass = False if ('%8s' %(bin(record[1]['TEST_FLG'])))[-8] == '1' else True
                    val = record[1]['RESULT']
                    val = str(val) if is_special_num(val) else val
                    if item_name not in all_items:
                        tmp = record[1].get('HI_LIMIT','None')
                        upper_limit = str(tmp) if is_special_num(tmp) else tmp
                        tmp = record[1].get('LO_LIMIT','None')
                        lower_limit = str(tmp) if is_special_num(tmp) else tmp
                        all_items[item_name] = {
                            '#': len(all_items),
                            'total': 0,
                            'pass': 0,
                        }
                        current_sheet = get_item_sheet(all_items[item_name])
                        col = (all_items[item_name]['#'] % 16000) + 6
                        current_sheet.set_column(col, col, 30)
                        current_sheet.write(0, col, 't%d' %(all_items[item_name]['#']+1))
                        current_sheet.write(1, col, item_name)
                        current_sheet.write(2, col, upper_limit, red_front)
                        current_sheet.write(3, col, lower_limit, green_front)
                    else:
                        current_sheet = get_item_sheet(all_items[item_name])
                        col = (all_items[item_name]['#'] % 16000) + 6
                    all_items[item_name]['total'] += 1
                    all_items[item_name]['pass'] += 1 if item_pass else 0
                    current_sheet.write(testing_sites.index(site)+test_item_row_cnt, col, val, red_front if not item_pass else None)
                elif 'PRR' in record:
                    test_item_row_cnt += len(testing_sites)
                    testing_sites = []
                    count += 1
                    sn = record[1]['SITE_NUM']
                    xc = record[1]['X_COORD']
                    yc = record[1]['Y_COORD']
                    test_time = record[1]['TEST_T'] / 1000
                    sb = record[1]['SOFT_BIN']
                    hb = record[1]['HARD_BIN']
                    stdf_type = 'FT' if (xc==-32768 and yc==-32768) else 'CP'
                    pf = False if ('%4s' %(bin(record[1]['PART_FLG'])))[-4] == '1' else True
                    if sb not in all_sb:
                        all_sb[sb] = {
                            'hard_bin': hb,
                            'pass': pf,
                        }
                    coords['x'].append(xc), coords['y'].append(yc)
                    if stdf_type == 'CP':
                        if (xc,yc) not in pos_bin:
                            pos_bin[(xc,yc)] = [[sb],sn]
                        else:
                            pos_bin[(xc,yc)][0].append(sb)
                    else:
                        pos_bin[count] = [[sb],sn]
                    for sheet in items_sheets:
                        sheet.write(count+5, 0, count)
                        sheet.write(count+5, 1, sn)
                        sheet.write(count+5, 2, xc)
                        sheet.write(count+5, 3, yc)
                        sheet.write(count+5, 4, test_time)
                        sheet.write(count+5, 5, sb)
                elif 'SBR' in record:
                    sb = record[1]['SBIN_NUM']
                    if sb in all_sb:
                        all_sb[sb]['bin_name'] = record[1].get('SBIN_NAM','')
        except:
            print(json.dumps(
                    { 
                        'target': 'parser', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '100% (incomplete STDF)',
                        }
                    }
                )
            )
        # print("\n--- %.3f seconds ---" % (time.time() - start_time))
        info = {
            'type':stdf_type,
            'records':record_info,
            'coords': pos_bin,
            'test_items': all_items,
            'soft_bins': all_sb,
            'x':{'max':max(coords['x']),'min':min(coords['x'])},
            'y':{'max':max(coords['y']),'min':min(coords['y'])},
        }
        return info

    header_sheet = wb.add_worksheet('Title')
    header_sheet.set_column('A:A', 14)
    header_sheet.set_column('B:B', 30)
    header_sheet.write('F1', 'HBin')
    header_sheet.write('G1', 'SBin')
    header_sheet.write('H1', 'P/F')
    header_sheet.write('I1', 'SB name')
    bin_table_sheet = wb.add_worksheet('Bin Table')
    bin_table_sheet.freeze_panes(1,0)
    bin_table_sheet.write('A1','H-Bin')
    bin_table_sheet.write('B1','S-Bin')
    bin_table_sheet.write('C1','P/F')
    bin_table_sheet.write('D1','SB name')

    stdf_values = get_stdf_info()
    tmp = stdf_values['records'].get('MIR',{}).get('START_T','')
    stdf_start_time = tmp if tmp == '' else datetime.fromtimestamp(tmp)
    tmp = stdf_values['records'].get('MRR',{}).get('FINISH_T','')
    stdf_end_time = tmp if tmp == '' else datetime.fromtimestamp(tmp)
    gross_die = len(stdf_values['coords'])
    
    def map_color(bins: list):
        if stdf_values['soft_bins'][bins[-1]]['pass'] == True:
            if len(bins) > 1:
                return retest_pass_yellow
            else:
                return pass_green
        else:
            return fail_red

    def get_bin_by_sites(mode: str) -> dict:
        p = 0 if mode=='first' else -1
        bin_by_sites = {x[1]:{} for x in stdf_values['coords'].values()}
        for x in stdf_values['coords'].values():
            if (mode == 'retest') and (len(x[0]) == 1):
                continue
            if x[0][p] not in bin_by_sites[x[1]]:
                bin_by_sites[x[1]][x[0][p]] = 1
            else:
                bin_by_sites[x[1]][x[0][p]] += 1
        return bin_by_sites
    
    def write_num(sheet: xlsxwriter.Workbook.worksheet_class, row: int, col: int, numer: int, denom: int, fmt):
        if fmt==None:
            sheet.write(row, col, numer)
        else:
            if denom==0:
                sheet.write(row, col, 0, fmt)
            else:
                sheet.write(row, col, numer/denom, fmt)

    get_bin_summary = lambda bin_list: {x:bin_list.count(x) for x in set(bin_list)}

    def write_summary(sheet: xlsxwriter.Workbook.worksheet_class, title: str, bins_qty: dict, bin_by_sn: dict, 
                        y_start: int, x_start: int, data_format=None) -> int:
        sheet.write(y_start, x_start, title)
        sheet.write(y_start+1, x_start, 'HBin')
        sheet.write(y_start+1, x_start+1, 'SBin')
        sheet.write(y_start+1, x_start+2, 'P/F')
        sheet.write(y_start+1, x_start+3, 'Qty')
        total = sum(bins_qty.values())
        pass_bin = sum([bins_qty[x] for x in bins_qty.keys() if stdf_values['soft_bins'][x]['pass']])
        for p, sn in enumerate(sorted(bin_by_sn.keys())):
            sheet.write(y_start+1, x_start+4+p, 'S%d' %(sn))
        sheet.write(y_start+1, x_start+5+p, 'SB_Name')
        for c, b in enumerate(sorted(bins_qty.keys(), key=lambda x: stdf_values['soft_bins'][x]['hard_bin'])):
            sheet.write(c+y_start+2, x_start, stdf_values['soft_bins'][b]['hard_bin'])
            sheet.write(c+y_start+2, x_start+1, b)
            sheet.write(c+y_start+2, x_start+2, 'P' if stdf_values['soft_bins'][b]['pass'] else 'F')
            write_num(sheet, c+y_start+2, x_start+3, bins_qty[b], gross_die, data_format)
            for p, sn in enumerate(sorted(bin_by_sn.keys())):
                write_num(sheet, c+y_start+2, x_start+4+p, bin_by_sn[sn].get(b, 0), sum(bin_by_sn[sn].values()), data_format)
            sheet.write(c+y_start+2, x_start+5+p, stdf_values['soft_bins'][b].get('bin_name', ''))
        sheet.write(c+y_start+3, x_start+2, 'Total')
        write_num(sheet, c+y_start+3, x_start+3, total, gross_die, data_format)
        for p, sn in enumerate(sorted(bin_by_sn.keys())):
            write_num(sheet, c+y_start+3, p+x_start+4, sum(bin_by_sn[sn].values()), sum(bin_by_sn[sn].values()), data_format)
        sheet.write(c+y_start+4, x_start+2, 'Pass:')
        sheet.write(c+y_start+4, x_start+3, pass_bin)
        sheet.write(c+y_start+5, x_start+2, 'Fail:')
        sheet.write(c+y_start+5, x_start+3, total-pass_bin)
        sheet.write(c+y_start+6, x_start+2, 'Yield:')
        if data_format==None:
            sheet.write(c+y_start+6, x_start+3, (pass_bin/total), percent)
        else:
            sheet.write(c+y_start+6, x_start+3, (pass_bin/gross_die), percent)
        if data_format!=None:
            sheet.set_row(c+y_start+7, None, underline)
        return c+y_start+6

    def write_recovery(sheet, bin_by_sn: dict, y_start: int, data_format=None) -> int:
        recover = {}
        recover_by_sites = {}
        for x in stdf_values['coords'].values():
            if len(x[0])>1 and x[0][-1] == 1:
                if (x[0][0],x[0][-1]) not in recover:
                    recover[x[0][0], x[0][-1]] = 1
                else:
                    recover[x[0][0], x[0][-1]] += 1
                if x[1] not in recover_by_sites:
                    recover_by_sites[x[1]] = {}
                if (x[0][0], x[0][-1]) not in recover_by_sites[x[1]]:
                    recover_by_sites[x[1]][x[0][0],x[0][-1]] = 1
                else:
                    recover_by_sites[x[1]][x[0][0],x[0][-1]] += 1
        sheet.write(y_start + 2, 2, 'Recovery')
        sheet.write(y_start + 2, 4, 'Qty')
        p = 0
        for p, x in enumerate(recover.keys()):
            sheet.write(y_start+3+p, 2, '%d -> %d' %(x))
            write_num(sheet, y_start+3+p, 4, recover[x], gross_die, data_format)
            for s, i in enumerate(sorted(recover_by_sites.keys())):
                sheet.write(y_start+2, 5+s, 'S%d' %i)
                if x not in recover_by_sites[i]:
                    write_num(sheet, y_start + 3 + p, 5 + s, 0, sum(bin_by_sn[i].values()), data_format)
                else:
                    write_num(sheet, y_start + 3 + p, 5 + s, recover_by_sites[i][x], sum(bin_by_sn[i].values()), data_format)
                write_num(sheet, y_start + 4 + p, 5 + s, sum(recover_by_sites[i].values()), sum(bin_by_sn[i].values()), data_format)
        sheet.write(y_start + 4 + p, 2, 'Total')
        write_num(sheet, y_start + 4 + p, 4, sum(recover.values()), gross_die, data_format)
        return y_start + 4 + p

    raw_sheet.write('A1','Tester Name: %s' %stdf_values['records'].get('MIR',{}).get('NODE_NAM',''))
    raw_sheet.write('A2','Job Name: %s' %stdf_values['records'].get('MIR',{}).get('NODE_NAM',''))
    raw_sheet.write('A3','Start Time: %s' %stdf_start_time)
    raw_sheet.write('A4','Finish Time: %s' %stdf_end_time)
    raw_sheet.write('A5','Lot ID: %s' %stdf_values['records'].get('MIR',{}).get('LOT_ID',''))
    raw_sheet.write('B1','Cust: %s' %stdf_values['records'].get('MIR',{}).get('USER_TXT',''))
    raw_sheet.write('B2','Device: %s' %stdf_values['records'].get('MIR',{}).get('PART_TYP',''))
    raw_sheet.write('B3','Stage: %s' %stdf_values['records'].get('MIR',{}).get('FLOW_ID',''))
    raw_sheet.write('B4','P/C ID: %s' %stdf_values['records'].get('SDR',{}).get('CARD_ID',''))
    raw_sheet.write('B5','Prober ID: %s' %stdf_values['records'].get('SDR',{}).get('HAND_ID',''))
    raw_sheet.write('C1','Test Head: %s' %stdf_values['records'].get('SDR',{}).get('HEAD_NUM',''))
    raw_sheet.write('C2','Gross Die: %d' %len(stdf_values['coords']))
    raw_sheet.write('C3','OP ID: %s' %stdf_values['records'].get('MIR',{}).get('OPER_NAM',''))
    # ========== yield of test items =========
    for k, v in stdf_values['test_items'].items():
        result = v['pass'] / v['total']
        if result <= 0.98:
            color = bad
        elif result < 1.0:
            color = warning
        else:
            color = all_pass
        itemSheet = get_item_sheet(v)
        col = (v['#'] % 16000) + 6
        itemSheet.write(5, col, result, color)
    # ======= write all header recrods =======
    header_row_cnt = 0
    for rec, fields in stdf_values['records'].items():
        header_sheet.write(header_row_cnt, 0, '%s' %rec, retest_pass_yellow)
        header_row_cnt += 1
        for k, v in fields.items():
            header_sheet.write(header_row_cnt, 0, '%s :' %k)
            if type(v)==list:
                v = str(v)
            header_sheet.write(header_row_cnt, 1, v)
            header_row_cnt += 1
    # ====== write all bin informations ======
    for n, sb in enumerate(sorted(stdf_values['soft_bins'].keys(), key=lambda k: stdf_values['soft_bins'][k]['hard_bin'])):
        bin_info = stdf_values['soft_bins'][sb]
        header_sheet.write(n+1, 5, bin_info['hard_bin'])
        header_sheet.write(n+1, 6, sb)
        header_sheet.write(n+1, 7, 'P' if bin_info['pass'] else 'F')
        header_sheet.write(n+1, 8, bin_info.get('bin_name',''))
        bin_table_sheet.write(n+1, 0, bin_info['hard_bin'])
        bin_table_sheet.write(n+1, 1, sb)
        bin_table_sheet.write(n+1, 2, 'P' if bin_info['pass'] else 'F')
        bin_table_sheet.write(n+1, 3, bin_info.get('bin_name',''))
    # ============= draw bin map =============
    if stdf_values['type'] == 'CP':
        map_sheet = wb.add_worksheet('Bin Map')
        map_sheet.freeze_panes(1, 1)
        map_sheet.set_column('A:ZZ',2.14)
        for i, num in enumerate(range(stdf_values['x']['min'],stdf_values['x']['max']+1)):
            map_sheet.write(0,i+1,num)
        for i, num in enumerate(range(stdf_values['y']['min'],stdf_values['y']['max']+1)):
            map_sheet.write(i+1,0,num)
        print_bin = lambda l: l[0] if len(l)==1 else '/'.join(str(x) for x in l)
        for x, y in stdf_values['coords'].keys():
            map_sheet.write(y-stdf_values['y']['min']+1, x-stdf_values['x']['min']+1, 
                            print_bin(stdf_values['coords'][(x,y)][0]), map_color(stdf_values['coords'][(x,y)][0]))
    summary_sheet = wb.add_worksheet('Summary')
    summary_sheet.write('A1','Tester Name: %s' %stdf_values['records'].get('MIR',{}).get('NODE_NAM',''))
    summary_sheet.write('A2','Job Name: %s' %stdf_values['records'].get('MIR',{}).get('NODE_NAM',''))
    summary_sheet.write('A3','Start Time: %s' %stdf_start_time)
    summary_sheet.write('A4','Finish Time: %s' %stdf_end_time)
    summary_sheet.write('A5','Lot ID: %s' %stdf_values['records'].get('MIR',{}).get('LOT_ID',''))
    summary_sheet.write('A6','Cust: %s' %stdf_values['records'].get('MIR',{}).get('USER_TXT',''))
    summary_sheet.write('A7','Device: %s' %stdf_values['records'].get('MIR',{}).get('PART_TYP',''))
    summary_sheet.write('A8','Stage: %s' %stdf_values['records'].get('MIR',{}).get('FLOW_ID',''))
    summary_sheet.write('A9','P/C ID: %s' %stdf_values['records'].get('SDR',{}).get('CARD_ID',''))
    summary_sheet.write('A10','Prober ID: %s' %stdf_values['records'].get('SDR',{}).get('HAND_ID',''))
    summary_sheet.write('A11','Test Head: %s' %stdf_values['records'].get('SDR',{}).get('HEAD_NUM',''))
    summary_sheet.write('A12','Gross Die: %d' %gross_die)
    summary_sheet.write('A13','OP ID: %s' %stdf_values['records'].get('MIR',{}).get('OPER_NAM',''))
    final_bin_qty = get_bin_summary([x[0][-1] for x in stdf_values['coords'].values()])
    first_bin_qty = get_bin_summary([x[0][0] for x in stdf_values['coords'].values()])
    retest_bin_qty = get_bin_summary([x[0][-1] for x in stdf_values['coords'].values() if len(x[0]) > 1])
    final_bin_by_site = get_bin_by_sites('final')
    first_bin_by_site = get_bin_by_sites('first')
    retest_bin_by_site = get_bin_by_sites('retest')
    end_pos = write_summary(summary_sheet, 'Final Result', final_bin_qty, final_bin_by_site, 15, 1)
    end_pos = write_summary(summary_sheet, '', final_bin_qty, final_bin_by_site, end_pos+2, 1, percent)
    end_pos = write_summary(summary_sheet, 'Final Test', first_bin_qty, first_bin_by_site, end_pos+2, 1)
    end_pos = write_summary(summary_sheet, '', first_bin_qty, first_bin_by_site, end_pos+2, 1, percent)
    if retest_bin_qty != {}:
        end_pos = write_summary(summary_sheet, 'Re-Test', retest_bin_qty, retest_bin_by_site, end_pos+2, 1)
        end_pos = write_summary(summary_sheet, '', retest_bin_qty, retest_bin_by_site, end_pos+2, 1, percent)
        end_pos = write_recovery(summary_sheet, final_bin_by_site, end_pos+2)
        end_pos = write_recovery(summary_sheet, final_bin_by_site, end_pos+2, percent)
    else:
        summary_sheet.write(end_pos+2, 1, 'No Re-Test')

def stdf_to_excel(stdf_path: str, excel_name: str):
    excel_name = r'files\output' + f'\\{excel_name}'
    workbook = xlsxwriter.Workbook(excel_name)
    write_report(workbook, stdf_path)
    workbook.close()
    # return basename(excel_name)