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

def motor(m, cycle):
    try:
        for i in range(1):
            m.ChangeDutyCycle(cycle)
            time.sleep(0.25)
    except KeyboardInterrupt:
        m.stop()
        print("Ctl C pressed - ending program")

def anglez():
    left = GPIO.PWM(13, 100)
    right = GPIO.PWM(18, 100)
    left.start(0)
    right.start(0)
    initval = 1000
    print("MotorZ start")
    while(True):
        if cli.get("statez") == "1":
            x = int(cli.get("anglez"))
            if initval == 1000:
                initval = x
            z = int(cli.get("targetz")) - compass(initval, x)
            #print(initval, z, x)
            if z < -2:
                motor(left, int(-1 * z * 4/9 + 50))
                motor(right, 0)
            elif z > 2:
                motor(right, int(z * 4/9 + 50))
                motor(left, 0)
            else:
                motor(right, 0)
                motor(left, 0)
        else:
            initval = 1000
            motor(right, 0)
            motor(left, 0)

def anglex():
    top = GPIO.PWM(11, 100)
    bottom = GPIO.PWM(16, 100)
    top.start(0)
    bottom.start(0)
    print("MotorX start")
    while(True):
        if cli.get("statex") == "1":
            x = int(cli.get("targetx")) - int(cli.get("anglex"))
            if abs(x) > 90:
                x = 90 * x/abs(x)
            if x < -2:
                motor(bottom, int(-1 * x * 4/9 + 50))
                motor(top, 0)
            elif x > 2:
                motor(top, int(x * 4/9 + 50))
                motor(bottom, 0)
            else:
                motor(top, 0)
                motor(bottom, 0)
        else:
            motor(top, 0)
            motor(bottom, 0)

if __name__ == '__main__':
    p1 = Process(target=anglex)
    p1.start()
    p2 = Process(target=anglez)
    p2.start()
#    GPIO.cleanup()

