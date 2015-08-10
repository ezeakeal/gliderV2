#!/usr/bin/python
##############################################
#
# Glider GroundStation Software 
# For use with launch of GliderV2:
#   Daniel Vagg 2015
#
##############################################

import sys
import signal
import logging
import argparse
import traceback

import core

#####################################
# GLOBALS
#####################################

#####################################
# FUNCTIONS
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
  logging.info("Shutting down GroundStation")
  core.shutdown()
  sys.exit(0)
  
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
  parser.add_argument('datadir', action='store', help='Path to Data directory', default="./data")
  parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of logging.')
  return parser

#####################################
# MAIN
#####################################
def main():
  parser = createParser()
  results = parser.parse_args()
  # Use the args
  loglevel = results.verbose
  xbee_path = results.xbee
  data_path = results.datadir
  
  signal.signal(signal.SIGINT, signal_handler_quit) # Manage Ctrl+C
  configureLogging(loglevel)

  try:
    core.XBEE_DEV["PATH"] = xbee_path
    core.initialize()
    core.run()
  except Exception:
    logging.error("Caught unexpected exception:")
    logging.error(traceback.format_exc())
      
  sys.exit(0)


main()