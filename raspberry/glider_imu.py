import log
import time
import math
import logging
from threading import Thread

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('imu')
LOG.setLevel(logging.WARN)


class IMU(object):
    """
    IMU class for obtaining orientation data
    """

    def __init__(self, O_IMU):
        self.O_IMU = O_IMU
        self.threadAlive = False
        self.configureOrientationChip()
        
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        
        self.poll_interval = self.getOrientPollInterval()

    def getOrientPollInterval(self):
        poll_interval = self.O_IMU.IMUGetPollInterval()
        LOG.info("Recommended Poll Interval: %dmS\n" % poll_interval)
        return poll_interval

    def configureOrientationChip(self):
        self.O_IMU.setSlerpPower(0.02)
        self.O_IMU.setGyroEnable(True)
        self.O_IMU.setAccelEnable(True)
        self.O_IMU.setCompassEnable(True)

    def start(self):
        sensorThread = Thread( target=self.updateOrientation, args=() )
        self.threadAlive = True
        LOG.info("Starting up orienation thread now")
        sensorThread.start()

    def stop(self):
        self.threadAlive = False

    def updateOrientation(self):
        while self.threadAlive:
            if self.O_IMU.IMURead():
                data = self.O_IMU.getIMUData()
                fusionPose = data["fusionPose"]
                ######## NOTE: THIS MUST BE INSPECTED! CHECK THIS IS RIGHT!
                self.roll = fusionPose[1]
                self.pitch = fusionPose[0]
                self.yaw = fusionPose[2]
                LOG.debug("r: %f p: %f y: %f" % (
                    math.degrees(self.roll), math.degrees(self.pitch), math.degrees(self.yaw))
                )
            time.sleep(self.poll_interval*1.0/1000.0)