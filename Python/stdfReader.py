# =============================
# Author : Fred Yeh
# E-mail : b0093069@gmail.com
# Python : 3.9.0
# Version: 1
# Last Update : 2022/1/6
# =============================
from stdf_spec import *
import struct
import time
import sys, os
import io, gzip, gc

def readSTDF(stdf, pos=0):
    stdf.seek(pos)  # Specify the start read position
    # Get REC_LEN first to prvent imcomplete record
    try:
        reclen, rectyp, recsub= struct.unpack('HBB',stdf.read(4))
    except struct.error:
        return ('!COM',pos)
    recHead = stdf.tell()   # Flag of record start
    REC = info.get((rectyp,recsub),'NAN')

    # Return original position if record imcomplete
    if len(stdf.read(reclen))!=reclen:
        return ('!COM',pos)

    # Complete record process
    stdf.seek(recHead)       # Return file cursor to record content
    content = stdf.read(reclen)
    return (getInfo(REC, content),stdf.tell())

def readSTDFspecifyRecs(stdf, pos, recList):
    # Read STDF with only specific records
    stdf.seek(pos)
    try:
        reclen, rectyp, recsub= struct.unpack('HBB',stdf.read(4))
    except struct.error:
        return ('!COM',pos)
    recHead = stdf.tell()
    REC = info.get((rectyp,recsub),'NAN')
    if REC not in recList:
        return ('NAN',pos+reclen+4) # skip the record not in list

    if len(stdf.read(reclen))!=reclen:
        return ('!COM',pos)

    stdf.seek(recHead)
    content = stdf.read(reclen)
    return (getInfo(REC, content),stdf.tell())

def getInfo(REC, content):
    # Exception of event 'NAN'
    if REC=='NAN':
        return REC
    
    # Get record all data fields & types from stdf_spec.py
    # Variable `count` is for process fields one by one
    # Finally, return dict data `fieldDict`
    recMap = RecordTypeMap[REC]
    count = 0
    fieldDict = {}
    while content!=b'':
        field, dataType = recMap[count]
        data, content = read(dataType,content)
        fieldDict.update({field:data})
        count += 1
    # Directly use record name as event
    return REC, fieldDict

# STDF parsing, 
# t stands for STDF type and l for bytes
def read(t, l):
    if t in unpackFormatMap:
        type_len = int(t[1])
        res, = struct.unpack_from(unpackFormatMap[t],l,0)
        l = l[type_len:]
        return res, l
    elif t == 'C1':
        c1, = struct.unpack_from("c",l,0)
        l = l[1:]
        return c1.decode("ascii"), l
    # ========Special case of j*xx, k*xx in STDF spec========
    elif t.endswith('k') or t.endswith('j'):
        res,l = read(t.strip('k').strip('j'),l)
        # Store the k value at tail of the data
        jkValue = int(res) if res!='' else 0
        jkCount.update({t[-1]:jkValue})
        return res, l
    elif t.startswith('k') or t.startswith('j'):
        n = jkCount[t[0]]
        res = []
        if t.endswith('N1'):    # for k(j)N1 data type
            n1s_len = int( (n+1)/2 )
            n1s = l[:n1s_len]
            l = l[n1s_len:]
            res = n1s.hex()
        else:
            for x in range(n):
                tmp,l = read(t.strip('k').strip('j'),l)
                res.append(tmp)
        return res, l
    # =================================================
    elif t==('Cn'):
        return getCn(l)
    # for Bn data type
    elif t==('Bn'):
        return getBn(l)
    # for Dn data type
    elif t==('Dn'):
        return getDn(l)
    # for Vn data type
    elif t==('Vn'):
        return None, b''

# for Cn data type
def getCn(l):
    n, = struct.unpack_from('B',l,0)
    l = l[1:]
    res, = struct.unpack_from('%ss' %n,l,0)
    l = l[n:]
    return res.decode("ascii"), l
# for Bn data type
def getBn(l):
    n, = struct.unpack_from('B',l,0)
    l = l[1:]
    res = []
    for x in range(n):
        tmp, = struct.unpack_from('B',l,0)
        l = l[1:]
        res.append(tmp)
    return res,l
# for Dn data type
def getDn(l):
    n, = struct.unpack_from('H',l,0)
    n = int(n/8) if n%8==0 else int(n/8)+1
    l = l[2:]
    res = []
    for x in range(n):
        tmp, = struct.unpack_from('B',l,0)
        l = l[1:]
        res.append(tmp)
    return res,l

if __name__ == '__main__':
    if len(sys.argv)<2:
        print('Usage: '+sys.argv[0]+' <STDF> <Start position>')
    else:
        stdf, pos = (sys.argv[1], int(sys.argv[2])) if len(sys.argv)==3 else (sys.argv[1], 0)
        fp = gzip.open(stdf,'rb') if stdf.endswith('.gz') else open(stdf,'rb')
        content = fp.read()
        eof = fp.tell()
        fp.close()
        f = io.BytesIO(content)
        del content
        output = open('%s.json' %os.path.splitext(stdf)[0], 'w')
        output.write('[\n')
        gc.collect()
        event = ''
        start_time = time.time()
        while 'MRR' not in event:
            event, pos = readSTDFspecifyRecs(f,pos,['MIR','SDR','PRR','MRR'])
            if '!COM' in event:
                print('!COM event: read imcomplete record, wait 3 seconds...')
                print('Next time start at', pos)
                import time
                time.sleep(3)
            elif 'NAN' not in event:
                # print(event,pos)
                output.write('    '+str(list(event))+',\n')
        f.close()
        output.write(']')
        output.close()
        print('End of processing.')
        print("--- %.3f seconds ---" % (time.time() - start_time))