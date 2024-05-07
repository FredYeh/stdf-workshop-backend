import sys, json
import stdfParser_noreadings
import stdfParser

filePath = sys.argv[1]
filename = sys.argv[2]
reading = sys.argv[3]

if reading == 'true':
    print(json.dumps({ 'target': 'reading', 'msg': 'reading' }))
    stdfParser.stdf_to_excel(filePath, filename)
else:
    print(json.dumps({ 'target': 'noreadings', 'msg': 'noreadings' }))
    stdfParser_noreadings.stdf_to_excel(filePath, filename)