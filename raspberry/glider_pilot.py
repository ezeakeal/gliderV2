import log
import time
import math
import logging
from threading import Thread

##############################################
# GLOBALS
##############################################
LOG = log.setup_custom_logger('pilot')
LOG.setLevel(logging.DEBUG)


class Pilot(object):
    """
    Pilot class for translating our heading, orientation, and desired 
    coordinates into intended wing angles
    """

    def __init__(self, O_IMU, 
        desired_yaw=0, desired_pitch=-0.175, 
        destination=(52.254197,-7.181244),
        location=(52.254197,-7.181244),
        wing_calc_interval=0.02,
        servo_range=30):
        
        self.O_IMU = O_IMU
        self.threadAlive = False
        self.configureOrientationChip()
        
        self.servo_range = servo_range
        self.wing_param = {
            "left": {"center": 90, "current": 0, "intended": 0},
            "right": {"center": 96, "current": 0, "intended": 0}
        }
        
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        
        self.desired_pitch = desired_pitch
        self.desired_yaw = desired_yaw

        self.destination = destination
        self.location = location

        self.poll_interval = self.getOrientPollInterval()
        self.wing_calc_interval = wing_calc_interval

    def updatePitch(self, angle):
        LOG.error("Updated desired pitch: %s" % angle)
        self.desired_pitch = angle

    def getWingCenterAndRange(self):
        lcenter = self.wing_param['left']['center']
        rcenter = self.wing_param['right']['center']
        servoRange = self.servo_range
        return lcenter, rcenter, servoRange

    def getOrientPollInterval(self):
        poll_interval = self.O_IMU.IMUGetPollInterval()
        LOG.info("Recommended Poll Interval: %dmS\n" % poll_interval)
        return poll_interval

    def configureOrientationChip(self):
        self.O_IMU.setSlerpPower(0.02)
        self.O_IMU.setGyroEnable(True)
        self.O_IMU.setAccelEnable(True)
        self.O_IMU.setCompassEnable(True)

    def start(self):
        sensorThread = Thread( target=self.updateOrientation, args=() )
        pilotThread = Thread( target=self.updateIntendWingAngle, args=() )
        self.threadAlive = True
        LOG.info("Starting up orienation and angle calculation threads now")
        sensorThread.start()
        pilotThread.start()

    def stop(self):
        self.threadAlive = False

    def updateOrientation(self):
        while self.threadAlive:
            if self.O_IMU.IMURead():
                data = self.O_IMU.getIMUData()
                fusionPose = data["fusionPose"]
                self.roll = fusionPose[0]
                self.pitch = fusionPose[1]
                self.yaw = fusionPose[2]
                LOG.debug("r: %f p: %f y: %f" % (
                    math.degrees(self.roll), math.degrees(self.pitch), math.degrees(self.yaw))
                )
            time.sleep(self.poll_interval*1.0/1000.0)


    def getDesiredRoll(self, yawDelta_rad):
        tanSigma = 2
        # tan cycles twice over 2pi, so scale rad_delta appropriately. 
        # We are getting a scalar between -1 and 1 here
        LOG.debug("Roll Delta: %f (%f)" % (
            yawDelta_rad, math.degrees(yawDelta_rad)
        ))
        tanScale = math.tan(yawDelta_rad/2)/tanSigma 
        if math.fabs(tanScale) > 1:
            tanScale = tanScale/math.fabs(tanScale) # limit it to 1
        maxAbsRange = math.pi/6 # Maximum absolute roll angle in radians(+/- 30degrees)
        return maxAbsRange * tanScale


    def updateIntendWingAngle(self):
        while self.threadAlive:
            # Initialize the wing adjustments at 0
            # We will add up all adjustments, then scale them to the ranges of the servos.
            wing_left = 0
            wing_right = 0

            # Now adjust for pitch
            deltaPitch = self.pitch - self.desired_pitch
            wing_left -= deltaPitch
            wing_right += deltaPitch

            # Calculate a desired roll from our yaw
            deltaYaw = min(self.desired_yaw - self.yaw, 
                self.yaw - self.desired_yaw)
            desired_roll = self.getDesiredRoll(deltaYaw)
            deltaRoll = desired_roll - self.roll # This is radians

            # Adjust the wings again for roll
            wing_left += deltaRoll
            wing_right -= deltaRoll

            # Scale these angles now based on maximum ranges of the servos
            maxAngle = max(math.fabs(wing_left), math.fabs(wing_right))
            wing_left_scaled = wing_left
            wing_right_scaled = wing_right
            if maxAngle > math.radians(self.servo_range):
                angleScale = maxAngle/math.radians(self.servo_range)
                wing_left_scaled /= angleScale
                wing_right_scaled /= angleScale

            # Calculate servo degrees
            self.wing_param['left']['intended'] = int(self.wing_param['left']['center'] + math.degrees(wing_left_scaled))
            self.wing_param['right']['intended'] = int(self.wing_param['right']['center'] + math.degrees(wing_right_scaled))
            LOG.debug("Wing Angles: %02.1f %02.1f" % (
                self.wing_param['left']['intended'], self.wing_param['right']['intended']))
            time.sleep(self.wing_calc_interval)

    
    def updateCurrentLocation(self, location):
        if not location:
            return 
        self.location = location
        self.updateDesiredYaw()


    def updateDesiredYaw(self):
        # http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        x1, y1 = self.location['lat'], self.location['lon']
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
        if (wl != cl) or (wr != cr):
            self.wing_param['left']['current'] = wl
            self.wing_param['right']['current'] = wr
            return [wl, wr]
