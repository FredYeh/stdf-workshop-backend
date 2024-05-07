import struct, json
import xlsxwriter
from os.path import basename
from os.path import splitext

def dat_to_excel(input_file:str, output: str):
    wb = xlsxwriter.Workbook(output)
    passGreen = wb.add_format()
    passGreen.set_align('center')
    passGreen.set_bg_color('lime')
    failRed = wb.add_format()
    failRed.set_align('center')
    failRed.set_bg_color('red')

    binMap = wb.add_worksheet('Bin Map')
    binMap.freeze_panes(1, 1)
    binMap.set_column('A:ZZ',2.14)

    print(json.dumps(
            { 
                'target': 'datReader', 
                'msg': {
                    'status':'parserProgress',
                    'number': '0% (--/--)'
                }
            }
        )
    )

    with open(input_file, 'rb') as fp:
        fp.read(25)
        fp.read(2)
        fp.read(1)
        fp.read(2)
        fp.read(1)
        struct.unpack('H',fp.read(2))
        struct.unpack('H',fp.read(2))
        total, = struct.unpack('H',fp.read(2))
        fp.read(12)
        fp.read(12)
        records, = struct.unpack('B',fp.read(1))
        records
        struct.unpack('h',fp.read(2))
        struct.unpack('h',fp.read(2))
        posBin = {}
        coords = {'x':set(),'y':set()}
        while True:
            sx, = struct.unpack('h',fp.read(2))
            if sx == -32768:
                break
            sy, = struct.unpack('h',fp.read(2))
            dies, = struct.unpack('B',fp.read(1))
            for x in range(dies):
                tmp = fp.read(2)
                try:
                    bitstr = tmp.hex()
                    b = int(bitstr[1])
                except:
                    continue
                posBin[(sx+x,sy)] = b
                coords['x'].add(sx+x)
                coords['y'].add(sy)
        # print(posBin)
        print(json.dumps(
                { 
                    'target': 'datReader', 
                    'msg': {
                        'status':'parserProgress',
                        'number': '50% (--/--)'
                    }
                }
            )
        )
        minx = min(coords['x'])
        maxx = max(coords['x'])
        miny = min(coords['y'])
        maxy = max(coords['y'])
        for i, num in enumerate(range(minx,maxx+1)):
            binMap.write(0,i+1,num)
        for i, num in enumerate(range(miny,maxy+1)):
            binMap.write(i+1,0,num)
        printBin = lambda l: l[0] if len(l)==1 else '/'.join(str(x) for x in l)
        for x, y in posBin.keys():
            binMap.write(y-miny+1, x-minx+1, posBin[(x,y)], passGreen if posBin[(x,y)]==1 else failRed)
        wb.close()

    print(json.dumps(
            { 
                'target': 'datReader', 
                'msg': {
                    'status':'parserProgress',
                    'number': '100% (--/--)'
                }
            }
        )
    )

if __name__ == '__main__':
    import sys
    file_name, excel_name = sys.argv[1], sys.argv[2]
    excel_name = r'files\output' + f'\\{excel_name}'
    dat_to_excel(file_name, excel_name)