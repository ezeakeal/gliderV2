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
import traceback
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
                # use 0 to send data if it exists, every chance you get
                "interval": 0,
                "last_sent": 0
            },
            "msg": {
                "interval": 0,
                "last_sent": 0
            }
        }

    def setMessage(self, msg):
        self.message += msg

    def sendImage(self, img):
        if self.image == "":
            self.image = img
        else:
            LOG.error("image set before finished broadcasting")

    def checkIfSend(self, telConsKey):
        timeNow = time.time()
        # Determine if it should be sent
        timeSinceSent = timeNow - \
            self.telemConstructor[telConsKey]['last_sent']
        send = timeSinceSent > self.telemConstructor[telConsKey]['interval']
        # Reset last sent, if send is true
        if send:
            self.telemConstructor[telConsKey]['last_sent'] = timeNow
        return send

    def constructTelemetry(self):
        telemObj = {}
        # Create telemetry strings for all parts
        telemObj["T"] = self.genTelemStr_timestamp()
        if self.checkIfSend("orientation"):
            telemObj["O"] = self.genTelemStr_orientation()
        if self.checkIfSend("wing"):
            telemObj["W"] = self.genTelemStr_wing()
        if self.checkIfSend("gps"):
            telemObj["G"] = self.genTelemStr_gps()
        if self.checkIfSend("msg"):
            telemObj["M"] = self.genTelemStr_msg()
        return hhmmss, lon_dec_deg, lat_dec_deg, lat_dil, alt, temp1, temp2, pressure

    ######################################################################
    # Telemetry Generators
    def genTelemStr_timestamp(self):
        telStr = "%s" % int(round(time.time() * 1000))
        return telStr

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
        try:
            data = self.gps.gpsd
            telStr = "%s_%s_%s" % (
                float(data.fix.latitude) / 100,
                float(data.fix.longitude) / (-100),
                data.fix.altitude,
            )
        except:
            telStr = ""
        return telStr

    def genTelemStr_msg(self):
        telStr = ""
        if self.message:
            # enforce some length on it.. though it shouldn't be a problem
            telStr = self.message[:50]
            self.message = ""
        return telStr
    # END --------
    ######################################################################

    def telemLoop(self):
        while self.threadAlive:
            try:
                hhmmss, lon_dec_deg, lat_dec_deg, lat_dil, alt, temp1, temp2, pressure = self.constructTelemetry()
                self.radio.send_telem(hhmmss, lon_dec_deg, lat_dec_deg, lat_dil, alt, temp1, temp2, pressure)
            except:
                LOG.error(traceback.format_exc())
            time.sleep(self.broadcast_interval)

    def start(self):
        LOG.info("Starting Telemetry thread")
        threadT = Thread(target=self.telemLoop, args=())
        self.threadAlive = True
        threadT.start()

    def stop(self):
        self.threadAlive = False

#---------- END CLASS -------------
