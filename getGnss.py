import pymongo
import json
from bson.json_util import dumps
import os

# Set up MongoDB connection
# client = pymongo.MongoClient("mongodb://192.168.1.6:27017")
client = pymongo.MongoClient("mongodb://localhost:27017")

# Access the database
db = client.cyber_data  # Replace 'your_database' with the actual name of your database

# Access the collection (similar to a table in relational databases)
collection = db.cyber_van  # Replace 'your_collection' with the actual name of your collection
meta =  db.cyber_meta

exp_id_list = [1,2,3,4,5,6,7]
topic_list = ['/apollo/localization/pose',
            "/apollo/sensor/gnss/gnss_status",
            "/apollo/sensor/gnss/ins_status",
            "/apollo/sensor/gnss/best_pose",
            "/apollo/sensor/gnss/corrected_imu",
            "/apollo/sensor/gnss/ins_stat",
            "/apollo/sensor/gnss/rtk_eph",
            "/apollo/sensor/gnss/rtk_obs",
            "/apollo/sensor/gnss/heading",
            "/apollo/sensor/gnss/imu",
            "/apollo/sensor/gnss/odometry",
            "/apollo/sensor/gnss/stream_status",
            "/apollo/sensor/gnss/raw_data",
            "/apollo/sensor/gnss/rtcm_data"
]

for exp_id in exp_id_list:
    metadID = meta.find_one({'experimentID': exp_id})

    print(metadID['groupMetadataID'])

    for topic in topic_list:

        query = {'groupMetadataID': metadID['groupMetadataID'], 
                'topic': topic}

        result = list(collection.find(query))

        dirName = f"./exp_{exp_id}"

        try:  
            os.mkdir(dirName)  
        except OSError as error:  
            print("DIR ALREADY THERE")

        t = topic.split("/")[-1]
        json_object = dumps(result, indent=4)
        with open(f"{dirName}/EXP{exp_id}_{t}.json", "w") as outfile:
            outfile.write(json_object)