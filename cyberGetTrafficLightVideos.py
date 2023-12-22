


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

        self.export_folder          = "./videos/traffic_light"
        self.export_dimensions      = (1920,1080)

        self.image = None
        # self.compression = 0.9
        self.addMeta = True

        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videWriter = cv2.VideoWriter(self.export_folder+"/exp34.avi", self.fourcc , 20.0, self.export_dimensions)


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

                
    def color_check(self, colorState):
        if colorState == 'GREEN':
            color = (0,255,0)
            cString = "green"
        elif colorState == 'RED':
            color = (0,0,255)
            cString = "red"
        elif colorState == 'YELLOW':
            color = (0,255,255)
            cString = "yellow"
        else:
            color = (0,0,0)
            cString = "unknown"
        return cString, color

    
    def tl_info_callback(self, tl_msg):
        print(tl_msg)
        self.tl_info = tl_msg
        
    def cropbox_printer(self, roi, bColor):
        
        cv2.rectangle(self.image,(roi['x'], roi['y']),(roi['x']+roi['width'], roi['y']+roi['width']),bColor, 5)
    
    def box_printer(self, roi, bColor):
        for b in roi:
            cv2.rectangle(self.image,(b['x'], b['y']),(b['x']+b['width'], b['y']+b['width']), bColor, 2)
            
    def debug_box_printer(self, roi, bColor):
        
        for b in roi:
            cv2.rectangle(self.image,(b['x'], b['y']),(b['x']+b['width'], b['y']+b['width']),bColor, 2)
            if hasattr(b, 'selected') and b.selected==True:
                cv2.rectangle(self.image,(b['x'], b['y']),(b['x']+b['width'], b['y']+b['width']),(255,255,255), 2)
                
    def text_handler(self, cString, dString, color):
        
        corg = (50, 50) 
        dorg = (50, 90) 
        font = cv2.FONT_HERSHEY_SIMPLEX 
        fontScale = 1
        thickness = 2     
        cv2.putText(self.image, cString, corg, font, fontScale, color, thickness, cv2.LINE_AA) 
        cv2.putText(self.image, dString, dorg, font, fontScale, color, thickness, cv2.LINE_AA)

###########################################################
if __name__ == "__main__":

    image_handler6mm  = VideoExporter(camera_topic="/apollo/sensor/camera/front_6mm/image/compressed")
    image_handler25mm = VideoExporter(camera_topic="/apollo/sensor/camera/front_25mm/image/compressed")
    traffiLightTopic =  "/apollo/perception/traffic_light"


    file_set = 1698251665
    direct = "/media/travis/moleski1/cyber_bags/" + str(file_set) + '/'

    showVid = True
    # file_count = 0
    files = os.listdir(direct)
    for filename in tqdm(os.listdir(direct)):
        print(filename)

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
                        if cam_id == "CAMERA_FRONT_SHORT":
                            image_handler = image_handler6mm
                        else:
                            image_handler = image_handler25mm

                        cString, color = image_handler.color_check(jdataTL['trafficLight'][0]['color'])

                        

                        # image_handler.debug_box_printer(image_handler.tl_info.traffic_light_debug.box, color)
                        
                        cString = cString+": "+str(round(jdataTL['trafficLight'][0]['confidence'],4))
                        dString = "distance to stop: "+str(round(jdataTL['trafficLightDebug']['distanceToStopLine'],4))
                        
                        image_handler.text_handler(cString, dString, color)


                try:
                    if(message.channel_name == image_handler.camera_topic) and  "containLights" in jdataTL:
                        jdata = MessageToJson(msg)
                        jdata = json.loads(jdata)

                        image_handler.image = jdata['data']
                        image_handler.stringToImage()
                        image_handler.toRGB()

                        image_handler.text_handler(cString, dString, color)

                        image_handler.cropbox_printer(jdataTL['trafficLightDebug']['cropbox'], color)
                        image_handler.box_printer(jdataTL['trafficLightDebug']['cropRoi'], color)

                        image_handler.box_printer(jdataTL['trafficLightDebug']['projectedRoi'], color)
                        image_handler.box_printer(jdataTL['trafficLightDebug']['rectifiedRoi'], color)
                        image_handler.box_printer(jdataTL['trafficLightDebug']['debugRoi'], color)
                        image_handler.debug_box_printer(jdataTL['trafficLightDebug']['box'], color)

                        image_handler.add_frame()

 

                        if showVid:
                            cv2.imshow("Traffic Light", image_handler.image)
                            cv2.waitKey(0)
                except:
                    continue

                # count += 1

            # file_count += 1
            # if file_count == 2:
            #     break
            
    # image_handler.export_video()
    # print("Message Count %d" % count)