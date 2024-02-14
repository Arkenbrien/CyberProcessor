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


if __name__ == "__main__":
    chassis_topic = "/apollo/canbus/chassis"
    comment_topic = "/apollo/drive_event"

    direct = "/media/travis/moleski2/cyber_bags/TRC"

        # IMPORT FILE CHECK
    if direct.endswith("/"):
        pass
    else:
        direct = direct + "/"
    files = sorted(os.listdir(direct))

    for file in files:
        filename = os.path.join(direct,file)
        print(filename)

        message, reader, pbfactory = initReader(filename)

        # Get meta data into arrays
        while reader.ReadMessage(message):
            
            # print(message)
            message_type = reader.GetMessageType(message.channel_name)

            if(message.channel_name == comment_topic):
                print(message_type)
                msg = pbfactory.GenerateMessageByType(message_type)
                msg.ParseFromString(message.content)


                json =  MessageToJson(msg)
                # print(json)

