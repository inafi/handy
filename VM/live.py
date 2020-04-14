import time
from collections import namedtuple
import json
import re
from multiprocessing import Process
import os
from redis import Redis
from PIL import Image
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
#from exec import area, rectfilter
#from exes import distance, angle

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})
cli = Redis('localhost')
Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')
pic = Image.open("../send.jpg")
width, height = pic.size
img_center = [width/2, height/2]

def filter_acc(l, acc):
    indexes = []
    for i in range(0, len(l)):
        if l[i][1] < acc:
            indexes.append(i)
    l = [i for j, i in enumerate(l) if j not in indexes]
    return l
 
def get_l(l):
    out = []
    final = []
    for i in range(len(l)):
        out.append(l[i][0])
    d = {x: out.count(x) for x in out}
    for x in d:
        final.append([x.replace(":", ""), d[x]])
    return final
 
def getavg(arg):
    sum = 0
    if len(arg) != 0:
        for i in range(len(arg)):
            sum += arg[i][1]
        return sum/len(arg)
    else:
        return -1
 
def filtercheck(outputs, acc):
    out = []
    avglist = []
 
    for i in range(len(outputs)):
        out.append(outputs[i][0])
    d = {x: out.count(x) for x in out}
 
    for labels in d:
        items = []
        sum = 0
        for k in range(len(outputs)):
            if outputs[k][0] == labels:
                items.append(outputs[k])
        for k in range(len(items)):
            sum += items[k][1]
        avg = sum / len(items)
        avglist.append([d[labels], labels, avg])
 
    for i in range(len(avglist)):
        if avglist[i][0] > 4 and avglist[i][2] < acc:
            times = int(avglist[i][0]/2 + 1.5)
            for k in range(len(outputs)):
                if outputs[k][0] == avglist[i][1] and times > 0:
                    outputs[k][1] = acc + 1
                    times -= 1
    return outputs
 
def removemultiple(arr):
    for i in range(len(arr) - 1):
        if "Bounds:" in arr[i]:
            continue
        if "Bounds:" not in arr and "Bounds:" not in arr[i + 1]:
            arr[i] = -1 
    arr[:] = (val for val in arr if val != -1)
    return arr

def run(acc, model):
    outputs = []
    classes = []
    if model == 3:
        text = cli.get('writev3').decode('utf-8')
    elif model == 9000:
        text = cli.get('write9000').decode('utf-8')
    elif model == 'oid':
        text = cli.get('writeoid').decode('utf-8')
    else:
        text = cli.get('writemrcnn').decode('utf-8')
    try:
        if (model != 'mrcnn'):
            text = text.split("Failed")[0]
            text = text.split("seconds.")[1].split("Not")[0]
            text = (text.replace('\n', '')).split("\r")
            del text[0]
            del text[-1]
            text = removemultiple(text)
            for i in range(int(len(text)/2)):
                classes.append([text[2 * i], text[2 * i + 1]])
            for i in range(int(len(classes))):
                box = [int(x) for x in classes[i][1].strip("Bounds:").split()]
                outputs.append([classes[i][0].split(": ")[0], int(classes[i][0].split(": ")[1].strip("%")), box])
            save = outputs
        else:
            text = text.split("  ")
            del text[-1]
            for i in range(len(text)):
                t = text[i].split(" ")
                if (len(t) > 6):
                    t[0] += " " + t[1]
                    del t[1]
                t = [t[0], int(t[1]), [int(t[2]), int(t[3]), int(t[4]), int(t[5])]]
                outputs.append(t)
            save = outputs
        outputs = filter_acc(outputs, acc)
        return outputs
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        return -1

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
    #print(ob, w, h, box)
    return int(w), int(h)

def area(a, b):  
    dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if (dx > 0) and (dy > 0):
        return dx*dy
    else:
        return -1

def rectfilter(lower, upper):
    for i in range(len(upper)):
        for k in range(len(lower)):
            if(lower[k] == -1):
                continue
            r3 = Rectangle(upper[i][2][0], upper[i][2][1], upper[i][2][0] + upper[i][2][2], upper[i][2][1] + upper[i][2][3])
            r9 = Rectangle(lower[k][2][0], lower[k][2][1], lower[k][2][0] + lower[k][2][2], lower[k][2][1] + lower[k][2][3])
            arr = int(area(r3, r9) * 1000)/1000
            if (arr == -1):
                continue
            percenta = float(1000 * (upper[i][2][2] * upper[i][2][3])/arr)/1000
            percentb = float(1000 * (lower[k][2][2] * lower[k][2][3])/arr)/1000
            if ((percenta > 0.7 or percentb > 0.7) and percenta < 2 and percentb < 2):
                lower[k] = -1
                break
    lower[:] = (value for value in lower if value != -1)
    return upper + lower

def areafilter(oid, v9, v3):
    yolo = [v9, oid, v3]
    if (yolo.count(-1) == 2):
        yolo[:] = (value for value in yolo if value != -1)
        return yolo[:]
    if v9 != -1:
        yolo = v9
    else:
        yolo = oid
    if v9 != -1 and oid != -1:
        yolo = rectfilter(v9, oid)
    if v3 != -1:
        yolo = rectfilter(yolo, v3)
    return yolo

def pluralize(arr):
    arr = tempremove(arr)
    cli.set("array", str(arr))
    out = []
    p = inflect.engine()
    for i in range(len(arr)):
        if arr[i][1] != 1:
            out.append([arr[i][1], p.plural(arr[i][0])])
        else:
            out.append([arr[i][1], arr[i][0]])
    read = ""
    for i in range(len(out)):
        if i != len(out) - 1 or len(out) == 1:
            read += str(out[i][0]) + " " + out[i][1] + ", "
        else:
            read += "and " + str(out[i][0]) + " " + out[i][1]
    print(read)

def tempremove(arr):
    for i in range(len(arr)):
        if (arr[i][0] in ['footwear', 'human face', 'wheel', 'vehicle registration plate', 'office building', 'machine']):
            arr[i][0] = -1
    for i in range(len(arr)):
        if arr[i][0] == -1:
            del arr[i]
            tempremove(arr)
            break
    return arr

def livev3():
    os.system("./darknetgcho detector demo cfg/coco.data cfg/yolov3.cfg yolov3.weights -dont_show -ext_output http://173.79.225.103:8080/video?dummy=param.mjpg -i 0 data/train.txt > livev3.txt")

def livev9():
    os.system("./darknetgcho detector demo cfg/combine9k.data cfg/yolo9000.cfg yolo9000.weights -dont_show -ext_output http://173.79.225.103:8080/video?dummy=param.mjpg -i 0 data/train.txt > livev9.txt")

def liveoid():
    os.system("./darknetgcho detector demo cfg/yolo.data cfg/oid.cfg yolov3-oid.weights -dont_show -ext_output http://173.79.225.103:8080/video?dummy=param.mjpg -i 1 data/train.txt > liveoid.txt -thresh 0.10")

def format(arr):
    out = []
    arr = arr.replace("\t", '').split("\n")
    del arr[-1]
    for i in range(len(arr)):
        try:
            out.append([arr[i].partition(":")[0], int(arr[i].split(" ")[1].strip("%")), [int(s) for s in re.findall('\d+', arr[i].partition("%")[2])]])
        except:
            pass
    return out

def getangle(arr):
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
    for i in range(len(closest)):
        x, y = angle(closest[i][2], closest[i][0])
        closest[i] = [closest[i][0], x, y]
    return closest

def main():
    v3 = []
    v9 = []
    oid = []
    while(True):
        livev3 = open("livev3.txt", "r+")
        livev9 = open('livev9.txt', 'r+')
        liveoid = open("liveoid.txt", "r+")
        v3text = re.split("FPS:\d+.\d\nObjects:\n\n", livev3.read())
        v9text = re.split("FPS:\d+.\d\nObjects:\n\n", livev9.read())
        oidtext = re.split("FPS:\d+.\d\nObjects:\n\n", liveoid.read())
        if v3text[-1] != '' or v9text[-1] != '' or oidtext[-1] != '':
            livev3.truncate(0)
            livev9.truncate(0)
            liveoid.truncate(0)
            v3c = format(v3text[-1])
            v9c = format(v9text[-1])
            oidc = format(oidtext[-1])
            if v3c != []:
                v3 = v3c
            if v9c != []:
                v9 = v9c
            if oidc != []:
                oid = oidc
            try:
                ref = db.reference("search")
                #print(v9, v3)
                out = getangle(tempremove(areafilter(oid, v9, v3)))
                for i in range(len(out)):
                    x, y = out[i][1], out[i][2]
                    ref = ref.update({out[i][0] : {"x" : x, "y" : y}})
                cli.set("live", json.dumps(out))
                print(out, "\n")
#                pluralize(out)
            except:
                if oidc == [] and v3c != []:
                    out = getangle(tempremove(areafilter(oidc, v9, v3)))
                    cli.set("live", json.dumps(out))
                elif v3c == [] and oidc != []:
                    out = getangle(tempremove(areafilter(oid, v9, v3c)))
                    cli.set("live", json.dumps(out))
#                pluralize(out)
                print(out, "\n")
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
                pass

def reset():
    livev3 = open("livev3.txt", "r+")
    livev3.truncate(0)
    liveoid = open("liveoid.txt", "r+")
    liveoid.truncate(0)
    livev9 = open("livev9.txt", "r+")
    livev9.truncate(0)
    cli.set('live', '')

if __name__ == '__main__':
    reset()
    p1 = Process(target=livev3)
    p1.start()
    p2 = Process(target=liveoid)
    p2.start()
    p3 = Process(target=livev9)
    p3.start()
    p4 = Process(target=main)
    p4.start()
