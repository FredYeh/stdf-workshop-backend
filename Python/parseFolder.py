import stdfReader
import xlsxwriter
from datetime import datetime
import time, os, gzip, io, gc, json
from math import ceil

def parse_folder(folder_path: str, output_file: str):
    titles = [
        'Device', 'Lot ID', 'Wafer ID', 'Fabwf ID', 'start time', 'end time',
        'test time', 'Program name', 'total', 'Pass', 'Yield', 'stage',
        'Tester', 'P/C ID', 'file name'
    ]
    workbook = xlsxwriter.Workbook(output_file)
    workbook.formats[0].set_font_size(10)
    workbook.formats[0].set_font('Arial')
    title_fmt = workbook.add_format({'bg_color':'#A5A5A5', 'bold':True,'font_size':10,'font':'Arial'})
    pctg_fmt = workbook.add_format({'font_size':10,'font':'Arial', 'num_format':'0.00%'})
    sheet = workbook.add_worksheet('STDFs')
    sheet.freeze_panes(1, 0)
    sheet.set_column('A:A', 23)
    sheet.set_column('B:B', 14)
    sheet.set_column('C:D', 17)
    sheet.set_column('E:F', 20)
    sheet.set_column('H:H', 20)
    sheet.set_column('M:M', 12)
    sheet.set_column('N:N', 25)
    sheet.set_column('O:O', 95)
    stdf_count = 1
    for n, x in enumerate(titles):
        sheet.write(0, n, x, title_fmt)
    all_files = os.listdir(folder_path)
    file_cnt = len(all_files)
    for n, file in enumerate(all_files):
        if (not file.endswith('.gz')) and (not file.endswith('.std')):
            continue
        st = time.time()
        # print(file)
        sheet.write(stdf_count, 13, file)
        if file.endswith('.gz'):
            fp = gzip.open('%s\\%s' %(folder_path, file),'rb')
            content = fp.read()
            fp.close()
            fp = io.BytesIO(content)
            del content
            gc.collect()
        else:
            fp = open('%s\\%s' %(folder_path, file), 'rb')
        record, pos = '', 0
        coords = {}
        while 'MRR' not in record:
            record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, ['MIR', 'SDR', 'PRR', 'WIR', 'WRR', 'MRR'])
            if record == '!COM':
                print(json.dumps(
                    { 
                        'target': 'parseFolder', 
                        'msg': {
                            'status':'error',
                            'number': '%.3f' %(((n+1) / file_cnt) * 100) + '%',
                            'err': '%s is an imcompleted STDF.' %file,
                        }
                    }
                ))
                break
            if 'MIR' in record:
                start_time_tstamp = record[1]['START_T']
                start_time = datetime.fromtimestamp(start_time_tstamp).strftime('%Y/%m/%d %H:%M:%S')
                sheet.write(stdf_count, titles.index('Device'), record[1]['PART_TYP'])
                sheet.write(stdf_count, titles.index('Lot ID'), record[1]['LOT_ID'])
                sheet.write(stdf_count, titles.index('start time'), start_time)
                sheet.write(stdf_count, titles.index('Program name'), record[1]['JOB_NAM'])
                sheet.write(stdf_count, titles.index('stage'), record[1]['FLOW_ID'])
                sheet.write(stdf_count, titles.index('Tester'), record[1]['NODE_NAM'])
            elif 'SDR' in record:
                sheet.write(stdf_count, titles.index('P/C ID'), record[1]['CARD_ID'])
            elif 'PRR' in record:
                xc = record[1]['X_COORD']
                yc = record[1]['Y_COORD']
                fail = ('%4s' %(bin(record[1]['PART_FLG'])))[-4] == '1'
                if (xc, yc) not in coords:
                    coords[(xc, yc)] = False
                coords[((xc, yc))] = not fail
            elif 'WIR' in record:
                sheet.write(stdf_count, titles.index('Wafer ID'), record[1]['WAFER_ID'])
            elif 'WRR' in record:
                sheet.write(stdf_count, titles.index('Fabwf ID'), record[1]['FABWF_ID'])
            elif 'MRR' in record:
                end_time_tstamp = record[1]['FINISH_T']
                total = len(coords)
                good = len([x for x in coords.values() if x==True])
                end_time = datetime.fromtimestamp(end_time_tstamp).strftime('%Y/%m/%d %H:%M:%S')
                lead_time = end_time_tstamp - start_time_tstamp
                lead_time = ceil(lead_time/60)
                sheet.write(stdf_count, titles.index('end time'), end_time)
                sheet.write(stdf_count, titles.index('test time'), lead_time)
                sheet.write(stdf_count, titles.index('total'), total)
                sheet.write(stdf_count, titles.index('Pass'), good)
                sheet.write(stdf_count, titles.index('Yield'), good / total,pctg_fmt)
        # print('--- %.3f ---' %(time.time() - st))
        print(json.dumps(
            { 
                'target': 'parseFolder', 
                'msg': {
                    'status':'parserProgress',
                    'number': '%.3f' %(((n+1) / file_cnt) * 100) + '%',
                }
            }
        ))
        stdf_count += 1
    workbook.close()

if __name__ == '__main__':
    import sys
    from os.path import isdir
    target_path = sys.argv[1]
    output = r'files\output\%s' %sys.argv[2]
    parse_folder(target_path, output)