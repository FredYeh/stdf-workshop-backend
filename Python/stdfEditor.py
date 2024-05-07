import gzip, io, gc, time, json
from os.path import getsize

import stdfReader, stdfWriter

def edit_stdf(stdf: str, new_heads: dict, new_stdf_name: str):
    if stdf.endswith('.gz'):
        fp = gzip.open(stdf,'rb')
        content = fp.read()
        eof = fp.tell()
        fp.close()
        fp = io.BytesIO(content)
        del content
        gc.collect()
    else:
        fp = open(stdf, 'rb')
        eof = getsize(stdf)
    record, pos = [], 0
    new_stdf = open(new_stdf_name, 'wb')
    progress_time = time.time()
    edit_records = sorted([rec for rec in new_heads.keys()], key=lambda k: ['MIR','SDR','WIR','WRR','WCR','MRR'].index(k))
    while edit_records[-1] not in record:
        record, nextpos = stdfReader.readSTDFspecifyRecs(fp, pos, edit_records)
        if time.time()-progress_time >= 3 or pos==eof:
            progress_time = time.time()
            print(json.dumps(
                    { 
                        'target': 'stdfEditor', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(round((pos/eof)*100), '%', pos, eof)
                        }
                    }
                )
            )
        if record == 'NAN':
            fp.seek(pos)
            line = fp.read(nextpos - pos)
        if record[0] in ['MIR','SDR','WIR','WRR','WCR','MRR']:
            line = stdfWriter.mkRecord(record[0], new_heads[record[0]])
        new_stdf.write(line)
        pos = nextpos
    print(json.dumps(
            { 
                'target': 'stdfEditor', 
                'msg': {
                    'status':'parserProgress',
                    'number': '100%s (%d/%d)' %('%', eof, eof)
                }
            }
        )
    )
    fp.seek(nextpos)
    new_stdf.write(fp.read())
    fp.close(), new_stdf.close()

if __name__ == "__main__":
    import sys
    output_path = r'files\output' + '\\' +  sys.argv[3]
    edit_stdf(sys.argv[1], json.loads(sys.argv[2]), output_path)