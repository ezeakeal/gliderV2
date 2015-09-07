import log
import time
import math
import RTIMU
import logging
import traceback
from threading import Thread

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('imu')
LOG.setLevel(logging.DEBUG)

SETTINGS_FILE = "RTIMULib"
s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)

class IMU(object):
    """
    IMU class for obtaining orientation data
    """

    def __init__(self, lock=None):
        self.O_IMU = imu
        self.lock = lock
        
        self.imu_reset_interval = 5000
        self.threadAlive = False
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

        self.imu_init()
        
    def imu_init(self):
        self.O_IMU.setSlerpPower(0.02)
        self.O_IMU.setGyroEnable(True)
        self.O_IMU.setAccelEnable(True)
        self.O_IMU.setCompassEnable(True)
        self.poll_interval = self.O_IMU.IMUGetPollInterval()
        LOG.info("Recommended Poll Interval: %dmS\n" % self.poll_interval)

    def start(self):
        sensorThread = Thread( target=self.updateOrientation, args=() )
        self.threadAlive = True
        LOG.info("Starting up orienation thread now")
        sensorThread.start()

    def stop(self):
        self.threadAlive = False

    def updateOrientation(self):
        time_reset = 0
        time_last = 0
        while self.threadAlive:
            time_now = time.time() * 1000

            if (time_now - time_reset > self.imu_reset_interval):
                time_reset = time_now
                self.O_IMU.IMUInit()
                self.O_IMU.resetFusion()
                
            while self.lock.get_locked():
                LOG.info("Waiting for unlock")
                time.sleep(0.1) # Wait for it to unlock
            
            if (time_now - time_last > self.poll_interval):
                time_last = time_now
                if self.O_IMU.IMURead():
                    p,r,y = self.O_IMU.getFusionData()
                    self.pitch = p
                    self.roll = r
                    self.yaw = y
                    LOG.debug("p: %f r: %f y: %f" % (
                        math.degrees(p), math.degrees(r), math.degrees(y))
                    )
            time.sleep(1.0/1000.0)