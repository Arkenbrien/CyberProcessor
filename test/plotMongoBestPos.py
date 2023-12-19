import pymongo
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

# Set up MongoDB connection
client = pymongo.MongoClient("mongodb://192.168.1.6:27017")

# Replace the placeholders with your actual MongoDB connection details
# - your_username: Your MongoDB username
# - your_password: Your MongoDB password
# - your_host: The host where your MongoDB server is running (e.g., localhost)
# - your_port: The port on which MongoDB is running (default is 27017)
# - your_database: The name of the MongoDB database

# Access the database
db = client.cyber_data  # Replace 'your_database' with the actual name of your database

# Access the collection (similar to a table in relational databases)
collection = db.cyber_van  # Replace 'your_collection' with the actual name of your collection

# Query to extract data (you can customize this based on your needs)
# query = {'topic': '/apollo/localization/pose'}
query = {}
# Extract data from MongoDB
result = collection.find(query)

# Print the extracted data
position_x = []
position_y = []

color = [[255,0,255]]

experiment_id = 34
metadID = db['cyber_meta'].find_one({'experimentID': experiment_id})
# metadID['groupID']
# print(metadID['groupID'])

# Query to extract data (you can customize this based on your needs)
query = {'groupMetadataID': metadID['groupID'], 'topic': '/apollo/localization/pose'}
# query = {}
# Extract data from MongoDB
result = collection.find(query)

count = 0
for document in tqdm(result):
    # print(document['topic'] )
    # print(count)
    if document['topic'] == "/apollo/localization/pose":
        position_x.append(float(document['pose']['position']['x']))
        position_y.append(float(document['pose']['position']['y']))

    count +=1
        # color.append(color[0])

    # elif document['topic'] == "/apollo/canbus/chassis":
    #     color.append([255,255,0])
print("DONE LOOPING")
fig = plt.figure()
ax = fig.add_subplot(111, aspect='equal')
ax.scatter(position_x, position_y)

# Close the MongoDB connection
client.close()

plt.show()