import pymongo
import matplotlib.pyplot as plt
import numpy as np

# Set up MongoDB connection
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")

# Replace the placeholders with your actual MongoDB connection details
# - your_username: Your MongoDB username
# - your_password: Your MongoDB password
# - your_host: The host where your MongoDB server is running (e.g., localhost)
# - your_port: The port on which MongoDB is running (default is 27017)
# - your_database: The name of the MongoDB database

# Access the database
db = client.cyber_aws  # Replace 'your_database' with the actual name of your database

# Access the collection (similar to a table in relational databases)
collection = db.cyber_aws  # Replace 'your_collection' with the actual name of your collection

# Query to extract data (you can customize this based on your needs)
# query = {'topic': '/apollo/localization/pose'}
query = {}
# Extract data from MongoDB
result = collection.find(query)

# Print the extracted data
position_x = []
position_y = []

color = [[255,0,255]]

for document in result:
    print(document['topic'] )
    if document['topic'] == "/apollo/localization/pose":
        position_x.append(float(document['pose']['position']['x']))
        position_y.append(float(document['pose']['position']['y']))
        color.append(color[0])

    elif document['topic'] == "/apollo/canbus/chassis":
        color.append([255,255,0])
        
fig = plt.figure()
ax = fig.add_subplot(111, aspect='equal')
ax.scatter(position_x, position_y)

# Close the MongoDB connection
client.close()

plt.show()