#!/usr/bin/python
##############################################
#
# Glider GroundStation Software 
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################

import sys
import math
import time
import json
import signal
import logging
import argparse
import traceback
import gsettings

import tornado.httpserver
import tornado.ioloop
import tornado.web

from transceiver import Transceiver

#####################################
# GLOBALS
#####################################
RADIO = None
TELEMFILE = "telem.raw"
LAST_TELEM = None
CURRENT_TELEM = {}


#####################################
# UTIL
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
    logging.info("Shutting down GroundStation")
    shutdown()
    sys.exit(0)


def startup(xbee_path):
    global RADIO
    
    if not DRYRUN:
        RADIO = Transceiver(xbee_path, 9600, datahandler=data_handler)
        logging.debug("Created Radio instance")
    
    if RADIO:
        logging.debug("Starting up Radio")
        RADIO.start()


def shutdown():
    logging.debug("Shutting down components")
    if RADIO and not DRYRUN:
        logging.debug("Shutting down RADIO")
        RADIO.stop()


def parse_data(raw_data):
    dataDict = {}
    msgParts = raw_data.split("&")
    for dat in msgParts:
        dataParts = dat.split("=")
        dataKey = dataParts[0]
        dataVal = "=".join(dataParts[1:])
        # Conditionally load the dataDictionary
        if (dataKey == "O"):
            dataDict['orientation'] = parseTelemStr_orientation(dataVal)
        if (dataKey == "W"):
            dataDict['wing'] = parseTelemStr_wing(dataVal)
        if (dataKey == "G"):
            dataDict['gps'] = parseTelemStr_gps(dataVal)
        if (dataKey == "I"):
            dataDict['image'] = parseTelemStr_image(dataVal)
        if (dataKey == "M"):
            dataDict['msg'] = parseTelemStr_msg(dataVal)
    return dataDict

###################################
# TELEM PARSERS
###################################
def parseTelemStr_orientation(telemStr):
    dataObj = {}
    telemStrParts = telemStr.split("_")
    dataObj['O_R'] = telemStrParts[0]
    dataObj['O_P'] = telemStrParts[1]
    dataObj['O_Y'] = telemStrParts[2]
    return dataObj

def parseTelemStr_wing(telemStr):
    dataObj = {}
    telemStrParts = telemStr.split("_")
    dataObj['W_L'] = telemStrParts[0]
    dataObj['W_R'] = telemStrParts[1]
    return dataObj
    
def parseTelemStr_gps(telemStr):
    dataObj = {}
    telemStrParts = telemStr.split("_")
    dataObj['G_LAT'] = telemStrParts[0]
    dataObj['G_LON'] = telemStrParts[1]
    dataObj['G_ALT'] = telemStrParts[2]
    dataObj['G_QTY'] = telemStrParts[3]
    return dataObj

def parseTelemStr_image(telemStr):
    dataObj = None
    return dataObj

def parseTelemStr_msg(telemStr):
    dataObj = None
    return dataObj


###################################
# COMMAND HANDLERS
###################################
def sendCommand_pitch(pitch):
    res = RADIO.write("PA_%2.2f" % pitch)
    return res

def sendCommand_state(state):
    res = RADIO.write("O_%s" % state)
    return res

def sendCommand_severity(severity):
    res = RADIO.write("TS_%s" % severity)
    return res

def sendCommand_location(lon, lat):
    res = RADIO.write("DEST_%s_%s" % (lon, lat))
    return res


#################################
# Configure Logging for pySel
#################################
def configureLogging(numeric_level):
    if not isinstance(numeric_level, int):
        numeric_level=0
    logging.basicConfig(level=numeric_level, format='%(asctime)s [%(levelname)s in %(module)s] %(message)s',  datefmt='%Y/%m/%dT%I:%M:%S')
    

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('xbee', action='store', help='Path to XBee interface', default="/dev/ttyUSB0")
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of logging.')
    parser.add_argument('-d', '--dry', action='store_true', help='Do not set up the radio.')
    
    return parser


#####################################
# Data Handler
#####################################
def data_handler(data):
    global CURRENT_TELEM, LAST_TELEM
    logging.debug("I received raw data: %s" % data)
    
    parsed_data = parse_data(data)
    logging.debug("Parsed data: %s" % parsed_data)
    
    if parsed_data:
        LAST_TELEM = parsed_data
        CURRENT_TELEM.update(LAST_TELEM)
    with open(TELEMFILE, "a") as telemFile:
        telemFile.write(data)
    logging.debug("Current Telem: %s" % json.dumps(CURRENT_TELEM, indent=2))


def generateFakeTelem():
    global CURRENT_TELEM
    millis = time.time()
    orientation = parseTelemStr_orientation("%s_%s_%s" % (
        math.sin(millis)*10, math.cos(millis)*5, math.cos(millis/2)))
    wing = parseTelemStr_wing("%s_%s" % (
        90 + math.sin(millis) * 90, 90 + math.cos(millis) * 90))
    gps = parseTelemStr_gps("%s_%s_%s_%s" % (
        30+math.sin(millis*2), -7+math.sin(millis/2), math.sin(millis*2)*500, 1))
    
    CURRENT_TELEM.update({"wing": wing, "gps": gps, "orientation": orientation})

#####################################
# WEB SERVER
#####################################
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/getTelem", TelemHandler),
            (r"/postCommand", CommandHandler),
        ]
        settings = {
            "template_path": gsettings.TEMPLATE_PATH,
            "static_path": gsettings.STATIC_PATH,
            "debug": True,
        }
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class TelemHandler(tornado.web.RequestHandler):
    def get(self):
        millis = time.time() * 10
        if DRYRUN:
            generateFakeTelem()
        self.write(json.dumps(CURRENT_TELEM))

class CommandHandler(tornado.web.RequestHandler):
    def post(self):
        pitch = self.get_argument('pitch', None)
        state = self.get_argument('state', None)
        severity = self.get_argument('severity', None)
        lon = self.get_argument('lon', None)
        lat = self.get_argument('lat', None)

        if not DRYRUN:
            if pitch:
                response = sendCommand_pitch(pitch)
            if state:
                response = sendCommand_state(state)
            if severity:
                response = sendCommand_severity(severity)
            if lon and lat:
                response = sendCommand_location(lon, lat)
        else:
            response = "Dryrun.."

        self.set_status(200)
        self.redirect('/?msg=%s' % response)

def runWebServer():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


#####################################
# MAIN
#####################################
def main():
    global DRYRUN

    parser = createParser()
    results = parser.parse_args()
    # Use the args
    loglevel = results.verbose
    xbee_path = results.xbee
    DRYRUN = results.dry
    
    signal.signal(signal.SIGINT, signal_handler_quit) # Manage Ctrl+C
    configureLogging(loglevel)

    startup(xbee_path)
    runWebServer()
    sys.exit(0)


if __name__ == "__main__":
    main()