##############################################
#
# GliderV2 Client Software 
# Author: Daniel Vagg
# 
##############################################
import log
import time
import serial
import logging
from xbee import XBee
from threading import Thread

# GUIDE
# http://ava.upuaut.net/?p=768

##########################################
# GLOBALS
##########################################
LOG = log.setup_custom_logger('radio')
LOG.setLevel(logging.WARN)

class Transceiver():
    def __init__(self, serialPath, baud, timeout=.5, datahandler=None, telemInterval=1):
        self.threadAlive = True
        
        self.datahandler = datahandler
        self.serialPath = serialPath
        self.readTimeout = timeout
        self.baud = baud
        self.xbee = None
        
        self.openConn()

    def reset(self):
        pass

    def getChecksum(self, strmsg):
        csum = 0
        for c in strmsg:
            csum ^= ord(c)
        return chr(csum)

    def write(self, msg):
        msg = "%s*%s\n" % (msg, self.getChecksum(msg))
        try:
            LOG.debug("Sending: '%s'" % msg.rstrip())
            self.xbee.serial.write(msg)
            return True
        except Exception, e:
            LOG.error(e)
            self.reset()

    def openConn(self):
        LOG.info("Opening Serial")
        while not self.xbee:
            try:
                ser = serial.Serial(self.serialPath, 9600, timeout=self.readTimeout)
                self.xbee = XBee(ser)
                LOG.debug("Initialized transceiver at BaudRate: %s" % (self.baud))
            except Exception, e:
                LOG.error(e)
                LOG.error("Error while using serial path: %s. Retrying.." % self.serialPath)
                time.sleep(1)

    def readLoop(self):
        while self.threadAlive:
            try:
                msg = self.xbee.serial.readline()
                msg = msg.rstrip() # Remove the newline part
                if msg and self.datahandler:
                    LOG.debug("Received: %s" % msg)
                    # Validate the message
                    msgparts = msg.split("*")
                    chksum = msgparts[-1]
                    msgtxt = "".join(msgparts[:-1])
                    calcsum = self.getChecksum(msgtxt)
                    if calcsum == chksum:
                        LOG.debug("Checksum validated (%s - %s) (%s)" % (calcsum, chksum, msg))
                        self.datahandler(msgtxt)
                    else:
                        LOG.warning("Checksum mismatch (%s - %s) (%s)" % (calcsum, chksum, msg))
            except Exception, e:
                LOG.error(e)

    def start(self):
        LOG.info("Starting RADIO thread")
        threadR = Thread( target=self.readLoop, args=() )
        self.threadAlive = True
        threadR.start()

    def stop(self):
        self.threadAlive = False

    def close(self):
        LOG.info("Closing Serial")
        self.xbee.serial.close()

#---------- END CLASS -------------
