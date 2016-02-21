import log
import sys
import time
import json
import smbus
import logging
import traceback
from threading import Thread
# GUIDE
# http://ava.upuaut.net/?p=768

LOG = log.setup_custom_logger("GPS")
LOG.setLevel(logging.DEBUG)


class GPS_USB(object):

    def __init__(self):
        threading.Thread.__init__(self)
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        self.current_value = None
        self.running = True #setting the thread running to true
 

    def run(self):
        global gpsd
        while gpsp.running:
            # this will continue to loop and grab EACH set of gpsd info to clear the buffer
            gpsd.next()


    def start(self):
        pilotThread = Thread( target=self.updateIntendWingAngle, args=() )
        self.threadAlive = True
        LOG.info("Starting up Pilot thread now")
        pilotThread.start()


    def stop(self):
        self.threadAlive = False


    def getData(self):
        pass