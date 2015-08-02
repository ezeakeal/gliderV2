##############################################
#
# CanSat Client Software 
# For use with launch of CanSat:
#   UCD, Space Science Masters, 2014
#
##############################################
#!/usr/bin/python

import os
import sys
import time
import json
import signal
import logging
import argparse
import traceback

import cSat_listener as listener
import cSat_analyser as analyser
from cSat_transceiver import transceiver

#####################################
# GLOBALS
#####################################
AUTO_RESTART = False

TMINUS_DEV = {
    "NAME": "TMINUS",
    "COMM": None,
    "PATH": None,
    "XBEE": False,
    "DATA": "./data/tminus.dat",
    "RAW": "./data/tminus.raw",
    "BAUDRATE": 19200
}

XBEE_DEV = {
    "NAME": "XBEE",
    "COMM": None,
    "PATH": None,
    "XBEE": True,
    "DATA": "./data/xbee.dat",
    "RAW": "./data/xbee.raw",
    "BAUDRATE": 9600
}

#####################################
# FUNCTIONS
#####################################
def initialize():
    global TMINUS_DEV, XBEE_DEV

    # Initialize the iBus interface or wait for it to become available.
    for device in [TMINUS_DEV, XBEE_DEV]:
        while device["COMM"] == None:
            if os.path.exists(device["PATH"]):
                device['COMM'] = transceiver(device["PATH"], device["NAME"], device["BAUDRATE"], xb=device["XBEE"])
                listener.DEVICES.append(device)
                analyser.DEVICES.append(device)
            else:
                logging.warning("Interface not found at (%s). Waiting 2 seconds.", (device["NAME"], device["PATH"]))
                time.sleep(2)

    listener.load_listeners()
    analyser.initialize()


def shutdown():
    global TMINUS_DEV, XBEE_DEV

    listener.stop_listening()

    for device in [TMINUS_DEV, XBEE_DEV]:
        if device['COMM']:
            logging.info("Killing %s interface" % (device['NAME']))
            device['COMM'].close()
            device['COMM'] = None


def run():
    listener.start_listening()
    print "Running"
    while listener.RUN:
        try:
            lastCompletePacket = analyser.getLastComplete()
            lastCompleteGPSPacket = analyser.getLastCompleteGPS()
            if lastCompletePacket:
                print "Last Packet Index: %s\t Pressure: (%s) Thermister: (%s) Temperature: (%s)" % (lastCompletePacket['index'], 
                    lastCompletePacket['pressure'], lastCompletePacket['thermister'], lastCompletePacket['temperature'])
            else:
                print "NO DATA YET"
            if lastCompleteGPSPacket and lastCompleteGPSPacket.get("gpsEpoch"):
                print "Last GPS Fix Time (UTC): %s" % time.strftime('%m/%d/%Y %H:%M:%S',  time.localtime(lastCompleteGPSPacket.get('gpsEpoch')))
            if lastCompleteGPSPacket and lastCompleteGPSPacket.get('gps', {}).get('lat'):
                print "Last GPS Index: %s\tCoordinate: %03.4f, %03.4f\tAltitude: %s" % (lastCompleteGPSPacket.get('index'), 
                        lastCompleteGPSPacket.get('gps', {}).get('lat'), lastCompleteGPSPacket.get('gps', {}).get('lon'), lastCompleteGPSPacket.get('gps', {}).get('alt'))
            print ""
            analyser.outputPredictData()
            analyser.updateCanSatPath()
            analyser.updateMap()
        except Exception, e:
            print "ERROR: %s" % e
            traceback.print_exc(file=sys.stdout)
        time.sleep(.5)
