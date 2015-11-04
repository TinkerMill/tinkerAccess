#!/usr/bin/python
#
########################################################################
#
#   badgeScanModule.py
#
########################################################################

import ConfigParser
import sys
import os
import serial
import serial.tools.list_ports
import time
import requests

C_portName = "/dev/ttyUSB0"
C_portSpeed = "9600"
C_server    = "http://10.2.107.169:5000"
C_deviceid  = "0"
C_unlockbin = "sudo python",os.getcwd(),"/unlock.py"
C_lockbin = "sudo python",os.getcwd(),"/lock.py"
C_scantxt   = "scan.txt"
C_clientServer = "client"
C_devicetimeout = "3600"
SUCCESS = "SUCCESS"
FAILCODE = "FAIL"
serialConnection = serial.Serial(C_portName, C_portSpeed)
########################################################################
#
#   scanInit
#
########################################################################
def scanInit():
    c = ConfigParser.SafeConfigParser()
    scanConfigPath=os.getcwd()+"/scan.cfg"
    #print "scanInit\n",scanConfigPath
    if os.path.isfile(scanConfigPath):
        c.read(scanConfigPath)
        C_portName = c.get('config', 'portName')
        C_portSpeed = c.get('config', 'portSpeed')
        C_server    = c.get('config', 'server')
        C_deviceid  = c.get('config', 'deviceid')
        C_unlockbin = c.get('config', 'unlockbin')
        C_lockbin = c.get('config', 'lockbin')
        C_scantxt   = c.get('config', 'scantxt')
        C_clientServer = c.get('config','clientserver') #could be client or server
        C_devicetimeout = int(c.get('config','devicetimeout')) # how many seconds before we close the device
    else:
      FAILCODE= FAILCODE+"1",scanConfigPath+" not found"
      return FAILCODE

    serialPort = False
    for port in list(serial.tools.list_ports.comports()):
      #print "Found device serial comport: "
      for portinfo in port:
        print "   "+portinfo
      for cfgPortName in C_portName.split():
        if port[0] == cfgPortName:
          serialPort = port[0]
          print ("Found a serial port that matches portName %s as defined in scan.cfg" % str(cfgPortName) )

    if not serialPort:
      FAILCODE = ": Unable to find a serial port that matches description %s as defined in scan.cfg" % C_portName
      return FAILCODE

    serialConnection = serial.Serial(serialPort, C_portSpeed)
    serialConnection.flushInput()
    serialConnection.flushOutput()
    return SUCCESS



########################################################################
#
#   watchPort
#
########################################################################
def watchPort():
  badgeId =  serialConnection.readline().strip()[-11:-1]
  #print("usercode=",str(badgeId) )
  return badgeId


# log a user out after so long
def logOut():
  print("Logout called")
