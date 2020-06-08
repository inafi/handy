from redis import Redis
import math
import json
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from PIL import Image

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis('localhost')
init = 0
prev = 0
pic = Image.open("../send.jpg")
width, height = pic.size
img_center = [width/2, height/2]

def distance(box):
    x = abs((box[0] + box[2])/2 - width/2)
    y = abs((box[1] + box[3])/2 - height/2)
    return math.sqrt(x**2 + y**2)

def angle(box, ob):
    box[3] = box[1] + box[3]
    box[2] = box[0] + box[2]
    pic_center = [int((box[0]+box[2])/2), int((box[1]+box[3])/2)]
    h = 77 * round(((img_center[1]-pic_center[1])/(height*1.0)) * 1000)/1000
    w = 145 * round(((pic_center[0]-img_center[0])/(width*1.0)) * 1000)/1000
    print(ob, w, h, box)
    return int(w), int(h)
   # return int(77 * (height/2 - (box[1] + box[3])/2)/height)

while(True):
    init = int(cli.get('confirm'))
    #prev = 5 means that exec has run
    if init == 0 and prev == 3:
        arr = json.loads(str(cli.get('search').decode('utf-8')))
        #simplifies conversion btwn string and list
        #print(arr)
        arr = sorted(arr, key=lambda x: x[0])
        closest = []
        current_class = arr[0][0]
        index = 0
        for i in range(len(arr)):
            if (arr[i][0] == current_class):
                if distance(arr[i][2]) < distance(arr[index][2]):
                    index = i
            if arr[i][0] != current_class and i == len(arr) - 1:
                closest.append(arr[i])
            if arr[i][0] != current_class or i == len(arr) - 1:
                closest.append(arr[index])
                index = i
                current_class = arr[i][0]
        ref = db.reference("search")
        ref.set("")
        for i in range(len(closest)):
            x, y = angle(closest[i][2], closest[i][0])
            closest[i] = [closest[i][0], x, y]
            ref2 = ref.update({closest[i][0] : {"x" : x, "y" : y}})
    prev = init
