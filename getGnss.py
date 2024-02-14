import pymongo
import json


# Set up MongoDB connection
# client = pymongo.MongoClient("mongodb://192.168.1.6:27017")
client = pymongo.MongoClient("mongodb://localhost:27017")

# Access the database
db = client.cyber_data  # Replace 'your_database' with the actual name of your database

# Access the collection (similar to a table in relational databases)
collection = db.cyber_van  # Replace 'your_collection' with the actual name of your collection
meta =  db.cyber_meta

metadID = meta.find_one({'experimentID': 39})

print(metadID['groupID'])

query = {'groupMetadataID': metadID['groupID'], 'topic': '/apollo/sensor/gnss/raw_data'}

result = collection.find(query)


print(result)

store_obj = {
    "time": [],
     "raw": []
}

count = 0
for i in result:
    print(i['data'])
    print(i['time'])

    store_obj['time'].append(i['time'])
    store_obj['raw'].append(i['data'])

    count += 1

    if count > 5:
        break

json_object = json.dumps(store_obj, indent=4)
print(json_object)

with open("experiment39_rawGNSS.json", "w") as outfile:
    outfile.write(json_object)