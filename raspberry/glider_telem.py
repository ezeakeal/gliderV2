##############################################
#
# GliderV2 Client Software 
# Author: Daniel Vagg
# 
##############################################
import log
import time
import math
import json
import logging
from threading import Thread

# GUIDE
# http://ava.upuaut.net/?p=768

##########################################
# GLOBALS
##########################################
LOG = log.setup_custom_logger('telemetry')
LOG.setLevel(logging.WARN)

class TelemetryHandler():
    def __init__(self, radio, imu, pilot, gps):
        self.threadAlive = True
        
        self.radio = radio
        self.imu = imu
        self.pilot = pilot
        self.gps = gps

        self.message = ""
        self.image = ""

        self.broadcast_interval = 0.2
        self.telemConstructor = {
            "orientation": {
                "interval": 0,
                "last_sent": 0
            },
            "wing": {
                "interval": 0,
                "last_sent": 0
            },
            "gps": {
                "interval": 30,
                "last_sent": 0
            },
            "completegps": {
                "interval": 300,
                "last_sent": 0
            },
            "image": {
                "interval": 0, # use 0 to send data if it exists, every chance you get
                "last_sent": 0
            },
            "msg": {
                "interval": 0,
                "last_sent": 0
            }
        }


    def setMessage(self, msg):
        self.message += msg


    def setImage(self, img):
        if self.image == "":
            self.image = img
        else:
            LOG.error("image set before finished broadcasting")


    def checkIfSend(self, telConsKey):
        timeNow = time.time()
        # Determine if it should be sent
        timeSinceSent = timeNow - self.telemConstructor[telConsKey]['last_sent']
        send = timeSinceSent > self.telemConstructor[telConsKey]['interval']
        # Reset last sent, if send is true
        if send:
            self.telemConstructor[telConsKey]['last_sent'] = timeNow
        return send


    def constructTelemetry(self):
        telemObj = {}
        # Create telemetry strings for all parts
        if self.checkIfSend("orientation"):
            telemObj["O"] = self.genTelemStr_orientation()
        if self.checkIfSend("wing"):
            telemObj["W"] = self.genTelemStr_wing()
        if self.checkIfSend("gps"):
            telemObj["G"] = self.genTelemStr_gps()
        if self.checkIfSend("image"):
            telemObj["I"] = self.genTelemStr_image()
        if self.checkIfSend("msg"):
            telemObj["M"] = self.genTelemStr_msg()
        # Deconstruct the object to a string
        telemStr = ""
        for k in telemObj:
            telemStr += "%s=%s&" % (k, telemObj[k])
        return telemStr


    ######################################################################
    # Telemetry Generators
    def genTelemStr_orientation(self):
        telStr = "%2.1f_%2.1f_%2.1f" % (
            math.degrees(self.imu.roll), 
            math.degrees(self.imu.pitch), 
            math.degrees(self.imu.yaw))
        return telStr

    def genTelemStr_wing(self):
        telStr = "%2.1f_%2.1f" % (
            self.pilot.wing_param['left']['current'], 
            self.pilot.wing_param['right']['current'])
        return telStr

    def genTelemStr_gps(self):
        telStr = "%s_%s_%s_%s" % (
            self.gps.gps_data['lat'], 
            self.gps.gps_data['lon'], 
            self.gps.gps_data['alt'], 
            self.gps.gps_data['fixQual'],
        )
        return telStr

    def genTelemStr_image(self):
        telStr = ""
        return telStr

    def genTelemStr_msg(self):
        telStr = ""
        if self.message:
            telStr = self.message[:50] # enforce some length on it.. though it shouldn't be a problem
            self.message = ""
        return telStr
    # END --------
    ######################################################################


    def telemLoop(self):
        while self.threadAlive:
            try:
                telemString = self.constructTelemetry()
                LOG.debug("Created telemetry: %s" % telemString)
                self.radio.write(telemString)
                LOG.debug("TelemConst: %s" % json.dumps(self.telemConstructor, indent=2))
            except Exception, e:
                LOG.error(e)
            time.sleep(self.broadcast_interval)

    def start(self):
        LOG.info("Starting Telemetry thread")
        threadT = Thread( target=self.telemLoop, args=() )
        self.threadAlive = True
        threadT.start()

    def stop(self):
        self.threadAlive = False

#---------- END CLASS -------------
