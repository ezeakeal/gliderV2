import log
import sys
import time
import json
import smbus
import logging
from threading import Thread
# GUIDE
# http://ava.upuaut.net/?p=768

LOG = log.setup_custom_logger("GPS")
LOG.setLevel(logging.ERROR)

class GPS_I2C(object):
    """
    GPS class using I2C comms with Blox-M8
    """
    def __init__(self, address=0x42, gpsReadInterval=0.1, busChannel=1, fakeData=False):
        self.address = address
        self.gps_read_interval = gpsReadInterval
        self.bus_channel = busChannel
        self.fake_data = fakeData
        self.gps_data = {
            'strType': None,
            'fixTime': None,
            'lat': None,
            'latDir': None,
            'lon': None,
            'lonDir': None,
            'fixQual': None,
            'numSat': None,
            'horDil': None,
            'alt': None,
            'altUnit': None,
            'galt': None,
            'galtUnit': None,
            'DPGS_updt': None,
            'DPGS_ID': None
        }
        self.bus = None
        self.connectBus()
        self.threadAlive = False

    def connectBus(self):
        LOG.info("Connecting GPS bus")
        self.bus = smbus.SMBus(self.bus_channel)

    def readGPS(self):
        LOG.info("Reading GPS data")
        c = None
        response = []
        try:
            while True:
                c = self.bus.read_byte(self.address)
                if c == 255: # badchar
                    return False # something has gone wrong
                elif c == 10: # newline
                    break # Stop now, and go parse something
                else:
                    response.append(c)
            if self.parseResponse(response):
                LOG.info("GPS has been parsed successfully")
            else:
                LOG.warning("GPS was received, but invalid")
                LOG.info("".join(chr(x) for x in response))
        except IOError:
            LOG.error("Bus got IOError, reconnecting")
            time.sleep(0.5)
            self.connectBus()
        except Exception, e:
            LOG.error(e)

    def parseResponse(self, gpsLine):
        gpsChars = ''.join(chr(c) for c in gpsLine)
        # Check if gps data is to be faked, and if not check if we have a * in it
        if self.fake_data:
            gpsChars = self.fake_data
        if "*" not in gpsChars:
            return False # We need to find this char to get the chksum val..
        # Split up GPS components
        gpsStr, chkSum = gpsChars.split('*')
        gpsComponents = gpsStr.split(',')
        gpsStart = gpsComponents[0]
        # Read in the GPS data
        if (gpsStart == "$GNGGA"):
            chkVal = 0
            for ch in gpsStr[1:]: # Remove the $
                chkVal ^= ord(ch)
            if (chkVal == int(chkSum, 16)):
                # Seems the checksum is good
                for i, k in enumerate(
                    ['strType', 'fixTime',
                    'lat', 'latDir', 'lon', 'lonDir',
                    'fixQual', 'numSat', 'horDil',
                    'alt', 'altUnit', 'galt', 'galtUnit',
                    'DPGS_updt', 'DPGS_ID']):
                    self.gps_data[k] = gpsComponents[i]
                return True
            else:
                LOG.warning("Bad checksum in GPS datastring")
                return False

    def readLoop(self):
        while self.threadAlive:
            self.readGPS()
            time.sleep(self.gps_read_interval)

    def start(self):
        LOG.info("Starting GPS thread")
        readThread = Thread( target=self.readLoop, args=() )
        self.threadAlive = True
        readThread.start()

    def stop(self):
        self.threadAlive = False

    def getData(self):
        return self.gps_data
