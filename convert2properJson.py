import json
import os
from datetime import datetime

directory = "./oldComments"
newDir    = "./newComments/"

for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    masterDict ={
        "comments": []
    }
    if os.path.isfile(f):
        with open(f) as file:
            subDict = {}
            lines = [line.rstrip() for line in file]
            for line in lines:
                try:
                    toDict = json.loads(line)

                    if 'data' in toDict.keys():
                        time_obj = datetime.strptime(toDict['data'][0], "%H%M%S.%f")
                        formatted_time = time_obj.strftime("%H:%M:%S+00:00")
                        formatted_time_str = str(formatted_time)
                        toDict['data'][0] = formatted_time_str

                    subDict.update(toDict)

                except:
                    masterDict["comments"].append(subDict)
                    subDict = {}
                    continue

    with open(newDir+filename, 'w') as fp:
        print("CREATED NEW FILE: ", newDir+filename)
        json.dump(masterDict, fp, indent=4)

