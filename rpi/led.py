import RPi.GPIO as GPIO
import time
from redis import Redis
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import RPi.GPIO as GPIO
from multiprocessing import Process

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis("localhost")

GPIO.setmode(GPIO.BCM)  
GPIO.setup(11, GPIO.OUT) #top
GPIO.setup(13, GPIO.OUT) #left
GPIO.setup(18, GPIO.OUT) #right
GPIO.setup(16, GPIO.OUT) #bottom

def compass(initval, curr):
    out = curr - initval
    if initval < 90 and curr > 180:
        out = -1 * (360 - curr + initval)
    if initval > 270 and curr < 180:
        out = 360 - initval + curr
    if abs(out) > 90:
        return 90 * int(out/abs(out))
    return out

def anglez():
    initval = 1000
    print("LEDZ start")
    while(True):
        if cli.get("statez") == "1":
            x = int(cli.get("anglez"))
            if initval == 1000:
                initval = x
            z = int(cli.get("targetz")) - compass(initval, x)
            #print(initval, z, x)
            if z < -2:
                GPIO.output(13, 1)
                GPIO.output(18, 0)
            elif z > 2:
                GPIO.output(13, 0)
                GPIO.output(18, 1)
            else:
                GPIO.output(13, 0)
                GPIO.output(18, 0)
        else:
            initval = 1000
            GPIO.output(13, 0)
            GPIO.output(18, 0)

def anglex():
    print("LEDX start")
    while(True):
        if cli.get("statex") == "1":
            x = int(cli.get("targetx")) - int(cli.get("anglex"))
            if abs(x) > 90:
                x = 90 * x/abs(x)
            if x < -2:
                GPIO.output(16, 1)
                GPIO.output(11, 0)
            elif x > 2:
                GPIO.output(16, 0)
                GPIO.output(11, 1)
            else:
                GPIO.output(16, 0)
                GPIO.output(11, 0)
        else:
            GPIO.output(16, 0)
            GPIO.output(11, 0)

if __name__ == '__main__':
    p1 = Process(target=anglex)
    p1.start()
    p2 = Process(target=anglez)
    p2.start()
#    GPIO.cleanup()

