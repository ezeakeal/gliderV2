#!/usr/bin/python
##############################################
#
# Glider GroundStation Software
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################

import sys
import log
import math
import time
import json
import signal
import logging
import argparse
import traceback
from datetime import datetime
from urlparse import urljoin

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver

import gsettings
from packet_handlers import TelemetryHandler, ImageHandler, DataHandler

GPIO = None
try:
    import RPi.GPIO as GPIO
except:
    print "Exception import RPI"

LOG = log.setup_custom_logger('groundstation')
LOG.setLevel(logging.WARNING)

#####################################
# GLOBALS
#####################################
RADIO = None
SOCKETS = []
RAWFILE = "output/raw.data"
TelemetryHandler = TelemetryHandler()
ImageHandler = ImageHandler()
DataHandler = DataHandler()
LED_ON = 12
LED_TX = 13
LED_RX = 15

RemoteServerURL = "http://tracker.ez.lv/"

#####################################
# UTIL
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
    LOG.info("Shutting down GroundStation")
    shutdown()
    sys.exit(0)

def startup_xbee(xbee_path):
    global RADIO
    import sat_radio
    RADIO = sat_radio.SatRadio(xbee_path, "GliderGroundstation", callback=data_handler)

def shutdown():
    LOG.debug("Shutting down components")
    if GPIO:
        GPIO.output(LED_ON, False) ## Turn on GPIO pin 7
    if RADIO:
        LOG.debug("Shutting down RADIO")
        RADIO.stop()


#####################################
# Data Handler
#####################################
def data_handler(packet):
    LOG.debug("I received raw data: %s" % packet)
    try:
        with open(RAWFILE, "a") as rawFile:
            rawFile.write("%s\n" % packet)
        parse_packet(packet)
    except Exception, e:
        traceback.print_exc(file=sys.stdout)


def parse_packet(data):
    if 'rf_data' not in data.keys():
        return
    data_packet = data['rf_data']
    source = data['source_addr']
    time_received = int(time.time())
    source = "%s" % source.encode('hex')
    LOG.debug("Parsing packet data: %s" % data_packet)

    dataDict = {}
    data_parts = data_packet.split("|")
    packet_type = data_parts[0]
    packet_data = data_parts[1:]
    push_data(source, packet_type, packet_data, time_received)
    push_data_gstation()
    handle_parsed_packet(source, packet_type, packet_data, time_received)
    

def handle_parsed_packet(source, packet_type, packet_data, time_received):
    if GPIO:
        GPIO.output(LED_RX, True)
    if packet_type == "T":
        TelemetryHandler.parse(source, packet_data, time_received)
    if packet_type == "I":
        ImageHandler.parse(source, packet_data, time_received)
    if packet_type == "D":
        DataHandler.parse(source, packet_data, time_received)
    if GPIO:
        GPIO.output(LED_RX, False)


def push_data(source, packet_type, packet_data, time_received):
    remote_post_url = urljoin(RemoteServerURL, "updateTelem")
    send_packet = {
        "secret_sauce": "captainmorgan",
        "source": source,
        "packet_type": packet_type,
        "packet_data": packet_data,
        "time_received": time_received
    }
    LOG.debug("Posting data to server: %s" % send_packet)
    if GPIO:
        GPIO.output(LED_TX, True)
    try:
        response = requests.post(remote_post_url, json=send_packet, timeout=1)
    except:
        pass
    if GPIO:
        GPIO.output(LED_TX, False)


def push_data_gstation():
    data_dictionary = {}
    all_data = TelemetryHandler.get_all_dict()
    data_dictionary.update(all_data.get("GliderV2", {}))
    data_dictionary.update({"all_data": all_data})
    data_dictionary.update(ImageHandler.get_dict())
    data_dictionary.update(DataHandler.get_dict())
    for socket in SOCKETS:
        socket.write_message(data_dictionary)


def get_data(): # Called from clients
    data_dictionary = TelemetryHandler.get_all_dict()
    return data_dictionary


###################################
# COMMAND HANDLERS
###################################
def sendCommand(command, dest_addr=None):
    if not dest_addr:
        dest_addr = RADIO.ADDR_GLIDER
    LOG.debug("Sending command: '%s' to (%s)" % (command, dest_addr))
    command = "".join([chr(ord(c)) for c in command]) # YES ITS THE FUCKING SAME
    # But no.. it's not. Not if the string comes from the dropdown list in the 
    # web page. Because even though the characters are what you'd expect.. they
    # arent the same. I compared and checked.. it's black magic.
    response = RADIO.send_packet("%s" % command, address=dest_addr)
    LOG.debug("Command response: %s" % (response))

def sendCommand_pitch(pitch):
    return sendCommand("PA|%2.2f" % pitch)

def sendCommand_state(state):
    return sendCommand("O|%s" % state)

def sendCommand_severity(severity):
    return sendCommand("TS|%s" % severity)

def sendCommand_location(lon, lat):
    return sendCommand("DEST|%s|%s" % (lon, lat))

def sendCommand_burn(image):
    return sendCommand("BURN|0", dest_addr=RADIO.ADDR_CANSAT_1)

def sendCommand_get_image(image):
    return sendCommand("IMAGE|0")

#################################
# Util
#################################
def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--xbee', action='store', 
        required=False,
        help='Path to XBee interface'
    )
    parser.add_argument(
        '--server', action='store_true',
    )
    parser.add_argument(
        '--port', '-p', default=8000,
        type=int, help="Server port"
    )
    parser.add_argument(
        '-v', '--verbose', action='count',
        default=0, help='Increases verbosity of logging.'
    )
    return parser

#####################################
# WEB SERVER
#####################################


class Application(tornado.web.Application):

    def __init__(self):
        settings = {
            "template_path": gsettings.TEMPLATE_PATH,
            "static_path": gsettings.STATIC_PATH,
            "debug": True,
        }
        handlers = [
            (r"/", MainHandler),
            (r"/map", MapHandler),
            (r"/basic", BasicHandler),
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': gsettings.STATIC_PATH}),
            (r"/getTelem", TelemHandler),
            (r"/getTelemSocket", TelemHandlerSocket),
            (r"/getPredict", PredictHandler),
            (r"/getPredictLand", PredictLandHandler),
            (r"/postCommand", CommandHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


class MapHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("map.html")


class BasicHandler(tornado.web.RequestHandler):

    def get(self):
        data = TelemetryHandler.get_all_dict()
        self.render("basic.html", data=data)


class TelemHandler(tornado.web.RequestHandler):

    def get(self):
        self.write(json.dumps(TelemetryHandler.get_all_dict()))


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
        state = self.get_argument('select_state', None)
        severity = self.get_argument('severity', None)
        lon = self.get_argument('lon', None)
        lat = self.get_argument('lat', None)
        image = self.get_argument('image', None)
        burn = self.get_argument('burn', None)

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
        if burn:
            response = sendCommand_burn(burn)
        self.set_status(200)
        self.redirect('/')


class PredictHandler(tornado.web.RequestHandler):
    def post(self):
        my_data = self.request.arguments
        LOG.debug("Received my_data: %s" % my_data)
        requrl="http://predict.habhub.org/ajax.php?action=submitForm"
        payload = {
            "launchsite": "Other",
            "lat": my_data['lat'][0],
            "lon": my_data['lon'][0],
            "initial_alt": my_data['alt'][0],
            "hour": datetime.now().hour,
            "min": datetime.now().min,
            "second": datetime.now().second,
            "day": datetime.now().day,
            "month": datetime.now().month,
            "year": datetime.now().year,
            "ascent": 5,
            "burst": 24000,
            "drag": 5,
            "submit": "Run Prediction"
        }
        res = requests.post(requrl, data=payload)
        res.raise_for_status()
        predict_url = "http://predict.habhub.org/#!/uuid=%s" % res.json()['uuid']
        LOG.debug("Sending to %s" % predict_url) 
        self.write(predict_url)


class PredictLandHandler(tornado.web.RequestHandler):
    def post(self):
        my_data = self.request.arguments
        LOG.debug("Received my_data: %s" % my_data)
        requrl="http://predict.habhub.org/ajax.php?action=submitForm"
        payload = {
            "launchsite": "Other",
            "lat": my_data['lat'][0],
            "lon": my_data['lon'][0],
            "initial_alt": my_data['alt'][0],
            "hour": datetime.now().hour,
            "min": datetime.now().min,
            "second": datetime.now().second,
            "day": datetime.now().day,
            "month": datetime.now().month,
            "year": datetime.now().year,
            "ascent": 5,
            "burst": my_data['alt'][0],
            "drag": 5,
            "submit": "Run Prediction"
        }
        res = requests.post(requrl, data=payload)
        res.raise_for_status()
        predict_url = "http://predict.habhub.org/#!/uuid=%s" % res.json()['uuid']
        LOG.debug("Sending to %s" % predict_url) 
        self.write(predict_url)
     

def runWebServer(port):
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    print "GO TO: http://localhost:%s/" % port
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()


#####################################
# MAIN
#####################################
def main():
    parser = createParser()
    results = parser.parse_args()
    if GPIO:
        GPIO.setmode(GPIO.BOARD)

    # Use the args
    loglevel = results.verbose
    xbee_path = results.xbee

    signal.signal(signal.SIGINT, signal_handler_quit)  # Manage Ctrl+C
    if xbee_path:
        print "Running with radio at: %s" % xbee_path
        startup_xbee(xbee_path)
    # Configure the GPIO
    if GPIO:
        GPIO.setup(LED_ON, GPIO.OUT)
    for led_ID in [LED_ON, LED_RX, LED_TX]:
        if GPIO:
            GPIO.setup(led_ID, GPIO.OUT) ## Setup GPIO to OUT

    if GPIO:
        GPIO.output(LED_ON,True)
    runWebServer(results.port)
    sys.exit(0)


if __name__ == "__main__":
    main()
