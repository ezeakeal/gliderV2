import sys
import math
import time
import types
import signal
import logging
import traceback
import importlib

# Glider Imports
import glider_lib
import glider_schedule as schedule
from glider_states import healthCheck, ascent, release, glide, parachute, recovery, errorState

##########################################
# TODO
##########################################

##########################################
# GLOBALS
##########################################
LOG               = glider_lib.setup_custom_logger("glider", loglevel=logging.DEBUG)
RUNNING           = True
DESIRED_PITCH     = 0.05
RELEASED          = False
PARACHUTE_HEIGHT  = 1000
GLIDE_INTERVAL    = 0.05

PERSIST_DATA = {}

STATE_MACHINE = {
    "HEALTH_CHECK"  : healthCheck(),
    "ASCENT"        : ascent(),                   
    "RELEASE"       : release(),                
    "FLIGHT"        : glide(),                    
    "PARACHUTE"     : parachute(),
    "RECOVER"       : recovery(),
    "ERROR"         : errorState()
}
CURRENT_STATE = "HEALTH_CHECK"

##########################################
# FUNCTIONS - UTIL
##########################################
def signal_handler(signal, frame):
    global RUNNING
    RUNNING = False


##########################################
# MAIN
##########################################      
def startUp():
    glider_lib.speak("Starting up")
    glider_lib.startUp()
    signal.signal(signal.SIGINT, signal_handler)


def shutDown():
    glider_lib.speak("Shutting down")
    glider_lib.shutDown()


def glide():
    global CURRENT_STATE
    glider_lib.speak("Initialized")
    while RUNNING:
        try:
            LOG.debug("Current state: %s" % CURRENT_STATE)
            stateClass = STATE_MACHINE[CURRENT_STATE]
            stateClass.rest()
            stateClass.execute()
            newState = stateClass.switch()
            if newState:
                LOG.debug("State is being updated from (%s) to (%s)" % (
                    CURRENT_STATE, newState))
                CURRENT_STATE = newState
        except:
            LOG.error(traceback.print_exc())
            CURRENT_STATE = "ERROR"


if __name__ == '__main__':
    startUp()
    glide()
    shutDown()
        