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


#####################################
# UTIL
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
    logging.info("Shutting down GroundStation")
    shutdown()
    sys.exit(0)


def startup():
    global RADIO
    # RADIO = Transceiver(xbee_path, 9600, datahandler=data_handler)
    logging.debug("Created Radio instance")
    
    if RADIO:
        logging.debug("Starting up Radio")
        RADIO.start()


def shutdown():
    logging.debug("Shutting down components")
    if RADIO:
        RADIO.stop()


def parse_data(raw_data):
    return raw_data


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
    logging.debug("I received raw data: %s" % data)
    parsed_data = parse_data(data)
    logging.debug("Parsed data: %s" % parsed_data)
    if parsed_data:
        LAST_TELEM = parsed_data
        with open(TELEMFILE) as telemFile:
            telemFile.write(parsed_data)


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
        telem = {
            "lat": (53.2769317 + math.cos(millis)*.0001),
            "lon": (-6.2179775 + math.cos(millis)*.005),
            "alt": (20000 + math.cos(millis)*100),
            "O_P": math.cos(millis)*5, # 
            "O_R": math.sin(millis)*3, # roll
            "O_Y": math.sin(millis),
        }
        self.write(json.dumps(telem))

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

    startup()
    runWebServer()
    sys.exit(0)


if __name__ == "__main__":
    main()