


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

import json
from tqdm import tqdm
from cybertools.cyberreaderlib import ProtobufFactory, RecordReader, RecordMessage
import base64



###########################################################
class VideoExporter:
    
    def __init__(self, camera_topic):
        
        # Topics
        self.camera_topic    = camera_topic
        self.record_folder          = None

        self.export_folder          = "./outputVideo/"
        self.export_dimensions      = (1920,1080)

        self.image = None
        # self.compression = 0.9
        self.addMeta = True

        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videWriter = cv2.VideoWriter(self.export_folder+"Exp34_6mm.avi", self.fourcc , 20.0, self.export_dimensions)


    # Take in base64 string and return PIL image
    def stringToImage(self):
        self.image = base64.b64decode(self.image)
        self.image = Image.open(io.BytesIO(self.image))

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
if __name__ == "__main__":

    image_handler6mm = VideoExporter(camera_topic="/apollo/sensor/camera/front_6mm/image/compressed")
    image_handler25mm = VideoExporter(camera_topic="/apollo/sensor/camera/front_25mm/image/compressed")

    traffiLightTopic =  "/apollo/perception/traffic_light"

    direct = "/mnt/h/cyber_bags/1698251665/"

    showVid = True
    file_count = 0
    files = os.listdir(direct)
    for filename in tqdm(os.listdir(direct)):
        # print("FILE COUNT:", file_count)

        filename = direct + filename
        if filename.endswith('.json'):
            print("FOUND METADATA IN: ", filename)
            j_file = open(filename)
            metadata = json.load(j_file)
            print(metadata)
            continue
        else:
            unqiue_channel = []
            pbfactory = ProtobufFactory()
            reader = RecordReader(filename)
            for channel in reader.GetChannelList():
                desc = reader.GetProtoDesc(channel)
                pbfactory.RegisterMessage(desc)
                unqiue_channel.append(channel)
                
            message = RecordMessage()
            count = 0
            while reader.ReadMessage(message):
                message_type = reader.GetMessageType(message.channel_name)
                msg = pbfactory.GenerateMessageByType(message_type)
                msg.ParseFromString(message.content)

                if(message.channel_name == traffiLightTopic):
                    jdataTL = MessageToJson(msg)
                    jdataTL = json.loads(jdataTL)


                    if "containLights" in jdataTL:
                        cam_id = jdataTL['cameraId']
                        print("GOT LIGHT...")

                        if cam_id == "CAMERA_FRONT_SHORT":
                            image_handler = image_handler6mm
                        else:
                            image_handler = image_handler25mm

                try:
                    if(message.channel_name == image_handler.camera_topic) and  "containLights" in jdataTL:
                        jdata = MessageToJson(msg)
                        jdata = json.loads(jdata)

                        image_handler.image = jdata['data']
                        image_handler.stringToImage()
                        image_handler.toRGB()
                        image_handler.add_frame()

                        if showVid:
                            cv2.imshow("Traffic Light", image_handler.image)
                            cv2.waitKey(1)
                except:
                    continue
                # count += 1

            # file_count += 1
            # if file_count == 2:
            #     break
            
    # image_handler.export_video()

            # print("Message Count %d" % count)