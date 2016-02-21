import os
import log
import math
import logging
import subprocess

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
LOG.setLevel(logging.WARNING)


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
ORIENT = IMU()
GPS = GPS_I2C()
RADIO = Transceiver("/dev/ttyAMA0", 9600, datahandler=dataHandler)
PILOT = Pilot(ORIENT, desired_pitch=math.radians(-10))
TELEM = TelemetryHandler(RADIO, ORIENT, PILOT, GPS)

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
    # Start GPS thread
    GPS.start()
    # Start Radio thread
    RADIO.start()
    # Start the Pilot
    PILOT.start()
    # Start the Telemetry handler
    TELEM.start()
    # Start ORIENT sensor thread
    ORIENT.start()
    

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
    LOG.info("Returning override state: %s" % OVERRIDE_STATE)
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


def speak(text, speed=150):
    LOG.info("Speaking %s" % text)
    with open(os.devnull, "w") as devnull:
        subprocess.Popen(["espeak", "-k10 -s%s" % (speed), text], stdout=devnull, stderr=devnull)


##########################################
# FUNCTIONS - Standard Operations
##########################################
def getBatteryStatus():
    status = {
        "health": True,
        "level": None,
        "temp": None
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
    setWingAngle([lcenter - servoRange, rcenter - servoRange])


def max_wings():
    lcenter, rcenter, servoRange = PILOT.getWingCenterAndRange()
    setWingAngle([lcenter + servoRange, rcenter + servoRange])


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
    controller.W_glider_command("D:")


def releaseParachute():
    controller.W_glider_command("P:")
