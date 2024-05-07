from os.path import basename
from os import remove
import gzip, time, json
import stdfReader
import stdfWriter

def remove_readings(stdf_path: str, output_file: str):
    delete = False
    if stdf_path.endswith('.gz') or '.gz' in stdf_path:
        unzip_filename = basename(stdf_path) + '.tmp_std'
        with gzip.open(stdf_path, 'rb') as f_in, open(unzip_filename, 'wb') as f_out:
            f_out.write(f_in.read())
        delete = True
    else:
        unzip_filename = stdf_path
    fp = open(unzip_filename, 'rb')
    fp.read()
    eof = fp.tell()
    fp.seek(0)
    new_fp = open(output_file, 'wb')
    record, pos = '', 0
    progress_time = time.time()
    needed_record = ['FAR','MIR','SDR','WIR','WCR','PIR','PRR','WRR','MRR']
    print(json.dumps(
            { 
                'target': 'rmReading', 
                'msg': {
                    'status':'parserProgress',
                    'number': '0%s (0/%d)' %('%', eof)
                }
            }
        )
    )
    while 'MRR' not in record:
        record, pos = stdfReader.readSTDFspecifyRecs(fp, pos, needed_record)
        if time.time()-progress_time >= 5 or pos==eof:
            progress_time = time.time()
            print(json.dumps(
                    { 
                        'target': 'rmReading', 
                        'msg': {
                            'status':'parserProgress',
                            'number': '%d%s (%d/%d)' %(round((pos/eof)*100), '%', pos, eof)
                        }
                    }
                )
            )
        if record == '!COM':
            raise EOFError('Incompleted record read, at %d' %pos)
        if record[0] in needed_record:
            new_fp.write(stdfWriter.mkRecord(record[0], record[1]))
    fp.close(), new_fp.close()
    if delete:
        remove(unzip_filename)

if __name__ == "__main__":
    import sys
    input_file_name, output_file_name = sys.argv[1], sys.argv[2]
    output_file_name = r'files\output' + f'\\{output_file_name}'
    remove_readings(input_file_name, output_file_name)