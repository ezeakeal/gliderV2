##############################################
#
# CanSat Client Software 
# For use with launch of CanSat:
#   UCD, Space Science Masters, 2014
#
##############################################
import os
import stat
import time
import json
import pygmaps
import logging

#####################################
# GLOBALS
#####################################
DEVICES = []
lastPacket = None
lastGPSPacket = None
MAP_PATH = []
MAPFILE = os.path.join(os.getcwd(), "cSatMap.html")
PREDICT_FILE = os.path.join(os.getcwd(), "predict.sh")
PREDICT_FILE2 = os.path.join(os.getcwd(), "predict2.sh")

#####################################
# FUNCTIONS
#####################################
def initialize():
    with open(MAPFILE, "w") as m:
        m.write("")
    try:
        os.system("google-chrome %s" % MAPFILE)
    except:
        print """Problem loading chrome on map file. 
        Load the following file using your browser of choice (%s)""" % MAPFILE

def getLastComplete():
    global lastPacket
    for device in DEVICES:
        deviceDataPath = device['DATA']
        with open(deviceDataPath, "r") as data:
            for line in reversed(data.readlines()):
                try:
                    dataLine = json.loads(line)
                    if lastPacket and dataLine['index'] <= lastPacket['index'] - 5: # 5 older packets allowed in case of recalled data packets
                        break
                    if not lastPacket or dataLine['index'] > lastPacket['index']:
                        lastPacket = dataLine
                except:
                    pass
    return lastPacket

def getLastCompleteGPS():
    global lastGPSPacket
    for device in DEVICES:
        deviceDataPath = device['DATA']
        with open(deviceDataPath, "r") as data:
            for line in reversed(data.readlines()):
                try:
                    dataLine = json.loads(line)
                    if lastGPSPacket and dataLine['index'] <= lastGPSPacket['index'] - 5: # 5 older packets allowed in case of recalled data packets
                        break
                    if (not lastGPSPacket or dataLine['index'] > lastGPSPacket['index']) and dataLine['gps']:
                        lastGPSPacket = dataLine
                except:
                    pass
    return lastGPSPacket

def updateCanSatPath():
    global MAP_PATH
    if lastGPSPacket and lastGPSPacket.get('gps', {}).get('lat'):
        MAP_PATH.append((lastGPSPacket['gps']['lat'], lastGPSPacket['gps']['lon']))


def updateMap():
    if lastGPSPacket and lastGPSPacket.get('gps', {}).get('lat'):
        mymap = pygmaps.maps(lastGPSPacket['gps']['lat'], lastGPSPacket['gps']['lon'], 14) # center location
        mymap.addpoint(lastGPSPacket['gps']['lat'], lastGPSPacket['gps']['lon'], "#FF00FF")
        tempPath = MAP_PATH[:]
        if len(MAP_PATH) > 1:
            mymap.addpath(tempPath,"#0088FF")
        mymap.draw(MAPFILE)
    
def outputPredictData():
    if (not lastGPSPacket) or (not lastGPSPacket.get('gps', {}).get('lat')):
        return
    drag = 5
    burstAlt = 30000
    ascentRate = 5

    dateString = time.strftime('%Y %m %d %H %M %S',  time.gmtime(time.time() + 10 + (60*60)))
    t_year, t_month, t_day, t_hour, t_min, t_second = dateString.split(" ")

    lat = lastGPSPacket['gps']['lat']
    lon = lastGPSPacket['gps']['lon']
    alt = lastGPSPacket['gps']['alt']

    with open(PREDICT_FILE, 'w') as predictFile:
        predictFile.write("""
            #!/usr/bin/env bash
            uid=$(curl -s 'http://predict.habhub.org/ajax.php?action=submitForm' \
            --data 'launchsite=Other&lat=%s&lon=%s&initial_alt=%s&hour=%s&min=%s&second=%s&day=%s&month=%s&year=%s&ascent=%s&burst=%s&drag=%s&submit=Run+Prediction' --compressed \
            | cut -d'"' -f 8)
            echo "UID is $uid"
            url="http://predict.habhub.org/#!/uuid=${uid}"
            echo "URL is $url"
            google-chrome $url
        """ % (lat, lon, alt, t_hour, t_min, t_second, t_day, t_month, t_year, ascentRate, burstAlt, drag))

    burstAlt = alt
    with open(PREDICT_FILE2, 'w') as predictFile:
        predictFile.write("""
            #!/usr/bin/env bash
            uid=$(curl -s 'http://predict.habhub.org/ajax.php?action=submitForm' \
            --data 'launchsite=Other&lat=%s&lon=%s&initial_alt=%s&hour=%s&min=%s&second=%s&day=%s&month=%s&year=%s&ascent=%s&burst=%s&drag=%s&submit=Run+Prediction' --compressed \
            | cut -d'"' -f 8)
            echo "UID is $uid"
            url="http://predict.habhub.org/#!/uuid=${uid}"
            echo "URL is $url"
            google-chrome $url
        """ % (lat, lon, alt, t_hour, t_min, t_second, t_day, t_month, t_year, ascentRate, burstAlt, drag))
