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
import urllib
import logging
import argparse
import requests
import traceback
from datetime import datetime
from urlparse import urljoin

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver

import site_settings
from packet_handlers import TelemetryHandler, DataHandler

GPIO = None
try:
    import RPi.GPIO as GPIO
except:
    pass

LOG = log.setup_custom_logger('online_station')
LOG.setLevel(logging.DEBUG)

#####################################
# GLOBALS
#####################################
RADIO = None
SOCKETS = []
RAWFILE = "output/raw.data"
TelemetryHandler = TelemetryHandler()
DataHandler = DataHandler()
LED_ON = 12
LED_TX = 13
LED_RX = 15

RemoteServerURL = "http://tracker.spacescience.ie/"

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
    RADIO = sat_radio.SatRadio(xbee_path, "Groundstation", callback=data_handler)

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


def parse_packet(raw_packet):
    if 'rf_data' not in raw_packet.keys():
        return
    data_packet = raw_packet['rf_data']
    source = raw_packet['source_addr']
    time_received = int(time.time())
    source = "%s" % source.encode('hex')
    LOG.debug("Parsing packet data: %s" % data_packet)
    dataDict = {}
    data_parts = data_packet.split("|")
    packet_type = data_parts[0]
    packet_data = data_parts[1:]
    push_data(source, packet_type, packet_data, time_received)
    handle_parsed_packet(source, packet_type, packet_data, time_received)


def handle_parsed_packet(source, packet_type, packet_data, time_received):
    if GPIO:
        GPIO.output(LED_RX, True)
    if packet_type == "T":
        TelemetryHandler.parse(source, packet_data, time_received)
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
        grequests.post(remote_post_url, json=send_packet, timeout=10)
    except Exception, e:
        LOG.error(e)
    if GPIO:
        GPIO.output(LED_TX, False)


def get_data(): # Called from clients
    data_dictionary = TelemetryHandler.get_all_dict()
    return data_dictionary


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
            "template_path": site_settings.TEMPLATE_PATH,
            "static_path": site_settings.STATIC_PATH,
            "debug": True,
        }
        handlers = [
            (r"/", MainHandler),
            (r"/basic", BasicHandler),
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': site_settings.STATIC_PATH}),
            (r"/getTelem", TelemHandler),
            (r"/getPredict", PredictHandler),
            (r"/getPredictLand", PredictLandHandler),
            (r"/updateTelem", TelemUpdateHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")

class BasicHandler(tornado.web.RequestHandler):

    def get(self):
        data = TelemetryHandler.get_all_dict()
        self.render("basic.html", data=data)

class TelemHandler(tornado.web.RequestHandler):

    def get(self):
        self.write(json.dumps(TelemetryHandler.get_all_dict()))


class TelemUpdateHandler(tornado.web.RequestHandler):

    def post(self):
        try:
            body = self.request.body
            web_packet = tornado.escape.json_decode(body)
            secret_sauce = web_packet.get("secret_sauce")
            LOG.debug("Received packet over internet: %s" % web_packet)
            if secret_sauce == "captainmorgan":
                handle_parsed_packet(
                    web_packet['source'], web_packet['packet_type'], 
                    web_packet['packet_data'], web_packet['time_received']
                )
        except Exception, e:
            LOG.error(traceback.format_exc())


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
