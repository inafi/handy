import io
import os
from google.cloud import vision
from google.cloud.vision import types
import enchant
import re
from redis import Redis
import math
import json
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from shapely.geometry import Polygon

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis('localhost')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="APIKEY.json"
client = vision.ImageAnnotatorClient()

def gettext():
    file_name = os.path.join(os.path.dirname(__file__), '../send.jpg')
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    reply = client.text_detection(image=image)
    labels = reply.text_annotations
    d = enchant.Dict("en_US")
    try:    
        while int(cli.get('confirm').decode('utf-8')) != 5:
            pass

        words = []
        for i in labels:
            if "\n" not in i.description and d.check(i.description):
                i.description = re.sub(r"[^a-zA-Z0-9]","", i.description).lower()
                words.append(i)

        arr = json.loads(str(cli.get('search').decode('utf-8')))
        out = [[None] for x in range(len(arr) + 1)] 

        for k in words:
            p2 = Polygon([(k.bounding_poly.vertices[0].x, k.bounding_poly.vertices[0].y), (k.bounding_poly.vertices[1].x, k.bounding_poly.vertices[1].y), (k.bounding_poly.vertices[2].x, k.bounding_poly.vertices[2].y), (k.bounding_poly.vertices[3].x, k.bounding_poly.vertices[3].y)])
            boxind = -1
            minarr = 0
            for j in range(len(arr)):
                i = arr[j]
                p1 = Polygon([(i[2][0], i[2][1]), (i[2][0] + i[2][2], i[2][1]), (i[2][0] + i[2][2], i[2][1] + i[2][3]), (i[2][0], i[2][1] + i[2][3])])
                pa = p1.intersection(p2).area
                if pa > 0:
                    # print(i[0], k.description, pa, max(p1.area/p2.area, p2.area/p1.area))
                    if max(pa/p2.area, pa/p1.area) > 0.7:
                        if boxind == -1:
                            boxind = j
                            minarr = max(p1.area/p2.area, p2.area/p1.area)
                        elif max(p1.area/p2.area, p2.area/p1.area) < minarr:
                            boxind = j
            # print(k.description, "\t", boxind, minarr, "\t", arr[boxind][0])
            if boxind != -1:
                out[boxind][0] = arr[boxind][0]
                out[boxind].append(k.description)
            else:
                out[-1].append(k.description)

        response = ""
        remove = ['tree', 'stop sign']
      
        for j in range(len(out)):
            i = out[j]
            if len(i) > 1 and i[0] not in remove:
                if i[0] != None:
                    response += i[0] + " says "
                elif j == len(out) - 1:
                    response += " the rest says "
                for k in range(1, len(i)):
                    response += i[k] + " "
                response += ", "
        if response == "":
            response = "no text found"
    except Exception as e:
        print(e)
        response = "no text found"
    return response

init = 0
prev = 0

while(True):
    init = int(cli.get('read').decode('utf-8'))
    s = time.time()
    if init != prev:
        text = gettext()
        print(text)
        ref = db.reference()
        ref.update({"text":text})
        print("text time:", time.time() - s, "\n")
    prev = init

print(gettext())
