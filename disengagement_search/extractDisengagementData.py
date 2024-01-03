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
import pyvista as pv
import pyvistaqt as pvqt
from PyQt5.QtCore import QCoreApplication

from findComments import getLatLonComments, nmeaGGA2decDeg, dms_to_dd, findNearestComment

# Take in base64 string and return PIL image
def stringToImage(base64_string):
    imgdata = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(imgdata))

def toRGB(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)


def drawPlots(dataList):
    ncols = 1
    nrows = len(dataList)
    plt.rcParams.update({'font.size': 22})
    # f = plt.figure()
    f, axes = plt.subplots(nrows,ncols,squeeze=False)

    for data in range(len(dataList)):
        print(dataList[data]['name'])
        axes[data][0].plot(dataList[data]['time'], dataList[data]['data'])
        axes[data][0].set_xlabel(dataList[data]['x_label'])
        axes[data][0].set_ylabel(dataList[data]['y_label'])
        axes[data][0].grid(True)



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

dis_time = dis_info['disengagement_times'][4]
dis_dt   = dis_info['disengagement_tolerance']
experiment_id = dis_info['experimentID']
# print(experiment_id)
# dis_time = 1698251665.5151424
# dis_dt = 2
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
p =  pvqt.BackgroundPlotter()
# p = pv.Plotter()
p.show()  # Start visualisation, non-blocking call
# p.show(auto_close=False, interactive_update=True)  # Start visualisation, non-blocking call
print("CREATED PLOT")


get_im = True
get_lidar = True
get_obstacles = True
get_pose = True
get_gnss = True

# tStart = time.time()

sol_type = "NOT_QUERIED"
lat = None
lon = None
std_2d = None
driving_mode = None
comment = "NONE"

master_cloud_x = []
master_cloud_y = []
master_cloud_z = []
master_cloud_i = []

master_obs_x = []
master_obs_y = []
master_obs_z = []
master_obs_c = []

num_sat_obj = {
    'time': [],
    'data': [],
    'name': "Tracked SVs",
    'x_label': 'time (s)',
    'y_label': 'SV Count'
}

std_obj = {
    'time': [],
    'data': [],
    'name': "2D STD (m)",
    'x_label': 'time (s)',
    'y_label': 'GNSS Position STD (m)'
}

spd_obj = {
    'time': [],
    'data': [],
    'name': "Speed (mph)",
    'x_label': 'time (s)',
    'y_label': 'Speed (mph)'
}

steer_obj = {
    'time': [],
    'data': [],
    'name': "Steering)",
    'x_label': 'time (s)',
    'y_label': 'steering percentage)'
}

brake_obj = {
    'time': [],
    'data': [],
    'name': "Brake",
    'x_label': 'time (s)',
    'y_label': 'Braking Percentage'
}



gnss_list    = []
chassis_list = []

print("STARTING LOOP...")
for document in tqdm(result):
    # print(document)
    # loopStart = time.time()
    # print(document['topic'],"\n")
    if document['topic'] == "/apollo/sensor/camera/front_6mm/image/compressed" and get_im:
        pil_im = stringToImage(document['data'])
        rgb_im = toRGB(pil_im)

        cv2.putText(rgb_im, sol_type, (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, ("(") + str(lat) + ', ' +str(lon) +  (")"), (10,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, 'STD: '+ str(std_2d), (10,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, str(driving_mode), (10,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, 'Experiment: '+dis_info['experimentID'], (10,250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, dis_info['vehicleID'], (10,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        cv2.putText(rgb_im, dis_info['other'], (10,1050), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(rgb_im, comment, (10,1015), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow(str(document['topic']), rgb_im)
        cv2.waitKey(1)

    if document['topic'] == "/apollo/localization/pose" and get_pose:
        vehicle_position = document['pose']['position']
        lat, lon = utm.to_latlon(vehicle_position['x'], vehicle_position['y'], 17,'S')
        comment = findNearestComment(lat,lon,lat_list, lon_list, probs)

        # print("COMMENT", comment)

        roll  = document['pose']['eulerAngles']['x']
        pitch = document['pose']['eulerAngles']['y']
        yaw   = document['pose']['eulerAngles']['z'] + np.pi/2

        vehicle_rot = R.from_euler('xyz',[roll,pitch,yaw],degrees=False)

        if driving_mode == 'COMPLETE_AUTO_DRIVE':
            v_col = 'green'
        elif driving_mode == 'EMERGENCY_MODE':
            v_col = 'yellow'
        elif driving_mode == None:
            v_col = 'purple'
        else:
            v_col = 'red'

        box_v = pv.Cube(center=(vehicle_position['x'], vehicle_position['y'], vehicle_position['z']),x_length=5.18922 , y_length=2.29616, z_length=1.77546)
        rotated = box_v.rotate_z(angle=np.rad2deg(yaw), point=[vehicle_position['x'],vehicle_position['y'],vehicle_position['z']])
        p.add_mesh(rotated, color=v_col, show_edges=True)


    if document['topic'] == '/apollo/sensor/velodyne32/PointCloud2':
        if get_lidar:
            x_master = np.zeros(len(document['point']))
            y_master = np.zeros(len(document['point']))
            z_master = np.zeros(len(document['point']))
            int_master = np.zeros(len(document['point']))

            for point in range(len(document['point'])):
                lPoint = [document['point'][point]['x'],document['point'][point]['y'],document['point'][point]['z']]
                lPoint = vehicle_rot.apply(lPoint)

                x_master[point] =  (lPoint[0] + vehicle_position['x'])
                y_master[point] =  (lPoint[1] + vehicle_position['y'])
                z_master[point] =  (lPoint[2] + vehicle_position['z'])
                int_master[point] =  (document['point'][point]['intensity'])

            master_cloud_x.extend(x_master)
            master_cloud_y.extend(y_master)
            master_cloud_z.extend(z_master)
            master_cloud_i.extend(int_master)

            # point_cloud = pv.PolyData(np.column_stack((x_master, y_master, z_master)))
            # point_cloud['colors'] = int_master
            # point_cloud.plot(point_cloud, cmap='jet', render_points_as_spheres=True)
            # p.add_points(point_cloud)

        # p.update()

    if document['topic'] == "/apollo/perception/obstacles" and get_obstacles:
        # p.clear()
        # p.update()

        if "perceptionObstacle" in document:
            for obs in document['perceptionObstacle']:
                # obs_point = np.array([obs['position']['x'],obs['position']['y'],obs['position']['z']])
                if obs['type'] == 'VEHICLE':
                    c = 'blue'
                else:
                    c = 'green'

                master_obs_x.append(obs['position']['x'])
                master_obs_y.append(obs['position']['y'])
                master_obs_z.append(obs['position']['z'])
                master_obs_c.append(c)


                # boxO = pv.Cube(center=(obs_point),x_length=obs['length'] , y_length=obs['width'], z_length= obs['height'])
                # boxRot = boxO.rotate_z(angle=np.rad2deg(obs['theta']),point=obs_point)
                # p.add_mesh(boxRot, color=c, show_edges=True)

    if document['topic'] == "/apollo/sensor/gnss/best_pose" and get_gnss:
        sol_type =document['solType']
        lat_std_gnss = document['latitudeStdDev']
        lon_std_gnss = document['longitudeStdDev']
        hgt_std_gnss = document['heightStdDev']
        
        num_sat = document['numSatsInSolution']
        std_2d = (lat_std_gnss + lon_std_gnss)/2

        num_sat_obj['time'].append(document['header']['timestampSec'])
        num_sat_obj['data'].append(document['numSatsInSolution'])

        std_obj['time'].append(document['header']['timestampSec'])
        std_obj['data'].append(std_2d)



        # print("SOLUTION TYPE", sol_type, "WITH 2D std (m)", std_2d)

    if document['topic'] == "/apollo/canbus/chassis":
        driving_mode = document['drivingMode']

        speed = round(document['speedMps'] * 2.23694, 2)

        spd_obj['time'].append(document['header']['timestampSec'])
        spd_obj['data'].append(speed)

        steer_obj['time'].append(document['header']['timestampSec'])
        steer_obj['data'].append(document['steeringPercentage'])

        brake_obj['time'].append(document['header']['timestampSec'])
        brake_obj['data'].append(document['brakePercentage'])


    # loopEnd = time.time()
    # rate_loop = 1 / (loopEnd - loopStart)
    # print("LOOP RATE: ", rate_loop)
    # time.sleep(.001)
    # p.update()
    # p.show(auto_close=False, interactive_update=True)  # Start visualisation, non-blocking call

    QCoreApplication.processEvents()

gnss_list.append(num_sat_obj)
gnss_list.append(std_obj)

chassis_list.append(spd_obj)
chassis_list.append(brake_obj)
chassis_list.append(steer_obj)

drawPlots(gnss_list)
drawPlots(chassis_list)

print("DRAWING MASTER CLOUD")
point_cloud = pv.PolyData(np.column_stack((master_cloud_x, master_cloud_y, master_cloud_z)))
point_cloud['intensity'] = master_cloud_i
point_cloud.plot(point_cloud, cmap='jet', render_points_as_spheres=True)
p.add_points(point_cloud)
print("DREW CLOUD???")

obstacles = pv.PolyData(np.column_stack((master_obs_x, master_obs_y, master_obs_z)))
# obstacles['intensity'] = master_obs_c
obstacles.plot(obstacles, cmap='jet', render_points_as_spheres=True)
p.add_points(obstacles)




try:
    while True:
        QCoreApplication.processEvents()
        plt.pause(0.001)
except KeyboardInterrupt:
    pass

cv2.waitKey(0)
# Close the MongoDB connection
p.close()
cv2.destroyAllWindows()
client.close()

