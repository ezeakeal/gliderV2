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

from glider_imu import IMU
from glider_gps import GPS_I2C
from glider_pilot import Pilot
from glider_radio import Transceiver
from glider_telem import TelemetryHandler

import RPi.GPIO as GPIO  

# http://raspi.tv/2013/automatic-exposure-compensation-testing-for-the-pi-camera
# http://bytingidea.com/2014/12/11/raspberry-pi-powered-long-exposures/

LOG = log.setup_custom_logger('glider_lib')
LOG.setLevel(logging.WARN)


##########################################
# CLASS - I2C bus locker
# Reading GPS data while reading IMU data
# causes a data shiticane
##########################################
class I2C_LOCK(object):
    def __init__(self):
        self.locked = False

    def lock(self):
        LOG.debug("Locking I2C")
        if not self.locked:
            self.locked = True
            return True
        else:
            LOG.warning("Attempted to lock I2C but already locked")
            return False

    def unlock(self):
        LOG.debug("Unlocking I2C")
        if self.locked:
            self.locked = False
            return True
        else:
            LOG.warning("Attempted to unlock I2C but already unlocked")
            return False

    def get_locked(self):
        LOG.debug("Returning lock status: %s" % self.locked)
        return self.locked


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
    if instruct == "TS":
        setTurnSeverity(data[0])
    if instruct == "DEST":
        setDestination(data[0], data[1])


##########################################
# GLOBAL COMPONENTS 
##########################################
##############################################
# ORIENTATION WAKE UP
# wake up
# aibpidbgpagd shake up
# shake up
# iopubadgaebadg make up
# make up
# ....
# YOU WANTED TO!
##############################################
LOCK        = I2C_LOCK() # Allows GPS to lock I2C bus 
ORIENT      = IMU(lock=LOCK)
GPS         = GPS_I2C(lock=LOCK, fakeData='$GNGGA,123519,5327.344,N,00777.830,E,1,08,0.9,545.4,M,46.9,M,,*57')
RADIO       = Transceiver("/dev/ttyAMA0", 9600, datahandler=dataHandler)
PILOT       = Pilot(ORIENT, desired_pitch=math.radians(-10))
TELEM       = TelemetryHandler(RADIO, ORIENT, PILOT, GPS)

##########################################
# GLOBALS
##########################################
OVERRIDE_STATE = None

# --- LED ---
LED_RUNNING = 11

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
    # Start ORIENT sensor thread
    ORIENT.start()
    # Start GPS thread
    GPS.start()
    # Start Radio thread
    RADIO.start()
    # Start the Pilot
    PILOT.start()
    # Start the Telemetry handler
    TELEM.start()


def shutDown():
    LOG.info("Shutting down")
    TELEM.stop()
    PILOT.stop()
    RADIO.stop()
    GPS.stop()
    ORIENT.stop()


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


def setTurnSeverity(newSev):
    try:
        PILOT.updateTurnSev(newSev)
    except Exception, e:
        LOG.error(e)


def setDestination(lat, lon):
    PILOT.updateDestination(lat, lon)


def speak(text):
    LOG.info("Speaking %s" % text)


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
    location = GPS.getData()
    return location


def sendMessage(msg):
    TELEM.setMessage(msg)


def sendImage(img):
    TELEM.setImage(img)


def updatePilotLocation(location):
    PILOT.updateLocation(location['lat'], location['lon'])


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
    controller.W_glider_command("W:%2.2f:%2.2f" % (leftAngle, rightAngle))


def updateWingAngles():
    wingAngles = PILOT.get_servo_angles()
    LOG.debug("Wing angles received: %s" % wingAngles)
    if wingAngles:
        setWingAngle(wingAngles)


########################
# Release Chute/Balloon
########################
def releaseChord():
    controller.release()


def releaseParachute():
    controller.releaseChute()
