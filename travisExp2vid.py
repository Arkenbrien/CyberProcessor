
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
import utm
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
    
    
    def export(self):
        with open(self.filename, 'a') as json_file:
            json.dump(self.frames, json_file, indent=4)
            json_file.write('\n')
    
    
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

    # direct = "/home/travis/Work/Apollo/apollo5/apollo5.5/apollo-5.5.0/data/bag/trafficlight"

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

                    
                if(message.channel_name == chassis_topic):
                    
                    chasdata = MessageToJson(msg)
                    chasdata = json.loads(chasdata)
                    
                if(message.channel_name == image_handler.camera_topic):

                    
                    imgdata = MessageToJson(msg)
                    imgdata = json.loads(imgdata)
                    
                    # Get the timestamp of the frame
                    img_ts = (imgdata['header']['timestampSec'])

                    try:

                        # Append data to a frame
                        frame = {
                            'localization': locdata,
                            'chassis': chasdata
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

                            lat,lon = utm.to_latlon(locdata['pose']['position']['x'], locdata['pose']['position']['y'], 17, 'S')

                            lat = round(lat,5)
                            lon = round(lon,5)

                            driving_mode = chasdata['drivingMode']
                            speed = round(chasdata['speedMps'] * 2.23694, 2)

                            text = f'Frame: {frame_count}, Lat: {lat}, Lon: {lon}, Driving Mode: {driving_mode}, Speed (mph): {speed}'
                            cv2.putText(image_handler.image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                            cv2.imshow(message.channel_name, image_handler.image)
                            cv2.waitKey(30)
                            
                        frame_count += 1

                    except:
                        continue
        


            # Break Condition
            file_count += 1
            
            if early_break:
                
                if file_count == max_files_to_process:
                    
                    break
            
    image_handler.export_video()
    json_export.export()
    
    

            # print("Message Count %d" % count)
