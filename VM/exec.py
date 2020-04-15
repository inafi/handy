import os 
import inflect 
from redis import Redis 
import sys 
from collections import namedtuple 
import json 
from ast import literal_eval

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
    for i in range(len(arr) - 1):
        if "Bounds:" in arr[i]:
            continue
        if "Bounds:" not in arr and "Bounds:" not in arr[i + 1]:
            arr[i] = -1 
    arr[:] = (val for val in arr if val != -1)
    return arr

# Runs command and filters through terminal outputs
def run(acc, model):
    outputs = []
    classes = []
    if model == 3:
        text = cli.get('writev3').decode('utf-8')
    else:
        text = cli.get('writemrcnn').decode('utf-8')
    try:
        outputs = literal_eval(text)
        
        for i in range(len(outputs)):
            outputs[i][1] = int(outputs[i][1])
            for k in range(4):
                outputs[i][2][k] = int(outputs[i][2][k])
#        print(model, outputs)
        outputs = filter_acc(outputs, acc)
        return outputs
    except Exception as e:
#        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
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

def areafilter(v9, oid, v3, mrcnn):
    print(v9, "\n\n", oid, "\n\n", v3, "\n\n", mrcnn, "\n\n")
    all = [v9, oid, v3, mrcnn]
    if (all.count(-1) == 3):
        all[:] = (value for value in all if value != -1)
        return all[0]
    yolo = v3
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
 #   print(arr)
    print(read)
    cli.set('exe', read)
    cli.set('confirm', 3)
 
# Runs everything and assume jpg input - jpegs must be in /data
def get_output():
    # Accuracy filters of v3 and 9000
    y3 = run(30, 3)
    mrcnn = run(30, 'mrcnn')
    final = areafilter(-1, -1, y3, mrcnn)
    cli.set("aray","[]")
    #for i in final:
    #    print(i)
    if y3 == [] and mrcnn == []:
        print("Could not detect any objects")
        cli.set("exe", "Could not detect any objects")
        cli.set('confirm', 3)
    elif not (y3 == -1 and mrcnn == -1):
        #just use json.dumps() to convert list to string
        cli.set('search', json.dumps(final))
        array = get_l(final)
        logical(array)
        pluralize(array)
    else:
        print("Unable to Classify")
        cli.set('confirm', 3)
 
# Must be jpg
get_output()
