import sys
import time
import json
import smbus
import logging 
from threading import Thread
# GUIDE
# http://ava.upuaut.net/?p=768

class XbeeRadio():
    """
    XbeeRadio class
    """
    def __init__(self):
        self.read_interval = .5
        pass

    def readLoop(self):
        while self.threadAlive:
            # self.readGPS()
            time.sleep(self.read_interval)

    def start(self):
        LOG.info("Starting GPS thread")
        readThread = Thread( target=self.readLoop, args=() )
        self.threadAlive = True
        readThread.start()

    def stop(self):
        self.threadAlive = False

def setup_custom_logger(name=None, loglevel=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler.setFormatter(formatter)
    logger.setLevel(loglevel)
    logger.addHandler(handler)
    return logger

##########################################
# GLOBALS
##########################################
LOG = setup_custom_logger("radio", loglevel=logging.ERROR)