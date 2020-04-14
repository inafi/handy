import os
import inflect
from redis import Redis
import sys
from collections import namedtuple
import json
import argparse
from ast import literal_eval

parser = argparse.ArgumentParser()
parser.add_argument("y3", nargs='?')
parser.add_argument("y9", nargs='?')
parser.add_argument("m", nargs='?')
parser.add_argument("o", nargs='?')
args = parser.parse_args()
 
#Sets type rectangle tuple for area intersection
Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

# Automatically changes directory in path
cpath = os.path.abspath(os.path.dirname(__file__))
os.chdir(cpath)
cli = Redis('localhost')
 
# Return array with filtered accuracy
def filter_acc(l, acc):
    indexes = []
    for i in range(0, len(l)):
        if l[i][1] < acc:
            indexes.append(i)
    l = [i for j, i in enumerate(l) if j not in indexes]
    return l
 
# Returns array of the frequency of labels of a certain label: [["apple", 2], ["orange", 7]]
def get_l(l):
    out = []
    final = []
    for i in range(len(l)):
        out.append(l[i][0])
    d = {x: out.count(x) for x in out}
    for x in d:
        final.append([x.replace(":", ""), d[x]])
    return final
 
# Get's the average accuracy of all the classifications
def getavg(arg):
    sum = 0
    if len(arg) != 0:
        for i in range(len(arg)):
            sum += arg[i][1]
        return sum/len(arg)
    else:
        return -1
 
# Checks if there are too many objects getting filtered at once
def filtercheck(outputs, acc):
    out = []
    avglist = []
 
    # Makes list of frequency of labels
    for i in range(len(outputs)):
        out.append(outputs[i][0])
    d = {x: out.count(x) for x in out}
 
    # Makes an array with the average array for each class group
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
 
    # Goes through outputs input and replaces with higher accuracy
    for i in range(len(avglist)):
        if avglist[i][0] > 4 and avglist[i][2] < acc:
            times = int(avglist[i][0]/2 + 1.5)
            for k in range(len(outputs)):
                if outputs[k][0] == avglist[i][1] and times > 0:
                    outputs[k][1] = acc + 1
                    times -= 1
    return outputs
 
#Removes multiple predictions on a single box:
def removemultiple(arr):
    for i in range(len(arr)):
        t = arr[i].split("%")
        if len(t) == 2:
            continue
        else:
            arr[i] = t[0] + "%" + t[-1]
    return arr

# Runs command and filters through terminal outputs
def run(acc, model):
    outputs = []
    classes = []
    if model == 3:
        text = cli.get('writev3').decode('utf-8')
        # print(cli.get('writev3').decode('utf-8'))
    elif model == 9000:
        text = cli.get('write9000').decode('utf-8')
    elif model == 'oid':
        text = cli.get('writeoid').decode('utf-8')
    else:
        text = cli.get('writemrcnn').decode('utf-8')
        # print(cli.get('writemrcnn').decode('utf-8'))
    try:
        if (model != 'mrcnn'):
            #yolos
            text = literal_eval(text)
            if text == []:
                return -1
            text = removemultiple(text)
            #Converts text to this format: ['person', 81, [365, 859, 496, 1099]
            for i in range(len(text)):
                text[i] = text[i].split("%")
                classes.append([text[i][0], text[i][1].strip()])
            for i in range(len(classes)):
                # print(classes[i][1])
                box = [int(x) for x in classes[i][1].strip("Bounds:").split()]
                outputs.append([classes[i][0].split(":")[0], int(classes[i][0].split(":")[1].strip("%")), box])
            save = outputs
        else:
            #maskrcnn
            #Converts text to this format: ['person', 81, [365, 859, 496, 1099]
            text = literal_eval(text)
            if text == []:
                return -1
            for i in range(len(text)):
                t = text[i].split(" ")
                if (len(t) > 6):
                    t[0] += " " + t[1]
                    del t[1]
                t = [t[0], int(t[1]), [int(t[2]), int(t[3]), int(t[4]), int(t[5])]]
                outputs.append(t)
            save = outputs
#        outputs = filtercheck(outputs, acc)
        outputs = filter_acc(outputs, acc)
        #if outputs == [] and getavg(save) != -1:
        #    outputs = filter_acc(save, getavg(save))
        #print(outputs)
        #print(model)
        return outputs
    except Exception as e:
        # print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        return -1

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
            if ((percenta > 0.7 or percentb > 0.7) and percenta < 2.2 and percentb < 2.2):
                lower[k] = -1
                break
    lower[:] = (value for value in lower if value != -1)
    return upper + lower

def areafilter(v3, v9, mrcnn, oid):
    # print(v3, "\n\n", v9, "\n\n", mrcnn, "\n\n", oid, "\n\n")
    all = [v9, oid, v3, mrcnn]
    if (all.count(-1) == 3):
        all[:] = (value for value in all if value != -1)
        return all[0]
    yolo = [v9, oid, v3]
    if (yolo.count(-1) == 2):
        yolo[:] = (value for value in yolo if value != -1)
        yolo = yolo[0]
    else:
        if v9 != -1:    
            yolo = v9
        else:
            yolo = oid
    if v9 != -1 and oid != -1:
        yolo = rectfilter(v9, oid)
    if v3 != -1:
        yolo = rectfilter(yolo, v3)
    if mrcnn != -1:
        return rectfilter(yolo, mrcnn)
    return yolo

#this removes clothing and other wierd stuff - this should be temporary
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

#Changes groupings - if there are oranges and fruits in the output then it deletes oranges an adds it to fruits
def logicalhelper(filter, generalclass, arr):
    classes = [c[0] for c in arr]
    if (any(i in filter for i in classes) and 'fruit' in classes):
        add = 0
        addind = []
        for i in range(len(classes)):
            if classes[i] in filter:
                addind.append(i)
        for i in addind:
            add += arr[i][1]
        for i in range(len(arr) - 1, -1, -1):
            if arr[i][0] in filter:
                del arr[i]
        for i in range(len(arr)):
            if arr[i][0] == generalclass:
                arr[i][1] += add
            
def logical(arr):
    fruits = ['orange', 'apple', 'banana', 'grapefruit', 'grape', 'peach', 'pear', 'pineapple', 'melon', 'pomegranate']
    veg = ['carrot', 'asparagus', 'broccoli', 'tomato', 'pepper', 'radish', 'bell pepper']
    logicalhelper(fruits, 'fruit', arr)
    logicalhelper(veg, 'vegetable', arr)

# Pluralizes array and returns array - input array in frequency format
def pluralize(arr):
    arr = tempremove(arr)
    cli.set("array", str(arr))
    out = []
    p = inflect.engine()
    for i in range(len(arr)):
        out.append([arr[i][0], arr[i][1]])
    read = ""
    for i in range(len(out)):
        if i != len(out) - 1 or len(out) == 1:
            read += out[i][0].replace(" ", "") + " " + str(out[i][1]) + ", "
        else:
            read += " " + out[i][0].replace(" ", "") + " " + str(out[i][1])
 #   print(arr)
    #print(read)
    return read

def grade(ns):
    #person 3,  ball 2
    #print(ns)
    glines = open("val/correct.txt", "r").read().splitlines()
    score = float(cli.get("score").decode("utf-8"))
    total =float(cli.get("total").decode("utf-8")) 
    miss = float(cli.get("miss").decode("utf-8"))
    #print(total)
    #print(score)
    gd = {}
    nd = {}
    index = int(cli.get("place").decode("utf-8"))
    gl = glines[index].split(" ")
    gl.pop(0)

    if(len(gl) < 2 and ns == ""):
        #print("NONE")
        #print("NONE")
        return
    for p in gl:
        k = p.split(",")[0]
        v = p.split(",")[1]
        gd[k] = float(v)
    if(ns == ""):
        #print(gd)
        total = total + len(gd)
        cli.set("total", str(total))
        #print("NONE")
        return
    for p in ns.split(","):
        if len(p) == 1:
            break
        p = p.strip()
        nl = p.split(" ")
        k = nl[0]
        v = nl[1]
        nd[k] = float(v)
    if(gd == {}):
        miss = miss + len(nd)
        return
    rem = ["mammal","wheel","tire","sportswear","carnivore","sportsequipment","chestofdrawers","gasstove","kitchenappliance",'homeappliance','filingcabinet','fashionaccessory']
    for i in rem:
        gd.pop(i, None)
    coo = 0 
    for g in gd:
        found = False
        for n in nd:
            if(gcheck(n,g)):
                coo = coo+1
                total = total+1
                score = score + 1
                found = True
        if(found == False and gd != {}):
            total = total + 1
    miss = miss + len(nd)-coo
    cli.set("score", str(score))
    cli.set("total", str(total))
    cli.set("miss",str(miss))
    '''
    print("MATCHES: " + str(coo))
    print(gd.keys())
    print(nd.keys())
    print("MISS: " + str(miss))
    print("TOTAL: " + str(total))
    print("SCORE: " + str(score))
    '''
def gcheck(n, g):
    a = [["footwear","humanmouth", "sportsuniform","woman","humaneye","humanface","girl", "dress", "humanear", "bicyclehelmet","humanhand", "human","humanhair", "person", "clothing", "humanbody", "man", "humanhead","swimwear","humanleg","worker","scuplture","bust",'bronzesculpture'],["cosmetics","personalcare"], ["van","vehicle","truck",'limousine','autopart' ,"car","bicycle" ,"landvehicle"],["watercraft", "boat", "vehicle"], ["flower","lavendar","plant","tree", "commonsunflower","pottedplant","houseplant","rose"],["beer","cup","fork","spoon","tableware","table","bottle","food"],['cake', 'dairyproduct', 'pastry', 'snack','food','milk','cup','bowl','pancake','icecream','bakedgoods'],['cheese', 'dessert', 'fastfood', 'tart', 'pizza','food','cheese',"cup","doughnut"],["bag","case","suitcase","backpack","handbag","briefcase"] , ["falcon", "canary","bird","animal", "eagle","turkey","chicken"],["animal","lion","fox","teddybear","bear","polarbear","commoniguana","dog","cat","porcupine","sheep","goat","mouse","domesticcat","horse","mule"],["tableware","chair","furniture",'cupboard','desk','cabinetry','table',],["food","cabbage","plant","vegetable","carrt","broccoli","salad","snack"],["food","fruit","fish","lobster","crab","bowl"] ,["food","apple", "bannana","salad","pear" ,"fruit", "pineapple","orange"],["insect","animal","spider",'blackandgoldgardenspider'], ["building","skyscraper","officebuilding","shop","house","tower"],["rifle","knife","weapon"],["clock","watch","wallclock"],["sunhat","hat","clothing","tie","sportswear","humanhead"],["rocket","missile"]]
    for i in range(len(a)):
        if ( n in a[i]) and (g in a[i] or 'human' in g):
            return True
      
    return n in g or n==g  or g in n

# Runs everything and assume jpg input - jpegs must be in /data
def get_output(y3b, y9b, mb, ob):
    # Accuracy filters of v3 and 9000
    y3 = y9 = mrcnn = oid = -1
    # print(y3b, y9b, mb, ob)
    if y3b:
        y3 = run(80, 3)
    if y9b:
        y9 = run(90, 9000)
    if mb:
        mrcnn = run(91, 'mrcnn')
    if ob:
        oid = run(10, 'oid')
    final = areafilter(y9, oid, y3, mrcnn)
    # for i in final:
    #     print(i)
    if y3 == [] and y9 == [] and mrcnn == [] and oid == []:
        print("Could not detect any objects")
        cli.set("exe", "Could not detect any objects")
        cli.set('confirm', 5)
    elif not (y3 == -1 and y9 == -1 and mrcnn == -1 and oid == -1):
        #just use json.dumps() to convert list to string
        cli.set('search', json.dumps(final))
        array = get_l(final)
        logical(array)
        pl=pluralize(array)
        grade(pl)
    else:
        grade("")
        #print("Unable to Classify")
 
# Must be jpg
get_output(args.y3 != "-1", args.y9 != "-1", args.m != "-1", args.o != "-1")
