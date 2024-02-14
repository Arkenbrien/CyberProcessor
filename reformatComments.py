import json
import os
from datetime import datetime

import datetime

def dms_to_dd(d, m, s):
    if d[0]=='-':
        dd = float(d) - float(m)/60 - float(s)/3600
    else:
        dd = float(d) + float(m)/60 + float(s)/3600
    return dd

def nmeaGGA2decDeg(GGA):
    if int(GGA[0]) != 0:
        deg = GGA[0] + GGA[1]
        min = GGA[2:]
    else:
        deg = GGA[0] + GGA[1] + GGA[2]
        min = GGA[3:]
    decimal = dms_to_dd(deg,min,0)
    return(decimal)

def getLatLonComments(comment):
    lat = nmeaGGA2decDeg(comment['data'][1])
    
    lat_dir = comment['data'][2]

    if lat_dir == 'S':
        lat = lat * -1

    lon = nmeaGGA2decDeg(comment['data'][3])
    lon_dir = comment['data'][4]

    if lon_dir == 'W':
        lon = lon * -1
    # print(lat,lon) 
        
    
    alt = float(comment['data'][8])

    return lat, lon, alt

def extractHMS(string):
    hour   = int(string[:2])
    minute = int(string[2:4])
    second = int(string[4:6])
    return hour, minute, second

year = 2023
month = 9
day = 14

# epoch = datetime.datetime(year, month, day, hour, minute, second).strftime('%s')
# print(epoch)


directory = "./newComments"
newDir    = "./reformattedComments/"

for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    print(f)
    masterDict ={
        'comments':[]
    }
    if os.path.isfile(f):
        with open(f) as file:
            old = json.load(file)

            for entry in old['comments']:
                current_dict = {}

                event = entry['problem']
                data = entry['data']
                time = data[0]
                h,m,s = extractHMS(time)
                epoch_time = float(datetime.datetime(year,month,day,h,m,s).strftime('%s'))

                current_dict['timestampSec']  = epoch_time
                current_dict['event'] = event
                current_dict['groupID'] = 3

                lat, lon, alt = getLatLonComments(entry)

                LLH = {
                    'latitude': lat,
                    'longitude': lon,
                    'alt_msl': alt
                }

                current_dict['gnssPosition'] = LLH

                masterDict['comments'].append(current_dict)

            # print(masterDict)

    with open(newDir+filename, 'w') as fp:
        print("CREATED NEW FILE: ", newDir+filename)
        json.dump(masterDict, fp, indent=4)

