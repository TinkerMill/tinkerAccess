#!/usr/bin/python

# https://docs.python.org/2/howto/logging.html#logging-basic-tutorial
# http://pyserial.readthedocs.org/en/latest/shortintro.html

import optparse
import ConfigParser
import os
import serial
import serial.tools.list_ports
import logging
import sys
import RPi.GPIO as GPIO
import time

# hold all the options loaded from the config file
configOptions = []
currentUser = False
currentUserTime = 0

parser = optparse.OptionParser()
parser.add_option("-f", "--config",
                  default="/opt/tinkerAccess/client.cfg",
                  help='config file to use', dest="configFileLocation", action="store")

(opts, args) = parser.parse_args()

# Begin Initalize ##

# Parse configuration
c = ConfigParser.SafeConfigParser()
if os.path.isfile(opts.configFileLocation):
  c.read(opts.configFileLocation)
  configOptions['logFile']         = c.get('config', 'logFile')
  configOptions['logLevel']        = c.get('config', 'logLevel')
  configOptions['server']          = c.get('config', 'server')
  configOptions['deviceID']        = c.get('config', 'deviceID')
  configOptions['serialPortName']  = c.get('config', 'serialPortName')
  configOptions['serialPortSpeed'] = c.get('config', 'serialPortSpeed')
  configOptions['pin_logout']      = c.get('config', 'pin_logout')

# setup logging
logging.basicConfig(filename=configOptions['logFile'] , level= configOptions['logLevel'] )

# configure GPIO
GPIO.setmode( GPIO.BCM )
GPIO.setmode( configOptions['pin_logout'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# configure the serial port
if not os.path.isfile(configOptions['serialPortName']):
  logging.fatal("Unable to find serial port %s" % name)
  sys.exit(1)

serialConnection = serial.Serial( configOptions['serialPortName'], configOptions['serialPortSpeed'] )
serialConnection.flushInput()
serialConnection.flushOutput()

# End Initialize ##

def requestAccess(badgeCode):
  url = "%s/device/%s/code/%s" % (configOptions['server'], configOptions['deviceID'], badgeCode)
  logging.debug("calling server:" + url)
  serverResponse = request.get(url)
  logging.debug("server response")
  logging.debug(serverResponse)
  return serverResponse


# what to do when the logout button is pressed
def event_logout():
  logging.info("%s logged out" % currentUser )
  # contact the server and let it know
  # clean up
  # update lcd message
  pass

def event_login(badgeCode):
  v = requestAccess(badgeCode)
  if v > 0:
    logging.info("Access granted for %s granted with time %s" % (badgeCode, v) )
    currentUser = "bob"
    currentUserTime = v
  else:
    logging.info("Access denied for %s " % (badgeCode, v) )


def loop():
  while True:

    time.sleep(.01)

    # if the user is logged in the tick the clock down
    if currentUser != False and currentUserTime > 0:
      currentUserTime = currentUserTime - 1
      # update lcd with new time

    # if the user runs out of time, log them out
    if currentUser != False and currentUserTime < 0:
      event_logout()
      continue

    # if the user logs out with the logout button log them out
    if GPIO.input( configOptions['pin_logout'] ) == GPIO.HIGH:
      event_logout()
      continue

    # if the serial port has data read it.
    if serialConnection.in_waiting > 0:
      badgeCode = SerialConnection.readline().strip()[-11:-1]
      event_login(badgeCode)
