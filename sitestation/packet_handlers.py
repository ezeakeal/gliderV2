#!/usr/bin/python
##############################################
#
# Glider GroundStation Software
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################
import os
import log
import time
import logging

LOG = log.setup_custom_logger('groundstation')
LOG.setLevel(logging.WARNING)

#####################################
# DATA HANDLERS
#####################################
class TelemetryHandler(object):
    def __init__(self, output="output/telemetry.data"):
        self.output = output
        self.last_packet = None
        self.all_sat_last_packets = {}
        self.components = [
            "callsign", "index", "hhmmss", 
            "NS", "lat", "EW", "lon", "gps_dil", "alt", 
            "temp1", "temp2", "pressure"
        ]
        with open(self.output, "a") as output:
            output.write("# " + ",".join(self.components) + "\n")
    
    def _store_packet(self, packet_parts, time_stamp):
        with open(self.output, "a") as output:
            packet_parts = ["%s" % time_stamp] + packet_parts
            output.write(",".join(packet_parts) + "\n")

    def parse(self, source_id, packet_parts, time_stamp):
        self.last_packet = packet_parts
        self._store_packet(packet_parts, time_stamp)
        self._parse_to_all_sat(time_stamp)

    def get_all_dict(self):
        return self.all_sat_last_packets

    def _parse_to_all_sat(self, time_stamp):
        data = {
            "time_received": time_stamp
        }
        if self.last_packet:
            for ind, key in enumerate(self.components):
                data[key] = self.last_packet[ind].strip()
        try:
            callsign = data['callsign']
            if float(data['lon']) != 0 and float(data['lat']) != 0:
                self.all_sat_last_packets[callsign] = data
            else:
                LOG.warning("Empty GPS coordinate received")
        except Exception, e:
            LOG.error("Error in parsing all_sat_last_packets")
            LOG.error(e)


class DataHandler(object):
    def __init__(self, data_output="output/data_packets.data"):
        self.data_output = data_output

    def _store_packet(self, source_id, packet_parts, time_stamp):
        with open(self.data_output, "a") as packet_output:
            packet_output.write("%s,%s," % (time_stamp, source_id))
            packet_output.write(",".join(packet_parts) + "\n")

    def parse(self, source_id, packet_parts, time_stamp):
        # We don't do anything with data here
        self._store_packet(source_id, packet_parts, time_stamp)
        

