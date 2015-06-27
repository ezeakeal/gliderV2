import getopt
import signal
import sys
sys.path.append('.')
# Some IMU explanation https://github.com/richards-tech/RTIMULib/tree/master/Linux/python/tests
import RTIMU
import os.path
import time
import math
import os
import spidev_test as controller
import RPi.GPIO as GPIO  

from threading import Thread
###############################
# ORIENTATION GLOBALS
###############################
RUNNING = True

LED_RUNNING = 11


###############################















def stop_test(signal, frame):
    global RUNNING
    print('You pressed Ctrl+C!')
    RUNNING = False
    GPIO.cleanup() 
    sys.exit(0)


