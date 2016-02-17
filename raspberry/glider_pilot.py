import log
import time
import math
import logging
from threading import Thread

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('pilot')
LOG.setLevel(logging.WARNING)

class Pilot(object):
    """
    Pilot class for translating our heading, orientation, and desired 
    coordinates into intended wing angles
    """

    def __init__(self, IMU, 
        desired_yaw=0, desired_pitch=-0.175, 
        turn_severity=.5, servo_range=0.5236,
        destination=[52.254197,-7.181244],
        location=[52.254197,-7.181244],
        wing_calc_interval=0.02):
        
        self.IMU = IMU
        self.threadAlive = False
        
        self.servo_range = servo_range
        self.wing_param = {
            "left": {"center": 90, "current": 0, "intended": 0},
            "right": {"center": 96, "current": 0, "intended": 0}
        }

        self.turn_severity = turn_severity
        self.desired_pitch = desired_pitch
        self.desired_yaw = desired_yaw

        self.destination = destination
        self.location = location

        self.wing_calc_interval = wing_calc_interval

        LOG.debug("Turn Sev: %2.2f" % turn_severity)
        LOG.debug("Servo Range: %2.2f" % math.degrees(servo_range))
        LOG.debug("Desired Pitch: %2.2f" % math.degrees(desired_pitch))


    def updatePitch(self, angle):
        LOG.warning("Updated desired pitch: %s" % angle)
        self.desired_pitch = angle


    def updateTurnSev(self, angle):
        LOG.warning("Updated turn severity: %s" % angle)
        self.turn_severity = angle


    def getWingCenterAndRange(self):
        lcenter = self.wing_param['left']['center']
        rcenter = self.wing_param['right']['center']
        servoRange = math.degrees(self.servo_range)
        return lcenter, rcenter, servoRange


    def start(self):
        pilotThread = Thread( target=self.updateIntendWingAngle, args=() )
        self.threadAlive = True
        LOG.info("Starting up Pilot thread now")
        pilotThread.start()


    def stop(self):
        self.threadAlive = False


    def scaleAbsToLimit(self, val, limit):
        if val > limit:
            val = limit
        elif val < -limit:
            val = -limit
        return val


    def getDesiredRoll(self, yawDelta_rad):
        # Turn severity defines how much the glider will roll 
        # proportional to the difference in desired direction
        # This multiplies the apparent difference in angle, as 
        # tan will ramp up to +/- infinity at either +/- 90deg
        # This gets limited later
        yawDelta_rad *= self.turn_severity 
        # Limit the delta to pi/2 on either side
        yawDelta_rad = self.scaleAbsToLimit(yawDelta_rad, math.pi/2)
        # Get the tan response to this figure 
        tanScale = math.tan(yawDelta_rad)
        tanScale = self.scaleAbsToLimit(tanScale, 1)
        roll = self.servo_range * tanScale
        roll *= -1 # Roll left (which is positive) if turning left (when yaw is negative)
        return roll


    def updateIntendWingAngle(self):
        while self.threadAlive:
            # Get the readings from the IMU
            current_pitch = self.IMU.pitch
            current_roll = self.IMU.roll
            current_yaw = self.IMU.yaw
            LOG.debug("P(%2.1f) R(%2.1f) Y(%2.1f)" % (
                math.degrees(current_pitch), math.degrees(current_roll), math.degrees(current_yaw)))
            # Initialize the wing adjustments at 0
            # We will add up all adjustments, then scale them to the ranges of the servos.
            wing_left = 0
            wing_right = 0
            LOG.debug("Delta wings = L(%2.1f) R(%2.1f)" % (math.degrees(wing_left), math.degrees(wing_right)))
            # Now adjust for pitch
            deltaPitch = self.desired_pitch - current_pitch
            wing_left += deltaPitch
            wing_right += deltaPitch
            LOG.debug("Delta pitch: %2.1f" % (math.degrees(deltaPitch)))
            LOG.debug("Delta wings = L(%2.1f) R(%2.1f)" % (math.degrees(wing_left), math.degrees(wing_right)))

            # Calculate a desired roll from our yaw
            deltaYaw = min(self.desired_yaw - current_yaw, 
                current_yaw - self.desired_yaw)
            desired_roll = self.getDesiredRoll(deltaYaw)
            LOG.debug("Delta yaw: %2.1f (roll: %2.1f)" % (math.degrees(deltaYaw), math.degrees(desired_roll)))

            deltaRoll = desired_roll - current_roll # This is radians
            LOG.debug("Delta roll: %2.1f" % (math.degrees(deltaRoll)))

            # Adjust the wings again for roll
            wing_left += deltaRoll
            wing_right -= deltaRoll
            LOG.debug("Delta wings = L(%2.1f) R(%2.1f)" % (math.degrees(wing_left), math.degrees(wing_right)))

            # Scale these angles now based on maximum ranges of the servos
            maxAngle = max(math.fabs(wing_left), math.fabs(wing_right))
            wing_left_scaled = wing_left
            wing_right_scaled = wing_right
            if maxAngle > self.servo_range:
                angleScale = maxAngle/self.servo_range
                wing_left_scaled /= angleScale
                wing_right_scaled /= angleScale
            LOG.debug("Scaled wing deltas = L(%2.1f) R(%2.1f)" % (math.degrees(wing_left_scaled), math.degrees(wing_right_scaled)))

            # Calculate servo degrees
            self.wing_param['left']['intended'] = int(self.wing_param['left']['center'] + math.degrees(wing_left_scaled))
            self.wing_param['right']['intended'] = int(self.wing_param['right']['center'] - math.degrees(wing_right_scaled))
            LOG.debug("Wing Angles: %02.1f %02.1f" % (
                self.wing_param['left']['intended'], self.wing_param['right']['intended']))
            time.sleep(self.wing_calc_interval)

    
    def updateLocation(self, lat, lon):
        self.location[0] = lat
        self.location[1] = lon
        return self.location


    def updateDestination(self, lat, lon):
        self.destination[0] = lat
        self.destination[1] = lon
        return self.destination


    def updateDesiredYaw(self):
        # http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        x1, y1 = self.location[0], self.location[1]
        x2, y2 = self.destination[0], self.destination[1]
        LOG.debug("X1 %s Y2 %s" % (x1, y1))
        LOG.debug("X2 %s Y2 %s" % (x2, y2))
        if None in [x1, x2, y1, y2]:
            LOG.warning("Some coordinates are blank")
            return
        # Convert gps coordinates to radian degrees
        lon1, lat1, lon2, lat2 = map(math.radians, [y1, x1, y2, x2])
        bearing = math.atan2(
            math.sin(lon2-lon1) * math.cos(lat2), 
            math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2-lon1)
        )
        bearing = (bearing + (2*math.pi)) % (2*math.pi)
        LOG.debug("ANG %s" % (bearing))
        self.desired_yaw = bearing


    def get_servo_angles(self):
        wl = self.wing_param['left']['intended']
        wr = self.wing_param['right']['intended']
        cl = self.wing_param['left']['current']
        cr = self.wing_param['right']['current']
        if (wl != cl) or (wr != cr) or True:
            self.wing_param['left']['current'] = wl
            self.wing_param['right']['current'] = wr
            return [wl, wr]
