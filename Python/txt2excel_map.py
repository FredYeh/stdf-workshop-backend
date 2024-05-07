import sys, json
import xlsxwriter
import time

def txt2excel_map(text_file, output_file):
    wb = xlsxwriter.Workbook(output_file)
    with open(text_file, 'r') as fp:
        content = fp.readlines()
    null_die = wb.add_format({"border":1})
    pass_die = wb.add_format({"border":1,"bg_color":"lime"})
    map_sheet = wb.add_worksheet("map ref die")
    map_sheet.set_column('A:ZZ',2.14)
    total = len(content)
    progress_time = time.time()
    try:
        for n, col in enumerate(content):
            if time.time()-progress_time >= 3 or n==total-1:
                progress_time = time.time()
                print(json.dumps(
                        { 
                            'target': 'textToExcel', 
                            'msg': {
                                'status':'parserProgress',
                                'number': '%d%s (%d/%d)' %(round((n/(total-1))*100), '%', n, total-1)
                            }
                        }
                    )
                )
                # print('\rPercentage: %3.6f%s (%d/%d)' %((pos/eof)*100, '%', pos, eof), end='')
            for m, die in enumerate(col):
                die = 1 if die=='1' else ''
                fmt = null_die if die != 1 else pass_die
                map_sheet.write(n, m, die, fmt)
    except:
        print(json.dumps(
                { 
                    'target': 'textToExcel', 
                    'msg': {
                        'status':'parserProgress',
                        'number': '100% (incomplete STDF)',
                    }
                }
            )
        )
    wb.close()

if __name__ == '__main__':
    text_file = sys.argv[1]
    output_file = r'files\output' + f'\\{sys.argv[2]}'
    txt2excel_map(text_file, output_file)