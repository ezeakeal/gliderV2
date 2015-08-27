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
    RADIO = Transceiver(xbee_path, 9600, datahandler=data_handler)
    logging.debug("Created Radio instance")
    
    if RADIO:
        logging.debug("Starting up Radio")
        RADIO.start()


def shutdown():
    logging.debug("Shutting down components")
    if RADIO:
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
        
        millis = time.time() * 10
        CURRENT_TELEM.update({"wing": {"W_L": (millis+5) % 180, "W_R": (millis/2) %180}})
    with open(TELEMFILE, "a") as telemFile:
        telemFile.write(data)
    logging.debug("Current Telem: %s" % json.dumps(CURRENT_TELEM, indent=2))


#####################################
# WEB SERVER
#####################################
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/getTelem", TelemHandler),
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
        self.write(json.dumps(CURRENT_TELEM))

def runWebServer():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


#####################################
# MAIN
#####################################
def main():
    parser = createParser()
    results = parser.parse_args()
    # Use the args
    loglevel = results.verbose
    xbee_path = results.xbee
    
    signal.signal(signal.SIGINT, signal_handler_quit) # Manage Ctrl+C
    configureLogging(loglevel)

    startup(xbee_path)
    runWebServer()
    sys.exit(0)


if __name__ == "__main__":
    main()