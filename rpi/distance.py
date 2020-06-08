import serial
from redis import Redis

cli = Redis("localhost")
ser = serial.Serial('/dev/serial0', 9600)

while (True): 
    if(ser.in_waiting >0):
        line = ser.readline()
        print(line)
