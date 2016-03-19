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
        self.glider_state = None

        self.glider_data_interval = 1
        self.glider_data_lastsent = time.time()
        self.telemetry_interval = 60
        self.telemetry_lastsent = time.time()

    def genTelemStr_orientation(self):
        telStr = "O:%2.1f_%2.1f_%2.1f" % (
            math.degrees(self.imu.roll),
            math.degrees(self.imu.pitch),
            math.degrees(self.imu.yaw))
        return telStr

    def genTelemStr_wing(self):
        telStr = "W:%2.1f_%2.1f" % (
            self.pilot.wing_param['left']['current'],
            self.pilot.wing_param['right']['current'])
        return telStr

    def send_glider_data(self):
        data = [
            self.genTelemStr_orientation(), 
            self.genTelemStr_wing(), 
            "S:%s" % self.glider_state
        ]
        self.radio.send_data(data)

    def send_telemetry(self):
        hhmmss = int(time.strftime("%H%M%S"))
        gps_fix = self.gps.getFix()
        lon_dec_deg, lat_dec_deg = self.gps.getLonLatDeg()
        alt = gps_fix.altitude
        lat_dil = gps_fix.epx
        temp1 = 0
        temp2 = 0
        pressure = 0
        self.radio.send_telem(hhmmss, lon_dec_deg, lat_dec_deg, lat_dil, alt, temp1, temp2, pressure)

    def set_state(self, state):
        self.glider_state = state

    def telemLoop(self):
        while self.threadAlive:
            try:
                now = time.time()
                if now - self.glider_data_lastsent > self.glider_data_interval:
                    self.send_glider_data()
                    self.glider_data_lastsent = now
                if now - self.telemetry_lastsent > self.telemetry_interval:
                    self.send_telemetry()
                    self.telemetry_lastsent = now
            except:
                LOG.error(traceback.format_exc())
            time.sleep(0.1)

    def start(self):
        LOG.info("Starting Telemetry thread")
        threadT = Thread(target=self.telemLoop, args=())
        self.threadAlive = True
        threadT.start()

    def stop(self):
        self.threadAlive = False

#---------- END CLASS -------------
