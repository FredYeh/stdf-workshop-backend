import stdfReader
import xlsxwriter
import gzip, io, gc, time, json
from os.path import basename

def read_stdf(stdf: str, percent_start: int, ratio: int) -> tuple[dict, dict]:
    header = {'filename': basename(stdf)}
    coords, bins = {}, {}
    progress_time = time.time()
    if stdf.endswith('.gz'):
        fp = gzip.open(stdf,'rb')
        content = fp.read()
        fp.close()
        fp = io.BytesIO(content)
        del content
        gc.collect()
    else:
        fp = open(stdf, 'rb')
    fp.read()
    eof = fp.tell()
    fp.seek(0)
    record, pos = [], 0
    try:
        while 'MRR' not in record:
            record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, ['MIR','SDR','PRR','WIR','WRR','MRR'])
            if record=='!COM':
                raise EOFError('STDF did not end properly.')
            if time.time()-progress_time >= 3 or pos==eof:
                progress_time = time.time()
                print(json.dumps(
                        { 
                            'target': 'stdfCompare', 
                            'msg': {
                                'status':'parserProgress',
                                'number': '%d%s (%d/%d)' %(round((pos/eof)*ratio) + percent_start, '%', pos, eof)
                            }
                        }
                    )
                )
            if record[0] in ['MIR','SDR','WIR','WRR','MRR']:
                header[record[0]] = record[1]
            elif 'PRR' in record:
                xc, yc = record[1]['X_COORD'], record[1]['Y_COORD']
                soft_bin = record[1]['SOFT_BIN']
                site = record[1]['SITE_NUM']
                pf = False if ('%4s' %(bin(record[1]['PART_FLG'])))[-4] == '1' else True
                if (xc, yc) not in coords:
                    coords[(xc, yc)] = {'bins':[],'sites':[]}
                if str(soft_bin) not in bins:
                    bins[str(soft_bin)] = {'num': soft_bin, 'pass': pf}
                coords[(xc, yc)]['bins'].append(str(soft_bin))
                coords[(xc, yc)]['sites'].append(str(site))
    except:
        print(json.dumps(
                { 
                    'target': 'stdfCompare', 
                    'msg': {
                        'status':'parserProgress',
                        'number': '100% (incomplete STDF)',
                    }
                }
            )
        )
    return {
        'header': header,
        'coords': coords,
        'bins': bins,
    }

def write_header(workbook: xlsxwriter.Workbook, header1: dict, header2: dict):
    header_sheet = workbook.add_worksheet('Titles')
    header_sheet.set_column('A:A',14)
    header_sheet.set_column('B:C',33)
    title_fmt = workbook.add_format({'align':'center','bg_color':'yellow','border':1})
    header_sheet.merge_range('A1:A2','Titles',title_fmt)
    header_sheet.merge_range('B1:C1','File name',title_fmt)
    header_sheet.write('B2',header1['filename'],title_fmt)
    header_sheet.write('C2',header2['filename'],title_fmt)
    count = 2
    for record in ['MIR','SDR','WIR','WRR','MRR']:
        if (record not in header1) and (record not in header2):
            continue
        elif record in header1:
            all_fields = header1[record].keys()
        elif record in header2:
            all_fields = header2[record].keys()
        header_sheet.merge_range(count, 0, count, 2, record, title_fmt)
        count += 1
        for field in all_fields:
            header_sheet.write(count, 0, field)
            header_sheet.write(count, 1, '%s' %header1.get(record,{}).get(field,''))
            header_sheet.write(count, 2, '%s' %header2.get(record,{}).get(field,''))
            count += 1

def compare(workbook: xlsxwriter.Workbook, coords1: dict, coords2: dict):
    detail_sheet = workbook.add_worksheet('Coords')
    detail_sheet.freeze_panes(2,0)
    detail_sheet.set_column('C:F',11)
    title_fmt = workbook.add_format({'align':'center','bg_color':'yellow','border':1})
    bad_fmt = workbook.add_format({'font_color':'red'})
    detail_sheet.merge_range('A1:A2','X',title_fmt)
    detail_sheet.merge_range('B1:B2','Y',title_fmt)
    detail_sheet.merge_range('C1:D1','Soft Bin',title_fmt)
    detail_sheet.merge_range('E1:F1','Site',title_fmt)
    detail_sheet.write('C2','first STDF',title_fmt)
    detail_sheet.write('D2','second STDF',title_fmt)
    detail_sheet.write('E2','first STDF',title_fmt)
    detail_sheet.write('F2','second STDF',title_fmt)
    static = {
        'site': {'same':0, 'diff':1},
        'bin': {'same':0, 'diff':1},
        'recover':{},
    }
    row_count = 2
    for ((xc, yc), info) in coords1.items():
        detail_sheet.write(row_count, 0, xc)
        detail_sheet.write(row_count, 1, yc)
        bs1, ss1 = info['bins'], info['sites']
        if (xc, yc) not in coords2:
            detail_sheet.write(row_count, 2, '%s' %('/'.join(bs1)), bad_fmt)
            detail_sheet.write(row_count, 4, '%s' %('/'.join(ss1)), bad_fmt)
            row_count += 1
        else:
            bs2, ss2 = coords2.get((xc, yc),{'bins':[]})['bins'], coords2.get((xc, yc),{'sites':[]})['sites']
            if bs1[-1] != bs2[-1]:
                bin_fmt = bad_fmt
                static['site']['diff'] += 1
            else:
                bin_fmt = None
                static['site']['same'] += 1
            if ss1[-1]!=ss2[-1]:
                site_fmt = bad_fmt
                static['bin']['diff'] += 1
            else:
                site_fmt = None
                static['bin']['same'] += 1
            detail_sheet.write(row_count, 2, '%s' %('/'.join(bs1)), bin_fmt)
            detail_sheet.write(row_count, 3, '%s' %('/'.join(bs2)), bin_fmt)
            detail_sheet.write(row_count, 4, '%s' %('/'.join(ss1)), site_fmt)
            detail_sheet.write(row_count, 5, '%s' %('/'.join(ss2)), site_fmt)
            row_count += 1
    for ((xc, yc), info)  in coords2.items():
        if (xc, yc) not in coords1:
            detail_sheet.write(row_count, 0, xc)
            detail_sheet.write(row_count, 1, yc)
            bs2, ss2 = info['bins'], info['sites']
            detail_sheet.write(row_count, 3, '%s' %('/'.join(bs2)), bad_fmt)
            detail_sheet.write(row_count, 5, '%s' %('/'.join(ss2)), bad_fmt)
            row_count += 1

def draw_site_map(workbook: xlsxwriter.Workbook, coords1: dict, coords2: dict):
    coors = {'x':[x[0] for x in coords1.keys()], 'y':[y[1] for y in coords1.keys()]}
    map_sheet = workbook.add_worksheet('Site Compare Map')
    map_sheet.freeze_panes(1, 1)
    map_sheet.set_column('A:ZZ',2.14)
    green_bg = workbook.add_format({'align':'center','bg_color':'lime'})
    red_bg = workbook.add_format({'align':'center','bg_color':'red'})
    gray_bg = workbook.add_format({'align':'center','bg_color':'gray'})
    black_bg = workbook.add_format({'align':'center','bg_color':'#BEBEBE'})
    minx = min(coors['x'])
    maxx = max(coors['x'])
    miny = min(coors['y'])
    maxy = max(coors['y'])
    for i, num in enumerate(range(minx,maxx+1)):
        map_sheet.write(0,i+1,num)
    for i, num in enumerate(range(miny,maxy+1)):
        map_sheet.write(i+1,0,num)
    for (x, y) in coords1.keys():
        if (x, y) not in coords2:
            fmt = gray_bg
            map_sheet.write(y-miny+1, x-minx+1, coords1[(x,y)]['sites'][-1], fmt)
        else:
            fmt = green_bg if coords1[(x,y)]['sites'][-1]==coords2[(x,y)]['sites'][-1] else red_bg
            map_sheet.write(y-miny+1, x-minx+1, '%s/%s' %(coords1[(x,y)]['sites'][-1], coords2[(x,y)]['sites'][-1]), fmt)
    for (x, y) in coords2.keys():
        if (x, y) not in coords1.keys():
            map_sheet.write(y-miny+1, x-minx+1, coords2[(x,y)]['bins'][-1], black_bg)

def draw_compare_bin_map(workbook: xlsxwriter.Workbook, coords1: dict, coords2: dict):
    coors = {'x':[x[0] for x in coords1.keys()], 'y':[y[1] for y in coords1.keys()]}
    map_sheet = workbook.add_worksheet('Bin Compare Map')
    map_sheet.freeze_panes(1, 1)
    map_sheet.set_column('A:ZZ',2.14)
    green_bg = workbook.add_format({'align':'center','bg_color':'lime'})
    red_bg = workbook.add_format({'align':'center','bg_color':'red'})
    gray_bg = workbook.add_format({'align':'center','bg_color':'gray'})
    black_bg = workbook.add_format({'align':'center','bg_color':'#BEBEBE'})
    minx = min(coors['x'])
    maxx = max(coors['x'])
    miny = min(coors['y'])
    maxy = max(coors['y'])
    for i, num in enumerate(range(minx,maxx+1)):
        map_sheet.write(0,i+1,num)
    for i, num in enumerate(range(miny,maxy+1)):
        map_sheet.write(i+1,0,num)
    for (x, y) in coords1.keys():
        if (x, y) not in coords2:
            fmt = gray_bg
            map_sheet.write(y-miny+1, x-minx+1, coords1[(x,y)]['bins'][-1], fmt)
        else:
            fmt = green_bg if coords1[(x,y)]['bins'][-1]==coords2[(x,y)]['bins'][-1] else red_bg
            map_sheet.write(y-miny+1, x-minx+1, '%s/%s' %(coords1[(x,y)]['bins'][-1], coords2[(x,y)]['bins'][-1]), fmt)
    for (x, y) in coords2.keys():
        if (x, y) not in coords1.keys():
            map_sheet.write(y-miny+1, x-minx+1, coords2[(x,y)]['bins'][-1], black_bg)

def draw_bin_map(workbook: xlsxwriter.Workbook, coords1: dict, coords2: dict, bin_def: dict):
    coors = {'x':[x[0] for x in coords1.keys()], 'y':[y[1] for y in coords1.keys()]}
    map_sheet = workbook.add_worksheet('Bin Map')
    map_sheet.freeze_panes(1, 1)
    map_sheet.set_column('A:ZZ',2.14)
    green_bg = workbook.add_format({'align':'center','bg_color':'lime'})
    yellow_bg = workbook.add_format({'align':'center','bg_color':'yellow'})
    red_bg = workbook.add_format({'align':'center','bg_color':'red'})
    gray_bg = workbook.add_format({'align':'center','bg_color':'gray'})
    black_bg = workbook.add_format({'align':'center','bg_color':'#BEBEBE'})
    minx = min(coors['x'])
    maxx = max(coors['x'])
    miny = min(coors['y'])
    maxy = max(coors['y'])
    recover = {}
    for i, num in enumerate(range(minx,maxx+1)):
        map_sheet.write(0,i+1,num)
    for i, num in enumerate(range(miny,maxy+1)):
        map_sheet.write(i+1,0,num)
    for (x, y) in coords1.keys():
        if (x, y) not in coords2:
            fmt = gray_bg
            map_sheet.write(y-miny+1, x-minx+1, coords1[(x,y)]['bins'][-1], fmt)
        else:
            if (coords1[(x,y)]['bins'][-1], coords2[(x,y)]['bins'][-1]) not in recover:
                recover[(coords1[(x,y)]['bins'][-1], coords2[(x,y)]['bins'][-1])] = 0
            recover[(coords1[(x,y)]['bins'][-1], coords2[(x,y)]['bins'][-1])] += 1
            if coords2[(x,y)]['bins'][-1] == '1':
                fmt = yellow_bg if bin_def.get(coords1[(x,y)]['bins'][-1],{}).get('pass', False) != '1' else green_bg
            else:
                fmt = red_bg
            map_sheet.write(y-miny+1, x-minx+1, '%s/%s' %(coords1[(x,y)]['bins'][-1], coords2[(x,y)]['bins'][-1]), fmt)
    for (x, y) in coords2.keys():
        if (x, y) not in coords1.keys():
            map_sheet.write(y-miny+1, x-minx+1, coords2[(x,y)]['bins'][-1], black_bg)
    return recover

def bin_swap(workbook: xlsxwriter.Workbook, first_filename: str, second_filename: str, recover: dict, bin_def: dict):
    stat_sheet = workbook.add_worksheet('Bin Swap')
    title_fmt = workbook.add_format({'align':'center','bg_color':'#FFBE00','border':1})
    left_title_fmt = workbook.add_format({'align':'center','bg_color':'#FFBE00','border':1, 'rotation':90})
    swap_bg = workbook.add_format({'align':'center','bg_color':'#BEBEBE','border':1})
    center_bg = workbook.add_format({'align':'center','bg_color':'yellow','border':1})
    none_bg = workbook.add_format({'align':'center','border':1})
    stat_sheet.write('A1','Bin Swap', title_fmt)
    stat_sheet.write('B2','SBIN', title_fmt)
    total, y_total = 0, []
    for xn, x in enumerate(sorted(bin_def, key=lambda k: bin_def[k]['num'])):
        stat_sheet.write(xn+2, 1, x, title_fmt)
        x_total = 0
        for yn, y in enumerate(sorted(bin_def, key=lambda k: bin_def[k]['num'])):
            if len(y_total)==yn:
                y_total.append(0)
            y_total[yn] += recover.get((x,y),0)
            x_total += recover.get((x,y),0)
            total += recover.get((x,y),0)
            stat_sheet.write(1, yn+2, y, title_fmt)
            fmt = none_bg if recover.get((x,y),0)==0 else swap_bg
            fmt = center_bg if y==x else fmt
            stat_sheet.write(xn+2,yn+2,recover.get((x,y),0), fmt)
        stat_sheet.write(xn+2, yn+3, x_total)
    for n, tmp in enumerate(y_total):
        stat_sheet.write(xn+3, n+2, tmp)
    stat_sheet.merge_range(0 ,1 ,0, n+2, second_filename, title_fmt)
    stat_sheet.merge_range(1 ,0 ,xn+2, 0, first_filename, left_title_fmt)
    stat_sheet.write(xn+3, n+3, total)


def main(stdf1: str, stdf2: str, wb_name: str):
    info1 = read_stdf(stdf1, 0, 35)
    info2 = read_stdf(stdf2, 35, 35)
    all_bins = info2['bins']
    all_bins.update(info1['bins'])
    wb = xlsxwriter.Workbook(wb_name)
    if info1['header']['MIR']['START_T'] <= info2['header']['MIR']['START_T']:
        first, second = info1, info2
    else:
        first, second = info2, info1
    write_header(wb, first['header'], second['header'])
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '75% (-/-)'}}))
    compare(wb, first['coords'], second['coords'])
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '80% (-/-)'}}))
    draw_site_map(wb, first['coords'], second['coords'])
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '85% (-/-)'}}))
    draw_compare_bin_map(wb, first['coords'], second['coords'])
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '90% (-/-)'}}))
    recover = draw_bin_map(wb, first['coords'], second['coords'], all_bins)
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '95% (-/-)'}}))    
    bin_swap(wb, first['header']['filename'], second['header']['filename'], recover, all_bins)
    print(json.dumps({'target': 'stdfCompare','msg': {'status':'parserProgress','number': '100% (-/-)'}}))    
    wb.close()

if __name__ == '__main__':
    import sys
    first_stdf, second_stdf = sys.argv[1], sys.argv[2]
    excel_name = r'files\output' + f'\\{sys.argv[3]}'
    main(first_stdf, second_stdf, excel_name)