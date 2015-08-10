##############################################
#
# Glider GroundStation Software 
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################
import os
import sys
import time
import json
import logging
import calendar
import threading
import traceback
from datetime import datetime
            
#####################################
# GLOBALS
#####################################
DEVICES = []
LISTEN_THREADS = []
RUN = False
COMMAND_PIPE = "./command.pipe"

#####################################
# FUNCTIONS
#####################################
def load_listeners():
    global LISTEN_THREADS
    for device in DEVICES:
        t = threading.Thread(target=transceiverLoop, args=(device,))
        t.daemon = True
        LISTEN_THREADS.append(t)        
        
def start_listening():
    global RUN
    RUN = True
    for thread in LISTEN_THREADS:
        time.sleep(.1) # splay them a bit
        thread.start()

def stop_listening():
    global RUN
    RUN = False

def parseResponse(dataString, device):
    print "Radio(%s) received response: " % (device['NAME'])
    print dataString
    
def parseData(dataString):
    corrupt = False
    data = {}
    
    if "|" not in dataString:
        corrupt = True
    else:
        try:
            lastSep = dataString[::-1].index("|") # reverse lookup of | character
            dataLength = len(dataString[:-lastSep])
            msgType, index, millis, gpsString, pressure, thermister, temperature, size = dataString.rstrip().split("|")
            data['index'] = int(index)
            data['millis'] = int(millis)
            data['epoch'] = int(time.time()) # epoch when received!
            data['pressure'] = pressure
            data['thermister'] = thermister
            data['temperature'] = temperature
            data['gpsString'] = gpsString
            data['gpsEpoch'] = None
            data['gps'] = None
            data['size'] = size

            if "GPGGA" in gpsString and "*" in gpsString:
                gpsData, checksum = gpsString.split("*")
                minSen, fixTime, lat, latOr, lon, lonOr, gpsQual, numSat, horDil, altMeanSea, aMS_m, altGeoid, aG_m, age, refStation = gpsData.split(",")
                # convert the fixtime to an epoch
                gpsEpoch = None
                if fixTime:
                    dt = datetime.strptime(fixTime, "%H%M%S.%f")
                    dt_now = datetime.now()
                    dt = dt.replace(year=dt_now.year, month=dt_now.month, day=dt_now.day)
                    gpsEpoch = calendar.timegm(dt.utctimetuple())
                data['gpsEpoch'] = gpsEpoch
                # convert lat and lon to suitable units and signs
                if lat and lon:
                    lat, lon = correctLatLonToDDD(lat, latOr, lon, lonOr) 
                # now store the data for the epoch and gps fix
                data['gps'] = {
                    "quality": gpsQual,
                    "lat": lat,
                    "lon": lon,
                    "alt": altGeoid, 
                    "horizontalDillution": horDil,
                    "numSat": numSat,
                    "checksum": checksum
                }
            
            if int(size) != dataLength:
                raise Exception("Packet size mismatch")
        except Exception, e:
            print "ERROR: %s" % e
            traceback.print_exc(file=sys.stdout)
            corrupt = True

    return data, corrupt

def correctLatLonToDDD(lat, latOr, lon, lonOr):
    newLat = 0
    newLon = 0

    newLat = float(lat[0:lat.index(".") - 2])
    newLat += float(lat[lat.index(".") - 2:-1])/60
    newLon = float(lon[0:lon.index(".") - 2])
    newLon += float(lon[lon.index(".") - 2:-1])/60
    if lonOr == "W": newLon *= -1
    if latOr == "S": newLat *= -1
    return newLat, newLon

####################################
# THREADED FUNCTIONS
####################################
def transceiverLoop(device): 
    lastCompletePacket = 0
    data_path = device['DATA']
    raw_path = device['RAW']
    while RUN:
        # check if there is a message to be sent and send it
        with open(COMMAND_PIPE, "r") as commPipe:
            commands = commPipe.readlines()
        if len(commands) > 0:
            lastCommand = commands[-1]
            deviceCommand = lastCommand.rstrip()
            print "Transmitting command(%s) via %s"  % (deviceCommand, device['NAME'])
            transmitted = device['COMM'].transmit(deviceCommand)
            if transmitted:
                del commands[-1]
        with open(COMMAND_PIPE, "w") as commPipe:
            commPipe.write("\n".join(commands))
            

        # readTelemetry and operate on it
        dataString = device['COMM'].readTelem()
        if not dataString:
            continue
        with open(raw_path, "a") as rawOut:
            rawOut.write(dataString + "\n")
        # Check the first character to see if it's telemetry or a response
        if dataString[0] == "R":
            parseResponse(dataString, device)
        if dataString[0] == "T":
            data, corrupt = parseData(dataString)
            if corrupt:
                device['COMM'].requestRepeat(lastCompletePacket+1)
            else:
                packetIndex = data['index']
                lastCompletePacket = int(packetIndex)
                with open(data_path, "a") as dataOut:
                    dataOut.write(json.dumps(data) + "\n")
        
        time.sleep(.5)
    print "Ending"
    return

