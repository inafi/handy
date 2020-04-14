import RPi.GPIO as GPIO
import os
import time
from multiprocessing import Process
from redis import Redis

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

cli = Redis("localhost")

s = 0
t = 0
o = 0
save = []
last = []
count = 0

while(True):
    if GPIO.input(4) == GPIO.HIGH:
        s = 0
        if o == 0:
            t = time.time()
            o = 1
    elif s == 0:
        s = 1
        cli.set("count", count)
        count += 1
        o = 0
        last.append(time.time())
        if len(last) == 3:
            del last[0]
        if len(save) == 3:
            del save[0]
        print(cli.get("count"))

GPIO.cleanup()
