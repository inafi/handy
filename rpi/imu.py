#GYRO HAS TO BE FLAT UPON START OF PROGRAM
import sys
import time
import math
import datetime
import os
from redis import Redis
from multiprocessing import Process
from ctypes import *
import smbus

cli = Redis("localhost")

path = "lib/liblsm9ds1cwrapper.so"
lib = cdll.LoadLibrary(path)
lib.lsm9ds1_create.argtypes = []
lib.lsm9ds1_create.restype = c_void_p

lib.lsm9ds1_begin.argtypes = [c_void_p]
lib.lsm9ds1_begin.restype = None

lib.lsm9ds1_calibrate.argtypes = [c_void_p]
lib.lsm9ds1_calibrate.restype = None

lib.lsm9ds1_gyroAvailable.argtypes = [c_void_p]
lib.lsm9ds1_gyroAvailable.restype = c_int
lib.lsm9ds1_accelAvailable.argtypes = [c_void_p]
lib.lsm9ds1_accelAvailable.restype = c_int
lib.lsm9ds1_magAvailable.argtypes = [c_void_p]
lib.lsm9ds1_magAvailable.restype = c_int

lib.lsm9ds1_readGyro.argtypes = [c_void_p]
lib.lsm9ds1_readGyro.restype = c_int
lib.lsm9ds1_readAccel.argtypes = [c_void_p]
lib.lsm9ds1_readAccel.restype = c_int
lib.lsm9ds1_readMag.argtypes = [c_void_p]
lib.lsm9ds1_readMag.restype = c_int

lib.lsm9ds1_getGyroX.argtypes = [c_void_p]
lib.lsm9ds1_getGyroX.restype = c_float
lib.lsm9ds1_getGyroY.argtypes = [c_void_p]
lib.lsm9ds1_getGyroY.restype = c_float
lib.lsm9ds1_getGyroZ.argtypes = [c_void_p]
lib.lsm9ds1_getGyroZ.restype = c_float

lib.lsm9ds1_getAccelX.argtypes = [c_void_p]
lib.lsm9ds1_getAccelX.restype = c_float
lib.lsm9ds1_getAccelY.argtypes = [c_void_p]
lib.lsm9ds1_getAccelY.restype = c_float
lib.lsm9ds1_getAccelZ.argtypes = [c_void_p]
lib.lsm9ds1_getAccelZ.restype = c_float

lib.lsm9ds1_getMagX.argtypes = [c_void_p]
lib.lsm9ds1_getMagX.restype = c_float
lib.lsm9ds1_getMagY.argtypes = [c_void_p]
lib.lsm9ds1_getMagY.restype = c_float
lib.lsm9ds1_getMagZ.argtypes = [c_void_p]
lib.lsm9ds1_getMagZ.restype = c_float

lib.lsm9ds1_calcGyro.argtypes = [c_void_p, c_float]
lib.lsm9ds1_calcGyro.restype = c_float
lib.lsm9ds1_calcAccel.argtypes = [c_void_p, c_float]
lib.lsm9ds1_calcAccel.restype = c_float
lib.lsm9ds1_calcMag.argtypes = [c_void_p, c_float]
lib.lsm9ds1_calcMag.restype = c_float

imu = lib.lsm9ds1_create()
lib.lsm9ds1_begin(imu)
if lib.lsm9ds1_begin(imu) == 0:
    print("Failed to communicate with LSM9DS1.")
    quit()
lib.lsm9ds1_calibrate(imu)

# If the IMU is upside down (Skull logo facing up), change this value to 1
IMU_UPSIDE_DOWN = 0	
RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070  	# [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA =  0.40      	# Complementary filter constant
MAG_LPF_FACTOR = 0.4 	# Low pass filter constant magnetometer
ACC_LPF_FACTOR = 0.4 	# Low pass filter constant for accelerometer
ACC_MEDIANTABLESIZE = 9    	# Median filter table size for accelerometer. Higher = smoother but a longer delay
MAG_MEDIANTABLESIZE = 9    	# Median filter table size for magnetometer. Higher = smoother but a longer delay

'''
magXmin =  -2699.0
magYmin =  -1794.0
magZmin =  -2741.0
magXmax =  3779.0
magYmax =  4401.0
magZmax =  3502.0

magXmax = 3613
magYmax = 2189
magZmax = -149
magXmin = -3735
magYmin = -4131
magZmin = -6594
'''
'''
magXmin = -2970.0
magXmax = 3633
magYmin = -4126
magYmax = 2092
magZmin = -7317
magZmax = -13
'''

magXmin = -2911
magXmax = 3433
magYmin = -3317
magYmax = 2932
magZmin = -2926
magZmax = 4189

Q_angle = 0.02
Q_gyro = 0.0015
R_angle = 0.005
y_bias = 0.0
x_bias = 0.0
XP_00 = 0.0
XP_01 = 0.0
XP_10 = 0.0
XP_11 = 0.0
YP_00 = 0.0
YP_01 = 0.0
YP_10 = 0.0
YP_11 = 0.0
KFangleX = 0.0
KFangleY = 0.0

def kalmanFilterY ( accAngle, gyroRate, DT):
	y=0.0
	S=0.0
	global KFangleY
	global Q_angle
	global Q_gyro
	global y_bias
	global YP_00
	global YP_01
	global YP_10
	global YP_11
	KFangleY = KFangleY + DT * (gyroRate - y_bias)
	YP_00 = YP_00 + ( - DT * (YP_10 + YP_01) + Q_angle * DT )
	YP_01 = YP_01 + ( - DT * YP_11 )
	YP_10 = YP_10 + ( - DT * YP_11 )
	YP_11 = YP_11 + ( + Q_gyro * DT )
	y = accAngle - KFangleY
	S = YP_00 + R_angle
	K_0 = YP_00 / S
	K_1 = YP_10 / S
	KFangleY = KFangleY + ( K_0 * y )
	y_bias = y_bias + ( K_1 * y )
	YP_00 = YP_00 - ( K_0 * YP_00 )
	YP_01 = YP_01 - ( K_0 * YP_01 )
	YP_10 = YP_10 - ( K_1 * YP_00 )
	YP_11 = YP_11 - ( K_1 * YP_01 )
	return KFangleY

def kalmanFilterX ( accAngle, gyroRate, DT):
	x=0.0
	S=0.0
	global KFangleX
	global Q_angle
	global Q_gyro
	global x_bias
	global XP_00
	global XP_01
	global XP_10
	global XP_11
	KFangleX = KFangleX + DT * (gyroRate - x_bias)
	XP_00 = XP_00 + ( - DT * (XP_10 + XP_01) + Q_angle * DT )
	XP_01 = XP_01 + ( - DT * XP_11 )
	XP_10 = XP_10 + ( - DT * XP_11 )
	XP_11 = XP_11 + ( + Q_gyro * DT )
	x = accAngle - KFangleX
	S = XP_00 + R_angle
	K_0 = XP_00 / S
	K_1 = XP_10 / S
	KFangleX = KFangleX + ( K_0 * x )
	x_bias = x_bias + ( K_1 * x )
	XP_00 = XP_00 - ( K_0 * XP_00 )
	XP_01 = XP_01 - ( K_0 * XP_01 )
	XP_10 = XP_10 - ( K_1 * XP_00 )
	XP_11 = XP_11 - ( K_1 * XP_01 )
	return KFangleX

gyroXangle = 0.0
gyroYangle = 0.0
gyroZangle = 0.0
CFangleX = 0.0
CFangleY = 0.0
CFangleXFiltered = 0.0
CFangleYFiltered = 0.0
kalmanX = 0.0
kalmanY = 0.0
oldXMagRawValue = 0
oldYMagRawValue = 0
oldZMagRawValue = 0
oldXAccRawValue = 0
oldYAccRawValue = 0
oldZAccRawValue = 0
a = datetime.datetime.now()

acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE
mag_medianTable1X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Z = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Z = [1] * MAG_MEDIANTABLESIZE

print("IMU start")
try:
    while True:
        while lib.lsm9ds1_gyroAvailable(imu) == 0:
            pass
        lib.lsm9ds1_readGyro(imu)
        while lib.lsm9ds1_accelAvailable(imu) == 0:
            pass
        lib.lsm9ds1_readAccel(imu)
        while lib.lsm9ds1_magAvailable(imu) == 0:
            pass
        lib.lsm9ds1_readMag(imu)
        gx = lib.lsm9ds1_getGyroX(imu)
        gy = lib.lsm9ds1_getGyroY(imu)
        gz = lib.lsm9ds1_getGyroZ(imu)

        ax = lib.lsm9ds1_getAccelX(imu)
        ay = lib.lsm9ds1_getAccelY(imu)
        az = lib.lsm9ds1_getAccelZ(imu)

        mx = lib.lsm9ds1_getMagX(imu)
        my = lib.lsm9ds1_getMagY(imu)
        mz = lib.lsm9ds1_getMagZ(imu)

        cgx = lib.lsm9ds1_calcGyro(imu, gx)
        cgy = lib.lsm9ds1_calcGyro(imu, gy)
        cgz = lib.lsm9ds1_calcGyro(imu, gz)

        cax = lib.lsm9ds1_calcAccel(imu, ax)
        cay = lib.lsm9ds1_calcAccel(imu, ay)
        caz = lib.lsm9ds1_calcAccel(imu, az)

        ACCx = cax
        ACCy = cay
        ACCz = caz
        GYRx = cgx
        GYRy = cgy
        GYRz = cgz
        MAGx = mx
        MAGy = my
        MAGz = mz
        MAGx -= (magXmin + magXmax) /2 
        MAGy -= (magYmin + magYmax) /2 
        MAGz -= (magZmin + magZmax) /2 
        b = datetime.datetime.now() - a
        a = datetime.datetime.now()
        LP = b.microseconds/(1000000*1.0)
        MAGx =  MAGx  * MAG_LPF_FACTOR + oldXMagRawValue*(1 - MAG_LPF_FACTOR);
        MAGy =  MAGy  * MAG_LPF_FACTOR + oldYMagRawValue*(1 - MAG_LPF_FACTOR);
        MAGz =  MAGz  * MAG_LPF_FACTOR + oldZMagRawValue*(1 - MAG_LPF_FACTOR);
        ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR);
        ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR);
        ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR);
        oldXMagRawValue = MAGx
        oldYMagRawValue = MAGy
        oldZMagRawValue = MAGz
        oldXAccRawValue = ACCx
        oldYAccRawValue = ACCy
        oldZAccRawValue = ACCz
        for x in range (ACC_MEDIANTABLESIZE-1,0,-1 ):
            acc_medianTable1X[x] = acc_medianTable1X[x-1]
            acc_medianTable1Y[x] = acc_medianTable1Y[x-1]
            acc_medianTable1Z[x] = acc_medianTable1Z[x-1]
        acc_medianTable1X[0] = ACCx
        acc_medianTable1Y[0] = ACCy
        acc_medianTable1Z[0] = ACCz    
        acc_medianTable2X = acc_medianTable1X[:]
        acc_medianTable2Y = acc_medianTable1Y[:]
        acc_medianTable2Z = acc_medianTable1Z[:]
        acc_medianTable2X.sort()
        acc_medianTable2Y.sort()
        acc_medianTable2Z.sort()
        ACCx = acc_medianTable2X[ACC_MEDIANTABLESIZE/2];
        ACCy = acc_medianTable2Y[ACC_MEDIANTABLESIZE/2];
        ACCz = acc_medianTable2Z[ACC_MEDIANTABLESIZE/2];
        for x in range (MAG_MEDIANTABLESIZE-1,0,-1 ):
            mag_medianTable1X[x] = mag_medianTable1X[x-1]
            mag_medianTable1Y[x] = mag_medianTable1Y[x-1]
            mag_medianTable1Z[x] = mag_medianTable1Z[x-1]
        mag_medianTable1X[0] = MAGx
        mag_medianTable1Y[0] = MAGy
        mag_medianTable1Z[0] = MAGz  
        mag_medianTable2X = mag_medianTable1X[:]
        mag_medianTable2Y = mag_medianTable1Y[:]
        mag_medianTable2Z = mag_medianTable1Z[:]
        mag_medianTable2X.sort()
        mag_medianTable2Y.sort()
        mag_medianTable2Z.sort()
        MAGx = mag_medianTable2X[MAG_MEDIANTABLESIZE/2];
        MAGy = mag_medianTable2Y[MAG_MEDIANTABLESIZE/2];
        MAGz = mag_medianTable2Z[MAG_MEDIANTABLESIZE/2];
        rate_gyr_x =  GYRx * G_GAIN
        rate_gyr_y =  GYRy * G_GAIN
        rate_gyr_z =  GYRz * G_GAIN
        gyroXangle+=rate_gyr_x*LP
        gyroYangle+=rate_gyr_y*LP
        gyroZangle+=rate_gyr_z*LP
        if not IMU_UPSIDE_DOWN:
            AccXangle =  (math.atan2(ACCy,ACCz)*RAD_TO_DEG)
            AccYangle =  (math.atan2(ACCz,ACCx)+M_PI)*RAD_TO_DEG
        else:
            AccXangle =  (math.atan2(-ACCy,-ACCz)*RAD_TO_DEG)
            AccYangle =  (math.atan2(-ACCz,-ACCx)+M_PI)*RAD_TO_DEG
        if AccYangle > 90:
            AccYangle -= 270.0
        else:
            AccYangle += 90.0
        CFangleX=AA*(CFangleX+rate_gyr_x*LP) +(1 - AA) * AccXangle
        CFangleY=AA*(CFangleY+rate_gyr_y*LP) +(1 - AA) * AccYangle
        kalmanY = kalmanFilterY(AccYangle, rate_gyr_y,LP)
        kalmanX = kalmanFilterX(AccXangle, rate_gyr_x,LP)
        if IMU_UPSIDE_DOWN:
            MAGy = -MAGy     
        heading = 180 * math.atan2(MAGy,MAGx)/M_PI
        if heading < 0:
            heading += 360
        if not IMU_UPSIDE_DOWN:        
            accXnorm = ACCx/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
            accYnorm = ACCy/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
        else:
            accXnorm = -ACCx/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
            accYnorm = ACCy/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
        pitch = math.asin(accXnorm)
        roll = -math.asin(accYnorm/math.cos(pitch))
        magXcomp = MAGx*math.cos(pitch)+MAGz*math.sin(pitch)
        magYcomp = MAGx*math.sin(roll)*math.sin(pitch)+MAGy*math.cos(roll)+MAGz*math.sin(roll)*math.cos(pitch)
        tiltCompensatedHeading = 180 * math.atan2(magYcomp,magXcomp)/M_PI
        if tiltCompensatedHeading < 0:
            tiltCompensatedHeading += 360
        #try out kalmanX too
        out = -1 * int(kalmanY)
        if out < -90:
            out = -90
        elif out > 90:
            out = 90
        cli.set("anglez", int(tiltCompensatedHeading))
        cli.set("anglex", out)
#        print ("Heading: " + str(int(heading)) + " " +  "tiltCompensatedHeading " +  str(int(tiltCompensatedHeading)) + " KalmanX " + str(out) + "\n")
        time.sleep(0.03)

except:
    lib.close()
    print("IMU Closed")
