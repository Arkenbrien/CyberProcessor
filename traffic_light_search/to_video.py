###########################################################
# Rhett Huston
# Last updated: 11/01/2023
###########################################################

# import packages
import sys, time, os
from importlib import import_module
from cyber_py import cyber
from cyber_py import record
from modules.drivers.proto.sensor_image_pb2 import CompressedImage
from traffic_light_pb2 import TrafficLightDetection, TrafficLightDebug, TrafficLight
from chassis_pb2 import Chassis
import numpy as np
import cv2

os.system('clear')

###########################################################

class VideoExporter:
    
    def __init__(self):
        
        # Topics
        self.camera_topic_25mm      = "/apollo/sensor/camera/front_25mm/image/compressed"
        self.camera_topic_06mm      = "/apollo/sensor/camera/front_6mm/image/compressed"
        
        # Record Locations
        # self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/cyber_bag_test"
        self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/10252023_blue_route"
        # self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/red_route"
        
        # This is an issue. :(
        if self.record_folder.endswith("/"):
            pass
        else:
            self.record_folder = self.record_folder + "/"

        # Sorts the files within the record folder
        self.record_files = sorted(os.listdir(self.record_folder))
        
        # Specify the range of desired bags. Comment out to have all bags examined
        # self.record_files = self.record_files[170:]

        # Export Options
        # self.export_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/10252023_blue_route/"
        self.export_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/video_export/"
        self.export_dimensions      = (1360,768)
        
        try:
            if not os.path.exists(self.export_folder):
                os.makedirs(self.export_folder)
                print('Export Folder Created: ', self.export_folder)
            else:
                print('Export Folder Already Exists: ', self.export_folder)
        except OSError:
            print('OSError: unable to create export_folder. Using default folder location: ', os.path.dirname(os.path.abspath(__file__)))
            self.export_folder = os.path.dirname(os.path.abspath(__file__))
            
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.output_name_06 = str(round(time.time())) + "_06.avi"
        self.output_name_25 = str(round(time.time())) + "_25.avi"
        
        self.video_06 = cv2.VideoWriter(self.output_name_06, self.fourcc, 20, (1360,768))
        self.video_25 = cv2.VideoWriter(self.output_name_25, self.fourcc, 20, (1360,768))
        
        self.show_video = False


        # Begin parsing data in files
        print("=" *80)
        print('--------- Parsing data ---------')

        for rfile in self.record_files:
            
            print("=" *80)
            print("parsing record file: %s" % rfile)

            # Reads the file
            freader = record.RecordReader(self.record_folder+'/'+rfile)
            
            # Reads each channel. If the channel name is one of the camera topics or the traffic light topic,
            # data is pulled and appended to 
            for channelname, msg, datatype, timestamp in freader.read_messages():
                
                if channelname == self.camera_topic_06mm:
                    
                    msg_camera = CompressedImage()
                    msg_camera.ParseFromString(str(msg))
                    
                    decoded_image = cv2.imdecode(np.frombuffer(msg_camera.data, np.uint8), cv2.IMREAD_COLOR)
                    rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
                    image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
                    self.add_frame_06(image)
                    

                elif channelname == self.camera_topic_25mm:
                    
                    msg_camera = CompressedImage()
                    msg_camera.ParseFromString(str(msg))
                    decoded_image = cv2.imdecode(np.frombuffer(msg_camera.data, np.uint8), cv2.IMREAD_COLOR)
                    rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
                    image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
                    self.add_frame_25(image)
                    
                    # print(msg_chassis.header.timestamp_sec)
                    
                    # time.sleep(10)
                    
                else:
                    
                    continue
            
            self.export_video
    
    def add_frame_06(self, img):
        
        img = cv2.resize(img, (1360,768))
        self.video_06.write(img)
        if self.show_video:
            print('frame added')
            cv2.imshow('Image', img)
            cv2.waitKey(50)
            
    def add_frame_25(self, img):
        
        img = cv2.resize(img, (1360,768))
        self.video_25.write(img)
        if self.show_video:
            print('frame added')
            cv2.imshow('Image', img)
            cv2.waitKey(50)
        
    def export_video(self):
        
        self.video_06.release()
        self.video_25.release()
        print('')
        print('VIDEO RELEASED') 
        print('')


###########################################################

if __name__ == '__main__':
    
    cyber.init()
    
    VideoExporter()

    cyber.shutdown()
