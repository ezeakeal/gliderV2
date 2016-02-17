import log
import time
import math
import redis
import logging
import traceback
from threading import Thread

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('imu')
LOG.setLevel(logging.WARNING)

class IMU(object):

    """
    IMU class for obtaining orientation data
    """

    def __init__(self, poll_interval_ms=10.):
        self.threadAlive = False
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.poll_interval_ms = poll_interval_ms
        self.setup_redis_conn()

    def setup_redis_conn(self):
        self.redis_client = redis.StrictRedis(
            host="127.0.0.1",
            port=6379,
            db=0
        )

    def start(self):
        readerThread = Thread(target=self.readRedisOrientation, args=())
        LOG.info("Starting up orienation reader thread now")
        self.threadAlive = True
        readerThread.start()

    def stop(self):
        self.threadAlive = False

    def readRedisOrientation(self):
        while self.threadAlive:
            self.pitch = float(self.redis_client.get("r")) # Switched because I mounted the chip wrong..
            self.roll = float(self.redis_client.get("p")) 
            self.yaw = float(self.redis_client.get("y"))
            LOG.debug("p: %f r: %f y: %f" % (
                math.degrees(self.pitch), math.degrees(self.roll), math.degrees(self.yaw))
            )
            time.sleep(self.poll_interval_ms/1000.0)
