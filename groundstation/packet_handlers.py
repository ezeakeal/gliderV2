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
        
    def get(self, param):
        if param not in self.components:
            LOG.error("Parameter %s is not in components (%s)" % (param, self.components))
        else:
            return self.last_packet[self.components.index(param)]

    def get_dict(self):
        data = {}
        if self.last_packet:
            for ind, key in enumerate(self.components):
                data[key] = self.last_packet[ind]
        return data

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
    def __init__(self, output="output/glider_data.data", data_output="output/data_packets.data"):
        # O:-3.5_4.3_11.7', 'W:0.0_0.0
        self.output = output
        self.data_output = data_output
        self.last_packet = None
        self.components = {"wings": [], "orientation": [], "state": []}
        with open(self.output, "a") as output:
            output.write("# time," + ",".join(sorted(self.components.keys())) + "\n")

    def _store_packet(self, source_id, packet_parts, time_stamp):
        with open(self.data_output, "a") as packet_output:
            packet_output.write("%s,%s," % (time_stamp, source_id))
            packet_output.write(",".join(packet_parts) + "\n")
        with open(self.output, "a") as output:
            log_components = ["%s" % time.time()]
            for key in sorted(self.components.keys()):
                log_components.append(" ".join(self.components[key]))
            output.write(",".join(log_components) + "\n")

    def parse(self, source_id, packet_parts, time_stamp):
        try:
            for packet in packet_parts:
                packet_type, packet_data = packet.split(":")
                for component in self.components.keys():
                    if component.startswith(packet_type.lower()):
                        self.components[component] = packet_data.split("_")
                        break
            self.last_packet = packet_parts
        except:
            pass
        self._store_packet(source_id, packet_parts, time_stamp)
        
    def get(self, param):
        if param not in components.keys():
            print "Parameter %s is not in components (%s)" % (param, components.keys())
        else:
            print components[param]

    def get_dict(self):
        return self.components


class ImageHandler(object):
    def __init__(self, output_dir="static/images/"):
        self.output_dir = output_dir
        self.current_image = None
        self.current_image_file = None
        self.last_image = None
        self.image_list = []
    
    def _start_image(self, name):
        image_path = os.path.join(self.output_dir, os.path.basename(name))
        self.current_image = image_path
        self.current_image_file = open(image_path, "wb")

    def _store_image_part(self, image_index, image_part):
        self.current_image_file.write(image_part)

    def _end_image(self):
        self.last_image = self.current_image
        self.current_image_file.close()
        self.image_list.insert(0, self.last_image)
        self.current_image = None
    
    def parse(self, source_id, packet_parts, time_stamp):
        image_signal = packet_parts[0]
        if image_signal == "S":
            print "Started receiving new image (From: %s)" % source_id
            self._start_image(packet_parts[1])
        if image_signal == "P" and self.current_image:
            print "Receiving image part %s" % packet_parts[1]
            self._store_image_part(packet_parts[1], "|".join(packet_parts[2:]))
        if image_signal == "E":
            print "Finished receiving image (%s)" % self.current_image
            self._end_image()
        
    def get(self, index=-1):
        if index < len(self.image_list):
            return self.image_list[index]
        else:
            return None

    def get_dict(self):
        data = {}
        data['images'] = self.image_list
        return data