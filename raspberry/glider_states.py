import os
import log
import time
import numpy
import logging

# Glider Imports
import glider_lib
import glider_schedule as schedule
import glider_states as states

##########################################
# GLOBALS
##########################################
LOG = log.setup_custom_logger('state_controller')
LOG.setLevel(logging.WARN)
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
        if self.nextState is None:
            raise Exception("NextState not defined")
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
        self.checkedWings = False
        self.sleepTime = 5

    def execute(self):
        glider_lib.center_wings()
        if not self.checkedWings:
            self.wingCheck()
        # Get the location data, figure if locked
        location = glider_lib.getLocation()
        locationLocked = (location.get("fixQual") != 0 and location.get("horDil") < 5)
        # Get battery data. Figure if healthy
        batteryStatus = glider_lib.getBatteryStatus()
        batteryHealthy = batteryStatus.get("health")
        if not locationLocked:
            LOG.warning("Location is not locked yet")
        elif not batteryHealthy:
            LOG.warning("Battery not healthy")
        else:
            # Seems all is good
            LOG.info("Health Check Passed")
            glider_lib.speak("Health Check Complete")
            glider_lib.sendMessage("Health Good")
            self.readyToSwitch = True
    
    def wingCheck(self):
        LOG.info("Moving wings")
        wingMoveInterval = 0.2
        # Move the wings to max range
        glider_lib.center_wings()
        time.sleep(wingMoveInterval)
        glider_lib.min_wings()
        time.sleep(wingMoveInterval)
        glider_lib.center_wings()
        time.sleep(wingMoveInterval)
        glider_lib.max_wings()
        time.sleep(wingMoveInterval)
        glider_lib.center_wings()
        self.checkedWings = True
        
#-----------------------------------
#         Ascent
#-----------------------------------
class ascent(gliderState):
    def __init__(self):
        super(ascent, self).__init__()
        self.ascent_nodes = []
        self.ascent_rates = []
        self.median_ascent_rate = 0
        self.sleepTime = 10
        self.minAltDelta = 500
        self.minRateCount = 10
        self.desiredAltitude = 22000
        self.releaseTime = None
        self.nextState = "RELEASE"

    def execute(self):
        glider_lib.center_wings()
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
    def __init__(self):
        super(glide, self).__init__()
        self.nextState = "PARACHUTE"
        self.parachute_height = 1500
        self.location = None
        self.sleepTime = 0.02

    def execute(self):
        # Get our new location
        self.location = glider_lib.getLocation()
        LOG.info("Current Location: %s" % self.location)
        # Update the pilot
        glider_lib.updatePilotLocation(self.location)
        # Update the servos
        glider_lib.updateWingAngles()
        
    def switch(self):
        if (self.location and self.location['alt'] and 
                    self.location['alt'] < self.parachute_height):
            self.readyToSwitch = True
        super(glide, self).switch()

#-----------------------------------
#         PARACHUTE
#-----------------------------------
class parachute(gliderState):
    def __init__(self):
        super(parachute, self).__init__()
        self.nextState = "RECOVER"
        self.parachute_height = 1500
        self.location = None
        self.sleepTime = 0.02

    def execute(self):
        glider_lib.speak("Releasing parachute!")
        location = glider_lib.getLocation()
        orientation = glider_lib.getOrientation()
        glider_lib.broadcastLocation()
        glider_lib.releaseParachute()

    def switch(self):
        self.readyToSwitch = True
        super(parachute, self).switch()


#-----------------------------------
#         EMERGENCY
#-----------------------------------
class recovery(gliderState):
    def __init__(self):
        super(recovery, self).__init__()
        self.nextState = "RECOVER"
        self.sleepTime = 15

    def execute(self):
        glider_lib.speak("Help me")
        LOG.critical("Attempting Recovery")

    def switch(self):
        pass


#-----------------------------------
#         EMERGENCY
#-----------------------------------
class errorState(gliderState):
    def __init__(self):
        super(errorState, self).__init__()
        self.nextState = "PARACHUTE"

    def execute(self):
        # Send data over radio.
        # Tell people there is something wrong
        # Send location, orientation
        # Send states of parachute/release motor
        # Send battery level
        # LOOK FOR A RESPONSE!
        # We need to set the state it should go in to..
        pass

    def switch(self):
        pass
