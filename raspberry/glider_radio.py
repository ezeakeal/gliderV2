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
from sat_radio import SatRadio

# GUIDE
# http://ava.upuaut.net/?p=768

##########################################
# GLOBALS
##########################################
LOG = log.setup_custom_logger('radio')
LOG.setLevel(logging.DEBUG)

class GliderRadio(SatRadio):
    
    def __init__(self, port, callsign, baud_rate=115200, callback=None):
        self.ready = True
        SatRadio.__init__(self, port, callsign, baud_rate=baud_rate, callback=callback)

    def send_data(self, data):
        LOG.debug("Sending Data: %s" % data)
        address = self.ADDR_GLIDER_GROUNDSTATION
        packet = "|".join(["D"] + data)
        self.send_packet(packet, address=address, mode=self.MODE_P2P)

    def sendImage(self, image_path):
        LOG.debug("Sending Image: %s" % image_path)
        # Start
        self.send_packet("I|S|%s" % image_path, address=address, mode=self.MODE_P2P)
        with open(image_path, "r") as image:
            while True:
                data = image.read(250)  
                if not piece:
                    break
                # Part
                packet = "I|P|%s" % data
                self.send_packet(packet, address=address, mode=self.MODE_P2P)
        # End
        self.send_packet("I|E" % image_path, address=address, mode=self.MODE_P2P)

#---------- END CLASS -------------
