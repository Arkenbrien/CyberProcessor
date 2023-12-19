import os

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/home/autobuntu/.local/lib/python3.10/site-packages/cv2/qt/plugins'



import pymongo
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io
import cv2
import base64 
import json
import sys

from scipy.spatial.transform import Rotation as R

import pyvista as pv
import pyvistaqt as pvqt
from PyQt5.QtCore import QCoreApplication

# Take in base64 string and return PIL image
def stringToImage(base64_string):
    imgdata = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(imgdata))

def toRGB(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)


# Set up MongoDB connection
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")

# Access the database
db = client.mongo_aws  # Replace 'your_database' with the actual name of your database

# Access the collection (similar to a table in relational databases)
collection = db.mongo_aws  # Replace 'your_collection' with the actual name of your collection

dis_info = open("657356cf4e8f29540c8a9d0f_.json")
dis_info = json.load(dis_info)
print(dis_info)

dis_time = dis_info['disengagement_times'][0]
dis_dt   = dis_info['disengagement_tolerance']
dis_dt = 30

# Query to extract data (you can customize this based on your needs)
# query = {'topic': '/apollo/localization/pose'}

query = {
    # 'topic': '/apollo/prediction/perception_obstacles',
    'header.timestampSec':{"$gte": dis_time-dis_dt, "$lte":dis_time+dis_dt}
}
# Extract data from MongoDB
print("LOOKING FOR DATA")
result = collection.find(query)

p =  pvqt.BackgroundPlotter()
# p.auto_update = False
print('='*100)
# init_position =[result[0]['pose']['position']['x'], result[0]['pose']['position']['y'],result[0]['pose']['position']['z']]
init_position= [0,0,0]
print('INIT',init_position)

p.show()  # Start visualisation, non-blocking call

obs_rot = R.from_euler('xyz',[180,180,-35],degrees=True)



# QCoreApplication.processEvents()
for document in result:
    if document['topic'] == "/apollo/sensor/camera/front_6mm/image/compressed":
        pil_im = stringToImage(document['data'])
        rgb_im = toRGB(pil_im)
        cv2.imshow(str(document['topic']), rgb_im)
        cv2.waitKey(1)

    if document['topic'] == "/apollo/localization/pose":
        vehicle_position = document['pose']['position']

        # print(document['pose'])
        vehicle_position['x'] = vehicle_position['x']-init_position[0]
        vehicle_position['y'] = vehicle_position['y']-init_position[1]
        vehicle_position['z'] = vehicle_position['z']-init_position[2]

        roll  = document['pose']['eulerAngles']['x']
        pitch = document['pose']['eulerAngles']['y']
        yaw   = document['pose']['eulerAngles']['z'] + np.pi/2

        vehicle_rot = R.from_euler('xyz',[roll,pitch,yaw],degrees=False)

        box_v = pv.Cube(center=(vehicle_position['x'], vehicle_position['y'], vehicle_position['z']),x_length=5.18922 , y_length=2.29616, z_length=1.77546)
        rotated = box_v.rotate_z(angle=np.rad2deg(yaw), point=[vehicle_position['x'],vehicle_position['y'],vehicle_position['z']])
        p.add_mesh(rotated, color='blue', show_edges=True)

        # points = pv.PolyData(np.column_stack((vehicle_position['x'], vehicle_position['y'], vehicle_position['z'])))
        # p.add_points(points,render_points_as_spheres=True, point_size=35.0,color='blue')

    if document['topic'] == '/apollo/sensor/velodyne32/PointCloud2':
        p.clear()
        x_master = []
        y_master = []
        z_master = []

        for point in range(len(document['point'])):
            lPoint = [document['point'][point]['x'],document['point'][point]['y'],document['point'][point]['z']]
            lPoint = vehicle_rot.apply(lPoint)

            x_master.append(lPoint[0] + vehicle_position['x'])
            y_master.append(lPoint[1] + vehicle_position['y'])
            z_master.append(lPoint[2] + vehicle_position['z'])

        points = pv.PolyData(np.column_stack((x_master, y_master, z_master)))
        p.add_points(points)

    if document['topic'] == "/apollo/perception/obstacles":
        x_Obmaster = []
        y_Obmaster = []
        z_Obmaster = []

        for obs in document['perceptionObstacle']:
            obs_point = np.array([obs['position']['x'],obs['position']['y'],obs['position']['z']])
            # obs_point -= init_position
            # obs_point = obs_rot.apply(obs_point)
            # obs_point = vehicle_rot.apply(obs_point)
            if obs['type'] == 'VEHICLE':
                c = 'red'
            else:
                c = 'green'
            # x_Obmaster.append(obs_point[0])
            # y_Obmaster.append(obs_point[1])
            # z_Obmaster.append(obs_point[2])

            xlength = obs['length'] 
            ylength = obs['width']  
            zlength = obs['height']

            boxO = pv.Cube(center=(obs_point),x_length=xlength, y_length=ylength, z_length=zlength)
            boxRot = boxO.rotate_z(angle=np.rad2deg(yaw),point=obs_point)
            p.add_mesh(boxRot, color=c, show_edges=True)

        # Opoints = pv.PolyData(np.column_stack((x_Obmaster, y_Obmaster, z_Obmaster)))
        # p.add_points(Opoints,render_points_as_spheres=True, point_size=35.0,color=c)

        # break
    # p.update()
    # p.show()
    QCoreApplication.processEvents()

# Close the MongoDB connection
p.close()
cv2.destroyAllWindows()
client.close()

