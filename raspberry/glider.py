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
from glider_states import healthCheck, ascent, release, glide, parachute, recovery

##########################################
# TODO
##########################################

##########################################
# GLOBALS
##########################################
LOGLEVEL          = logging.WARN
LOG               = None
RUNNING           = True
DESIRED_PITCH     = 0.05
RELEASED          = False
PARACHUTE_HEIGHT  = 1000
GLIDE_INTERVAL    = 0.05

PERSIST_DATA = {}

STATE_MACHINE = {
    "HEALTH_CHECK"  : healthCheck,
    "ASCENT"        : ascent,                   
    "RELEASE"       : release,                
    "FLIGHT"        : glide,                    
    "PARACHUTE"     : parachute,
    "RECOVER"       : recovery
}
CURRENT_STATE = "HEALTH_CHECK"

##########################################
# FUNCTIONS - UTIL
##########################################
def setup_custom_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler.setFormatter(formatter)
    logger.setLevel(LOGLEVEL)
    logger.addHandler(handler)
    return logger


def signal_handler(signal, frame):
    global RUNNING
    RUNNING = False


##########################################
# MAIN
##########################################      
def startUp():
    glider_lib.speak("Starting up")
    signal.signal(signal.SIGINT, signal_handler)


def shutDown():
    glider_lib.speak("Shutting down")


def glide():
    global CURRENT_STATE
    glider_lib.speak("Initialized")
    while RUNNING:
        try:
            stateClass = STATE_MACHINE[CURRENT_STATE]
            
            eResponse = stateClass.execute()
            newState = stateClass.switch()
            if newState:
                LOG.debug("State is being updated from (%s) to (%s)" % (
                    CURRENT_STATE, newState))
                CURRENT_STATE = newState
            time.sleep(GLIDE_INTERVAL)
        except:
            LOG.error(traceback.print_exc())
            states.setState("RECOVER")


if __name__ == '__main__':
    LOG = setup_custom_logger("drone")
    startUp()
    glide()
    shutDown()
        