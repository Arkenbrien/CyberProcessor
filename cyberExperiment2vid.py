
# import packages
import sys, time, os
from importlib import import_module
# from cyber_py import cyber
# from cyber_py import record
# from modules.drivers.proto.sensor_image_pb2 import CompressedImage
# from traffic_light_pb2 import TrafficLightDetection, TrafficLightDebug, TrafficLight
# from chassis_pb2 import Chassis
import numpy as np
import cv2
from PIL import Image
import io
import google.protobuf as protobuf
import google.protobuf.descriptor_pb2 as descriptor_pb2
import apollopy.proto.record_pb2 as record_pb2
import apollopy.proto.proto_desc_pb2 as proto_desc_pb2
from google.protobuf.json_format import MessageToJson
# import apollopy.proto.localization_pb2 as localization_pb2# import Uncertainty, LocalizationEstimate, LocalizationStatus
import json
from tqdm import tqdm
from cybertools.cyberreaderlib import ProtobufFactory, RecordReader, RecordMessage
import base64
from datetime import datetime

# from sensor_image_pb2 import CompressedImage


###########################################################
class VideoExporter:
    
    def __init__(self, camera_topic, export_dir, time_set):
        
        # Topics
        self.camera_topic           = camera_topic

        self.export_folder          = ""
        self.export_dimensions      = (1920,1080)

        self.image = None
        self.addMeta = True

        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videWriter = cv2.VideoWriter(export_dir+ "/" +str(time_set) + ".avi", self.fourcc , 20.0, self.export_dimensions)

    def stringToImage(self):
        self.image = base64.b64decode(self.image)
        self.image = Image.open(io.BytesIO(self.image))        
        self.image_ts = 0
        return self.image_ts


    def toRGB(self):
        self.image = cv2.cvtColor(np.array(self.image), cv2.COLOR_BGR2RGB)

    
    def add_frame(self):
        
        img = cv2.resize(self.image, self.export_dimensions)
        self.videWriter.write(img)
               
               
    def export_video(self):
        
        self.videWriter.release()
        print('')
        print('VIDEO RELEASED') 
        print('')
        
        
###########################################################


class GetMetadataToJson():
    def __init__(self,export_dir,time_set):
        print(export_dir, time_set)
        self.filename = export_dir+ "/" +str(time_set) + ".json"
        print(self.filename)
        self.frames = []
        
        
    def createHeader(self, header_json):
        self.frames = [header_json] + self.frames
        pass
    
    def getMatchedLocalizationMetaData(self, ts, to_match_data):
        
        # Extract timestamps from the first column of localization_data (ts)
        timestamps = np.array(to_match_data)[:, 0]
        
        # Find the index of the closest timestamp
        closest_index = np.argmin(np.abs(timestamps - ts))
        
        # Get the closest timestamp
        # closest_timestamp = timestamps[closest_index]
        localization_metadata = {
            
            'ts': to_match_data[closest_index][0],
            'pose_x': to_match_data[closest_index][1],
            'pose_y': to_match_data[closest_index][2],
            'pose_z': to_match_data[closest_index][3],
            'ori_qx': to_match_data[closest_index][4],
            'ori_qy': to_match_data[closest_index][5],
            'ori_qz': to_match_data[closest_index][6],
            'ori_qw': to_match_data[closest_index][7],
            'lin_vel_x': to_match_data[closest_index][8],
            'lin_vel_y': to_match_data[closest_index][9],
            'lin_vel_z': to_match_data[closest_index][10],
            'lin_acc_x': to_match_data[closest_index][11],
            'lin_acc_y': to_match_data[closest_index][12],
            'lin_acc_z': to_match_data[closest_index][13],
            'ang_vel_x': to_match_data[closest_index][14],
            'ang_vel_y': to_match_data[closest_index][15],
            'ang_vel_z': to_match_data[closest_index][16],
            'heading': to_match_data[closest_index][17],
            'lin_acc_vrf_x': to_match_data[closest_index][18],
            'lin_acc_vrf_y': to_match_data[closest_index][19],
            'lin_acc_vrf_z': to_match_data[closest_index][20],
            'ang_vel_vrf_x': to_match_data[closest_index][21],
            'ang_vel_vrf_y': to_match_data[closest_index][22],
            'ang_vel_vrf_z': to_match_data[closest_index][23],
            'euler_x': to_match_data[closest_index][24],
            'euler_y': to_match_data[closest_index][25],
            'euler_z': to_match_data[closest_index][26],
            'measurement_time': to_match_data[closest_index][27]
            
        }
        
        return localization_metadata 
    
    def getMatchedChassisMetaData(self, ts, to_match_data):
        
        # Extract timestamps from the first column of localization_data (ts)
        # Note that if the to_match_data contains strings, everything in the array is a string.
        # Convert the column to float there.....
        timestamps = np.array(to_match_data)[:, 0].astype(float)
                
        # Find the index of the closest timestamp
        closest_index = np.argmin(np.abs(timestamps - ts))
        
        chassis_metadata = {
            
            'ts': to_match_data[closest_index][0],
            'engine_started': to_match_data[closest_index][1],
            'speed_mps': to_match_data[closest_index][2],
            'fuel_range_m': to_match_data[closest_index][3],
            'throttle_percentage': to_match_data[closest_index][4],
            'brake_percentage': to_match_data[closest_index][5],
            'steering_percentage': to_match_data[closest_index][6],
            'driving_mode': to_match_data[closest_index][7],
            'error_code': to_match_data[closest_index][8],
            'gear_location': to_match_data[closest_index][9],
            'turn_signal': to_match_data[closest_index][10],
            'engage_advice': to_match_data[closest_index][11],
            'is_wheel_spd_rr_valid': to_match_data[closest_index][12],
            'wheel_spd_rr': to_match_data[closest_index][13],
            'is_wheel_spd_rl_valid': to_match_data[closest_index][14],
            'wheel_spd_rl': to_match_data[closest_index][15],
            'is_wheel_spd_fr_valid': to_match_data[closest_index][16],
            'wheel_spd_fr': to_match_data[closest_index][17],
            'is_wheel_spd_fl_valid': to_match_data[closest_index][18],
            'wheel_spd_fl': to_match_data[closest_index][19],
            'yaw_rate': to_match_data[closest_index][20],
            'steering_rate': to_match_data[closest_index][21]
            
        }
        return chassis_metadata
    
    def export(self):
        
        with open(self.filename, 'a') as json_file:
            json.dump(self.frames, json_file, indent=4)
            json_file.write('\n')
    
    
    
###########################################################

class GetLocalizationData():
    
    def __init__(self) -> None:
        self.localization_data = []
        
    def parseData(self, locdata):
        
        ts = locdata['header']['timestampSec']

        pose_x = locdata['pose']['position']['x']
        pose_y = locdata['pose']['position']['y']
        pose_z = locdata['pose']['position']['z']

        ori_qx = locdata['pose']['orientation']['qx']
        ori_qy = locdata['pose']['orientation']['qy']
        ori_qz = locdata['pose']['orientation']['qz']
        ori_qw = locdata['pose']['orientation']['qw']

        lin_vel_x = locdata['pose']['linearVelocity']['x']
        lin_vel_y = locdata['pose']['linearVelocity']['y']
        lin_vel_z = locdata['pose']['linearVelocity']['z']

        lin_acc_x = locdata['pose']['linearAcceleration']['x']
        lin_acc_y = locdata['pose']['linearAcceleration']['y']
        lin_acc_z = locdata['pose']['linearAcceleration']['z']

        ang_vel_x = locdata['pose']['angularVelocity']['x']
        ang_vel_y = locdata['pose']['angularVelocity']['y']
        ang_vel_z = locdata['pose']['angularVelocity']['z']

        heading = locdata['pose']['heading']

        lin_acc_vrf_x = locdata['pose']['linearAccelerationVrf']['x']
        lin_acc_vrf_y = locdata['pose']['linearAccelerationVrf']['y']
        lin_acc_vrf_z = locdata['pose']['linearAccelerationVrf']['z']

        ang_vel_vrf_x = locdata['pose']['angularVelocityVrf']['x']
        ang_vel_vrf_y = locdata['pose']['angularVelocityVrf']['y']
        ang_vel_vrf_z = locdata['pose']['angularVelocityVrf']['z']

        euler_x = locdata['pose']['eulerAngles']['x']
        euler_y = locdata['pose']['eulerAngles']['y']
        euler_z = locdata['pose']['eulerAngles']['z']

        measurement_time = locdata['measurementTime']
        
        to_append = [
                        ts,
                        pose_x, pose_y, pose_z,
                        ori_qx, ori_qy, ori_qz, ori_qw,
                        lin_vel_x, lin_vel_y, lin_vel_z,
                        lin_acc_x, lin_acc_y, lin_acc_z,
                        ang_vel_x, ang_vel_y, ang_vel_z,
                        heading,
                        lin_acc_vrf_x, lin_acc_vrf_y, lin_acc_vrf_z,
                        ang_vel_vrf_x, ang_vel_vrf_y, ang_vel_vrf_z,
                        euler_x, euler_y, euler_z,
                        measurement_time
                    ]
                
        self.localization_data.append(to_append)
    
###########################################################

class GetChassisData():
    
    def __init__(self) -> None:
        
        self.chassis_data = []
        
    def parseData(self, canbus_data):
        
        ts_canbus = canbus_data['header']['timestampSec']

        engine_started = canbus_data['engineStarted']
        speed_mps = canbus_data['speedMps']
        fuel_range_m = canbus_data['fuelRangeM']
        throttle_percentage = canbus_data['throttlePercentage']
        brake_percentage = canbus_data['brakePercentage']
        steering_percentage = canbus_data['steeringPercentage']

        driving_mode = canbus_data['drivingMode']
        error_code = canbus_data['errorCode']
        gear_location = canbus_data['gearLocation']

        turn_signal = canbus_data['signal']['turnSignal']
        engage_advice = canbus_data['engageAdvice']['advice']

        is_wheel_spd_rr_valid = canbus_data['wheelSpeed']['isWheelSpdRrValid']
        wheel_spd_rr = canbus_data['wheelSpeed']['wheelSpdRr']
        is_wheel_spd_rl_valid = canbus_data['wheelSpeed']['isWheelSpdRlValid']
        wheel_spd_rl = canbus_data['wheelSpeed']['wheelSpdRl']
        is_wheel_spd_fr_valid = canbus_data['wheelSpeed']['isWheelSpdFrValid']
        wheel_spd_fr = canbus_data['wheelSpeed']['wheelSpdFr']
        is_wheel_spd_fl_valid = canbus_data['wheelSpeed']['isWheelSpdFlValid']
        wheel_spd_fl = canbus_data['wheelSpeed']['wheelSpdFl']

        yaw_rate = canbus_data['yawRate']
        steering_rate = canbus_data['steeringRate']
        
        to_append = [

                        ts_canbus,
                        engine_started,
                        speed_mps,
                        fuel_range_m,
                        throttle_percentage,
                        brake_percentage,
                        steering_percentage,
                        driving_mode,
                        error_code,
                        gear_location,
                        turn_signal,
                        engage_advice,
                        is_wheel_spd_rr_valid,
                        wheel_spd_rr,
                        is_wheel_spd_rl_valid,
                        wheel_spd_rl,
                        is_wheel_spd_fr_valid,
                        wheel_spd_fr,
                        is_wheel_spd_fl_valid,
                        wheel_spd_fl,
                        yaw_rate,
                        steering_rate
                        
        ]
        
        # print(chassis_data.chassis_data)
        
        # time.sleep(1)
        
        self.chassis_data.append(to_append)


    
###########################################################

def initReader(filename):
    
    unqiue_channel = []
    pbfactory = ProtobufFactory()
    reader = RecordReader(filename)
    
    for channel in reader.GetChannelList():
        
        desc = reader.GetProtoDesc(channel)
        pbfactory.RegisterMessage(desc)
        unqiue_channel.append(channel)
        
    message = RecordMessage()
    
    return message, reader, pbfactory

###########################################################


if __name__ == "__main__":
    
    ### OPTIONS ###
    file_set = 1698251665
    direct = "/media/travis/moleski1/cyber_bags/" + str(file_set)
    export_dir = "./videos/full_route/" + str(file_set)

    print(export_dir)


    if not os.path.exists(export_dir):
        # Create the directory if it doesn't exist
        os.makedirs(export_dir)
        print(f"Directory '{export_dir}' created successfully.")
    else:
        print(f"Directory '{export_dir}' already exists.")


    # TOPICS
    image_handler = VideoExporter(camera_topic="/apollo/sensor/camera/front_6mm/image/compressed", export_dir=export_dir, time_set=file_set)
    localization_topic = "/apollo/localization/pose"
    chassis_topic = "/apollo/canbus/chassis"
    
    # FILE LOCATION
    # direct = "/mnt/h/cyber_bags/1698251665/"
    # direct = "/media/travis/moleski1/cyber_bags/1698251665"
    # direct = "/media/autobuntu/chonk/chonk/git_repos/apollo/10252023_blue_route/"

    # VIDEO
    showVid = False
    
    # FILE CUTOFF
    max_files_to_process = 1
    early_break = False
    
    ### VAR INIT ###

    # IMPORT FILE CHECK
    if direct.endswith("/"):
        pass
    else:
        direct = direct + "/"
        
    files = sorted(os.listdir(direct))

    
    # LIST FILES IN ORDER
    
    
    # JSON INIT
    json_export = GetMetadataToJson(export_dir, time_set=file_set)
    
    # COUNTERS
    file_count = 0
    frame_count = 0
    
    # ARRAYS
    loc_data_to_metadata = {}
    

    ### MAIN CODE ###
    
    for file in files:

        # Get the file
        filename = os.path.join(direct,file)
        print(filename)
        
        # Init the metadata from the desired topics
        localization_data = GetLocalizationData()
        chassis_data = GetChassisData()
        # print(localization_data.localization_data)

        
        if filename.endswith('.json'):
            print("FOUND METADATA IN: ", filename)
            j_file = open(filename)
            metadata = json.load(j_file)
            json_export.createHeader(metadata)
            continue
        
        else:

            message, reader, pbfactory = initReader(filename)
            
            # print(message)
            # print(type(message))
            
            # Get meta data into arrays
            while reader.ReadMessage(message):
                
                message_type = reader.GetMessageType(message.channel_name)
                msg = pbfactory.GenerateMessageByType(message_type)
                msg.ParseFromString(message.content)
                
                if(message.channel_name == localization_topic): 
                    
                    locdata = MessageToJson(msg)
                    locdata = json.loads(locdata)
                    
                    localization_data.parseData(locdata)
                    
                elif(message.channel_name == chassis_topic):
                    
                    chasdata = MessageToJson(msg)
                    chasdata = json.loads(chasdata)
                    
                    chassis_data.parseData(chasdata)
            
            # print(localization_data.localization_data[:][:][0])       
            # print(chassis_data.chassis_data[0][:])
                
            # print(chassis_data.chassis_data)
                    
            # print(len(localization_data.localization_data))
            # time.sleep(100)

            message, reader, pbfactory = initReader(filename)
            
            # Video Maker...
            while reader.ReadMessage(message):
                
                
                message_type = reader.GetMessageType(message.channel_name)
                msg = pbfactory.GenerateMessageByType(message_type)
                msg.ParseFromString(message.content)
                
                if(message.channel_name == image_handler.camera_topic):
                    
                    imgdata = MessageToJson(msg)
                    imgdata = json.loads(imgdata)
                    
                    # Get the timestamp of the frame
                    img_ts = (imgdata['header']['timestampSec'])
                    
                    
                    # Get the localization data with the closest matching timestamp to the frame.
                    # Further metadata will go here...
                    loc_data_to_metadata = json_export.getMatchedLocalizationMetaData(img_ts, localization_data.localization_data)
                    chas_data_to_metadata = json_export.getMatchedChassisMetaData(img_ts, chassis_data.chassis_data)
                    
                    # Append data to a frame
                    frame = {
                        'localization': loc_data_to_metadata,
                        'chassis': chas_data_to_metadata
                    }
                    # Append to the json variable
                    json_export.frames.append(frame)
                    
                    # print(json_export.getMatchedLocalizationMetaData(img_ts, localization_data.localization_data))
                    # print(loc_data_to_metadata[frame_count])

                    image_handler.image = imgdata['data']
                    image_ts = image_handler.stringToImage()
                    image_handler.toRGB()
                    image_handler.add_frame()

                    if showVid:
                        
                        cv2.imshow(message.channel_name, image_handler.image)
                        cv2.waitKey(1)
                        
                    frame_count += 1


            # Break Condition
            file_count += 1
            
            if early_break:
                
                if file_count == max_files_to_process:
                    
                    break
            
    image_handler.export_video()
    json_export.export()
    
    

            # print("Message Count %d" % count)
