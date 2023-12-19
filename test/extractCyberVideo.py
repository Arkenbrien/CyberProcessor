import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging
from matplotlib import pyplot as plt
import time
import json
from decimal import Decimal
import os
from pymongo import MongoClient

import pickle

##### CODE INIT #####

# Dynamodb setup
# Create a DynamoDB local client
dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:5000')
# Define the table name
table_name = 'cyber_aws_with_vid' 
# Get the DynamoDB table
table = dynamodb.Table(table_name)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)  # Convert Decimal to string
        return super(DecimalEncoder, self).default(o)  

class DynamoDB_Query:
    def __init__(self, topic, table_name, table):

        self.segment_size = 4
        self.frame_time = 1698251687183398667
        
        # VAR INIT
        last_evaluated_key = None
        json_idx = 0
        queryStartTime = time.time()
        topic_export_string = topic.replace('/','_')

        response = table.query(
            IndexName='TopicIndex',  # Specify the name of the global secondary index
            KeyConditionExpression=Key('topic').eq(topic) ,
            FilterExpression =Attr('time').eq(self.frame_time)
        )
        # MAIN LOOP

        i = 0
        self.response_list = [response]
        while True:
            
            if last_evaluated_key:
                response = table.query(
                    IndexName='TopicIndex',
                    KeyConditionExpression=Key('topic').eq(topic),
                    FilterExpression =Attr('time').eq(self.frame_time),
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = table.query(
                    IndexName='TopicIndex',
                    KeyConditionExpression=Key('topic').eq(topic),
                    FilterExpression =Attr('time').eq(self.frame_time )
                )
            last_evaluated_key = response.get('LastEvaluatedKey')
            self.response_list.append(response)

            if not last_evaluated_key:
                break
            
            print(f"Found... {len(response)} entries for table: {table} in key {last_evaluated_key}")
            i += 1
            print(i)
            
        queryEndTime = time.time() - queryStartTime
        print("QUERY TIME:", queryEndTime)

        print("STITCHING IMAGES...")
        frame_master = []
        for response in self.response_list:
            for frame in response['Items']:
                frame_master.append(frame)

        frame_master = sorted(frame_master,  key=lambda x: (x['time']))
        frame_time = frame_master[0]['time']
        frame = []

        sorted_master = []
        for frame_segment in frame_master:
            if frame_segment['time'] != frame_time:
                frame_time = frame_segment['time']
                print("NEW FRAME")
                frame = []
            else:
                frame.append(frame_segment)
                print("SAME FRAME")
                if len(frame) == self.segment_size:
                    print("GOT FULL FRAME...")
                    frame = sorted(frame, key=lambda x: (x['image_string_idx']))

                    # it = iter(frame)
                    # res_dct = dict(zip(it,it))

                    with open("./pickleFrames/"+str(frame_time)+".pickle", 'wb') as handle:
                        pickle.dump(frame, handle, protocol=pickle.HIGHEST_PROTOCOL)


                    print(frame)

                    sorted_master.append(frame)



                    break

            print(frame_segment['time'])


if __name__ == '__main__':

    # topics = ['/apollo/localization/pose',
    #           '/apollo/perception/traffic_light',
    #           '/apollo/sensor/gnss/best_pose',
    #           '/apollo/canbus/chassis']
    
    metatable = dynamodb.Table("cyber_aws_with_vid_meta")
    response = metatable.scan(
        TableName= 'cyber_aws_meta',
        FilterExpression=Key("experimentID").eq(34)
    )
    # print(response['Items'][0]['topics'])
    # topics = response['Items'][0]['topics']
    ignore_list = ["/apollo/control/pad", "/apollo/canbus/chassis_detail", "/tf_static", "/apollo/sensor/gnss/raw_data", 
                   "/apollo/sensor/gnss/ins_stat","/apollo/sensor/gnss/ins_status","/apollo/sensor/gnss/corrected_imu","/apollo/sensor/gnss/gnss_status"]
    topics = ["/apollo/sensor/camera/front_6mm/image/compressed"]
    for topic in topics:
        print("Looking for:", topic)
        if topic not in ignore_list:
            DynamoDB_Query(topic, table_name, table)
            print("QUERIED: ", topic)
        else:
            print("SKIPPING:", topic)

