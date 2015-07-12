#!/usr/bin/python
#
# Scan deamon
#
# responsible for scanning the serial port, updating scan.txt, and running
# the unlock.py if the access is correct
#
#

import ConfigParser
import sys
import os
import serial
import serial.tools.list_ports
import time
import requests
import threading

c = ConfigParser.SafeConfigParser()
if os.path.isfile("/root/tinkerAccess/scan.cfg"):
  c.read('/root/tinkerAccess/scan.cfg')
  C_portName = c.get('config', 'portName')
  C_portSpeed = c.get('config', 'portSpeed')
  C_server    = c.get('config', 'server')
  C_deviceid  = c.get('config', 'deviceid')
  C_unlockbin = c.get('config', 'unlockbin')
  C_scantxt   = c.get('config', 'scantxt')
  C_clientServer = c.get('config','clientserver') #could be client or server
  C_devicetimeout = int(c.get('config','devicetimeout')) # how many seconds before we close the device

else:
  print("config scan.cfg not found")
  sys.exit(1)

serialPort = False
for port in list(serial.tools.list_ports.comports()):
  if port[1] == C_portName:
    serialPort = port[0]

if not serialPort:
  print("Unable to find a serial port that match description %s as defined in run_client.cfg" % C_portName )
  sys.exit()

serialConnection = serial.Serial(serialPort, C_portSpeed)
serialConnection.flushInput()
serialConnection.flushOutput()

def watchPort():

  timerThread = False

  # just sit here and scan badges and allow access as long as the server says ok
  while True:
    usercode =  serialConnection.readline()[2:-4].strip()

    # the first time you scan, it missses the first
    # character, so just try again
    if len(usercode) != 10:
      continue

    # if this is a server
    if C_clientServer == "server":
      code = "server"

    # if this is a client
    if C_clientServer == "client":
      #code = requests.get( url="%s/device/%s/code/%s" % ( C_server, C_deviceid, usercode) )
      code = ""

      # if access was granted run the unlock binary
      if code == "":
        os.system( C_unlockbin)

        # if there is a timer running already then stop it and
        # start a new timer
        if timerThread:
          timerThread.cancel()

        timerThread = threading.Timer(C_devicetimeout , logOut)
        timerThread.start()

    # log out the last scan data
    outfile = open(C_scantxt, "w")
    outfile.write("%s,%s\n" % (usercode, code))
    outfile.close()

    time.sleep(1)


# log a user out after so long
def logOut():
  print("Logout called")

d1 = threading.Thread(name='daemon', target=watchPort)
d1.setDaemon(True)

d1.start()

while True:
  time.sleep(1)
