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
        self.components = [
            "callsign", "index", "hhmmss", 
            "NS", "lon", "EW", "lat", "gps_dil", "alt", 
            "temp1", "temp2", "pressure"
        ]
        with open(self.output, "a") as output:
            output.write("# " + ",".join(self.components))
    
    def _store_packet(self, packet_parts):
        with open(self.output, "a") as output:
            output.write(",".join(packet_parts))

    def parse(self, packet_parts):
        self.last_packet = packet_parts
        self._store_packet(packet_parts)
        
    def get(self, param):
        if param not in self.components:
            print "Parameter %s is not in components (%s)" % (param, self.components)
        else:
            return self.last_packet[self.components.index(param)]

    def get_dict(self):
        data = {}
        if self.last_packet:
            for ind, key in enumerate(self.components):
                data[key] = self.last_packet[ind]
        return data


class DataHandler(object):
    def __init__(self, output="output/glider_data.data"):
        # O:-3.5_4.3_11.7', 'W:0.0_0.0
        self.output = output
        self.last_packet = None
        self.components = {"wings": [], "orientation": [], "state": []}
        with open(self.output, "a") as output:
            output.write("# " + ",".join(self.components.keys()))
    
    def _store_packet(self, packet_parts):
        with open(self.output, "a") as output:
            output.write(",".join(packet_parts))

    def parse(self, packet_parts):
        for packet in packet_parts:
            packet_type, packet_data = packet.split(":")
            for component in self.components.keys():
                if component.startswith(packet_type.lower()):
                    self.components[component] = packet_data.split("_")
                    break
        self.last_packet = packet_parts
        self._store_packet(packet_parts)
        
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
    
    def parse(self, packet_parts):
        image_signal = packet_parts[0]
        if image_signal == "S":
            print "Started receiving new image"
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