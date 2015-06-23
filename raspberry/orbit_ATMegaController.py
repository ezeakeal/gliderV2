import sys
import math
import time
import serial
import logging
import datetime

##########################################
# TODO
##########################################

##########################################
# GLOBALS
##########################################
SOCK      = None
LOG       = logging.getLogger()
LAST_DAT  = None

buffer_len = 100
delay_reset = 0.1
delay_xfer = 0.05
delay_respond = 0.05
spi_bus = 0
spi_dev = 0
spi = None
char_respond = "-" # this character is reqquired in the arduino code for a response

##########################################
# FUNCTIONS
##########################################
# Initialize the serial connection - then use some commands I saw somewhere once
def create_spi():
    global spi
    if not spi:
        spi = spidev.SpiDev()
    spi.close()
    time.sleep(1)
    spi.open(spi_bus, spi_dev)
    spi.max_speed_hz = 40000 # fuckit.. keep it that low.
    LOG.debug("Initialized Flight Controller")

def stop():
    LOG.info("Closing SPI connection")
    spi.close()


def RW_glider_command(command):
    W_glider_command(command)
    time.sleep(delay_respond)
    char_arr = [ord(char_respond) for i in range(buffer_len)] # Create an array of nothing to receive the SPI response..
    response = raw_xfer(char_arr)
    response = ''.join([chr(r) for r in response])
    LOG.debug("RESPONSE: %s" % response)
    return response


def W_glider_command(command):
    LOG.debug("SENDING: %s" % cStr)
    comm_string = "$%s;" % command
    char_arr = [ord(i) for i in comm_string]
    LOG.debug("Command = %s" % (comm_string))
    
    while True:
        response = raw_xfer(char_arr)
        if response == char_arr:
            LOG.debug("Success")
            break
        else Exception, e::
            LOG.critical("Failure")
            LOG.critical(e)
            create_spi()
        time.sleep(delay_reset)


def raw_xfer(bytestr):
    send_arr = bytestr + [0] # add blank byte to receive the last character sent in response 
    LOG.debug("Sending hex array: %s" % hex_str(send_arr))
    response = spi.xfer(send_arr)
    response = response[1:] # remove first char as it contains a copy of the blank from last command
    LOG.debug("Received hex array: %s" % hex_str(response))
    time.sleep(delay_xfer)
    return response


def hex_str(dec_str):
    return ''.join(["0x%02X " % x for x in dec_str]).strip()


def setWing(angleLeft, angleRight):
    LOG.debug("Setting Wing Angle")
    send("W:%s:%s" % (angleLeft, angleRight))


def release():
    LOG.debug("Releasing")
    send("D:")
    

def releaseChute():
    LOG.debug("Releasing Parachute")
    send("P:")


def getTelem():
    global LAST_DAT
    dat = RW_glider_command("G:")
    if dat and dat.startswith("T|"):
        LAST_DAT = dat
    else:
        LOG.warn("Failed")
