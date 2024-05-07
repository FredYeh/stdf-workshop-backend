import gzip
import io, gc
import time
import json

import stdfReader

def read_headers(fp: io.BytesIO|io.BufferedReader, percent_start: int, ratio: int) -> dict:
    headers = {}
    fp.read()
    eof = fp.tell()
    fp.seek(0)
    required_headers = ['MIR','SDR','WIR','WCR','WRR','MRR']
    record, pos = '', 0
    progress_time = time.time()
    while 'MRR' not in record:
        record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, required_headers)
        if time.time()-progress_time >= 3 or pos==eof:
            progress_time = time.time()
            print(json.dumps(
                    { 
                        'target': 'mergeSTDFs', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(round((pos/eof)*ratio) + percent_start, '%', pos, eof)
                        }
                    }
                )
            )
        if record == '!COM':
            raise EOFError('imcompleted STDF read.')
        elif record[0] in required_headers:
            headers[record[0]] = record[1]
    fp.seek(0)
    return headers


def merge_stdf(filename1: str, filename2: str, outputname: str):
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
    fp_1 = get_io(filename1)
    fp_2 = get_io(filename2)
    header_1 = read_headers(fp_1,  0, 10)
    header_2 = read_headers(fp_2, 10, 20)
    get_start_time = lambda d: d.get('MIR', {}).get('START_T', time.time())
    if get_start_time(header_1) > get_start_time(header_2):
        header_2, header_1 = header_1, header_2
        fp_2, fp_1 = fp_1, fp_2
    output = open(outputname, 'wb')

    # first file
    flag_records = ['PIR','PRR','BPS','GDR','WRR']
    record, pos = '', 0
    last_record = ''
    fp_1.read()
    eof = fp_1.tell()
    fp_1.seek(0)
    progress_time = time.time()
    while 'WRR' not in record:
        record, next_pos = stdfReader.readSTDFspecifyRecs(fp_1, pos, flag_records)
        if time.time()-progress_time >= 3 or pos==eof:
            progress_time = time.time()
            print(json.dumps(
                    { 
                        'target': 'mergeSTDFs', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(round((pos/eof)*50) + 20, '%', pos, eof)
                        }
                    }
                )
            )
        if ('WRR' in record) or (last_record == 'PRR' and record[0] not in ['PIR','PRR','BPS','GDR']):
            fp_1.seek(0)
            output.write(fp_1.read(pos))
            print(json.dumps(
                    { 
                        'target': 'mergeSTDFs', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(70, '%', pos, eof)
                        }
                    }
                )
            )
            break
        last_record, pos = record[0], next_pos
    # second file
    flag_records = ['PIR']
    record, pos = '', 0
    last_record = ''
    fp_2.read()
    eof = fp_2.tell()
    fp_2.seek(0)
    progress_time = time.time()
    while 'PIR' not in record:
        record, next_pos = stdfReader.readSTDFspecifyRecs(fp_2, pos, flag_records)
        if time.time()-progress_time >= 3 or pos==eof:
            progress_time = time.time()
            print(json.dumps(
                    { 
                        'target': 'mergeSTDFs', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(round((pos/eof)*30) + 70, '%', pos, eof)
                        }
                    }
                )
            )
        if 'PIR' in record:
            fp_2.seek(pos)
            output.write(fp_2.read())
            print(json.dumps(
                    { 
                        'target': 'mergeSTDFs', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(100, '%', pos, eof)
                        }
                    }
                )
            )
            break
        last_record, pos = record[0], next_pos
    output.close()
    fp_1.close(), fp_2.close()


if __name__ == '__main__':
    import sys
    first_stdf, second_stdf = sys.argv[1], sys.argv[2]
    output_name = r'files\output' + f'\\{sys.argv[3]}'
    merge_stdf(first_stdf, second_stdf, output_name)