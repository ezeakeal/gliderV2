import sys
import types
import datetime, time
import json
import logging
from math import *

import glider_ATMegaController as controller
try:
    import RPi.GPIO as GPIO  
except:
    print "RPi.GPIO can't be imported"
# http://raspi.tv/2013/automatic-exposure-compensation-testing-for-the-pi-camera
# http://bytingidea.com/2014/12/11/raspberry-pi-powered-long-exposures/

##########################################
# GLOBALS
##########################################
STATE       = "OK"
LOG         = logging.getLogger('glider_lib')

##########################################
# FUNCTIONS - UTILITY
##########################################
def startUp():
    if (GPIO):
        GPIO.setmode(GPIO.BOARD)  
        GPIO.setup(LED_RUNNING, GPIO.OUT)

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
    return {
        "health":None, 
        "level":None, 
        "temp":None
    }


def getLocation():
    global LOCATION
    location = {}
    # READ the gps data from the chip
    # parse it
    # then set it here..
    LOCATION = location 


def sendRadio(msg=""):
    try:
        orient = None
        orient = "%02d %02d %02d" % (degrees(orient['yaw']), degrees(orient['pitch']), degrees(orient['roll']))
        loc = "%s %s %s" % (LOCATION['latitude'], LOCATION['longitude'], LOCATION['altitude'])
        dest = "%s %s" % (DEST_COORD[0], DEST_COORD[1])
        battData = getBatteryStatus()
        textMsg = "%s::T:(%s)\nO:(%s)\nL(%s)\nD(%s)\nB(%s)\nC(%s)" % (msg, time.time(), orient, loc, dest, battData['level'], battData['temp'])
        LOG.debug("Sending message to (%s) : %s" % (PHONEHOME, textMsg))
        # DROID.smsSend(PHONEHOME,textMsg)
    except:
        pass


def setWingAngle(leftAngle, rightAngle):
    LOG.debug("Setting: %02d %02d" % (leftAngle, rightAngle))
    controller.setWing(leftAngle, rightAngle)


def releaseChord():
    controller.release()


def releaseParachute():
    controller.releaseChute()


