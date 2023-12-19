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

class sequential_tl_cyberbag_image_exporter:
    
    def __init__(self):
        
        # Topics
        self.camera_topic_25mm      = "/apollo/sensor/camera/front_25mm/image/compressed"
        self.camera_topic_06mm      = "/apollo/sensor/camera/front_6mm/image/compressed"
        self.traffic_light_topic    = "/apollo/perception/traffic_light"
        self.chassis_topic          = "/apollo/canbus/chassis"
        
        # Record Locations
        # self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/cyber_bag_test"
        self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/10252023_blue_route"
        # self.record_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/red_route"

        # Sorts the files within the record folder
        self.record_files = sorted(os.listdir(self.record_folder))
        
        # Specify the range of desired bags. Comment out to have all bags examined
        # self.record_files = self.record_files[170:]

        # Export Options
        # self.export_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/10252023_blue_route/"
        self.export_folder          = "/media/autobuntu/chonk/chonk/git_repos/apollo/traffic_light_multi_cyberbag_export/"
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
        
        # Init the video logic - If the field changes from True -> False, the video will be exported.
        # Conversely, if the field changes from False -> true, a new video instance will be created using the
        # self.to_video function. The reason why this exists is that the field may be true/false across multiple
        # cyberbags, and this value will track persistance across the cyberbags. A video is also created at the
        # end of all the cyberbags if one is being appended too. 
        self.ready_to_append        = False
        self.last_file              = False
        self.old_tl_id              = int(0000)

        # Begin parsing data in files
        print("=" *80)
        print('--------- Parsing data ---------')

        for rfile in self.record_files:
            
            print("=" *80)
            print("parsing record file: %s" % rfile)
            
            self.file_name = rfile
            
            # Probably a more elegant way to do this but this initiates the temporary data bins for each message
            # This is re-initiated each loop so that each file gets examined individually.
            data_dump_06mm = {}
            data_dump_25mm = {}
            data_dump_tl = {}
            data_dump_chassis = {}
            
            idx_06 = 0
            idx_25 = 0
            idx_tl = 0
            idx_ch = 0

            # Reads the file
            freader = record.RecordReader(self.record_folder+'/'+rfile)
            
            # Reads each channel. If the channel name is one of the camera topics or the traffic light topic,
            # data is pulled and appended to 
            for channelname, msg, datatype, timestamp in freader.read_messages():
                
                if channelname == self.camera_topic_06mm:
                    
                    msg_camera = CompressedImage()
                    msg_camera.ParseFromString(str(msg))
                    data_dump_06mm[idx_06] = msg_camera
                    idx_06 += 1

                elif channelname == self.camera_topic_25mm:
                    
                    msg_camera = CompressedImage()
                    msg_camera.ParseFromString(str(msg))
                    data_dump_25mm[idx_25] = msg_camera
                    idx_25 += 1

                elif channelname == self.traffic_light_topic:
                    
                    msg_traffic_light = TrafficLightDetection()
                    msg_traffic_light.ParseFromString(str(msg))
                    data_dump_tl[idx_tl] = msg_traffic_light
                    idx_tl += 1
                    
                elif channelname == self.chassis_topic:
                    
                    msg_chassis = Chassis()
                    msg_chassis.ParseFromString(str(msg))
                    data_dump_chassis[idx_ch] = msg_chassis
                    idx_ch += 1
                    
                    # print(msg_chassis.header.timestamp_sec)
                    
                    # time.sleep(10)
                    
                else:
                    
                    continue
            
                    
            # Sends the data from the single file to be compiled in a seperate function
            self.message_compiler(data_dump_06mm, data_dump_25mm, data_dump_tl, data_dump_chassis)
            
            # If it's the last file in the folder, it will export any video that may be open at the end of the file.
            if rfile == len(self.record_files)-1:
                self.last_file = True
            
            
    def message_compiler(self, data_06mm, data_25mm, data_tl, data_chassis):

        # For each message in the traffic light array, check to see if it contains lights.
        # If true:
        # 1) Video is created if one has not been created previously (see note on self.ready_to_append) in the __init__ section
        # 2) Determine which camera is being used to detect the light
        # 2.5) Grabs the drive state text
        # 3) Grab current traffic light topic camera ts as well as the next sequential one
        # 4) Grab all camera frames between the two time stamps 
        # 5) Grab the traffic light text and boxes
        # 6) Create the image and push the rectangles
        
        # If false:
        # Export the video if a video is currently being created
        for msg in data_tl:
            
            # 1) Video is created if one has not been created previously (see note on self.ready_to_append) in the __init__ section
            # OR
            # Export the video if a video is currently being created
            if data_tl[msg].contain_lights is True:
                
                self.new_tl_id = int(data_tl[msg].traffic_light[0].id)
                
                if self.new_tl_id != self.old_tl_id:
                    
                    self.old_tl_id = self.new_tl_id
                
                    file_name = str(self.file_name) + '_' + str(self.new_tl_id)
                    
                    self.to_video = cv2_video_writer(file_name, self.export_dimensions, self.export_folder)
                    print('NEW VIDEO CREATED WITH NAME: ' + file_name)
                    
                elif self.new_tl_id == self.old_tl_id:
                    
                    # print('Continuing video')
                    
                    pass

            # Handling the case of a single tl frame not containing lights for some bizzare reason. 
            # Will not handle cross-handle blips where the last frame is false but the first frame in the next file is true
            elif data_tl[msg].contain_lights is False:
                
                try: 
                    if data_tl[msg+2].contain_lights is False and self.ready_to_append is True:
                        self.to_video.export_video
                        self.ready_to_append = False
                        print('VIDEO EXPORTED!')
                except:
                    
                    try:
                        if self.ready_to_append is True:
                            self.to_video.export_video
                            self.ready_to_append = False
                            print('VIDEO EXPORTED!')
                        
                    except:
                        
                        pass

            if data_tl[msg].contain_lights == True:
                
                self.cString, self.color = self.color_check(data_tl[msg].traffic_light[0].color)
                
                # 2) Determine which camera is being used to detect the light
                camera_id = data_tl[msg].camera_id
                tl_ts = round(data_tl[msg].header.camera_timestamp/(10e8),2)
                
                # 2.5) Grabs the drive state text
                self.drive_state_idx = self.get_timestamp(tl_ts, data_chassis)
                self.drive_state = data_chassis[self.drive_state_idx].driving_mode
                self.dsString, self.dsColor = self.get_drive_state(self.drive_state)

                if camera_id == 0:
                    
                    # 3) Grab current traffic light topic camera ts as well as the next sequential one
                    self.camera_idx_start = self.get_timestamp(tl_ts, data_25mm)
                    
                    if msg < len(data_tl)-1:
                        
                        camera_ts_next = round(data_tl[msg+1].header.camera_timestamp/(10e8),2)
                        self.camera_idx_end = self.get_timestamp(camera_ts_next, data_25mm)
                        
                    else:
                        
                        self.camera_idx_end = len(data_25mm)-1
                    
                    # 4) Grab all camera frames between the two time stamps
                    # 5) Grab the traffic light text and boxes
                    # 6) Create the image and push the rectangles
                    self.append_images(self.camera_idx_start, self.camera_idx_end, self.cString, self.color, self.dsString, self.dsColor, data_tl[msg], data_25mm)
                        
                if camera_id == 2:
                    
                    # 3) Grab current traffic light topic camera ts as well as the next sequential one
                    self.camera_idx_start = self.get_timestamp(tl_ts, data_06mm)
                    
                    if msg < len(data_tl)-1:
                        
                        camera_ts_next = round(data_tl[msg+1].header.camera_timestamp/(10e8),2)
                        self.camera_idx_end = self.get_timestamp(camera_ts_next, data_06mm)
                        
                    else:
                        
                        self.camera_idx_end = len(data_06mm)-1
                    
                    # 4) Grab all camera frames between the two time stamps
                    # 5) Grab the traffic light text and boxes
                    # 6) Create the image and push the rectangles
                    self.append_images(self.camera_idx_start, self.camera_idx_end, self.cString, self.color, self.dsString, self.dsColor, data_tl[msg], data_06mm)
                    

    def get_timestamp(self, ts, data):
        
        # Finds the index of the closest matching timestamp with a desired timestamp.
        # In this case, ts is the desired time stamp, and data is the timestamp data
        # that must be matched.
        
        # Var init - 0 in case the ts is the first item in the array and there's
        # some weirdness going on with the ts not matching up
        matched_idx = 0

        for idx in data:
            
            if round(data[idx].header.timestamp_sec,2) == ts:
                
                matched_idx = idx
                break
            
        return matched_idx
    

    def append_images(self, start_idx, end_idx, cString, color, dsString, dsColor, data_tl, data_cam):
        
        # 4) Grab all camera frames between the two time stamps
        # 5) Grab the traffic light text and boxes
        # 6) Create the image and push the rectangles
        
        # print('range to grab: ', range(start_idx, end_idx+1))
        for img_idx in range(start_idx, end_idx+1):

            # Process image data
            self.to_video.decoded_image = cv2.imdecode(np.frombuffer(data_cam[img_idx].data, np.uint8), cv2.IMREAD_COLOR)
            self.to_video.rgb_image = cv2.cvtColor(self.to_video.decoded_image, cv2.COLOR_BGR2RGB)
            self.to_video.image = cv2.cvtColor(self.to_video.rgb_image, cv2.COLOR_RGB2BGR)
            
            # Add boxes
            self.cropbox_printer(data_tl.traffic_light_debug.cropbox, color)
            self.box_printer(data_tl.traffic_light_debug.box, color)
            self.debug_box_printer(data_tl.traffic_light_debug.box, color)
            
            # Determine distance to stoping line and append to string
            dString = "distance to stop: "+str(round(data_tl.traffic_light_debug.distance_to_stop_line,4))
            
            # Create traffic light ID String
            idString = "id: " + str(self.new_tl_id)
            
            self.tl_text_handler(cString, dString, idString, color)
            self.ds_text_handler(dsString, dsColor)
            
            self.to_video.add_frame(self.to_video.image)
            
        if self.last_file:
            self.to_video.export_video
                        
    
    def cropbox_printer(self, roi, bColor):
        
        # Prints the cropbox.
        # Box is colored the same as the predicted light
        
        cv2.rectangle(self.to_video.image,(roi.x, roi.y),(roi.x+roi.width, roi.y+roi.width),bColor, 5)
    
    def box_printer(self, roi, bColor):
        
        # Prints all boxes in the box sub-topic
        # Boxes are colored the same as the predicted light
        
        for b in roi:
            
            cv2.rectangle(self.to_video.image,(b.x, b.y),(b.x+b.width, b.y+b.width), bColor, 2)
            
    def debug_box_printer(self, roi, bColor):
        
        # Boxes are colored the same as the predicted light except in the case if the box is the 
        # 'selected' box. In which case, the box is white.
        for b in roi:
            
            cv2.rectangle(self.to_video.image,(b.x, b.y),(b.x+b.width, b.y+b.width),bColor, 2)
            
            if hasattr(b, 'selected') and b.selected==True:
                
                cv2.rectangle(self.to_video.image,(b.x, b.y),(b.x+b.width, b.y+b.width),(255,255,255), 2)
                
                
    def tl_text_handler(self, cString, dString, idString, color):
        
        # Displays the predicted traffic light color and distance to the traffic light
        
        corg = (50, 50) 
        dorg = (50, 90) 
        idorg = (50, 130)
        font = cv2.FONT_HERSHEY_SIMPLEX 
        fontScale = 1
        thickness = 2     
        cv2.putText(self.to_video.image, cString, corg, font, fontScale, color, thickness, cv2.LINE_AA) 
        cv2.putText(self.to_video.image, dString, dorg, font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(self.to_video.image, idString, idorg, font, fontScale, color, thickness, cv2.LINE_AA)
        
        
    def ds_text_handler(self, dsString, dsColor):
        
        # Prints the drive state - full auto/manual etc
        
        chorg = (50,170)
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        thickness = 2 
        cv2.putText(self.to_video.image, dsString, chorg, font, fontScale, dsColor, thickness, cv2.LINE_AA) 
                
                
    def color_check(self, colorState):
        
        # Generates the texts' & boxes' color based on the traffic light's prediction string
        
        # Var Init
        color = (0,0,0)
        cString = "unknown"
        
        if colorState == 0:
            
            color = (0,0,0)
            cString = "unknown"        
            
        elif colorState == 1:
            
            color = (0,0,255)
            cString = "red"
            
        elif colorState == 2:
            
            color = (0,255,255)
            cString = "yellow"
            
        elif colorState == 3:
            
            color = (0,255,0)
            cString = "green"

        return cString, color
    
    
    def get_drive_state(self, drive_state):
        
        # Gets the string for the drive state
        
        # Var Init
        dsString = "Unknown"
        dsColor = (255, 255, 255)
        
        if drive_state == 0:
            dsString = "COMPLETE_MANUAL"
            dsColor = (255, 0, 0)
            
        elif drive_state == 1:
            dsString = "COMPLETE_AUTO_DRIVE"
            dsColor = (0, 255, 0)
        
        return dsString, dsColor
        
class cv2_video_writer:
    
    # Handles the video formating, adding frames, and exporting
    
    def __init__(self, name, dim, export_folder):
        
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.output_name = export_folder + name + ".avi"
        self.video = cv2.VideoWriter(self.output_name, self.fourcc, 20, dim)
        self.dim = dim
        self.show_video = False

    def add_frame(self, img):
        
        img = cv2.resize(img, self.dim)
        self.video.write(img)
        if self.show_video:
            print('frame added')
            cv2.imshow('Image', img)
            cv2.waitKey(50)
        
    def export_video(self):
        
        self.video.release()
        print('')
        print('VIDEO RELEASED') 
        print('')


###########################################################

if __name__ == '__main__':
    
    cyber.init()
    
    sequential_tl_cyberbag_image_exporter()

    cyber.shutdown()
