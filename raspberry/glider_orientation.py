import math
import logging

##############################################
# GLOBALS
##############################################
LOG = logging.getLogger("orbit")
LOCATION    = None
DEST_COORD  = (52.254197,-7.181244)

DESIRED_YAW = 0 # direction (radians)
DESIRED_PITCH = -0.175 # ground attack (radians)

ORIENTATION = {
    'yaw':0, 'pitch':0, 'roll':0
} 
SERVO_RANGE = 30
WING_PARAM = {
  "LEFT": {"CENTER": 90, "CURRENT": 0, "INTENDED": 0},
  "RIGHT": {"CENTER": 90, "CURRENT": 0, "INTENDED": 0}
}
O_IMU = None 
##############################################
# FUNCTIONS - UTIL
##############################################
# For some reason, if I put this in a function
# it doesn't initialise correctly.. well it does
# but I can't read anything from it after!
SETTINGS_FILE = "RTIMULib"
s = RTIMU.Settings(SETTINGS_FILE)
O_IMU = RTIMU.RTIMU(s)
if (not O_IMU.IMUInit()):
    sys.exit(1)
else:
    LOG.info("IMU Init Succeeded")

def configureOrientationChip():
    global O_IMU
    O_IMU.setSlerpPower(0.02)
    O_IMU.setGyroEnable(True)
    O_IMU.setAccelEnable(True)
    O_IMU.setCompassEnable(True)

def getOrientPollInterval():
    poll_interval = O_IMU.IMUGetPollInterval()
    LOG.info("Recommended Poll Interval: %dmS\n" % poll_interval)
    return poll_interval

##############################################
# FUNCTIONS - ORIENTATION
##############################################
def getDesiredRoll(yawDelta_rad):
    tanSigma = 2
    # tan cycles twice over 2pi, so scale rad_delta appropriately. 
    # We are getting a scalar between -1 and 1 here
    LOG.debug("Delta: %f (%f)" % (
        yawDelta_rad, math.degrees(yawDelta_rad)
    ))
    tanScale = math.tan(yawDelta_rad/2)/tanSigma 
    if math.fabs(tanScale) > 1:
        tanScale = tanScale/math.fabs(tanScale) # limit it to 1
    maxAbsRange = math.pi/6 # Maximum absolute roll angle in radians(+/- 30degrees)
    return maxAbsRange * tanScale


def getOrientation():
    data = imu.getIMUData()
    fusionPose = data["fusionPose"]
    roll = fusionPose[0]
    pitch = fusionPose[1]
    yaw = fusionPose[2]
    LOG.debug("r: %f p: %f y: %f" % (
        math.degrees(roll), math.degrees(pitch), math.degrees(yaw))
    )
    return roll, pitch, yaw


def getDesiredHeading():
    x1, y1 = LOCATION['latitude'], LOCATION['longitude']
    x2, y2 = DEST_COORD[0], DEST_COORD[1]
    lon1, lat1, lon2, lat2 = map(radians, [y1, x1, y2, x2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    dLon = lon2 - lon1
    y = sin(dLon) * cos(lat2)
    x = cos(lat1) * sin(lat2) \
            - sin(lat1) * cos(lat2) * cos(dLon)
    rads = atan2(y, x)
    LOG.debug("X1 %s Y2 %s" % (x1, y1))
    LOG.debug("X2 %s Y2 %s" % (x2, y2))
    LOG.debug("ANG %s" % (rads))
    return rads


def calculateWingAngle(roll, pitch, yaw):
    # Initialize the wing adjustments at 0
    # We will add up all adjustments, then scale them to the ranges of the servos.
    wing_left = 0
    wing_right = 0
    # Now adjust for pitch
    deltaPitch = DESIRED_PITCH - pitch
    wing_left += deltaPitch
    wing_right += deltaPitch
    # Calculate a desired roll from our yaw
    deltaYaw = min(DESIRED_YAW - yaw, yaw - DESIRED_YAW)
    desired_roll = getDesiredRoll(deltaYaw)
    deltaRoll = desired_roll - roll # This is radians
    # Adjust the wings again for roll
    wing_left += deltaRoll
    wing_right -= deltaRoll
    # Scale these angles now based on maximum ranges of the servos
    maxAngle = max(math.fabs(wing_left), math.fabs(wing_right))
    wing_left_scaled = wing_left
    wing_right_scaled = wing_right
    if maxAngle > math.radians(SERVO_RANGE):
        angleScale = maxAngle/math.radians(SERVO_RANGE)
        wing_left_scaled /= angleScale
        wing_right_scaled /= angleScale
    # Calculate servo degrees
    wing_left_servo = WING_PARAM['LEFT']['CENTER'] + math.degrees(wing_left_scaled)
    wing_right_servo = WING_PARAM['RIGHT']['CENTER'] - math.degrees(wing_right_scaled)
    LOG.debug("Wing Angles: %02.1f %02.1f" % ()wing_left_servo, wing_right_servo)
    return wing_left_servo, wing_right_servo


def update_target_wings():
    global INTEND_WING_LEFT
    global INTEND_WING_RIGHT
    
    counter = 0
    while RUNNING:
        goodIMU = imu.IMURead() # We MUST read it this fast. Otherwise its shite.
        time.sleep(poll_interval*1.0/1000.0)

        counter += 1
        if goodIMU:
            debug=(counter % 50 == 0)
            roll, pitch, yaw = getOrientation()
            INTEND_WING_LEFT, INTEND_WING_RIGHT = calculateWingAngle(roll, pitch, yaw, debug=debug)


def set_servo_angles():
    while RUNNING:
        wl = math.ceil(INTEND_WING_LEFT)
        wr = math.ceil(INTEND_WING_RIGHT)
        cl = WING_PARAM['LEFT']['CURRENT']
        cr = WING_PARAM['RIGHT']['CURRENT']
        if (wl != cl) or (wr != cr):
            controller.W_glider_command("W:%s:%s" % (wl, wr))
            WING_PARAM['LEFT']['CURRENT'] = wl
            WING_PARAM['RIGHT']['CURRENT'] = wr
            print "%2.2f %2.2f" % (wl, wr)
        time.sleep(0.02)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop_test)
    controller.reset_spi()
    orientThread = Thread( target=update_target_wings, args=() )
    servoThread = Thread( target=set_servo_angles, args=() )

    orientThread.start()
    servoThread.start()
    while True:
        time.sleep(1) # Keep this thread active
