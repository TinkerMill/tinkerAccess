#!/usr/bin/python

# https://docs.python.org/2/howto/logging.html#logging-basic-tutorial
# http://pyserial.readthedocs.org/en/latest/shortintro.html

import optparse
import ConfigParser
import os
import serial
import serial.tools.list_ports
import logging
import logging.handlers
import sys
import RPi.GPIO as GPIO
import time
import requests
import signal
import lcdModule as LCD

# hold all the options loaded from the config file
configOptions = {}
currentUser = False
currentBadge = False
currentUserID = False
currentUserTime = 0
globalDeviceName = False
marioMode = False

parser = optparse.OptionParser()
parser.add_option("-f", "--config",
                  default="/opt/tinkeraccess/client.cfg",
                  help='config file to use', dest="configFileLocation", action="store")

(opts, args) = parser.parse_args()


def exitme():
  sys.exit()
signal.signal(signal.SIGINT, exitme)

# Begin Initalize ##

# Parse configuration
c = ConfigParser.SafeConfigParser()
if os.path.isfile(opts.configFileLocation):
  c.read(opts.configFileLocation)
  configOptions['logFile']         = c.get('config', 'logFile')
  configOptions['logLevel']        = c.getint('config', 'logLevel')
  configOptions['server']          = c.get('config', 'server')
  configOptions['deviceID']        = c.get('config', 'deviceID')
  configOptions['serialPortName']  = c.get('config', 'serialPortName')
  configOptions['serialPortSpeed'] = c.get('config', 'serialPortSpeed')
  configOptions['pin_logout']      = c.getint('config', 'pin_logout')
  configOptions['pin_relay']      = c.getint('config', 'pin_relay')
  configOptions['pin_led_r']      = c.getint('config', 'pin_led_r')
  configOptions['pin_led_g']      = c.getint('config', 'pin_led_g')
  configOptions['pin_led_b']      = c.getint('config', 'pin_led_b')
  configOptions['pin_current_sense']      = c.getint('config', 'pin_current_sense')
  configOptions['logout_coast_time']      = c.getint('config', 'logout_coast_time')

# setup logging
lg = logging.getLogger()
lg.addHandler( logging.handlers.SysLogHandler('/dev/log') )
lg.addHandler( logging.FileHandler(configOptions['logFile']) )
lg.setLevel( configOptions['logLevel'] )
#logging.basicConfig(filename=configOptions['logFile'] , level=configOptions['logLevel'] )
#logging.basicConfig(level=configOptions['logLevel'] )

def led(r,g,b):
  global configOptions
  GPIO.output(configOptions['pin_led_r'], r)
  GPIO.output(configOptions['pin_led_g'], g)
  GPIO.output(configOptions['pin_led_b'], b)

# configure GPIO
GPIO.setmode( GPIO.BCM )
GPIO.cleanup()
GPIO.setwarnings(False)

GPIO.setup( configOptions['pin_logout'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup( configOptions['pin_current_sense'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup( configOptions['pin_relay'], GPIO.OUT)
GPIO.setup( configOptions['pin_led_r'], GPIO.OUT)
GPIO.setup( configOptions['pin_led_g'], GPIO.OUT)
GPIO.setup( configOptions['pin_led_b'], GPIO.OUT)
GPIO.output( configOptions['pin_relay'], GPIO.LOW )
GPIO.output(configOptions['pin_led_r'], False)
GPIO.output(configOptions['pin_led_g'], False)
GPIO.output(configOptions['pin_led_b'], False)

# configure the serial port
if not os.path.exists(configOptions['serialPortName']):
  logging.fatal("Unable to find serial port %s" % configOptions['serialPortName'] )
  sys.exit(1)

serialConnection = serial.Serial( configOptions['serialPortName'], configOptions['serialPortSpeed'] )
serialConnection.flushInput()
serialConnection.flushOutput()

LCD.lcd_init()
LCD.lcd_string("Scan Badge" ,LCD.LCD_LINE_1)
LCD.lcd_string("To Login" ,LCD.LCD_LINE_2)
led(False,False,True)

# End Initialize ##



def requestAccess(badgeCode):
  global configOptions
  url = "%s/device/%s/code/%s" % (configOptions['server'], configOptions['deviceID'], badgeCode)
  logging.debug("calling server:" + url)

  serverResponse = requests.get(url)
  data       = serverResponse.json()
  username   = data['username']
  devicename = data['devicename']
  userid     = data['userid']
  timelimit  = data['time']

  logging.debug("server response %s,%s,%s,%s" % (username, devicename, userid, timelimit))
  return (username, devicename, timelimit, userid)



# what to do when the logout button is pressed
def event_logout():
  global configOptions, currentBadge, currentUser,currentUserID, marioMode, currentTrainerId, currentTrainerCode
  isMachineRunning = False
  currentBadge = False
  currentTrainerId = False
  currentTrainerCode = False
  marioMode = False

  # the loop makes sure the machine is powered down all the way 
  # before logging the user off
  while True:
    
    # if the current pin is not high, break out of the loop
    if not GPIO.input( configOptions['pin_current_sense']  ) == GPIO.HIGH:
      break

    #check if machine is running, if so, flag machine running status and prevent shutdown
    while GPIO.input( configOptions['pin_current_sense']  ) == GPIO.HIGH:
        isMachineRunning = True
        LCD.lcd_string("Waiting for" ,LCD.LCD_LINE_1)
        LCD.lcd_string("Machine to Stop" ,LCD.LCD_LINE_2)
        time.sleep(1)

    # If logout was attempted while machine is running, delay for coast time (seconds) defined in config file
    if isMachineRunning == True:
      LCD.lcd_string("Machine" ,LCD.LCD_LINE_1)
      LCD.lcd_string("Coasting Down" ,LCD.LCD_LINE_2)
      time.sleep(configOptions['logout_coast_time'] )
      isMachineRunning = False
    
  if currentUser:
    # tell the server we have logged out
    url = "%s/device/%s/logout/%s" % (configOptions['server'], configOptions['deviceID'], currentUserID)
    logging.debug("calling server:" + url)
    re = requests.get(url)
    logging.debug("server response:" + re.text)

    logging.info("%s logged out" % currentUser )
    GPIO.output( configOptions['pin_relay'], GPIO.LOW )
    currentUser = False
    currentUserTime = 0
    currentUserID = False
  else:
    currentUserTime = 0
  
  #LCD Waiting Status   
  LCD.lcd_string("Scan Badge" ,LCD.LCD_LINE_1)
  LCD.lcd_string("To Login" ,LCD.LCD_LINE_2)
  led(False,False,True) #Blue LED

def event_login(badgeCode):
  global currentUser,currentBadge, currentUserID, currentUserTime,globalDeviceName,configOptions

  if currentBadge == badgeCode:
    currentUserTime = time.time() + ( 100 * 60 )
    return

  v = requestAccess(badgeCode)

  # if the server returned that we have more than 0 min left on device
  # then we have access.
  if v[2] > 0:
    logging.info("Access granted for %s granted with time %s" % (badgeCode, v) )
    GPIO.output( configOptions['pin_relay'], GPIO.HIGH)
    currentUser = v[0]
    currentUserID = v[3]
    currentUserTime = time.time() + ( v[2] * 60 )
    globalDeviceName = v[1]
    currentBadge = badgeCode
    led(False,True,False)
  else:
    if currentUser:
      logging.info("Access denied for %s but %s already logged in" % (badgeCode, currentUser))
      return
    logging.info("Access denied for %s " % badgeCode )
    led(True,False,False)
    LCD.lcd_string("Access Denied" ,LCD.LCD_LINE_1)
    LCD.lcd_string("Take the class" ,LCD.LCD_LINE_2)
    time.sleep(2)
    led(False,False,True)
    LCD.lcd_string("Scan Badge" ,LCD.LCD_LINE_1)
    LCD.lcd_string("To Login" ,LCD.LCD_LINE_2)
    GPIO.output( configOptions['pin_relay'], GPIO.LOW )


def loop():
  global currentUserTime, currentUser, configOptions, marioMode, currentTrainerId , currentTrainerCode

  while True:
    time.sleep(.01)

    if (not marioMode) and currentUser:
      LCD.lcd_string(currentUser,LCD.LCD_LINE_1)
      LCD.lcd_string( str( int(round( (currentUserTime - time.time())/3600 ))) + ":" + str( int(round( (currentUserTime - time.time())%60 ))) + ":" + str( int(round( (currentUserTime - time.time())))) ,LCD.LCD_LINE_2)
      if currentUserTime - time.time() < 300:
        led(True,False,True)

    # if the user runs out of time, log them out
    if currentUser != False and currentUserTime < time.time():
      event_logout()
      continue

    # if the user logs out with the logout button log them out
    if GPIO.input( configOptions['pin_logout'] ) == GPIO.HIGH:
      
      holdDownCount=0
      marioMode = False

      # if the logout button is held down for over 2 seconds
      # you enter mario mode and any badge scanned after this
      # will become authorized to use this device.
      while GPIO.input( configOptions['pin_logout'] ) == GPIO.HIGH:
        time.sleep(.1)
        holdDownCount = holdDownCount + 1
        if holdDownCount > 25 and currentUser:
          marioMode = True
          currentTrainerId = currentUserID
          currentTrainerCode = currentBadge
          LCD.lcd_string("Mario Mode" ,LCD.LCD_LINE_1)
          LCD.lcd_string("Activated" ,LCD.LCD_LINE_2)
          while GPIO.input( configOptions['pin_logout'] ) == GPIO.HIGH:
            time.sleep(.1)
          break

      if not marioMode:
        event_logout()
        time.sleep(.2)
      
      continue

    # if the serial port has data read it.
    if serialConnection.inWaiting() > 1:
      badgeCode = serialConnection.readline().strip()[-12:]
      serialConnection.flushInput()
      serialConnection.flushOutput()  

      # if mario mode is active, then register this badge on the machine
      if marioMode:

        # don't re-register the trainer if she scans her badge again
        if badgeCode == currentTrainerCode:
          continue

        # contact the server and register this new badge on this equipment  
        url = "%s/admin/marioStar/%s/%s/%s/%s" % (configOptions['server'], currentTrainerId, currentTrainerCode, configOptions['deviceID'], badgeCode)
        logging.debug("calling server:" + url)
        LCD.lcd_string("Calling Server" ,LCD.LCD_LINE_1)
        LCD.lcd_string("Please Wait..." ,LCD.LCD_LINE_2) 

        try:
          re = requests.get(url)
          
          if re.text == "true":
            LCD.lcd_string("Register of" ,LCD.LCD_LINE_1)
            LCD.lcd_string(badgeCode ,LCD.LCD_LINE_2)
          else:
            LCD.lcd_string("!!FAILED!!" ,LCD.LCD_LINE_1)
            LCD.lcd_string(badgeCode ,LCD.LCD_LINE_2)

        except Exception as e: 
          logging.debug("Error talking to server: %s" % str(e))
          LCD.lcd_string("Error Talking" ,LCD.LCD_LINE_1)
          LCD.lcd_string("To Server" ,LCD.LCD_LINE_2) 

        logging.debug("server response:" + re.text)

        
      
      # otherwise just do a normal login
      else:
        try:
          data = event_login(badgeCode)
        except Exception as e:
          logging.debug("Error logging in: %s" % str(e))
          LCD.lcd_string("Error" ,LCD.LCD_LINE_1)
          LCD.lcd_string("Logging in" ,LCD.LCD_LINE_2) 
      continue


loop()
