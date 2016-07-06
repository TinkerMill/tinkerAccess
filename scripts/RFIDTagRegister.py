# Python code to import RFID tag numbers to the TinkerMill membership system
# 
# This program receives RFID tag numbers sent from Sparkfun RFID reader connected via USB
# and then auto-types the received tag number for inserting into the TinkerMill membership system.
#
# This version expects the Sparkfun RFID reader.  The Sparkfun RFID reader only reads
# tags once when they are in range so no code is needed to check for duplicate tags.
# 
# To run on Windows, t

import sys			# library for system functions
import serial		# library for connecting to the rfid reader
import pyautogui    # library for GUI interoperability

# default port for the sparkfun rfid reader for my system - update to match your system
default_rfid_reader_port = "COM3"


# main program for reading and pasting tag numbers
def main(rfid_reader = default_rfid_reader_port):      
  print "Connecting to Sparkfun RFID reader on port ", rfid_reader
  try:
    ser = serial.Serial(rfid_reader, timeout=1)                 # connect to the rfid reader
    print "Successfully connected to RFID reader on ", rfid_reader
    rfid_reader_opened = 1
  except:
    print "Failed to connect to RFID reader on port ", rfid_reader
    rfid_reader_opened = 0

  # if the RFID reader was successfully connected, start reading and processing tags    
  if rfid_reader_opened:

     while 1:       # loop forever
  
      ser.flushInput()                    # flush any extra data from the serial port
      rfid_data = ser.readline().strip()  # read the  rfid data 

      # if data has been received
      if len(rfid_data) > 0:

        rfid_data = rfid_data[1:13]     # strip off all data but the tag number
        print "Tag data:", rfid_data    # print the tag number to console
        pyautogui.typewrite(rfid_data)  # auto-type the tag number to focus window      
        pyautogui.typewrite(['tab'])    # auto-type a tab to the focus window to move to the next field


# this code enables starting the program from the command line
if __name__ == '__main__':
  if (len(sys.argv) > 1):
    main(sys.argv[1])
  else:
    main()
