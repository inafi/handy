import RPi.GPIO as GPIO
import time
from redis import Redis
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import RPi.GPIO as GPIO

cred = credentials.Certificate("fire-sdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fire-30e38.firebaseio.com/'
})

cli = Redis("localhost")

GPIO.setmode(GPIO.BOARD)  
GPIO.setup(11, GPIO.OUT) 
GPIO.setup(13, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
top = GPIO.PWM(11, 100)
bottom = GPIO.PWM(16, 100)
left = GPIO.PWM(13, 100)
right = GPIO.PWM(18, 100)
top.start(0)
bottom.start(0)
left.start(0)
right.start(0)
#cli.set("vibr", 50)

def motor(m, angle):
    try:
       i = 0 
       while True:
            m.ChangeDutyCycle(angle)
            i += 1
            time.sleep(0.25)
            if i == 1:
                break
    except KeyboardInterrupt:
        print("Ctl C pressed - ending program")

def loop(m):
   print("start " + str(m)) 
   for i in range(30, 100, 10):
        motor(m, i)
        time.sleep(0.25)

motor(top, 0)
motor(bottom, 0)
motor(left, 0)
motor(right, 0)
#loop(top)
#loop(left)
#loop(right)
#loop(bottom)
#top.stop()
#bottom.stop()
#left.stop()
#right.stop()
GPIO.cleanup()

