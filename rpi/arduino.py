import serial
from redis import Redis

cli = Redis("localhost")
ser = serial.Serial('/dev/serial0', 115200)

while (True): 
    if(ser.in_waiting >0):
        line = ser.readline()
        arr = line.split(" ")
        cli.set("distance", arr[0])
        cli.set("anglex", arr[2])
        cli.set("anglez", arr[1])
        print(line)
