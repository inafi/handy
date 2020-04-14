import picamera
import time
import os
from multiprocessing import Process
from redis import Redis
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase import *
import RPi.GPIO as GPIO
import re

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis("localhost")

def activatevoice():
#    camera()
    ref = db.reference()
    ref.update({"status/start":1})

def button():
    init = cli.get("count")
    prev = init
    while(True):
        ref = db.reference("status/mode")
        mode = int(ref.get())
        init = cli.get("count")
        if init != prev and mode == 0:
            activatevoice()
        prev = init

def buttonhelper():
    os.system("python buttoncount.py")

def motor():
    os.system("python motor.py")

def gyro():
    os.system("python arduino.py")

def controller():
    prev = ""
    curr = ""
    while(True):
        stat = int(db.reference("status/mode").get())
        inp = db.reference("input").get()
#        if(stat == 1 and inp != "null"):
        if int(cli.get("count")) == 2:
            print("search test")
            search()
        if curr != prev and re.search("\d", str(curr)):
            if "scan" in str(curr):
                print("scan")
#                scan()
            elif "search" in str(curr):
                print("search")
#                search()
            else:
#                print("text")
                text()
        prev = curr

def camera():
    print("camera start")
    os.system("raspistill -t 1000 -o zoid.jpg -w 3280 -h 2464")
    print("pic taken")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="fire-sdk.json"
    client = storage.Client()
    bucket = client.get_bucket('fire-30e38.appspot.com')
    # posting to firebase storage
    imageBlob = bucket.blob("/")
    imagePath = "zoid.jpg"
    imageBlob = bucket.blob("sent.jpg")
    imageBlob.upload_from_filename(imagePath)
    print("pic uploaded")

def scan():
    print("Scanning")
    ref = db.reference()
    camera()
    ref.update({"status/mode":4})

def text():
    ref = db.reference()
    camera()
    ref.update({"status/mode":2})

#angle in format z, x
def search():   
    ref1 = db.reference()
    ref1.update({"status/mode":1})
    ref = db.reference("search")
    inp = db.reference("input").get()
    dict = ref.get()
#    print(dict)
    lst = []
    for key, value in dict.items():
        name = key
        if(inp == name):
            temp = []
            for key, value in value.items():
                temp.append(value)    
            lst = [[name, temp]]
            print(lst)
            break
        print(name, lst)
        
     
    lst = [["thing", [20, 60]]] #remove this line when you uncomment the rest
    #the state variables determine if the motors are on or when they should stop
    cli.set("targetx", lst[0][1][1])
    cli.set("targetz", lst[0][1][0])
    cli.set("statex", 1)
    cli.set("statez", 1)
    ref1.update({"status/mode":0})
    ref1.update({"input":"null"})
    init = cli.get("count")
    prev = init
    while(True):
        init = cli.get("count")
        if init != prev:
            cli.set("statex", 0)
            cli.set("statez", 0)
            ref1.update({"searchdone":1})
            ref1.update({"status/mode":0})
            break
        prev = init

def reset():
    cli.set("action", "")
    cli.set("count", 0)
    cli.set("statex", 0)
    cli.set("statez", 0)

if __name__ == '__main__':
    reset()
    p1 = Process(target = button)
    p1.start()
    p2 = Process(target = buttonhelper)
    p2.start()
    p3 = Process(target = controller)
    p3.start()
    p4 = Process(target = arduino)
    p4.start()
    p5 = Process(target = motor)
    p5.start()
