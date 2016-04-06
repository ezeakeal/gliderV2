import os
import log
import logging

from gps import *
from time import *
from threading import Thread

# GUIDE
# http://ava.upuaut.net/?p=768

LOG = log.setup_custom_logger("GPS")
LOG.setLevel(logging.WARN)


class GPS_USB(object):

    def __init__(self):
        self.gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info

    def poll_gps(self):
        while self.threadAlive:
            self.gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
            LOG.debug("GPS data:")
            LOG.info('Error     %s %s' % (self.gpsd.fix.epx, self.gpsd.fix.epy))
            LOG.debug('latitude     %s' % self.gpsd.fix.latitude)
            LOG.debug('longitude    %s' % self.gpsd.fix.longitude)
            LOG.debug('time utc     %s + %s' % (self.gpsd.utc, self.gpsd.fix.time))
            LOG.debug('altitude (m) %s' % self.gpsd.fix.altitude)
 
    def start(self):
        pilotThread = Thread( target=self.poll_gps, args=() )
        self.threadAlive = True
        LOG.info("Starting up GPS thread now")
        pilotThread.start()

    def stop(self):
        self.threadAlive = False

    def getFix(self):
        return self.gpsd.fix

    def _parse_fucked_gps_val(self, val):
        return val
        # Apparently it was coming in fine!
        val_deg = int(val/100)
        val_min = val % 100
        return val_deg + (val_min/60)

    def getLonLatDeg(self):
        fucked_lat = self.gpsd.fix.latitude
        fucked_lon = self.gpsd.fix.longitude
        lat = self._parse_fucked_gps_val(fucked_lat)
        lon = self._parse_fucked_gps_val(fucked_lon)
        return lon, lat

    def getTime(self):
        return self.gpsd.utc