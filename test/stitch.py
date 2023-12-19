
import pickle
import cv2
import base64 
import numpy as np
from PIL import Image
import io

def load_from_pickle(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    return data

# Take in base64 string and return PIL image
def stringToImage(base64_string):
    imgdata = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(imgdata))

def toRGB(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

# Specify the filename for the pickle file
pickle_filename = './test/pickleFrames/1698251687183398667.pickle'

# Load the data from the pickle file
loaded_data = load_from_pickle(pickle_filename)

# Display the contents of the loaded data
# print("Contents of the loaded data:")

imageString = ''
for item in loaded_data:
    imageString += item['data']


img = stringToImage(imageString)
img = toRGB(img)

cv2.imshow("yeet", img)
cv2.waitKey(10000)

# print(imageString)
