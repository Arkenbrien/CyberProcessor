import pymongo
import numpy as np
import matplotlib.pyplot as plt
import csv
import time
import numpy as np
import json
        
class ChassisSearch:
    
    def __init__(self, metadID):

        ### VAR INIT ###
        self.auto_times = []
        self.query = {'groupMetadataID': metadID['groupID'], 'topic': '/apollo/canbus/chassis'}
        self.chassis_data = []
        self.disengagement_times = []
        
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
        
        json_export_filename = self.experimentID + ".json"

        print("EXPORT TIMES:", self.auto_times)
        
        # self.auto_start = self.auto_times[0][:]
        # self.auto_end   = self.auto_times[1][:]

        for time_range in auto_times:
            self.disengagement_times.append(time_range[1])

        json_export = {
            '_id': self.id,
            'filename': self.filename,
            'foldername': self.foldername,
            'endTime': self.endTime,
            'msgnum': self.msgnum,
            'size': self.size,
            'topics': self.topics,
            'type': self.type,
            'vehicleID': self.vehicleID,
            'experimentID': self.experimentID,
            'other': self.other,
            'auto_times': self.auto_times,
            'disengagement_times':self.disengagement_times,
            'disengagement_tolerance':dt
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



if __name__ == '__main__':
    ### OPTIONS ###
    # Set how much time in seconds before and after the autonomous driving disengament
    dt = 5
        
    ### GET MONGO DATA ###
    ### REPLACE WITH DESIRED MONGODB INFO ###
    myclient = pymongo.MongoClient("mongodb://localhost:27017")
    mydb = myclient["cyber_data"]

    db_data = mydb["cyber_van"]
    db_metadata = mydb["cyber_meta"]

    metadID = mydb["cyber_meta"].find_one({'experimentID': 39})

    print(metadID['groupID'])
    
    print('Starting search for auto -> manual! :D')
    print('Getting disegagment timestamps')
    
    auto_times_instance = ChassisSearch(metadID)
    chassis_data = auto_times_instance.mongodbChassisSearch()
    auto_times = auto_times_instance.disengagmentSearch()
    metadata_base_json = auto_times_instance.getMetaData(db_metadata)
    auto_times_instance.jsonAutoTimesExport()
    
    print("FOUND ", len(auto_times), "DISENGAGEMENTS")



