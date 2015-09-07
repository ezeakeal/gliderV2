import log
import time
import math
import logging
import traceback

from glider_imu import IMU
from glider_gps import GPS_I2C
from glider_lib import I2C_LOCK

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('test')
LOG.setLevel(logging.WARN)

LOCK        = I2C_LOCK() # Lock between I2C devices
ORIENT      = IMU(lock=LOCK)
GPS         = GPS_I2C(lock=LOCK, fakeData='$GNGGA,123519,5327.344,N,00777.830,E,1,08,0.9,545.4,M,46.9,M,,*57')


def startUp():
    LOG.info("Starting up")
    ORIENT.start()
    GPS.start()


def shutDown():
    LOG.info("Shutting down")
    GPS.stop()
    ORIENT.stop()


if __name__ == '__main__':
    startUp()
    while True:
        try:
            time.sleep(.05)
            print "Current Orientation | R:%03.02f P:%03.02f Y:%03.02f" % (
                math.degrees(ORIENT.roll), 
                math.degrees(ORIENT.pitch), 
                math.degrees(ORIENT.yaw)
            )
        except KeyboardInterrupt:
            shutDown()
            break
        except:
            print traceback.print_exc()
