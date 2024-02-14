#!/usr/bin/env python

# ****************************************************************************
# Travis Moleski, Rhett Huston
# Updated 11/01/2023
# ****************************************************************************

from cyber_py import cyber
from modules.drivers.proto.sensor_image_pb2 import CompressedImage
from traffic_light_pb2 import TrafficLightDetection, TrafficLightDebug, TrafficLight
import time
import numpy as np
import cv2

class traffic_img_listener:
    
    def __init__(self):
        
        self.camera_topic_25mm      = "/apollo/sensor/camera/front_25mm/image/compressed"
        self.camera_topic_06mm      = "/apollo/sensor/camera/front_6mm/image/compressed"
        self.traffic_light_topic    = "/apollo/perception/traffic_light"
        self.is_first_frame         = True

    def image_callback_6mm(self, msg_camera):
        
        decoded_image = cv2.imdecode(np.frombuffer(msg_camera.data, np.uint8), cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
        self.image_6mm = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR) 
        self.image_6mm_ts = msg_camera.header.timestamp_sec
        
        if self.is_first_frame == True:
            
            self.init_ts = msg_camera.header.timestamp_sec
            self.is_first_frame = False

    def image_callback_25mm(self, msg_camera):
        
        decoded_image = cv2.imdecode(np.frombuffer(msg_camera.data, np.uint8), cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
        self.image_25mm = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        self.image_25mm_ts = msg_camera.header.timestamp_sec
        
        # print(msg_camera.header)
        if self.is_first_frame == True:
            
            self.init_ts = msg_camera.header.timestamp_sec
            self.is_first_frame = False
        
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
        
        cv2.rectangle(img,(roi.x, roi.y),(roi.x+roi.width, roi.y+roi.width),bColor, 5)
    
    def box_printer(self, roi, bColor):
        
        for b in roi:
            cv2.rectangle(img,(b.x, b.y),(b.x+b.width, b.y+b.width), bColor, 2)
            
    def debug_box_printer(self, roi, bColor):
        
        for b in roi:
            cv2.rectangle(img,(b.x, b.y),(b.x+b.width, b.y+b.width),bColor, 2)
            if hasattr(b, 'selected') and b.selected==True:
                cv2.rectangle(img,(b.x, b.y),(b.x+b.width, b.y+b.width),(255,255,255), 2)
                
    def text_handler(self, cString, dString, color):
        
        corg = (50, 50) 
        dorg = (50, 90) 
        font = cv2.FONT_HERSHEY_SIMPLEX 
        fontScale = 1
        thickness = 2     
        cv2.putText(img, cString, corg, font, fontScale, color, thickness, cv2.LINE_AA) 
        cv2.putText(img, dString, dorg, font, fontScale, color, thickness, cv2.LINE_AA)
        
class cv2_video_writer:
    
    def __init__(self, name, init_ts):
        
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.output_name = name + ".avi"
        self.video = cv2.VideoWriter(self.output_name, self.fourcc, 120, (1360,768))
        self.append_ready = True
        self.init_ts = init_ts
        
        self.first_frame = True
        self.exported = False
        
    def add_frame(self, img, ts):
        
        self.ts = ts
        
        if self.first_frame == True:
            self.video.write(img)
            self.first_frame = False
            
        elif self.ts!= self.init_ts and self.first_frame == False and self.append_ready == True:
            self.video.write(img)
            
        elif self.ts == self.init_ts and self.first_frame == False:

            self.append_ready = False
            
            if self.exported == False:
                self.video.write(img)
                self.export_video()
                self.exported = True
        
    def export_video(self):
        self.video.release()
        print('VIDEO RELEASED') 
        
if __name__ == '__main__':
    
    traffic_light_handler = traffic_img_listener()
    
    cyber.init()
        
    tl_node = cyber.Node("listener")

    time.sleep(1)

    tl_node.create_reader(traffic_light_handler.traffic_light_topic, TrafficLightDetection, traffic_light_handler.tl_info_callback)
    tl_node.create_reader(traffic_light_handler.camera_topic_06mm, CompressedImage, traffic_light_handler.image_callback_6mm)
    tl_node.create_reader(traffic_light_handler.camera_topic_25mm, CompressedImage, traffic_light_handler.image_callback_25mm)
    
    time.sleep(1)
    
    # out_video = cv2_video_writer(str(time.time()), traffic_light_handler.image_6mm_ts)

    while 1:
        
        ts = traffic_light_handler.image_6mm_ts
        
        if traffic_light_handler.tl_info.contain_lights:
            # print(traffic_light_handler.tl_info)
            
            if traffic_light_handler.tl_info.camera_id == 2:
               img = traffic_light_handler.image_6mm
               
            elif traffic_light_handler.tl_info.camera_id == 0:
               img = traffic_light_handler.image_25mm  
                            
            cString, color = traffic_light_handler.color_check(traffic_light_handler.tl_info.traffic_light[0].color)
                        
            traffic_light_handler.cropbox_printer(traffic_light_handler.tl_info.traffic_light_debug.cropbox, color)
            traffic_light_handler.box_printer(traffic_light_handler.tl_info.traffic_light_debug.crop_roi, color)
            traffic_light_handler.box_printer(traffic_light_handler.tl_info.traffic_light_debug.projected_roi, color)
            traffic_light_handler.box_printer(traffic_light_handler.tl_info.traffic_light_debug.rectified_roi, color)
            traffic_light_handler.box_printer(traffic_light_handler.tl_info.traffic_light_debug.debug_roi, color)
            traffic_light_handler.debug_box_printer(traffic_light_handler.tl_info.traffic_light_debug.box, color)
            
            cString = cString+": "+str(round(traffic_light_handler.tl_info.traffic_light[0].confidence,4))
            dString = "distance to stop: "+str(round(traffic_light_handler.tl_info.traffic_light_debug.distance_to_stop_line,4))
            
            traffic_light_handler.text_handler(cString, dString, color)
            
            img = cv2.resize(img, (1360,768))
            
            # out_video.add_frame(img, ts)
            
            cv2.imshow('Image', img)
            cv2.waitKey(1)
            
        else:
            
            img = traffic_light_handler.img_6mm
            # out_video.add_frame(img, traffic_light_handler.image_6mm_ts)
            cv2.imshow('Image', img)
            cv2.waitKey(1)

    cyber.shutdown()