import os
import time
import numpy
import logging

# Glider Imports
import glider_lib
import glider_schedule as schedule
import glider_states as states

from glider_gps import GPS_I2C
##########################################
# GLOBALS
##########################################
LOG               = glider_lib.setup_custom_logger("state", loglevel=logging.DEBUG)
GPS               = GPS_I2C()

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
class gliderState(object):
    """
    This is a base class which enforces an execute
    and switch method
    """
    def __init__(self):
        self.readyToSwitch = False
        self.nextState = None
        self.exitState = ""
        self.sleepTime = 1

    def rest(self):
        time.sleep(self.sleepTime)

    def execute(self):
        raise NotImplementedError("Execute function is required")

    def switch(self):
        LOG.info("Next state: %s" % self.nextState)
        assert(self.nextState is not None)
        if self.readyToSwitch:
            glider_lib.speak("Switching state to %s" % self.nextState)
            return self.nextState
        else:
            return None

##########################################
# CLASSES - STATE
##########################################
#-----------------------------------
#         Health Check
#-----------------------------------
class healthCheck(gliderState):
    def __init__(self):
        super(healthCheck, self).__init__()
        self.nextState = "ASCENT"

    def execute(self):
        # Get the location data, figure if locked
        location = glider_lib.getLocation()
        locationLocked = (location.get("fixQual") != 0 and location.get("horDil") < 5)
        # Get battery data. Figure if healthy
        batteryStatus = glider_lib.getBatteryStatus()
        batteryHealthy = batteryStatus.get("health")
        if not locationLocked:
            LOG.error("Location is not locked yet")
        elif not batteryHealthy:
            LOG.error("Battery not healthy")
        else:
            # Seems all is good
            LOG.info("Health Check Passed")
            glider_lib.speak("Health Check Complete")
            glider_lib.sendMessage("Health Good")
            self.readyToSwitch = True
 
#-----------------------------------
#         Ascent
#-----------------------------------
class ascent(gliderState):
    def __init__(self):
        super(ascent, self).__init__()
        self.ascent_nodes = []
        self.ascent_rates = []
        self.median_ascent_rate = 0
        self.sleepTime = 30
        self.minAltDelta = 500
        self.minRateCount = 10
        self.desiredAltitude = 22000
        self.releaseTime = None
        self.nextState = "RELEASE"

    def execute(self):
        LOG.info("ASCENDING!")
        lastNode = None
        if len(self.ascent_nodes) > 0:
            lastNode = self.ascent_nodes[-1]
        if not lastNode:
            return
        
        # Ok, we have a lastNode now so we can do some work
        location  = glider_lib.getLocation()
        currentAlt = location['altitude']
        lastNodeAlt = lastNode['altitude']
        if (lastNodeAlt - currentAlt) < self.minAltDelta:
            return
        
        # Alright, we are sufficiently far from the last node for this to be a decent measurement
        timeSeconds = time.time()
        newNode = {
            'altitude': location['altitude'],
            'time': timeSeconds
        }
        # Append that node
        self.ascent_nodes.append(newNode)
        # Ensure there are enough nodes to get a decent calculation from
        if len(self.ascent_nodes) < 2:
            return
        
        # We have 2 nodes, lets rock with our first ascent rate
        deltaAlt = newNode['altitude'] - lastNode['altitude']
        deltaSec = newNode['time'] - lastNode['time']
        newRate = deltaAlt / deltaSec
        # Append the rate of ascent
        self.ascent_rates.append(newRate)
        if len(self.ascent_rates) < self.minRateCount:
            LOG.debug("Not enough ascent rates have been recorded: %s" % self.ascent_rates)
            return

        self.median_ascent_rate = numpy.median(numpy.array(self.ascent_rates))
        LOG.debug("Calculated ascent rate at: %s" % self.median_ascent_rate)
        remainingAltitude = self.desiredAltitude - location['altitude']
        remainingSeconds = remainingAltitude / self.median_ascent_rate
        glider_lib.sendMessage("Alt (%s) Rate (%s) SecRemain(%s)" % (
            location['altitude'], newRate, remainingSeconds))

    def switch(self):
        if not self.releaseTime:
            return
        # Figure out if we have passed that time
        currentTime = time.time()
        if currentTime > self.releaseTime:
            self.readyToSwitch = True 
        super(switch, self).switch()
        
#-----------------------------------
#         Release
#-----------------------------------
class release(gliderState):
    def __init__(self):
        super(release, self).__init__()
        self.nextState = "FLIGHT"
        self.mp3Play = "mpg321"
        self.releaseMP3 = "release_song.mp3" # Make this full path
        self.releaseDelay = 143

    def execute(self):
        LOG.info("Playing song")
        subprocess.Popen([self.mp3Play, self.releaseMP3])
        time.sleep(self.releaseDelay)
        LOG.info("Releasing cable")
        glider_lib.releaseChord()

    def switch(self):
        self.readyToSwitch = True
        super(release, self).switch()
    
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
        super(glide, self).switch()

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


#-----------------------------------
#         EMERGENCY
#-----------------------------------
class errorState(gliderState):
    def execute(self):
        # Send data over radio.
        # Tell people there is something wrong
        # Send location, orientation
        # Send states of parachute/release motor
        # Send battery level
        # LOOK FOR A RESPONSE!
        # We need to set the state it should go in to..
        pass
