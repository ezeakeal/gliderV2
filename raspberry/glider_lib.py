import sys
import json
import types
import serial
import logging
import datetime, time

import glider_ATMegaController as controller
from glider_gps import GPS_I2C
from glider_radio import XbeeRadio

import RPi.GPIO as GPIO  
# http://raspi.tv/2013/automatic-exposure-compensation-testing-for-the-pi-camera
# http://bytingidea.com/2014/12/11/raspberry-pi-powered-long-exposures/

##########################################
# GLOBALS
##########################################
LOG         = None
LED_RUNNING = 11
STATE       = "OK"
LAST_LOC    = {}
GPS         = GPS_I2C(fakeData=True)
RADIO       = XbeeRadio()

##########################################
# FUNCTIONS - UTILITY
##########################################
def startUp():
    LOG.info("Starting up")
    # Set up some flashy lights
    GPIO.setmode(GPIO.BOARD)  
    GPIO.setup(LED_RUNNING, GPIO.OUT)
    # Start GPS thread
    GPS.start()
    # Connect Serial
    RADIO.start()


def shutDown():
    LOG.info("Shutting down")
    GPS.stop()


def alert(msg):
    text = str(msg)


def speak(text):
    LOG.info("Speaking %s" % text)


def logLocation(location, orientation):
    logStr = "%s %s %s %s %s %s %s" % (
        datetime.datetime.now(),
        location['longitude'], location['latitude'], location['altitude'], 
        degrees(orientation[0]), degrees(orientation[1]), degrees(orientation[2])
    )
    LOG.info(logStr)


##########################################
# FUNCTIONS - GET - DROID
##########################################
def getBatteryStatus():
    status = {
        "health":True, 
        "level":None, 
        "temp":None
    }
    return status


def getLocation():
    global GPS
    location = GPS.gps_data
    return location


def sendTelem(msg=""):
    try:
        orient = None
        orient = "%02d %02d %02d" % (degrees(orient['yaw']), degrees(orient['pitch']), degrees(orient['roll']))
        loc = "%s %s %s" % (LAST_LOC['latitude'], LAST_LOC['longitude'], LAST_LOC['altitude'])
        dest = "%s %s" % (DEST_COORD[0], DEST_COORD[1])
        battData = getBatteryStatus()
        telemMsg = "%s::T:(%s)\nO:(%s)\nL(%s)\nD(%s)\nB(%s)\nC(%s)" % (msg, time.time(), orient, loc, dest, battData['level'], battData['temp'])
        LOG.debug("Sending message to (%s) : %s" % (PHONEHOME, telemMsg))
        sendMessage(telemMsg)
    except:
        pass

def sendMessage(msg):
    pass


def setWingAngle(leftAngle, rightAngle):
    LOG.debug("Setting: %02d %02d" % (leftAngle, rightAngle))
    controller.setWing(leftAngle, rightAngle)


def releaseChord():
    controller.release()


def releaseParachute():
    controller.releaseChute()



def setup_custom_logger(name=None, loglevel=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler.setFormatter(formatter)
    logger.setLevel(loglevel)
    logger.addHandler(handler)
    return logger

LOG = setup_custom_logger('glider_lib', loglevel=logging.DEBUG)