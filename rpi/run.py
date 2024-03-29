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
import serial

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis("localhost")

def activatevoice():
    camera()
    ref = db.reference()
    ref.update({"status/start":1})

def button():
    init = cli.get("count")
    prev = init
    while(True):
        init = cli.get("count")
        if init != prev:
            activatevoice()
        prev = init

def buttonhelper():
    os.system("python buttoncount.py")

def motor():
#    os.system("python motor.py")
    os.system("python led.py")

def arduino():
    print("arduino start")
    ser = serial.Serial('/dev/ttyUSB0', 115200)
    while (True): 
        if(ser.in_waiting > 0):
            line = ser.readline()
            try:
                arr = line.split(" ") 
                cli.set("distance", arr[0])
                cli.set("anglex", arr[2])
                cli.set("anglez", arr[1])
            except:
                pass
#           print(line)

def gyro():
    os.system("python imu.py")

def controller():
    prev = ""
    curr = ""
    while(True):
        stat = int(db.reference("status/mode").get())
        inp = db.reference("input").get()
        if prev != curr and inp != "null":
            search()
        prev = curr

def camera():
    s1 = time.time()
    print("camera start")
    os.system("raspistill -t 1000 -vf -hf -o zoid.jpg -w 3280 -h 2464")
    print("pic taken", str(time.time()-s1))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="fire-sdk.json"
    client = storage.Client()
    bucket = client.get_bucket('fire-30e38.appspot.com')
    # posting to firebase storage
    imageBlob = bucket.blob("/")
    imagePath = "zoid.jpg"
    imageBlob = bucket.blob("sent.jpg")
    imageBlob.upload_from_filename(imagePath)
    print("pic uploaded", str(time.time()-s1))
#    os.system("python upload.py")

#angle in format z, x
def search():   
    ref = db.reference("search")
    inp = db.reference("input").get()
    dict = ref.get()
#   print(dict)
    lst = []
    for key, value in dict.items():
        name = key
        if(inp == name):
            temp = []
            for key, value in value.items():
                temp.append(value)    
            lst = [name, temp[0], temp[1]]
            print(lst)
            break
        #print(name, lst)
    #lst = [["thing", [20, 60]]] #remove this line when you uncomment the rest
    #the state variables determine if the motors are on or when they should stop
    try:
        print("searching for " + str(lst))
        cli.set("targetx", lst[2])
        cli.set("targetz", lst[1])
        cli.set("statex", 1)
        cli.set("statez", 1)
        print("state: " + str(cli.get("statex")))
        ref1.update({"status/mode":0})
        ref1.update({"input":""})
        init = cli.get("count")
        prev = init
        while(True):
            init = cli.get("count")
            if init != prev:
                cli.set("statex", 0)
                cli.set("statez", 0)
                ref1.update({"searchdone":0})
                ref1.update({"status/mode":0})
                break
            prev = init
    except:
        ref1.update({"status/mode":0})
        ref1.update({"input":""})
        ref1.update({"searchdone":0})
        ref1.update({"status/mode":0})

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
    #Gyro method isn't needed when arduino is also on
    #p4 = Process(target = gyro)
    #p4.start()
    p5 = Process(target = motor)
    p5.start()
    p6 = Process(target = arduino)
    p6.start()

