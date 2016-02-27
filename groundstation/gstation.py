#!/usr/bin/python
##############################################
#
# Glider GroundStation Software
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################

import sys
sys.path.append("/home/dvagg/Dropbox/satellite/")

import math
import time
import json
import signal
import logging
import argparse
import traceback
import gsettings

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver

import sat_radio
from packet_handlers import TelemetryHandler, ImageHandler, DataHandler

#####################################
# GLOBALS
#####################################
RADIO = None
SOCKETS = []
RAWFILE = "output/raw.data"
TelemetryHandler = TelemetryHandler()
ImageHandler = ImageHandler()
DataHandler = DataHandler()


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
    RADIO = sat_radio.SatRadio(xbee_path, "GliderGroundstation", callback=data_handler)

def shutdown():
    logging.debug("Shutting down components")
    if RADIO:
        logging.debug("Shutting down RADIO")
        RADIO.stop()


#####################################
# Data Handler
#####################################
def data_handler(packet):
    logging.debug("I received raw data: %s" % packet)
    try:
        with open(RAWFILE, "a") as rawFile:
            rawFile.write("%s"% packet)
        parse_packet(packet)
        push_data()
    except Exception, e:
        traceback.print_exc(file=sys.stdout)


def parse_packet(data):
    if 'rf_data' not in data.keys():
        return
    packet = data['rf_data']
    logging.debug("Parsing packet data: %s" % packet)
    dataDict = {}
    data_parts = packet.split("|")
    packet_type = data_parts[0]
    packet_data = data_parts[1:]
    if packet_type == "T":
        TelemetryHandler.parse(packet_data)
    if packet_type == "I":
        ImageHandler.parse(packet_data)
    if packet_type == "D":
        DataHandler.parse(packet_data)
    

def push_data():
    data_dictionary = {}
    data_dictionary.update(TelemetryHandler.get_dict())
    data_dictionary.update(ImageHandler.get_dict())
    data_dictionary.update(DataHandler.get_dict())
    for socket in SOCKETS:
        socket.write_message(data_dictionary)
    logging.debug("Current Telem: %s" % json.dumps(data_dictionary, indent=2))


###################################
# COMMAND HANDLERS
###################################
def sendCommand(command):
    glider_addr = RADIO.ADDR_GLIDER
    response = RADIO.send_packet(command, address=glider_addr)
    logging.debug("Command response: %s" % response)

def sendCommand_pitch(pitch):
    return sendCommand("PA_%2.2f" % pitch)

def sendCommand_state(state):
    return sendCommand("O_%s" % state)

def sendCommand_severity(severity):
    return sendCommand("TS_%s" % severity)

def sendCommand_location(lon, lat):
    return sendCommand("DEST_%s_%s" % (lon, lat))

def sendCommand_get_image(image):
    return sendCommand("IMAGE")

#################################
# Configure Logging for pySel
#################################
def configureLogging(numeric_level):
    if not isinstance(numeric_level, int):
        numeric_level = 0
    logging.basicConfig(
        level=numeric_level, format='%(asctime)s [%(levelname)s in %(module)s] %(message)s',  datefmt='%Y/%m/%dT%I:%M:%S')


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'xbee', action='store', help='Path to XBee interface', default="/dev/ttyUSB0")
    parser.add_argument('-v', '--verbose', action='count',
                        default=0, help='Increases verbosity of logging.')

    return parser




#####################################
# WEB SERVER
#####################################


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/getTelem", TelemHandler),
            (r"/getTelemSocket", TelemHandlerSocket),
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
        self.write(json.dumps(CURRENT_TELEM))


class TelemHandlerSocket(tornado.websocket.WebSocketHandler):

    def open(self):
        print "WebSocket opened"
        SOCKETS.append(self)

    def on_close(self):
        print "WebSocket closed"
        SOCKETS.remove(self)


class CommandHandler(tornado.web.RequestHandler):

    def post(self):
        pitch = self.get_argument('pitch', None)
        state = self.get_argument('state', None)
        severity = self.get_argument('severity', None)
        lon = self.get_argument('lon', None)
        lat = self.get_argument('lat', None)
        image = self.get_argument('image', None)

        if pitch:
            response = sendCommand_pitch(pitch)
        if state:
            response = sendCommand_state(state)
        if severity:
            response = sendCommand_severity(severity)
        if lon and lat:
            response = sendCommand_location(lon, lat)
        if image:
            response = sendCommand_get_image(image)
        self.set_status(200)
        self.redirect('/')


def runWebServer():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    print "GO TO: http://localhost:8888/"
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

    signal.signal(signal.SIGINT, signal_handler_quit)  # Manage Ctrl+C
    configureLogging(loglevel)

    startup(xbee_path)
    runWebServer()
    sys.exit(0)


if __name__ == "__main__":
    main()
