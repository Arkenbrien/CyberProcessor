import pymongo
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io
import cv2
import base64 
import json
import sys

import utm

from scipy.spatial.transform import Rotation as R
import time

from tqdm import tqdm

def findNearestComment(lat,lon,commentLat,commentLon, comments):
    diffs = []
    for i in range(len(commentLat)):
        dis = np.sqrt(
            (lat - commentLat[i])**2 + 
            (lon - commentLon[i])**2
                      )
        
        # print(dis)
        
        diffs.append(dis)

    closest = np.argmin(diffs)
    # print("NEAREST INDEX: ", closest)
    # print("AT: ", commentLat[closest], commentLon[closest])
    # print(comments[closest])
    # print(lat,lon)

    return comments[closest]

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

def getLatLonComments(com_file):
    lat_list = []
    lon_list = []
    probs = []
    for comment in com_file['comments']:
        lat = nmeaGGA2decDeg(comment['data'][1])
        
        lat_dir = comment['data'][2]

        if lat_dir == 'S':
            lat = lat * -1

        lon = nmeaGGA2decDeg(comment['data'][3])
        lon_dir = comment['data'][4]

        if lon_dir == 'W':
            lon = lon * -1
        # print(lat,lon) 

        lat_list.append(lat)
        lon_list.append(lon)
        probs.append(comment['problem'])

    return lat_list, lon_list, probs

if __name__ == "__main__":
    #IMPORT COMMENTS
    com_file = "/media/travis/moleski1/cyber_bags/1698251665/comments.json"
    com_file = open(com_file)
    com_file = json.load(com_file)
    lat_list, lon_list, probs = getLatLonComments(com_file)

    # Set up MongoDB connection
    # client = pymongo.MongoClient("mongodb://192.168.1.6:27017")
    client = pymongo.MongoClient("mongodb://localhost:27017")

    # Access the database
    db = client.cyber_data  # Replace 'your_database' with the actual name of your database

    # Access the collection (similar to a table in relational databases)
    collection = db.cyber_van  # Replace 'your_collection' with the actual name of your collection
    meta =  db.cyber_meta

    dis_info = open("./disengagement_times/34.json")
    dis_info = json.load(dis_info)
    # print(dis_info)

    dis_time = dis_info['disengagement_times'][0]
    # dis_dt   = dis_info['disengagement_tolerance']
    experiment_id = dis_info['experimentID']
    # print(experiment_id)
    # dis_time = 1698251665.5151424
    dis_dt = 1
    # experiment_id = 34

    metadID =  meta.find_one({'experimentID': int(experiment_id)})
    print(metadID)
    query = {
        'groupMetadataID': metadID['groupID'],
        'header.timestampSec':{"$gte": dis_time-dis_dt, "$lte":dis_time+dis_dt}
    }
    # Extract data from MongoDB
    print("LOOKING FOR DATA")
    result = collection.find(query)
    # 

    av_lat = []
    av_lon = []
    for dis in result:
        if dis['topic'] == "/apollo/localization/pose":
            vehicle_position = dis['pose']['position']
            lat, lon = utm.to_latlon(vehicle_position['x'], vehicle_position['y'], 17,'S')
            av_lat.append(lat)
            av_lon.append(lon)

    lat = np.mean(av_lat)
    lon = np.mean(av_lon)
    print("LOCATION: ", lat, lon)

    findNearestComment(lat,lon,lat_list,lon_list, probs)

        