import pymongo
import numpy as np
# import matplotlib
# matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import csv
import time
import numpy as np
import json
import lib.GetDisengagmentVideoData as GDVD
import lib.GetDisengagmentLocalizationData as GDLD
# import ChassisSearch as CS
# import GetDisengagmentLidarData as GDLiD

### OPTIONS ###

# Set how much time in seconds before and after the autonomous driving disengament
dt = 5
    
### GET MONGO DATA ###
### REPLACE WITH DESIRED MONGODB INFO ###
myclient = pymongo.MongoClient("mongodb://localhost:27017")
mydb = myclient["cyber19"]
db_data = mydb["cyber19"]
db_metadata = mydb["metadata"]
        
class ChassisSearch:
    
    def __init__(self):
        
        ### VAR INIT ###
        self.auto_times = []
        self.query = {'topic': '/apollo/canbus/chassis'}
        self.chassis_data = []
        
        self.drivestate_data = []
        
    def mongodbChassisSearch(self):
        
        print(f"Downloading chassis data {self.query}...")
        
        if db_data.find_one(self.query) is not None:
            
            cursor = db_data.find(self.query)
            
            for data in cursor:
                
                timestamp = float(data['header']['timestampSec'])
                drivestate = data['drivingMode']
                speed = float(data['speedMps'])
                steer_rate = float(data['steeringRate'])
                steeringPercentage = float(data['steeringPercentage'])
                throttlePercentage = float(data['throttlePercentage'])
                brakePercentage = float(data['brakePercentage'])
                
                self.chassis_data.append((timestamp, drivestate, speed, steer_rate, steeringPercentage, throttlePercentage, brakePercentage))

        self.chassis_data = sorted(self.chassis_data, key= lambda x: x[0])
            
        print('Chassis data donwloaded from MongoDB.')
        
        return self.chassis_data
        
    
    def disengagmentSearch(self):
        
        ### how this works ###
        # GOAL: GET START AND END TIMES FOR AUTONOMOUS DRIVING!
        # For each row in the sorted chassis data, it checks the drive state. 
        # If the drivestate is COMPLETE_AUTO_DRIVE, it checks to see if the is_auto is False.
            # If false, it turns the auto state to true.
            # Then, it sets the auto_time_start equal to the timestamp. This gives the starting point for the autonomous driving and endpoint for manual driving.
        # IF is_auto IS TRUE, IT SIMPLY SKIPS THE ROW! 
        # If the drivestate is COMPLETE_MANUAL, it checks to see if the is_auto is True
            # If is_auto is True, it turns the auto state to false.
            # Then, it sets the auto_time_end equal to the timestamp. This gives the ending point for the autonomous driving and the start point for manual driving.
        # The goal is to get the start and end times for when the van is in autonomous drive mode.
        
        print('Searching for disengagments...')
        
        # Initializes the drive state
        is_auto = False
                
        for row in self.chassis_data:
            
            timestamp, drivestate, speed, steer_rate, steeringPercentage, throttlePercentage, brakePercentage = row
                
            if drivestate == 'COMPLETE_AUTO_DRIVE' and is_auto is False:
                
                is_auto = True
                auto_time_start = timestamp
                
            elif drivestate == 'COMPLETE_MANUAL' and is_auto is True or drivestate == 'EMERGENCY_MODE' and is_auto is True:
                
                is_auto = False
                auto_time_end = timestamp
                self.auto_times.append((auto_time_start, auto_time_end))

            # self.drivestate_data.append([timestamp, drivestate, speed, steer_rate, steeringPercentage, throttlePercentage, brakePercentage, is_auto])
            

    
        
            
    def csvEmModeCheckTimesExport(self):
        
        filename = str(round(time.time())) + '_emMode_check.csv'
        # Open the CSV file in write mode
        with open(filename, 'w', newline='') as csvfile:
            
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header
            header = ["timestamp", "drivestate", "speed", "steer_rate", "steeringPercentage", "throttlePercentage", "brakePercentage", "is_auto"]
            csv_writer.writerow(header)

            # Write the data
            csv_writer.writerows(self.drivestate_data)
            
            
            
        return self.auto_times
        
    def csvAutoTimesExport(self):
        
        filename = str(round(time.time())) + '_autotimes_check.csv'
        
        # Open the CSV file in write mode
        with open(filename, 'w', newline='') as csvfile:
            
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header
            header = ["START", "END"]
            csv_writer.writerow(header)

            # Write the data
            csv_writer.writerows(self.auto_times)

        print(f"Auto to Manual timestamp data exported to {filename}")


    def csvChassisExport(self):
        
        filename = str(round(time.time())) + '_chassis_check.csv'
        
        # Open the CSV file in write mode
        with open(filename, 'w', newline='') as csvfile:
            
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header
            header = ["Timestamp", "DriveState", "Speed", "SteerRate", "SteeringPercentage", "ThrottlePercentage", "BrakePercentage"]
            csv_writer.writerow(header)

            # Write the data
            csv_writer.writerows(self.chassis_data)

        print(f"Chassis topic data exported to {filename}")
        
    
    
    def jsonAutoTimesExport(self):
        
        json_export_filename = str(self.id) + "_.json"
        
        self.auto_start = self.auto_times[0][:]
        self.auto_end = self.auto_times[1][:]
        
        json_export = {
            '_id': self.id,
            'filename': self.filename,
            'foldername': self.foldername,
            'startTime': self.startTime,
            'endTime': self.endTime,
            'msgnum': self.msgnum,
            'size': self.size,
            'topics': self.topics,
            'type': self.type,
            'vehicleID': self.vehicleID,
            'experimentID': self.experimentID,
            'other': self.other,
            'auto_times': self.auto_times,
            'start_auto': self.auto_start,
            'end_auto': self.auto_end
        }
        
        with open(json_export_filename, 'w') as json_file:
            json.dump(json_export, json_file, default=str, indent=4)
            
        print(f"AutoTimes exported to json: {json_export_filename}")
        
    
    def getMetaData(self, db_metadata):
        
        print('Getting meta data...')

        cursor = db_metadata.find()
        idx = 0
        
        # In the event that there are multiple metadata tables uploaded, this just grabs the first. 
        # (There should be only one anyways...?)
        data = cursor[0]

        self.id = str(data['_id'])
        self.filename = str(data['filename'])
        self.foldername = str(data['foldername'])
        self.startTime = str(data['startTime'])
        self.endTime = str(data['endTime'])
        self.msgnum = str(data['msgnum'])
        self.size = str(data['size'])
        self.topics = str(data['topics'])
        self.type = str(data['type'])
        self.vehicleID = str(data['vehicleID'])
        self.experimentID = str(data['experimentID'])
        self.other = str(data['other'])
        
        print('Metadata obtained!')
        
        metadata_base_json = {
            '_id': self.id,
            'filename': self.filename,
            'foldername': self.foldername,
            'startTime': self.startTime,
            'endTime': self.endTime,
            'msgnum': self.msgnum,
            'size': self.size,
            'topics': self.topics,
            'type': self.type,
            'vehicleID': self.vehicleID,
            'experimentID': self.experimentID,
            'other': self.other,
            'auto_times': self.auto_times
        }
        
        return metadata_base_json

class GetDisengagmentData():
    
    def __init__(self, auto_times, dt):
                
        self.auto_times = auto_times
        self.dt = dt
        
        self.fps = 20
        self.dims = (1360,768)
        self.video_base_name = str(round(time.time())) + "_cyber19_front_6mm_compressed_"
        
        self.best_pos_data = []
        self.localization_data = []
        self.image_data = []
        
        self.grabbed_best_pos_data = []
        self.grabbed_localization_data = []
        self.grabbed_image_data = []
        
        self.autonomous_localization_data = []
        
        self.best_pos_query = {'topic': '/apollo/sensor/gnss/best_pose'}
        self.localization_query = {'topic': '/apollo/localization/pose'}
                
        # Best Pose Data
        # self.getBestPoseData()
        # self.getBestPoseDisengagment()
        
        # Localization Data
        # self.getLocalizationData()
        # self.getLocalizationDisengagment()

        
    def getBestPoseData(self):
        
        print(f"Getting {self.best_pos_query} data")
        
        if db_data.find_one(self.best_pos_query) is not None:
            
            cursor = db_data.find(self.best_pos_query)
            
            for data in cursor:
                
                timestamp = float(data['header']['timestampSec'])
                latitude = float(data['latitude'])
                longitude = float(data['longitude'])
                latitudeStdDev = float(data['latitudeStdDev'])
                longitudeStdDev = float(data['longitudeStdDev'])
                heightStdDev = float(data['heightStdDev'])
                galileoBeidouUsedMask = data['galileoBeidouUsedMask']
                solutionAge = data['solutionAge']
                extendedSolutionStatus = data['extendedSolutionStatus']
                solStatus = data['solStatus']
                heightMsl = data['heightMsl']
                baseStationId = data['baseStationId']
                numSatsTracked = data['numSatsTracked']
                numSatsInSolution = data['numSatsInSolution']
                solType = data['solType']
                datumId = data['datumId']
                numSatsL1 = data['numSatsL1']
                differentialAge = data['differentialAge']
                
                self.best_pos_data.append((
                    timestamp,
                    latitude,
                    longitude,
                    latitudeStdDev,
                    longitudeStdDev,
                    heightStdDev,
                    galileoBeidouUsedMask,
                    solutionAge,
                    extendedSolutionStatus,
                    solStatus,
                    heightMsl,
                    baseStationId,
                    numSatsTracked,
                    numSatsInSolution,
                    solType,
                    datumId,
                    numSatsL1,
                    differentialAge
                ))
                
        self.best_pos_data = sorted(self.best_pos_data, key= lambda x: x[0])
        
        # DEBUG csv export 
        # self.csvBestPoseExport()
        # print(self.best_pos_data)
        
        print(f"{self.best_pos_query} data pull complete")
        
    def getLocalizationData(self):
        
        print(f"Getting {self.localization_query} data")
        
        if db_data.find_one(self.localization_query) is not None:
            
            cursor = db_data.find(self.localization_query)
            
            for data in cursor: 
                
                timestamp = float(data['header']['timestampSec'])
                position_x = float(data['pose']['position']['x'])
                position_y = float(data['pose']['position']['y'])
                position_z = float(data['pose']['position']['z'])
                self.localization_data.append((
                    timestamp,
                    position_x,
                    position_y,
                    position_z
                )) 
                
            self.localization_data = sorted(self.localization_data, key = lambda x: x[0])
            
        print(f"{self.localization_query} data pull complete")
        
    def getBestPoseDisengagment(self):
        
        instance_value = 0

        for row in self.auto_times:
            
            # print(self.best_pos_data[0][0])
            # print(type(self.best_pos_data[0][0])) 
                  
            start_time, end_time = row

            end_time_start = float(end_time) - self.dt
            end_time_end = float(end_time) + self.dt
            
            start_idx_to_grab = min(range(len(self.best_pos_data)),
                            key=lambda i: abs(float(self.best_pos_data[i][0]) - float(end_time_start)))
            
            end_idx_to_grab = min(range(len(self.best_pos_data)),
                            key=lambda i: abs(float(self.best_pos_data[i][0]) - float(end_time_end)))

            # print(start_idx_to_grab, end_idx_to_grab)
            
            for idx in range(start_idx_to_grab, end_idx_to_grab):
                
                self.grabbed_best_pos_data.append((
                    instance_value,
                    self.best_pos_data[idx]
                ))
                
            instance_value += 1
            
        # print(self.grabbed_best_pos_data)
        
    def getLocalizationDisengagment(self):
        
        instance_value = 0
        
        for row in self.auto_times:
            
            start_time, end_time = row

            end_time_start = float(end_time) - self.dt
            end_time_end   = float(end_time) + self.dt
            
            start_idx_to_grab = min(range(len(self.localization_data)),
                            key=lambda i: abs(float(self.localization_data[i][0]) - float(end_time_start)))
            
            end_idx_to_grab = min(range(len(self.localization_data)),
                            key=lambda i: abs(float(self.localization_data[i][0]) - float(end_time_end)))
            
            start_idx_to_grab_auto = min(range(len(self.localization_data)),
                            key=lambda i: abs(float(self.localization_data[i][0]) - float(start_time)))
            
            end_idx_to_grab_auto = min(range(len(self.localization_data)),
                            key=lambda i: abs(float(self.localization_data[i][0]) - float(end_time)))
            
            # print(start_idx_to_grab_auto, end_idx_to_grab_auto)
            
            for idx in range(start_idx_to_grab, end_idx_to_grab):
                self.grabbed_localization_data.append((
                    instance_value,
                    self.localization_data[idx]
                ))
                
            for jdx in range(start_idx_to_grab_auto, end_idx_to_grab_auto):
                self.autonomous_localization_data.append((
                    instance_value,
                    self.localization_data[jdx]
                ))
                
            instance_value += 1

    def csvBestPoseExport(self):

        bestpos_csv_file = str(round(time.time())) +  '_bestpos.csv'

        with open(bestpos_csv_file, 'w', newline='') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header
            header = [
                "Timestamp", "Latitude", "Longitude", "LatitudeStdDev", "LongitudeStdDev", "HeightStdDev",
                "GalileoBeidouUsedMask", "SolutionAge", "ExtendedSolutionStatus", "SolStatus",
                "HeightMsl", "BaseStationId", "NumSatsTracked", "NumSatsInSolution", "SolType",
                "DatumId", "NumSatsL1", "DifferentialAge" 
            ]
            csv_writer.writerow(header)

            # Write the data
            csv_writer.writerows(self.best_pos_data)

        print(f'Data has been exported to {bestpos_csv_file}')
        
    def csvLocalizationExport(self):

        localization_csv_file = str(round(time.time())) +  '_localization.csv'

        with open(localization_csv_file, 'w', newline='') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)

            # Write the header
            header = [
                "Timestamp", "x", "y", "z"
            ]
            csv_writer.writerow(header)

            # Write the data
            csv_writer.writerows(self.best_pos_data)

        print(f'Data has been exported to {localization_csv_file}')

if __name__ == '__main__':
    
    print('Starting search for auto -> manual! :D')
    print('Getting disegagment timestamps')
    
    auto_times_instance = ChassisSearch()
    chassis_data = auto_times_instance.mongodbChassisSearch()
    auto_times = auto_times_instance.disengagmentSearch()
    metadata_base_json = auto_times_instance.getMetaData(db_metadata)
    
    # auto_times_instance = CS()
    # chassis_data = auto_times_instance.mongodbChassisSearch()
    # auto_times = auto_times_instance.disengagmentSearch()
    # metadata_base_json = auto_times_instance.getMetaData(db_metadata)
    
    # auto_times_instance.jsonAutoTimesExport()
    
    print("FOUND ", len(auto_times), "DISENGAGEMENTS")

    print('Pulling data from timestamps')
    
    ### Handling localization queries
    # disengagment_instance = GDLD.GetDisengagmentLocalizationData(auto_times, dt)
    
    # # Using best pos topic
    # # disengagment_instance.getBestPoseData(db_data)
    # # bp_data = disengagment_instance.getBestPoseDisengagment()
    
    # Using localization topic
    # l_all_data = disengagment_instance.getLocalizationData(db_data)
    # l_data_dt_disengagment_point, l_data_auto_times_only = disengagment_instance.getLocalizationDisengagment()
    
    # Using LiDAR topic
    # lidar_instance = GDLiD.GetDisengagmentLidarData(db_data, auto_times, dt)
    # lidar_instance.getLiDARData()
    

    # ### Handling image queries
    # do_images = GDVD.DesengagmentVideoExporter()
    # do_images.getImageData(db_data, auto_times, dt)
    # do_images.exportImageDataWithMetadata(db_data, metadata_base_json, l_all_data, auto_times, dt)
    
    # # Print the extracted data
    # position_x = []
    # position_y = []

    # # color = [[255,0,255]]
    
    # # Getting all the data into a nicer array 
    # for idx in range(len(l_all_data)):
        
    #     position_x.append(l_all_data[idx][1])
    #     position_y.append(l_all_data[idx][2])
    #     # color.append(color[0])
    #     # print(disengagment_instance.localization_data[i])

    
    # # Getting all the disengagment +- dt seconds data into a nicer array 
    # dis_position_x = []
    # dis_position_y = []
    
    # for jdx in range(len(l_data_dt_disengagment_point)):
    #     # print(disengagment_instance.grabbed_localization_data[j][0])
    #     dis_position_x.append(l_data_dt_disengagment_point[jdx][1][1])
    #     dis_position_y.append(l_data_dt_disengagment_point[jdx][1][2])

    # # Getting all the auto driving data into a nicer array 
    # auto_only_position_x = []
    # auto_only_position_y = []
    
    # for kdx in range(len(l_data_auto_times_only)):
        
    #     auto_only_position_x.append(l_data_auto_times_only[kdx][1][1])
    #     auto_only_position_y.append(l_data_auto_times_only[kdx][1][2])

    
    # print(dis_position_x) 
    # print('='*100)
    # print(dis_position_y)

    # fig = plt.figure()
    # plt.scatter(position_x, position_y)
    # ax = fig.add_subplot(111, aspect='equal')
    # ax.scatter(position_x, position_y, c='red', alpha=0.9)
    # ax.scatter(dis_position_x, dis_position_y, c='blue', label='Disengaged within: '+str(dt)+'s')
    # ax.set_xlabel('X UTM (m)')
    # ax.set_ylabel('Y UTM (m)')
    # ax.legend()
    # ax.grid(True)
    
    # fig2 = plt.figure()
    # ax2 = fig2.add_subplot(111, aspect='equal')
    # ax2.scatter(position_x, position_y, c='red', alpha=0.9, label='Manual Driving')
    # ax2.scatter(auto_only_position_x, auto_only_position_y, c='blue', label='Autonomous Driving')
    # ax2.set_xlabel('X UTM (m)')
    # ax2.set_ylabel('Y UTM (m)')
    # ax2.legend()
    # ax2.grid(True)
    
    # plt.show()


