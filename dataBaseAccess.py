#!/usr/bin/python
#
# dataBaseAccess.py

import sys
import ConfigParser
import os
import requests


def queryUserNameFromBadgeId(badgeId):
  c = ConfigParser.SafeConfigParser()
  scanConfigPath=os.getcwd()+"/scan.cfg"

  if os.path.isfile(scanConfigPath):
    c.read(scanConfigPath)
    C_server    = c.get('config', 'server')
    C_deviceid  = c.get('config', 'deviceid')
    userData = 'NoUser'
    retData = {'key1':'value1','key2':'value2','key3':'value3','key4':'value4'}
    try:
      #url="%s/user/code/%s" % ( C_server, badgeId )
      url="%s/device/%s/code/%s" % ( C_server,C_deviceid, badgeId )
      print "url=",url
      #userData = requests.get(url,params=payload)
      userData = requests.get(url,params=retData)
      #print("request returned ",userData.text )
      print("request returned ",userData.text )
      
    except ValueError:
      print "Oppps! I could not get the url %s/device/%s/code/%s" % ( C_server, C_deviceid, usercode)
    #return userData.text  
    return userData.json()


def queryUserAccessLevel(userName):
  c = ConfigParser.SafeConfigParser()
  scanConfigPath=os.getcwd()+"/scan.cfg"

  if os.path.isfile(scanConfigPath):
    c.read(scanConfigPath)
    C_server    = c.get('config', 'server')
    C_deviceid  = c.get('config', 'deviceid')
    accessLevel = 'NoUser'
    try:
      url="%s/user/%s/device/C_deviceid" % ( C_server, userName )
      print "url=",url
      accessLevel = requests.get(url)
      print("request returned ",accessLevel.text )
      
    except ValueError:
      print "Oppps! I could not get the url %s/device/%s/code/%s" % ( C_server, C_deviceid, usercode)
    return accessLevel  



