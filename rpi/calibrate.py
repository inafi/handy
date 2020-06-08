from ctypes import *
import time
from redis import Redis
from math import *

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

magXmax = -32767
magYmax = -32767
magZmax = -32767
magXmin = 32767
magYmin = 32767
magZmin = 32767

if __name__ == "__main__":
    imu = lib.lsm9ds1_create()
    lib.lsm9ds1_begin(imu)
    if lib.lsm9ds1_begin(imu) == 0:
        print("Failed to communicate with LSM9DS1.")
        quit()
    lib.lsm9ds1_calibrate(imu)
    x = 0
    y = 0
    z = 0
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

        cmx = lib.lsm9ds1_calcMag(imu, mx)
        cmy = lib.lsm9ds1_calcMag(imu, my)
        cmz = lib.lsm9ds1_calcMag(imu, mz)

        magRaw = [mx, my, mz]

        if (magRaw[0] > magXmax): 
            magXmax = magRaw[0]
        if (magRaw[1] > magYmax): 
            magYmax = magRaw[1]
        if (magRaw[2] > magZmax): 
            magZmax = magRaw[2]
        if (magRaw[0] < magXmin): 
            magXmin = magRaw[0]
        if (magRaw[1] < magYmin): 
            magYmin = magRaw[1]
        if (magRaw[2] < magZmin): 
            magZmin = magRaw[2]

        print(magXmin, magXmax, magYmin, magYmax, magZmin, magZmax)
