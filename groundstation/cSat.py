#!/usr/bin/python
##############################################
#
# CanSat Client Software 
# For use with launch of CanSat:
#   UCD, Space Science Masters, 2014
#
##############################################

import sys
import signal
import logging
import argparse
import traceback

import cSat_core as core

#####################################
# GLOBALS
#####################################

#####################################
# FUNCTIONS
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
  logging.info("Shutting down cSat")
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
  parser.add_argument('tminus', action='store', help='Path to tMinux interface')
  parser.add_argument('xbee', action='store', help='Path to XBee interface')
  parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of logging.')
  return parser

#####################################
# MAIN
#####################################
def main():
  parser = createParser()
  results = parser.parse_args()
  loglevel = results.verbose
  tminus_path = results.tminus
  xbee_path = results.xbee
  
  signal.signal(signal.SIGINT, signal_handler_quit) # Manage Ctrl+C
  configureLogging(loglevel)

  try:
    core.TMINUS_DEV["PATH"] = tminus_path
    core.XBEE_DEV["PATH"] = xbee_path
    core.initialize()
    core.run()
  except Exception:
    logging.error("Caught unexpected exception:")
    logging.error(traceback.format_exc())
      
  sys.exit(0)


main()