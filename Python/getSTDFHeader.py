import gzip, io, gc, json, time
import stdfReader, stdfWriter
from os.path import getsize

def get_headers(stdf: str) -> dict:
    header = {}
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
    progress_time = time.time()
    while 'MRR' not in record:
        record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, ['MIR','SDR','WIR','WRR','WCR','MRR'])
        if (time.time()-progress_time >= 3) or (pos == eof):
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
        if record[0] in ['MIR','SDR','WIR','WRR','WCR','MRR']:
            header[record[0]] = record[1]
        if record == '!COM':
            break
    return header

if __name__ == '__main__':
    import sys
    output = get_headers(sys.argv[1])
    print(json.dumps(
            { 
                'target': 'stdfEditor', 
                'msg': {
                    'status':'header',
                    'output': output,
                }
            }
        )
    )