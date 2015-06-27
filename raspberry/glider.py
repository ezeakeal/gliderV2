import sys
import math
import time
import types
import signal
import logging
import traceback

# Orbit Imports
import glider_lib
import glider_schedule as schedule

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
    glider_lib.speak("Initialized")
    while RUNNING:
        try:
            LOG.debug("Current State: %s" % CURRENT_STATE)
            # Determine state data and
            #   execution function, switch function
            stateData = STATE_ORDER[CURRENT_STATE]
            funcExec = getattr(self, stateData['execute'])
            funcSwitch = getattr(self, stateData['switch'])
            
            eResponse = funcExec()
            sResponse = funcSwitch()
            time.sleep(GLIDE_INTERVAL)
        except:
            LOG.error(traceback.print_exc())
            glider_states.setState("RECOVER")


if __name__ == '__main__':
    LOG = setup_custom_logger("drone")
    startUp()
    glide()
    shutDown()
        