import sys
import math
import time
import serial
import logging
import datetime

##########################################
# TODO
##########################################

##########################################
# GLOBALS
##########################################
SERVOTICK = 0.05
SOCK      = None
LOG       = logging.getLogger()
LAST_DAT  = None

##########################################
# FUNCTIONS
##########################################
# Initialize the serial connection - then use some commands I saw somewhere once
def init(target="00:13:03:14:16:68"):
  global SOCK
  global TARGET
  SOCK    = None
  TARGET  = target
  sConnect()
  LOG.debug("Initialized Flight Controller")
  
def disconnect():
  if SOCK:
    try: 
      SOCK.close()
    except: 
      LOG.info("Closing SOCK failed")
    
def sConnect():
  global SOCK
  disconnect()
  try:
    LOG.info("Connecting to Serial")
    SOCK = serial.Serial('/dev/ttyAMA0', 19200, timeout=.1)
    SOCK.flush()
  except Exception, e:
    LOG.critical(e)
    print e
    LOG.critical("Reconnecting in 3 seconds")
    time.sleep(3)
    sConnect()

def send(cStr):
  LOG.debug("SENDING: %s" % cStr)
  try:
    SOCK.write("%s;" % cStr)
    SOCK.flush()
    dat =  SOCK.readline()
    return dat
  except Exception, e:
    LOG.critical("Communication Failed!")
    LOG.critical(e)
    sConnect()
    
def setWing(angleLeft, angleRight):
  LOG.debug("Setting Wing Angle")
  send("W:%s:%s" % (angleLeft, angleRight))
  time.sleep(SERVOTICK) # sleep a bit


def release():
  LOG.debug("Releasing")
  send("D:")
  time.sleep(SERVOTICK) # sleep a bit
    

def releaseChute():
  LOG.debug("Releasing Parachute")
  send("P:")
  time.sleep(SERVOTICK) # sleep a bit
    

def sendRadio(rString):
  LOG.debug("Sending Radio Packet: %s" % rString)
  send("R:%s" % rString)
  

def stop():
  SOCK.close()
  LOG.info("Closing Module")


def requestData():
  global LAST_DAT
  while True:
    dat = send("G:")
    print "Recieved: %s" % dat
    if dat and dat.startswith("T|"):
      LAST_DAT = dat
      print "Received"
      break
    else:
      time.sleep(0.5)


def getGPS():
  requestData()
