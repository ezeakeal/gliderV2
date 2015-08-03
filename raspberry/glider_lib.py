import sys
import log
import json
import math
import types
import RTIMU
import serial
import logging
import datetime, time

import glider_ATMegaController as controller
from glider_gps import GPS_I2C
from glider_radio import Transceiver
from glider_pilot import Pilot

import RPi.GPIO as GPIO  
# http://raspi.tv/2013/automatic-exposure-compensation-testing-for-the-pi-camera
# http://bytingidea.com/2014/12/11/raspberry-pi-powered-long-exposures/

LOG = log.setup_custom_logger('glider_lib')
LOG.setLevel(logging.WARN)

##############################################
# ORIENTATION WAKE UP
##############################################
# For some reason, if I put this in a function
# it doesn't initialise correctly.. well it does
# but I can't read anything from it after!
SETTINGS_FILE = "RTIMULib"
s = RTIMU.Settings(SETTINGS_FILE)
O_IMU = RTIMU.RTIMU(s)
if (not O_IMU.IMUInit()):
    sys.exit(1)
else:
    LOG.info("IMU Init Succeeded")


##########################################
# FUNCTION - Received instruction!
##########################################
def dataHandler(packet):
    global OVERRIDE_STATE
    LOG.info("Data packet recieved: %s" % packet)
    packetParts = packet.split("_")
    LOG.info("Data parts: %s" % packetParts)
    instruct = packetParts[0]
    data = packetParts[1:]
    if instruct == "O":
        setOverrideState("_".join(data))
    if instruct == "PA":
        setPitchAngle(data[0])


##########################################
# GLOBALS
##########################################
LED_RUNNING = 11
STATE       = "OK"
LAST_LOC    = {}
GPS         = GPS_I2C(fakeData='$GNGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47')
RADIO       = Transceiver("/dev/ttyAMA0", 9600, datahandler=dataHandler)
PILOT       = Pilot(O_IMU, desired_pitch=0)

OVERRIDE_STATE = None

##########################################
# FUNCTIONS - UTILITY
##########################################
def startUp():
    LOG.info("Starting up")
    # Reset the SPI interface for some reason..
    controller.reset_spi()
    # Set up some flashy lights
    GPIO.setmode(GPIO.BOARD)  
    GPIO.setup(LED_RUNNING, GPIO.OUT)
    # Start GPS thread
    GPS.start()
    # Start Radio thread
    RADIO.start()
    # Start the Pilot
    PILOT.start()


def shutDown():
    LOG.info("Shutting down")
    GPS.stop()
    RADIO.stop()
    PILOT.stop()


def alert(msg):
    text = str(msg)


def getOverrideState():
    LOG.info("Returning state: %s" % OVERRIDE_STATE)
    return OVERRIDE_STATE


def setOverrideState(newstate):
    global OVERRIDE_STATE
    LOG.info("Setting override state: %s" % newstate)
    OVERRIDE_STATE = newstate
 

def setPitchAngle(newAngle):
    try:
        angle = math.radians(float(newAngle))
        PILOT.updatePitch(angle)
    except Exception, e:
        LOG.error(e)

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
# FUNCTIONS - Standard Operations
##########################################
def getBatteryStatus():
    status = {
        "health":True, 
        "level":None, 
        "temp":None
    }
    return status


def getLocation():
    gpsData = GPS.getData()
    return gpsData


def sendTelem(msg=""):
    try:
        orient = None
        orient = "%02d %02d %02d" % (degrees(orient['yaw']), degrees(orient['pitch']), degrees(orient['roll']))
        loc = "%s %s %s" % (LAST_LOC['latitude'], LAST_LOC['longitude'], LAST_LOC['altitude'])
        dest = "%s %s" % (DEST_COORD[0], DEST_COORD[1])
        battData = getBatteryStatus()
        telemMsg = "%s::T:(%s)\nO:(%s)\nL(%s)\nD(%s)\nB(%s)\nC(%s)" % (msg, time.time(), orient, loc, dest, battData['level'], battData['temp'])
        sendMessage(telemMsg)
    except:
        pass


def sendMessage(msg):
    RADIO.write(msg)


def updatePilotLocation(location):
    PILOT.updateCurrentLocation(location)


def getPilotWingCommand():
    wingAngles = PILOT.get_servo_angles()
    return wingAngles


#################
# WING MOVEMENTS
#################
def center_wings():
    lcenter, rcenter, servoRange = PILOT.getWingCenterAndRange()
    setWingAngle([lcenter, rcenter])


def min_wings():
    lcenter, rcenter, servoRange = PILOT.getWingCenterAndRange()
    setWingAngle([lcenter-servoRange, rcenter-servoRange])


def max_wings():
    lcenter, rcenter, servoRange = PILOT.getWingCenterAndRange()
    setWingAngle([lcenter+servoRange, rcenter+servoRange])
    

def setWingAngle(angles):
    leftAngle = angles[0]
    rightAngle = angles[1]
    LOG.debug("Setting: %d %d" % (leftAngle, rightAngle))
    controller.W_glider_command("W:%s:%s" % (leftAngle, rightAngle))


########################
# Release Chute/Balloon
########################
def releaseChord():
    controller.release()


def releaseParachute():
    controller.releaseChute()

