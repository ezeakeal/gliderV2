#!/usr/bin/python
##############################################
##############################################

import os
import json
import time
import requests
from urlparse import urljoin

TELEM_JSON = "/tmp/telem.json"
RemoteServerURL = "http://tracker.spacescience.ie/"
last_packet = {}

def push_data():
    global last_packet
    remote_post_url = urljoin(RemoteServerURL, "updateTelem")
    if not os.path.exists(TELEM_JSON):
        time.sleep(.1)
        return
    with open(TELEM_JSON, 'r') as telem:
        send_packet = json.load(telem)
    if last_packet != send_packet:
        last_packet = send_packet
        print "Pushing packet: %s" % json.dumps(send_packet)
        requests.post(remote_post_url, json=send_packet)

while True:
    try:
        push_data()
    except Exception, e:
        print e
        