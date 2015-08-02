##############################################
#
# CanSat Client Software 
# For use with launch of CanSat:
#   UCD, Space Science Masters, 2014
#
##############################################

import time
import serial
import logging
from xbee import XBee
from serial import SerialException

class transceiver():
    devName = None
    serialPath = None
    receiveTimeout = 15

    # Initialize the serial connection - then use some commands I saw somewhere once
    def __init__(self, serialPath, name, baud):
        self.devName = name
        self.lastReceive = time.time()
        self.serialPath = serialPath
        self.baud = baud

        self.openConn()
            
        logging.debug("Initialized transceiver (%s) at BaudRate: %s" % (name, baud))

    def readTelem(self):
        dataString = None
        try:
            dataString = self.SDEV.readline()
        except Exception, e:
            logging.warning(e)
            self.reset()
        # if the dataString was empty, and we haven't received something in a while.. reset
        if (not dataString or dataString == ''): 
            self.reset()
        return dataString

    def requestRepeat(self, index):
        requestStr = "RT:%s" % index
        self.transmit(requestStr)

    def reset(self):
        pass

    def transmit(self, msg):
        csum = 0
        for c in msg:
            csum ^= ord(c)
        msg = "%s*%s" % (msg, chr(csum))
        try:
            self.SDEV.write(msg)
            return True
        except SerialException, e:
            logging.warning(e)
            self.reset()

    def openConn(self):
        logging.info("Opening Serial for %s" % self.devName)
        try:
            ser = serial.Serial(self.serialPath, 9600)
            xbee = XBee(ser)
            self.SDEV = xbee.serial
        except:
            logging.error("No Serial device found at path: %s. Retrying in 10 seconds" % self.serialPath)
            self.SDEV = None
            time.sleep(10)

    def close(self):
        logging.info("Closing Serial for %s" % self.devName)
        self.SDEV.close()

#---------- END CLASS -------------
