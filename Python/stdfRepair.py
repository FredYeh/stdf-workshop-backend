import gzip, io, gc, time, json
from datetime import datetime
from os.path import basename, getsize
import xlsxwriter

import stdfReader, stdfWriter

def repair_stdf(wb: xlsxwriter.Workbook, stdf_path: str, new_stdf_path: str):
    merge_format = wb.add_format({'border':1,'align':'center','valign':'vcenter','bg_color':'yellow','font_size':10,'font':'Arial'})
    map_green = wb.add_format({'align':'center','bg_color':'lime'})
    map_yellow = wb.add_format({'align':'center','bg_color':'yellow'})
    map_red = wb.add_format({'align':'center','bg_color':'red'})
    percent_fmt = wb.add_format({'num_format': '0.00%'})
    underline = wb.add_format({'bottom':True})
    edit_fmt = wb.add_format({'font':'Arial','border':1,'font_size':10})
    log_sheet = wb.add_worksheet('Comparison')
    log_sheet.merge_range('A1:A2','No.',merge_format)
    log_sheet.merge_range('B1:B2','Rec',merge_format)
    log_sheet.merge_range('C1:C2','x-coord',merge_format)
    log_sheet.merge_range('D1:D2','y-coord',merge_format)
    log_sheet.merge_range('E1:G1','STDF',merge_format)
    log_sheet.write('E2','site no.',merge_format)
    log_sheet.write('F2','SB',merge_format)
    log_sheet.write('G2','HB',merge_format)
    log_sheet.merge_range('H1:H2','Edit',merge_format)
    log_sheet.merge_range('I1:I2','Desciption',merge_format)
    log_sheet.set_column('I:I',60)

    def write_log(log_row: int, log_info: dict) -> int:
        log_sheet.write(log_row, 0, log_row - 1, edit_fmt)
        log_sheet.write(log_row, 1,  log_info['rec'], edit_fmt)
        log_sheet.write(log_row, 2, log_info['x'], edit_fmt)
        log_sheet.write(log_row, 3, log_info['y'], edit_fmt)
        log_sheet.write(log_row, 4, log_info['site'], edit_fmt)
        log_sheet.write(log_row, 5, log_info['soft_bin'], edit_fmt)
        log_sheet.write(log_row, 6, log_info['hard_bin'], edit_fmt)
        log_sheet.write(log_row, 7, log_info['mode'], edit_fmt)
        log_sheet.write(log_row, 8, log_info['desc'], edit_fmt)
        return log_row + 1
    
    get_bin_summary = lambda l: {x:l.count(x) for x in set(l)}
        
    def get_bin_by_sites(pos_bin: dict, mode: str = 'last') -> dict:
        p = 0 if mode == 'first' else -1
        ans = {}
        for x in pos_bin.values():
            if x[1] not in ans:
                ans[x[1]] = {}
            if mode == 'retest' and len(x[0]) == 1:
                continue
            if x[0][p] not in ans[x[1]]:
                ans[x[1]][x[0][p]] = 1
            else:
                ans[x[1]][x[0][p]] += 1
        return ans

    def main(new_stdf_fp: io.BufferedWriter):
        if stdf_path.endswith('.gz'):
            fp = gzip.open(stdf_path,'rb')
            content = fp.read()
            eof = fp.tell()
            fp.close()
            fp = io.BytesIO(content)
            del content
            gc.collect()
        else:
            fp = open(stdf_path,'rb')
            eof = getsize(stdf_path)
        record, pos = '', 0
        pos_bin, bin_info, record_info = {}, {}, {}
        coords = {'x': [], 'y': []}
        bin_summary, bin_by_sites = {}, {}
        writed_data_len = 0
        count = 0
        pir_needed, prr_needed= [], []
        last_record = ''
        total_test_time = 0
        log_row = 2
        all_needed_recs = ['MIR','SDR','WIR','PIR','BPS','EPS','PTR','FTR','MPR','PRR','PCR','SBR','HBR','WRR','MRR']
        record_counts = {r:0 for r in stdfReader.info.values()}
        st = time.time()
        progress_time = st

        def get_all_sbr() -> list:
            all_sbr = [('summary', x) for x in bin_summary.keys()]
            for site, bins in bin_by_sites.items():
                all_sbr.extend([(site, x) for x in bins.keys()])
            return all_sbr

        def get_all_hbr() -> list:
            all_hbr = []
            for b in bin_summary.keys():
                if ('summary', bin_info[b]['hard_bin']) not in all_hbr:
                    all_hbr.append(('summary', bin_info.get(b)['hard_bin']))
            for site, bins in bin_by_sites.items():
                for b in bins.keys():
                    if (site, bin_info[b]['hard_bin']) not in all_hbr:
                        all_hbr.append((site, bin_info.get(b)['hard_bin']))
            return all_hbr
    
        def get_testing_sites() -> tuple:
            lastRecord = 'PIR'
            record = ''
            start_p = fp.tell()
            pos = start_p
            pirSites = []
            prrSites = []
            while '!COM' not in record:
                record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, ['PIR','PRR'])
                if lastRecord != 'PIR' and 'PIR' in record:
                    break
                if 'PIR' in record:
                    pirSites.append(record[1]['SITE_NUM'])
                if 'PRR' in record:
                    prrSites.append(record[1]['SITE_NUM'])
                lastRecord = record[0]
            fp.seek(start_p)
            needed = list(set(prrSites).intersection(set(pirSites)))
            return needed, list(needed)

        while 'MRR' not in record:
            record, nextpos = stdfReader.readSTDFspecifyRecs(fp, pos, all_needed_recs)
            # record, nextpos = stdfReader.readSTDF(stdfile,pos)
            fp.seek(pos)
            next_data_string = fp.read(nextpos - pos)
            if (time.time()-progress_time >= 3) or (pos == eof):
                progress_time = time.time()
                print(json.dumps(
                        { 
                            'target': 'stdfRepair', 
                            'msg': {
                                'status':'parserProgress',
                                'number': '%d%s (%d/%d)' %(round((pos/eof)*100), '%', pos, eof)
                            }
                        }
                    )
                )
            if record not in ['NAN','!COM']:
                record_counts[record[0]] += 1
            if record[0] in ['MIR','SDR','WIR','MRR']:
                record_info[record[0]] = record[1]
            if 'PIR' in record:
                sn = record[1]['SITE_NUM']
                if (pir_needed == []) and (last_record != 'PIR'):
                    fp.seek(pos)
                    pir_needed, prr_needed = get_testing_sites()
                    bps_flag = True if pir_needed != [] else False
                    if last_record == 'PRR':
                        total_test_time += tt
                if sn not in pir_needed:
                    record_counts['PIR'] -= 1
                    next_data_string = b''
                    log_row = write_log(log_row, {
                        'rec': 'PIR', 'x': 'N/A', 'y': 'N/A',
                        'site': sn, 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'remove', 'desc': 'Remove redundant "PIR" record.',
                    })
                    # print('remove PIR, site: %d, pos: %d' %(sn,pos))
                else:
                    pir_needed.remove(sn)
            elif 'BPS' in record:
                if not bps_flag:
                    record_counts['BPS'] -= 1
                    next_data_string = b''
                    log_row = write_log(log_row, {
                        'rec': 'BPS', 'x': 'N/A', 'y': 'N/A',
                        'site': 'N/A', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'remove', 'desc': 'Remove redundant "BPS" record.',
                    })
                    # print('remove BPS, pos: %d' %pos)
            elif 'EPS' in record:
                if record_counts['EPS'] > record_counts['BPS']:
                    record_counts['EPS'] -= 1
                    next_data_string = b''
                    log_row = write_log(log_row, {
                        'rec': 'EPS', 'x': 'N/A', 'y': 'N/A',
                        'site': 'N/A', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'remove', 'desc': 'Remove redundant "EPS" record.',
                    })
                    # print('remove EPS, pos: %d' %pos)
            elif ('PTR' in record) or ('FTR' in record) or ('MPR' in record):
                sn = record[1]['SITE_NUM']
                if sn not in prr_needed:
                    record_counts[record[0]] -= 1
                    next_data_string = b''
            elif 'PRR' in record:
                bps_flag = False
                new_wrr_position = writed_data_len + len(next_data_string)
                sn = record[1]['SITE_NUM']
                xc = record[1]['X_COORD']
                yc = record[1]['Y_COORD']
                sb = record[1]['SOFT_BIN']
                hb = record[1]['HARD_BIN']
                tt = record[1]['TEST_T'] / 1000
                stdf_type = 'FT' if (xc==-32768 and yc==-32768) else 'CP'
                if sb not in bin_info:
                    pf = ('%4s' %(bin(record[1]['PART_FLG'])))[-4] != '1'
                    bin_info[sb] = {'pass': pf, 'hard_bin': hb}
                if sn not in prr_needed:
                    next_data_string = b''
                    record_counts['PRR'] -= 1
                    log_row = write_log(log_row, {
                        'rec': 'PRR', 'x': xc, 'y': yc,
                        'site': sn, 'soft_bin': sb, 'hard_bin': hb,
                        'mode': 'remove', 'desc': 'Remove redundant "PRR" record.',
                    })
                    # print('remove PRR, site: %d; coord: (%s,%s)' %(sn, xc, yc))
                else:
                    prr_needed.remove(sn)
                    count += 1
                    if stdf_type == 'CP':
                        if (xc,yc) not in pos_bin:
                            pos_bin[(xc,yc)] = [[sb],sn]
                        else:
                            pos_bin[(xc,yc)][0].append(sb)
                    else:
                        pos_bin[count] = [[sb],sn]
                    coords['x'].append(xc), coords['y'].append(yc)
            elif 'WRR' in record:
                oper = 'check'
                wrr_desc = '"WRR" checked, no any problem.'
                finish_t = record[1]['FINISH_T']
                wafer_id = record[1].get('WAFER_ID', '')
                fabwf_id = record[1].get('FABWF_ID', '')
                old_part_count = record[1].get('PART_CNT', 0)
                new_part_count = record_counts['PIR']
                old_good_count = record[1].get('GOOD_CNT', 0)
                new_good_count = len([bs[0][-1] for bs in pos_bin.values() if bin_info.get(bs[0][-1], {}).get('pass', False)])
                rtst_count = record[1].get('RSTS_CNT', 0)
                abrt_count = record[1].get('ABRT_CNT', 0)
                func_count = record[1].get('FUNC_CNT', 0)
                if old_part_count != new_part_count or old_good_count != new_good_count:
                    oper = 'edit'
                    wrr_desc = 'Change "WRR", "PART_CNT" from %d to %d, "GOOD_CNT" from %d to %d.' %(old_part_count, new_part_count, old_good_count, new_good_count)
                new_record = ('WRR',{
                    'HEAD_NUM':1, 'SITE_GRP':255, 'FINISH_T':finish_t, 'PART_CNT':new_part_count,
                    'RSTS_CNT':rtst_count, 'ABRT_CNT':abrt_count, 'GOOD_CNT':new_good_count,
                    'FUNC_CNT':func_count, 'WAFER_ID':wafer_id, 'FABWF_ID':fabwf_id,
                })
                next_data_string = stdfWriter.mkRecord(*new_record)
                # print('change WRR at pos %d' %new_stdf_fp.tell())
                log_row = write_log(log_row, {
                    'rec': 'WRR', 'x': 'N/A', 'y': 'N/A',
                    'site': 'N/A', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                    'mode': oper, 'desc': wrr_desc,
                })
            elif 'SBR' in record:
                if bin_summary == {}:
                    bin_summary = get_bin_summary([x[0][-1] for x in pos_bin.values()])
                    bin_by_sites = get_bin_by_sites(pos_bin)
                    all_sbr, all_hbr = get_all_sbr(), get_all_hbr()
                tempDict = record[1]
                is_allsites = True if record[1]['HEAD_NUM']==255 else False
                site_num = record[1]['SITE_NUM']
                sb_num = record[1]['SBIN_NUM']
                sb_count = record[1]['SBIN_CNT']
                bin_name = record[1].get('SBIN_NAM','')
                if is_allsites:
                    if ('summary', sb_num) in all_sbr:
                        all_sbr.remove(('summary', sb_num))
                else:
                    if (site_num, sb_num) in all_sbr:
                        all_sbr.remove((site_num, sb_num))
                if sb_num not in bin_info:
                    pf = True if record[1].get('SBIN_PF', '') == 'P' else False
                    bin_info[sb_num] = {'pass':pf}
                bin_info[sb_num]['name'] = bin_name
                compare_qty = bin_summary.get(sb_num, 0) if is_allsites else bin_by_sites[site_num].get(sb_num, 0)
                if sb_count != compare_qty:
                    # print('change SBR site %d, Sbin %d' %(site_num, sb_num))
                    sbr_desc = 'Change "SBR" qty from %d to %d' %(sb_count, compare_qty)
                    tempDict['SBIN_CNT'] = compare_qty
                    next_data_string = stdfWriter.mkRecord('SBR', tempDict)
                    log_row = write_log(log_row, {
                        'rec': 'SBR', 'x': 'N/A', 'y': 'N/A',
                        'site': site_num, 'soft_bin': sb_num, 'hard_bin': 'N/A',
                        'mode': 'edit', 'desc': sbr_desc,
                    })
            elif 'HBR' in record:
                if bin_summary == {}:
                    bin_summary = get_bin_summary([x[0][-1] for x in pos_bin.values()])
                    bin_by_sites = get_bin_by_sites(pos_bin)
                    all_sbr, all_hbr = get_all_sbr(), get_all_hbr()
                tempDict = record[1]
                is_allsites = True if record[1]['HEAD_NUM']==255 else False
                site_num = record[1]['SITE_NUM']
                hb_num = record[1]['HBIN_NUM']
                hb_count = record[1]['HBIN_CNT']
                if is_allsites:
                    compare_qty = sum([bin_summary[b] for b in bin_summary.keys() if bin_info.get(b, {}).get('hard_bin', None) == hb_num])
                    if ('summary', hb_num) in all_hbr:
                        all_hbr.remove(('summary', hb_num))
                else:
                    if (site_num, hb_num) in all_hbr:
                        all_hbr.remove((site_num, hb_num))
                    sitesumm = bin_by_sites[site_num]
                    compare_qty = sum([sitesumm[b] for b in sitesumm if bin_info.get(b, {}).get('hard_bin', None) == hb_num])
                if hb_count != compare_qty:
                    # print('change HBR site %d, Hbin %d' %(site_num, hb_num))
                    hbr_desc = 'Change \"HBR\" qty from %d to %d' %(site_num, compare_qty)
                    tempDict['HBIN_CNT'] = compare_qty
                    next_data_string = stdfWriter.mkRecord('HBR',tempDict)
                    log_row = write_log(log_row, {
                        'rec': 'HBR', 'x': 'N/A', 'y': 'N/A',
                        'site': site_num, 'soft_bin': 'N/A', 'hard_bin': hb_num,
                        'mode': 'edit', 'desc': hbr_desc,
                    })
            elif record == '!COM' or nextpos == eof:
                if bin_summary == {}:
                    bin_summary = get_bin_summary([x[0][-1] for x in pos_bin.values()])
                    bin_by_sites = get_bin_by_sites(pos_bin)
                    all_sbr, all_hbr = get_all_sbr(), get_all_hbr()
                if 'MRR' in record:
                    # print('MRR exsisted, STDF end normally.')
                    finish_t = record[1]['FINISH_T']
                else:
                    finish_t = record_info['MIR']['START_T'] + int(total_test_time)
                if record_counts['WRR'] == 0:   # Add WRR if not exist, or edit if exist. 
                    # print('add missing WRR at %d' %new_wrr_position)
                    new_record = ('WRR',{
                        'HEAD_NUM': 1, 'SITE_GRP': 255, 'FINISH_T': finish_t,
                        'PART_CNT': record_counts['PIR'], 'RSTS_CNT': 0, 'ABRT_CNT': 0,
                        'GOOD_CNT': len([
                            bs[0][-1] for bs in pos_bin.values() if bin_info.get(bs[0][-1],{}).get('pass',False)
                        ]),
                        'FUNC_CNT': 0, 'WAFER_ID': record_info.get('WIR',{}).get('WAFER_ID',''), 'FABWF_ID': '',
                    })
                    with open(new_stdf_fp.name,'rb') as tmp:
                        head = tmp.read(new_wrr_position)
                        tail = tmp.read()
                    reOpen = new_stdf_fp.name
                    new_stdf_fp.close()
                    new_stdf_fp = open(reOpen,'wb')
                    new_stdf_fp.write(head)
                    new_stdf_fp.write(stdfWriter.mkRecord(*new_record))
                    new_stdf_fp.write(tail)
                    new_stdf_fp.flush()
                    log_row = write_log(log_row, {
                        'rec': 'WRR', 'x': 'N/A', 'y': 'N/A',
                        'site': 'N/A', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'add', 'desc': 'Added missing "WRR".',
                    })
                if record_counts['PCR'] == 0:   # Add PCR if not exist.
                    # print(record_counts)
                    total_good = 0
                    for sn in record_info['SDR']['SITE_NUM']:
                        part_cnt = sum([x for x in bin_by_sites[sn].values()])
                        gd_count = sum([x for k, x in bin_by_sites[sn].items() if bin_info[k].get('pass',False)])
                        total_good += gd_count
                        new_record = ('PCR',{
                            'HEAD_NUM': 1, 'SITE_NUM': sn, 'PART_CNT': part_cnt,
                            'RSTS_CNT': 0, 'ABRT_CNT': 0, 'GOOD_CNT': gd_count,
                            'FUNC_CNT': 0
                        })
                        new_bin_record = stdfWriter.mkRecord(*new_record)
                        new_stdf_fp.write(new_bin_record)
                        new_stdf_fp.flush()
                        writed_data_len += len(new_bin_record)
                        # print("Adding missing \'PCR\', site: %d. pos: %d" %(sn, writed_data_len), new_stdf_fp.tell())
                        log_row = write_log(log_row, {
                            'rec': 'PCR', 'x': 'N/A', 'y': 'N/A',
                            'site': sn, 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                            'mode': 'add', 'desc': 'Added missing "PCR".',
                        })
                    part_cnt = len(pos_bin)
                    new_record = ('PCR',{
                        'HEAD_NUM': 255, 'SITE_NUM': 0, 'PART_CNT': part_cnt,
                        'RSTS_CNT': 0, 'ABRT_CNT': 0, 'GOOD_CNT': total_good,
                        'FUNC_CNT': 0
                    })
                    new_bin_record = stdfWriter.mkRecord(*new_record)
                    new_stdf_fp.write(new_bin_record)
                    new_stdf_fp.flush()
                    writed_data_len += len(new_bin_record)
                    # print("Adding missing \'PCR\', site: 255. pos: %d" %writed_data_len, new_stdf_fp.tell())
                    log_row = write_log(log_row, {
                        'rec': 'PCR', 'x': 'N/A', 'y': 'N/A',
                        'site': 'summary', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'add', 'desc': 'Added missing "PCR".',
                    })
                for hbrs in all_hbr:            # Add missing HBRs records.
                    is_allsite = True if hbrs[0] == 'summary' else False
                    hbin_cnt = sum([
                        bin_summary[b] for b in bin_summary.keys() if bin_info[b]['hard_bin'] == hbrs[1]
                    ]) if is_allsite else sum([
                        bin_by_sites[hbrs[0]][b] for b in bin_by_sites[hbrs[0]] if bin_info[b]['hard_bin'] == hbrs[1]
                    ])
                    new_record = ('HBR',{
                        'HEAD_NUM': 255 if is_allsite else 1,
                        'SITE_NUM': 0 if is_allsite else hbrs[0],
                        'HBIN_NUM': hbrs[1],
                        'HBIN_CNT': hbin_cnt,
                    })
                    new_bin_record = stdfWriter.mkRecord(*new_record)
                    new_stdf_fp.write(new_bin_record)
                    new_stdf_fp.flush()
                    writed_data_len += len(new_bin_record)
                    # print('add missing HBR. pos: %d' %writed_data_len, new_stdf_fp.tell())
                    log_row = write_log(log_row, {
                        'rec': 'HBR', 'x': 'N/A', 'y': 'N/A',
                        'site': hbrs[0], 'soft_bin': 'N/A', 'hard_bin': hbrs[1],
                        'mode': 'add', 'desc': 'Added missing "HBR".',
                    })
                for sbrs in all_sbr:            # Add missing SBRs records.
                    is_allsite = True if sbrs[0] == 'summary' else False
                    sbcnt = bin_summary[sbrs[1]] if is_allsite else bin_by_sites[sbrs[0]][sbrs[1]]
                    new_record = ('SBR',{
                        'HEAD_NUM': 255 if is_allsite else 1,
                        'SITE_NUM': 0 if is_allsite else sbrs[0],
                        'SBIN_NUM': sbrs[1],
                        'SBIN_CNT': sbcnt,
                    })
                    new_bin_record = stdfWriter.mkRecord(*new_record)
                    new_stdf_fp.write(new_bin_record)
                    new_stdf_fp.flush()
                    writed_data_len += len(new_bin_record)
                    # print('add missing SBR. pos: %d' %writed_data_len, new_stdf_fp.tell())
                    log_row = write_log(log_row, {
                        'rec': 'SBR', 'x': 'N/A', 'y': 'N/A',
                        'site': sbrs[0], 'soft_bin': 'N/A', 'hard_bin': sbrs[1],
                        'mode': 'add', 'desc': 'Added missing "SBR".',
                    })
                if record_counts['MRR'] == 0:
                    new_record = ('MRR',{
                        'FINISH_T': finish_t, 'DISP_COD': ' '
                    })
                    record_info['MRR'] = {'FINISH_T': finish_t, 'DISP_COD': ' '}
                    new_bin_record = stdfWriter.mkRecord(*new_record)
                    new_stdf_fp.write(new_bin_record)
                    new_stdf_fp.flush()
                    writed_data_len += len(new_bin_record)
                    # print('add missing MRR. pos: %d' %writed_data_len, new_stdf_fp.tell())
                    next_data_string = b''
                    log_row = write_log(log_row, {
                        'rec': 'MRR', 'x': 'N/A', 'y': 'N/A',
                        'site': 'N/A', 'soft_bin': 'N/A', 'hard_bin': 'N/A',
                        'mode': 'add', 'desc': 'Added missing "MRR".',
                    })
                record = 'MRR'
            if record != 'NAN':
                last_record = record[0]
            pos = nextpos
            new_stdf_fp.write(next_data_string)
            writed_data_len += len(next_data_string)
            new_stdf_fp.flush()
        # print('--- %.3fs ---' %(time.time()-st))
        print(json.dumps(
                { 
                    'target': 'stdfRepair', 
                    'msg': {
                        'status':'parserProgress',
                        'number': '100% (---/---)',
                    }
                }
            )
        )
        fp.close()
        new_stdf_fp.close()
        
        return {
            'stdf_type': stdf_type,
            'records': record_info,
            'coords': pos_bin,
            'soft_bins': bin_info,
            'x':{'max':max(coords['x']),'min':min(coords['x'])},
            'y':{'max':max(coords['y']),'min':min(coords['y'])},
        }
    
    new_stdf_fp = open(new_stdf_path, 'wb')

    stdf_values = main(new_stdf_fp)
    gross_die = len(stdf_values['coords'])
    
    def map_color(bins: list):
        if stdf_values['soft_bins'][bins[-1]]['pass'] == True:
            if len(bins) > 1:
                return map_yellow
            else:
                return map_green
        else:
            return map_red
    
    def write_num(sheet: xlsxwriter.Workbook.worksheet_class, row: int, col: int, numer: int, denom: int, fmt):
        if fmt==None:
            sheet.write(row, col, numer)
        else:
            if denom==0:
                sheet.write(row, col, 0, fmt)
            else:
                sheet.write(row, col, numer/denom, fmt)

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
            sheet.write(c+y_start+6, x_start+3, (pass_bin/total), percent_fmt)
        else:
            sheet.write(c+y_start+6, x_start+3, (pass_bin/gross_die), percent_fmt)
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
    
    if stdf_values['stdf_type'] == 'CP':
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
    summary_sheet.write('A1','Tester Name: %s' %stdf_values['records']['MIR']['NODE_NAM'])
    summary_sheet.write('A2','Job Name: %s' %stdf_values['records']['MIR']['JOB_NAM'])
    summary_sheet.write('A3','Start Time: %s' %datetime.fromtimestamp(stdf_values['records']['MIR']['START_T']))
    summary_sheet.write('A4','Finish Time: %s' %datetime.fromtimestamp(stdf_values['records']['MRR']['FINISH_T']))
    summary_sheet.write('A5','Lot ID: %s' %stdf_values['records']['MIR']['LOT_ID'])
    summary_sheet.write('A6','Cust: %s' %stdf_values['records']['MIR']['USER_TXT'])
    summary_sheet.write('A7','Device: %s' %stdf_values['records']['MIR']['PART_TYP'])
    summary_sheet.write('A8','Stage: %s' %stdf_values['records']['MIR']['FLOW_ID'])
    summary_sheet.write('A9','P/C ID: %s' %stdf_values['records']['SDR']['CARD_ID'])
    summary_sheet.write('A10','Prober ID: %s' %stdf_values['records']['SDR']['HAND_ID'])
    summary_sheet.write('A11','Test Head: %s' %stdf_values['records']['SDR']['HEAD_NUM'])
    summary_sheet.write('A12','Gross Die: %d' %gross_die)
    summary_sheet.write('A13','OP ID: %s' %stdf_values['records']['MIR']['OPER_NAM']  )
    final_bin_qty = get_bin_summary([x[0][-1] for x in stdf_values['coords'].values()])
    first_bin_qty = get_bin_summary([x[0][0] for x in stdf_values['coords'].values()])
    retest_bin_qty = get_bin_summary([x[0][-1] for x in stdf_values['coords'].values() if len(x[0]) > 1])
    final_bin_by_site = get_bin_by_sites(stdf_values['coords'], 'final')
    first_bin_by_site = get_bin_by_sites(stdf_values['coords'], 'first')
    retest_bin_by_site = get_bin_by_sites(stdf_values['coords'], 'retest')
    end_pos = write_summary(summary_sheet, 'Final Result', final_bin_qty, final_bin_by_site, 15, 1)
    end_pos = write_summary(summary_sheet, '', final_bin_qty, final_bin_by_site, end_pos+2, 1, percent_fmt)
    end_pos = write_summary(summary_sheet, 'Final Test', first_bin_qty, first_bin_by_site, end_pos+2, 1)
    end_pos = write_summary(summary_sheet, '', first_bin_qty, first_bin_by_site, end_pos+2, 1, percent_fmt)
    if retest_bin_qty != {}:
        end_pos = write_summary(summary_sheet, 'Re-Test', retest_bin_qty, retest_bin_by_site, end_pos+2, 1)
        end_pos = write_summary(summary_sheet, '', retest_bin_qty, retest_bin_by_site, end_pos+2, 1, percent_fmt)
        end_pos = write_recovery(summary_sheet, final_bin_by_site, end_pos+2)
        end_pos = write_recovery(summary_sheet, final_bin_by_site, end_pos+2, percent_fmt)
    else:
        summary_sheet.write(end_pos+2, 1, 'No Re-Test')

def stdf_repairment(stdf_path: str, fixed_stdf_name: str, log_excel_name: str):
    new_stdf_path = r'files\output' + f'\\{fixed_stdf_name}'
    excel_name = r'files\output' + f'\\{log_excel_name}'
    workbook = xlsxwriter.Workbook(excel_name)
    repair_stdf(workbook, stdf_path, new_stdf_path)
    workbook.close()

import sys
stdf_repairment(sys.argv[1], sys.argv[2], sys.argv[3])