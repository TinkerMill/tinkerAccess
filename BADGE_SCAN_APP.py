#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Spyder Editor
 
This is a temporary script file.
"""
import threading
import Queue
import time
import lcdModule as LCD
import badgeScanModule as SCAN
import dataBaseAccess as DB
import RPi.GPIO as GPIO
#!/usr/bin/python
import sys
from select import select


    
deviceAccessQ = Queue.Queue() 
LcdQ= Queue.Queue()
eventQ = Queue.Queue()
EVENT_MSG_NULL                = 0
EVENT_MSG_RESET               = 1
EVENT_MSG_BADGE_SCAN          = 2
EVENT_MSG_USER_GRANTED_ACCESS = 3
EVENT_MSG_TIMER_EXPIRE        = 4

KILL_APP_PIN = 13
RESET_PIN = 16
LOCK_PIN = 17
############################################################
def taskResetButton():
    GPIO.setup(RESET_PIN, GPIO.IN)
    GPIO.setup(KILL_APP_PIN, GPIO.IN)
    resetPinVal = GPIO.LOW
    killAppPinVal = GPIO.LOW
    while 1:
        time.sleep(0.1)
        resetPinVal = GPIO.input(RESET_PIN)
        if resetPinVal == GPIO.HIGH:
            print "\nIn taskResetButton - reset button pressed"
            eventQ.put( (EVENT_MSG_RESET,"LOGGING OFF",time.time()) )
            resetPinVal = GPIO.LOW
            time.sleep(3)
        
            resetPinVal = GPIO.input(KILL_APP_PIN)
            if killAppPinVal == GPIO.HIGH:
               print "\n\nKILL APP!!!\n\n"
               taskLCD_ID.exit()
               taskBadgeScan_ID.exit()
               taskDeviceAccessControl_ID.exit()
               return 0;
            


LCD.lcd_init() 
def taskLCD():
  
    while 1:
        #print "in taskLCD"
        time.sleep(0.3)
        if not LcdQ.empty():
            LcdText = LcdQ.get()
            print "-------------------------------LCD Display:", LcdText
            LCD.lcd_string(LcdText[0],LCD.LCD_LINE_1)
            LCD.lcd_string(LcdText[1],LCD.LCD_LINE_2)
           
        
def taskBadgeScan():
  
    retcode = SCAN.scanInit()
    while 1:
        badgeId = SCAN.watchPort()  # wait here until a badge is scanned
        eventQ.put( (EVENT_MSG_BADGE_SCAN,badgeId, 0 ) )
        print "\nIn taskBadgeScan - badge scanned event", badgeId

EXPIRED = "00:00"
def taskDeviceAccessControl():
    time_until_expire = ('INIT',EXPIRED)
    while 1:
        
        time.sleep(0.3)
        if not deviceAccessQ.empty():
          time_until_expire = deviceAccessQ.get()
          print "in taskDeviceAccessControl ", time_until_expire
        if time_until_expire[1] == EXPIRED:
          GPIO.output(LOCK_PIN, False)
        else:
          GPIO.output(LOCK_PIN, True)
 
 
#########################################################
STATE_INIT                  = 0
STATE_IDLE                  = 1
STATE_VALIDATE_BADGE        = 2
STATE_USER_LOGGED_IN        = 3   
STATE_IN_USE                = 4   
STATE_LOGGING_OFF           = 5   
STATE_TIMER_EXPIRE          = 6
STATE_INVALID_USER          = 7   
STATE_FAILURE               = 0xf
def stateMachine():
    print "Main State Machine"
    curState = STATE_INIT
    eventMsg = (EVENT_MSG_NULL,"","")
    prevEventMsg = eventMsg
    while(1):
        time.sleep(0.5)
       
        if not eventQ.empty():
            prevEventMsg = eventMsg
            eventMsg = eventQ.get()
            
       
        if curState == STATE_INIT:
            curState = state_init(eventMsg)
           
        elif curState == STATE_IDLE:
            curState = state_idle(eventMsg)
           
        elif curState == STATE_VALIDATE_BADGE:
            curState = state_validate_user_badge(eventMsg)
           
        elif curState == STATE_USER_LOGGED_IN:
            curState = state_user_logged_in(eventMsg)
       
        elif curState == STATE_INVALID_USER:
            eventMsg = prevEventMsg
            curState = state_user_logged_in(eventMsg)
            eventQ.put( eventMsg)
                
        elif curState == STATE_LOGGING_OFF:
            curState = state_logoff_user(eventMsg)
           
#####################################
#
#####################################           
def state_init(eventMsg):
    print "state_init = ", eventMsg
    LcdQ.put( ("WELCOME",time.ctime(time.time())) )
    time.sleep(1)
    if eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        nextState = STATE_VALIDATE_BADGE  
    else: 
        nextState = STATE_IDLE    
    return nextState
 
def state_idle(eventMsg):
    print "state_idle = ", eventMsg
    LcdQ.put( ("SCAN YOUR BADGE", time.ctime(time.time())) )
    time.sleep(1)
    if eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        nextState = STATE_VALIDATE_BADGE
    elif eventMsg[0] == EVENT_MSG_RESET:
        nextState = STATE_INIT
    else: 
        nextState = STATE_IDLE  
    return nextState
 
def state_validate_user_badge(eventMsg):
    print "state_validate_user_badge = ", eventMsg
    LcdQ.put( ("CHECKING BADGE", time.ctime(time.time())) )
    if eventMsg[0] == EVENT_MSG_NULL:
        nextState = STATE_IDLE  
    elif eventMsg[0] == EVENT_MSG_RESET:
        nextState = STATE_INIT 
    elif eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        dbUserValues = {}
        dbUserValues = DB.queryUserNameFromBadgeId(eventMsg[1])
        if (float(dbUserValues['time']) > 0 ):
          timeend = float(dbUserValues['time']) +time.time()
          eventQ.put( (EVENT_MSG_USER_GRANTED_ACCESS, dbUserValues['username'], timeend ) )
          nextState = STATE_USER_LOGGED_IN
        else:
          LcdQ.put( (dbUserValues['username'], ("NOT PERMITTED") ) )
          time.sleep(5)
          nextState = STATE_IDLE
           
    elif eventMsg[0] == EVENT_MSG_TIMER_EXPIRE: 
        nextState = STATE_IDLE  
    else: 
        nextState = STATE_IDLE  
    return nextState
 
def state_user_logged_in(eventMsg):
    print "state_user_logged_in = ", eventMsg
    if eventMsg[0] == EVENT_MSG_RESET:
        deviceAccessQ.put( ("LOGGING OFF", ("00:00") ) )
        nextState = STATE_LOGGING_OFF 
    elif eventMsg[0] == EVENT_MSG_USER_GRANTED_ACCESS:
        logged_in_user_name = eventMsg[1]
        tempname = logged_in_user_name
        time_end = eventMsg[2]
        if time_end < time.time():
          time_remaining = 0;
        else:
          time_remaining = time_end-time.time()

        print " time remaining",(time.ctime( time_remaining ) )[14:19]
        if (time.ctime( time_remaining ) )[14:19] == EXPIRED:  
          LcdQ.put( (logged_in_user_name, (time.ctime( time_remaining ) )[14:19]) )
          deviceAccessQ.put( (logged_in_user_name, (time.ctime( time_remaining ) )[14:19]) )
          nextState = STATE_LOGGING_OFF
        else:  
          LcdQ.put( (logged_in_user_name, (time.ctime( time_remaining ) )[14:19]) )
          deviceAccessQ.put( (logged_in_user_name, (time.ctime( time_remaining ) )[14:19]) )
          nextState = STATE_USER_LOGGED_IN
          
    elif eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        dbUserValues = {}
        dbUserValues = DB.queryUserNameFromBadgeId(eventMsg[1])
        if (float(dbUserValues['time']) > 0 ):
          nextState = STATE_VALIDATE_BADGE
        else:
          LcdQ.put( (dbUserValues['username'], "NOT AUTH TO USE" ) )         
          time.sleep(5)
          nextState = STATE_INVALID_USER
          
    elif eventMsg[0] == EVENT_MSG_TIMER_EXPIRE: 
        nextState = STATE_LOGGING_OFF  
    else: 
        nextState = STATE_IDLE  
    return nextState
 
def state_logoff_user(eventMsg):
    print "state_loggoff_user = ", eventMsg
    LcdQ.put( ("LOGOFF USER", time.ctime(time.time())) )
    time.sleep(1)
    if eventMsg[0] == EVENT_MSG_RESET:
        nextState = STATE_INIT 
    else: 
        nextState = STATE_IDLE  
    return nextState
   
def state_error_report(eventMsg):
    print "state_XXXX = ", eventMsg
    LcdQ.put( ("FAILED", eventMsg[1]) )
    if eventMsg[0] == EVENT_MSG_RESET:
        nextState = STATE_INIT
    elif eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        nextState = STATE_VALIDATE_BADGE
    else: 
        nextState = STATE_FAILURE  
    return nextState
   
############################     
    
 
###########################
#  state XXXX
#############################
def state_XXXX_(eventMsg):
    print "state_XXXX = ", eventMsg
    LcdQ.put( ("XXXX", time.ctime(time.time())) )
    if eventMsg[0] == EVENT_MSG_NULL:
        nextState = STATE_IDLE
    elif eventMsg[0] == EVENT_MSG_RESET:
        nextState = STATE_IDLE 
    elif eventMsg[0] == EVENT_MSG_BADGE_SCAN:
        nextState = STATE_IDLE
    elif eventMsg[0] == EVENT_MSG_TIMER_EXPIRE: 
        nextState = STATE_IDLE  
    else: 
        nextState = STATE_IDLE  
    return nextState
############################   
    
##########################################################
 
####   using    geany ~/../../etc/rc.local 
#### to autolauncn
def main():
    timeout = 3
    print "Hit Enter within ",timeout," sec to skip BADGE access and get command prompt:"
    rlist, _, _ = select([sys.stdin], [], [], timeout)
    if rlist:
        s = sys.stdin.readline()
        print s
        return 0
    else:
        print "No input. Starting BADGE ACCESS APPLICATION"
  
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LOCK_PIN, GPIO.OUT)
    
    taskResetButton_ID=threading.Thread( group=None, target=taskResetButton, name="taskResetButton", args=(), kwargs=None, verbose=None)
    taskResetButton_ID.start()
 
    taskLCD_ID=threading.Thread( group=None, target=taskLCD, name="taskLCD", args=(), kwargs=None, verbose=None)
    taskLCD_ID.start()
 
    taskBadgeScan_ID=threading.Thread( group=None, target=taskBadgeScan, name="taskBadgeScan", args=(), kwargs=None, verbose=None)
    taskBadgeScan_ID.start()
    
    taskDeviceAccessControl_ID=threading.Thread( group=None, target=taskDeviceAccessControl, name="taskDeviceAccessControl", args=(), kwargs=None, verbose=None)
    taskDeviceAccessControl_ID.start()   
 
    stateMachine()
   
    print 'done'
   
 
main()
 
 
