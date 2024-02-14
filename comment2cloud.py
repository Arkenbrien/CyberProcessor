import numpy as np
from PIL import Image
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
# from nltk.corpus import stopwords
import json
import os
from collections import Counter

def transform_zeros(val):
    if val.any() == 0:
        return 255
    else:
        return 0

ignoreList = ["manual", "takeover", "road", "travis", "van", "cant", "onto","good", "car"]
directory = "./newComments"
txt_master = ""


mask = np.array(Image.open("./maskImg/van.png"))
maskable_image = np.ndarray((mask.shape[0],mask.shape[1]), np.int32)
print(maskable_image)
for i in range(len(mask)):
    maskable_image[i] = list(map(transform_zeros, mask[i]))
    
print(maskable_image)
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        with open(f) as file:
            dat = json.load(file)
            for comment in dat["comments"]:
                for word in comment['problem'].split():
                    if word in ignoreList:
                        print("Skipped: ", word)
                    else:
                        txt_master += word
                        txt_master += " "

stop = set(STOPWORDS)


word_dict = Counter(txt_master)
print(word_dict)

wc = WordCloud(background_color="white", mask=maskable_image, stopwords=stop, contour_width=1, contour_color='black')
wc.generate(txt_master)


# plot the WordCloud image                       
plt.figure()
plt.imshow(wc)
plt.axis("off")
plt.tight_layout(pad = 0)
 
plt.show()