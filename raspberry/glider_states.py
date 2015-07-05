import logging

# Glider Imports
import glider_lib
import glider_schedule as schedule
import glider_states as states


##########################################
# GLOBALS
##########################################
LOGLEVEL          = logging.WARN
LOG               = logging.getLogger('state')

##########################################
# FUNCTIONS - UTIL
##########################################
def setState(newState):
    """Sets the global state which is used for various updates"""
    global STATE
    if getattr(states, newState):
        STATE = newState
    else:
        raise Exception("State (%s) does not exist" % newState)


def scheduleRelease():
    global CURRENT_STATE
    CURRENT_STATE = "release"


def runStateMachine():
    currentStateName = states.CURRENT_STATE
    stateClass = states.STATE_ORDER[currentStateName]
    stateClass = getattr(states, "healthCheck")
    
    eResponse = stateClass.execute()
    sResponse = stateClass.switch()

##########################################
# CLASSES - BASE
##########################################
class gliderState():
    """
    This is a base class which enforces an execute
    and switch method
    """

    def execute(self):
        raise NotImplementedError("Execute function is required")

    def switch(self):
        raise NotImplementedError("Switch function is required")

##########################################
# CLASSES - STATE
##########################################
#-----------------------------------
#         Health Check
#-----------------------------------
class healthCheck(gliderState):
    def execute(self):
        time.sleep(5)
        
    def switch(self):
        location = glider_lib.getLocation()
        orientation = glider_lib.getOrientation()
        battStatus = glider_lib.getBatteryStatus()
        if (location['provider'] != 'gps'):
            LOG.error("Network Provider not sufficient: %s" % location['provider'])  
            return False
        if (battStatus['level'] < 85):
            LOG.error("Battery too low: %s" % battStatus['level'])  
            return False
        LOG.info("Health Check Passed")
        glider_lib.speak("Health Check Complete")
        glider_lib.sendTextData("Health Good")
        glider_lib.speak("Beginning Ascent")
        return "ASCENT"
        
#-----------------------------------
#         Ascent
#-----------------------------------
class ascent(gliderState):
    def __init__(self):
        self.ascent_nodes = []
        # target release countdown is int.
        # Recalc at every node update 
        ## node updates at >500m intervals only
        ## below 20km
        # Median used to update release time
        # If time has passed (dont countdown, check time.time() against a future time)
        # Then switch

    def execute(self):
        LOG.info("ASCENDING!")
        time.sleep(60)

    def switch(self):
        global CURRENT_STATE
        location  = glider_lib.getLocation()
        if location['altitude'] > 15000 and PERSIST_DATA.get('15000') == None:
            PERSIST_DATA['15000'] = time.time()
        if location['altitude'] > 17000 and PERSIST_DATA.get('17000') == None:
            PERSIST_DATA['17000'] = time.time()
        if PERSIST_DATA.get('17000') and PERSIST_DATA.get('15000'):
            diff = int(PERSIST_DATA['17000'] - PERSIST_DATA['15000'])
            schedule.enableFunc("scheduleRelease", scheduleRelease, diff)
        if STATE['ascent_complete']:
            LOG.info("Ascent Complete")
        
#-----------------------------------
#         Release
#-----------------------------------
class release(gliderState):
    def execute(self):
        global RELEASED
        LOG.info("RELEASING!")
        glider_lib.speak("Releasing in")
        time.sleep(3)
        for t in [5,4,3,2,1]:
            glider_lib.speak(t)
            time.sleep(1)
        glider_lib.releaseChord()
        RELEASED = True

    def switch(self):
        global CURRENT_STATE
        glider_lib.speak("Performing Flight")
        CURRENT_STATE = "FLIGHT"
    
#-----------------------------------
#         Guided Flight
#-----------------------------------
class glide(gliderState):
    def execute(self):
        desired_heading = glider_lib.getDesiredHeading()
        LOG.debug("Nav Heading: %s " % desired_heading)
        orientation = glider_lib.getOrientation()
        LOG.debug("Current Heading: %s " % orientation['yaw'])
        headingDelta = min(desired_heading - orientation['yaw'], orientation['yaw'] - desired_heading) # shouldn't be required, but may have non-cyclic manipulation of angles
        
        LOG.debug("Current Roll: %s" % orientation['roll'])
        desired_roll = getDesiredRoll(headingDelta)
        LOG.debug("Desired Roll: %s" % (desired_roll)) 
        deltaRoll = desired_roll - orientation['roll'] # required change in current roll
        LOG.debug("Delta Roll: %s" % (deltaRoll)) 

        LOG.debug("Current Pitch: %s" % orientation['pitch'])
        LOG.debug("Desired Pitch: %s" % (DESIRED_PITCH)) 
        LOG.warn("%s %s %s" % (desired_heading, orientation['yaw'], headingDelta)) 
        deltaPitch = DESIRED_PITCH - orientation['pitch']
        glider_lib.wing_turnDelta(deltaRoll, deltaPitch)
        
    def switch(self):
        global CURRENT_STATE
        location = glider_lib.getLocation()
        if location['altitude'] < PARACHUTE_HEIGHT:
            CURRENT_STATE = "PARACHUTE"

#-----------------------------------
#         PARACHUTE
#-----------------------------------
class parachute(gliderState):
    def execute(self):
        glider_lib.speak("Releasing parachute!")
        location = glider_lib.getLocation()
        orientation = glider_lib.getOrientation()
        glider_lib.broadcastLocation()
        glider_lib.releaseParachute()

    def switch(self):
        global CURRENT_STATE
        LOG.info("Attempting Recovery")
        if RELEASED:
            CURRENT_STATE = "PARACHUTE"
        else:
            CURRENT_STATE = "RELEASE"


#-----------------------------------
#         EMERGENCY
#-----------------------------------
class recovery(gliderState):
    def execute(self):
        glider_lib.speak("Recovery!")
        LOG.critical("Attempting Recovery")
        location = glider_lib.getLocation()
        orientation = glider_lib.getOrientation()
        glider_lib.broadcastLocation()

    def switch(self):
        global CURRENT_STATE
        LOG.info("Attempting Recovery")
        if RELEASED:
            CURRENT_STATE = "PARACHUTE"
        else:
            CURRENT_STATE = "RELEASE"

