#!/usr/bin/python

# http://flask.pocoo.org/docs/0.10/patterns/sqlite3/
# http://ryrobes.com/python/running-python-scripts-as-a-windows-service/
# http://stackoverflow.com/questions/23550067/deploy-flask-app-as-windows-service
# http://gouthamanbalaraman.com/blog/minimal-flask-login-example.html

from flask import Flask,g,request,render_template,redirect
import sqlite3
import ConfigParser
import sys
import os
import os.path
import json
import requests
import base64
import csv
import re
from collections import defaultdict, namedtuple
import datetime
from calendar import monthrange
import logging
from threading import Thread

app = Flask("simpleServer")


c = ConfigParser.ConfigParser()
configPath=None

for p in ["/opt/tinkeraccess/server.cfg", "server.cfg"]:
  if os.path.isfile(p):
    configPath=p
    break

if configPath:
  c.read(configPath)
  C_password = c.get('config', 'password')
  C_database = c.get('config', 'db') 
  C_slackPostUrl = c.get('config', 'slackurl')
  c_webcam_username = None
  c_webcam_password = None
  c_imgur_client_id = None
  if c.has_option('config', 'webcam_username'): c_webcam_username = c.get('config', 'webcam_username')
  if c.has_option('config', 'webcam_password'): c_webcam_password = c.get('config', 'webcam_password')
  if c.has_option('config', 'imgur_client_id'): c_imgur_client_id = c.get('config', 'imgur_client_id')

  c_webcam_urls = dict()
  if c.has_section('webcam_urls'):
    if c_webcam_username is None or c_webcam_password is None or c_imgur_client_id is None:
        print("To post webcam images, `webcam_username`, `webcam_password`,\n" +
              "and `imgur_client_id` must all be specified in the `config`\n" +
              "section")
    else: c_webcam_urls = dict(c.items(section='webcam_urls'))

else:
  print("config server.cfg not found")
  sys.exit(1)


######### Slack function #############

def post_to_slack(message):
  try:
    requests.post(C_slackPostUrl, data=json.dumps(message))
  except Exception as e:
    logging.exception(e)

######### Database functions #########

def init_db():
  with app.app_context():
    if os.path.isfile("/opt/tinkeraccess/db.db"):
      os.remove("/opt/tinkeraccess/db.db")

    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

def exec_db(query):
  db = get_db()
  db.cursor().execute(query)
  db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(C_database)
    return db

def insert(table, fields=(), values=()):
  # g.db is the database connection
  cur = get_db().cursor()
  query = 'INSERT INTO %s (%s) VALUES (%s)' % (
  table,
    ', '.join(fields),
    ', '.join(['?'] * len(values))
  )
  cur.execute(query, values)
  get_db().commit()
  id = cur.lastrowid
  cur.close()
  return id

def addNewUser(code, deviceid):
  o = query_db("select code from newuser where code='%s'" % code)
  if len(o) == 0:
    o = query_db("select code from user where code='%s'" % code)
    if len(o) == 0:
      exec_db("insert into newuser (code,deviceID) values ('%s', %s)" % (code, deviceid) )


######### Webserver functions #########

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# logout
@app.route("/device/<deviceid>/logout/<uid>")
def deviceLogout(deviceid, uid):
  output = query_db("select device.name from device where id=%s" % deviceid)
  exec_db("insert into log (message) values ('logout:%s:%s')" % (deviceid,uid) )

  message_content = {'text': '{} is now available'.format(output[0][0])}
  if output[0][0] in c_webcam_urls:
      image_url = captureImage(c_webcam_urls[output[0][0]])
      if len(image_url) > 0:
          message_content['attachments'] = [{
              'fallback': 'Webcam image of {}'.format(output[0][0]),
              'image_url': image_url
              }]

  t = Thread(target=post_to_slack, args=(message_content,))
  t.start()

  return ""

# given a device and a rfid code return if there is access to that device
# this is the login
@app.route("/device/<deviceid>/code/<code>")
def deviceCode(deviceid,code):

  deviceinfo = query_db("select name,allUsers,lockout,lockout_start,lockout_end from device where id=%s" % deviceid)
  
  if len(deviceinfo) == 0:
    # Device ID not found, so deny access
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )

  devicename    = deviceinfo[0][0]
  allusers      = deviceinfo[0][1]
  lockout       = deviceinfo[0][2]
  lockout_start = deviceinfo[0][3]
  lockout_end   = deviceinfo[0][4]

  if lockout == 2:
    # Device is locked out, so deny access
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )

  # Customize the query based upon the device settings
  if lockout == 0:
    # Device access is not time limited

    if allusers:
      # Device access is granted to all users and is not time limited
      output = query_db("select user.name, user.id from user where user.code='%s' and user.status IN ('A','S')" % (code))
      
    else:
      # Device access is granted at an individual user level and is not time limited
      output = query_db("select user.name, user.id, deviceAccess.time from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user \
                         where user.code='%s' and user.status IN ('A','S') and device.id=%s" % (code,deviceid))

  elif lockout == 1:
    # Device access is time limited

    now = datetime.datetime.now()
    now = 100 * now.hour + now.minute

    x = re.split(':| ',lockout_start)
    start_time = 100*((int(x[0]) % 12) + (12 if x[2]=="PM" else 0)) + int(x[1])

    x = re.split(':| ',lockout_end)
    end_time = 100*((int(x[0]) % 12) + (12 if x[2]=="PM" else 0)) + int(x[1])
    
    if start_time <= end_time:
      during_time_limit = start_time <= now < end_time
    else:
      during_time_limit = now >= start_time or now < end_time

    if during_time_limit:
      # Current time is during the time limited range, only select those with 24hr access

      if allusers:
        # Device access is granted to all users only with 24 hr access during time limited range
        output = query_db("select user.name, user.id from user where user.code='%s' and user.status='S'" % (code))

      else:
        # Device access is granted at an individual user level only with 24 hr access during time limited range
        output = query_db("select user.name, user.id, deviceAccess.time from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user \
                          where user.code='%s' and user.status='S' and device.id=%s" % (code,deviceid))

    else:
      # Device access is time limited but current time is not within the range

      if allusers:
        # Device access is granted to all users, outside the time limited range
        output = query_db("select user.name, user.id from user where user.code='%s' and user.status IN ('A','S')" % (code))

      else:
        #  Device access is granted at an individual user level, outside the time limited range
        output = query_db("select user.name, user.id, deviceAccess.time from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user \
                          where user.code='%s' and user.status IN ('A','S') and device.id=%s" % (code,deviceid))

  else:
    # Unknown lockout status, deny access
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )
    
  if len(output) == 0:
    # User badge code not found, or is inactive, or does not have 24hr access, so deny access
    addNewUser(code, deviceid)
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )
      
  # User badge code found, so grant access

  username = output[0][0]
  userid   = output[0][1]
  accesstime = 100 if allusers else output[0][2]
  
  if lockout == 1:
    # post to slack only if device access is time limited
    message_content = {'text': '{} is now in use by {}'.format(devicename, username)}
    if devicename in c_webcam_urls:
      image_url = captureImage(c_webcam_urls[devicename])
      if len(image_url) > 0:
        message_content['attachments'] = [{
          'fallback': 'Webcam image of {}'.format(devicename),
          'image_url': image_url
        }]

    t = Thread(target=post_to_slack, args=(message_content,))
    t.start()

  # log it to the database
  exec_db("insert into log (message) values ('login:%s:%s')" % (deviceid, userid) )

  return json.dumps(
    {
      'devicename': devicename,
      'username': username,
      'userid': userid,
      'time': accesstime
    }
  )

@app.route("/")
def defaultRoute():
  return render_template('admin_login.html')

@app.route("/checkLogin/<user>/<password>" )
def checkLogin(user,password):
  if password == C_password:
    return "true"
  else:
    return "false"

# given a name and badge code, add the user to the database
# and clear out any perms that id might have had in the past
def userAdd(name, badgeCode):
  exec_db("insert into user (name,code) values ('%s','%s')" % (name, badgeCode))

  # if the database is dirty, make sure that any existing records are cleared out
  userAccess = query_db("select id from user where code='%s'" % badgeCode)
  if len(userAccess) > 0:
    exec_db("delete from deviceAccess where user=%s" % userAccess[0][0] )

@app.route("/admin/addUser/<userid>/name/<name>")
def addUser(userid, name):
  if request.cookies.get('password') != C_password:
    return False

  name = name.strip()
  output = query_db("select code from newuser where id=%s" % userid)
  badgeCode = output[0][0]

  output = query_db("select code from user where name='%s' and status IN ('A','S')" % name)
  
  if len(output) == 0:
    # No active user with same name, go ahead and add this user id
    userAdd(name,badgeCode)
    exec_db("delete from newuser where id=%s" % userid)
    return redirect("/admin/interface/user")
  else:
    # User with same name already active, popup error window
    existingBadge = output[0][0]
    return redirect("/admin/interface/newuser/modal/useractive/%s/%s/%s" % (name, existingBadge, badgeCode))
  
@app.route("/admin/loadcsv", methods=['POST'])
def loadCSV():
  if request.cookies.get('password') != C_password:
    return False

  data = request.form['csv']

  # stip leading , if it is there
  data = map(lambda x: re.sub('^,', '', x), data.split("\n"))
  reader = csv.reader(data, delimiter=',')
  for row in reader:
    if len(row) == 0:
      continue

    name = row[0].strip()
    code = row[1].strip()

    output = query_db("select code from user where code='%s'" % code)
    if len(output) == 0:
      # Badge does not already exist in database
      output = query_db("select name from user where name='%s' and status IN ('A','S')" % name)
      if len(output) == 0:
        # Name does not exist in database of an active user
        userAdd(name, code)
        
  return redirect("/admin/interface/user")


"""
when a trainer logs in, he can register anyone on this device as a user
http://localhost:5000/admin/marioStar/1/150060E726B4/0/2
"""
@app.route("/admin/marioStar/<trainerid>/<trainerBadge>/<deviceid>/<userBadge>")
def marioStarMode(trainerid,trainerBadge, deviceid, userBadge):
  trainer = query_db("select user.id from user join deviceAccess on deviceAccess.user=user.id where user.id=%s and user.code='%s' and user.status IN ('A','S') and deviceAccess.trainer=1 and deviceAccess.device=%s" % (trainerid, trainerBadge, deviceid))
  
  # the user must already exist in the system
  userid = query_db("select id from user where code='%s' and status IN ('A','S')" % (userBadge) )

  #print("userId", userid)
  #print("lenUserId=1", len(userid))
  #print("trainer", trainer)
  #print("lentrainer=1", len(trainer))

  if len(userid) == 1 and len(trainer) == 1:
    userid = userid[0][0]
    exec_db("delete from deviceAccess where user=%s and device=%s" % (userid, deviceid))
    exec_db("insert into deviceAccess (user,device,time) values (%s, %s, 100)" % (userid, deviceid))
    return "true"
  else:
    return "false"

@app.route("/admin/addUserAccess/<userid>/<deviceid>")
def addUserAccess(userid, deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("delete from deviceAccess where user=%s and device=%s" % (userid, deviceid))
  exec_db("insert into deviceAccess (user,device,time) values (%s, %s, 100)" % (userid, deviceid))
  return redirect("/admin/interface/userAccess/%s" % userid)

@app.route("/admin/toggle24Hr/user/<userid>")
def toggle24HrAccess(userid):
  if request.cookies.get('password') != C_password:
    return False

  output = query_db("select status from user where id=%s" % userid)

  if output[0][0] == 'A':
    exec_db("update user set status='S' where id=%s" % userid)
  elif output[0][0] == 'S':
    exec_db("update user set status='A' where id=%s" % userid)
  
  return redirect("/admin/interface/userAccess/%s" % userid)

@app.route("/admin/removeTrainer/<userid>/<deviceid>")
def delUserTrainerAccess(userid, deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update deviceAccess set trainer=0 where user=%s and device=%s" % (userid, deviceid))
  return redirect("/admin/interface/userAccess/%s" % userid)

@app.route("/admin/addTrainer/<userid>/<deviceid>")
def addUserTrainerAccess(userid, deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update deviceAccess set trainer=1 where user=%s and device=%s" % (userid, deviceid))
  return redirect("/admin/interface/userAccess/%s" % userid)

@app.route("/admin/delUserAccess/<userid>/<deviceid>")
def delUserAccess(userid, deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("delete from deviceAccess where user=%s and device=%s" % (userid, deviceid))
  return redirect("/admin/interface/userAccess/%s" % userid)

@app.route("/admin/delNewUser/<userid>")
def delNewUser(userid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("delete from newuser where id=%s" % userid)
  return redirect("/admin/interface/newuser")

@app.route("/admin/delUser/<userid>")
def delUser(userid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("delete from user where id=%s" % userid)
  return redirect("/admin/interface/inactiveuser")

@app.route("/admin/activateUser/<userid>")
def activateUser(userid):
  if request.cookies.get('password') != C_password:
    return False

  # Get the name and badge code to be activated
  output = query_db("select name,code from user where id=%s" % userid)

  name = output[0][0]
  newbadge = output[0][1]

  output = query_db("select code from user where name='%s' and status IN ('A','S')" % name)
  
  if len(output) == 0:
    # No active user with same name, make this user id active
    exec_db("update user set status='A' where id=%s" % userid)
    return redirect("/admin/interface/inactiveuser")
  else:
    # User with same name already active, popup error window
    badge = output[0][0]
    return redirect("/admin/interface/inactiveuser/modal/useractive/%s/%s/%s" % (name, badge, newbadge))

@app.route("/admin/deactivateUser/<userid>")
def deactivateUser(userid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update user set status='I' where id=%s" % userid)
  return redirect("/admin/interface/user")

@app.route("/admin/deviceUnlimitedHr/<deviceid>")
def deviceUnlimitedHr(deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update device set lockout=0 where id=%s" % deviceid)
  return redirect("/admin/interface/devices")

@app.route("/admin/deviceLimitedHr/<deviceid>")
def deviceLimitedHr(deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update device set lockout=1 where id=%s" % deviceid)
  return redirect("/admin/interface/devices")

@app.route("/admin/deviceLockout/<deviceid>")
def deviceLockout(deviceid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update device set lockout=2 where id=%s" % deviceid)
  return redirect("/admin/interface/devices")

@app.route("/admin/deviceLockoutTimes/<deviceid>/time/<start>/<end>")
def deviceLockoutTimes(deviceid, start, end):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("update device set lockout_start='%s', lockout_end='%s' where id=%s" % (start, end, deviceid))
  return redirect("/admin/interface/devices")

@app.route("/admin/interface/newuser")
def newUserInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select newuser.id,newuser.code,device.name from newuser left join device on newuser.deviceID = device.id")
  #users = query_db("select id,code,deviceID from newuser")
  return render_template('admin_newuser.html', users=users)

@app.route("/admin/interface/inactiveuser")
def inactiveUserInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select name,code,id from user where status='I' order by name")
  return render_template('admin_inactiveuser.html', users=users)

@app.route("/admin/interface/inactiveuser/modal/deluser/<userid>/<name>/<badge>")
def delUserModal(userid, name, badge):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select name,code,id from user where status='I' order by name")
  return render_template('modal_deluser.html', users=users, userid=userid, name=name, badge=badge)

@app.route("/admin/interface/inactiveuser/modal/useractive/<name>/<badge>/<newbadge>")
def userActiveModal(name, badge, newbadge):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select name,code,id from user where status='I' order by name")
  return render_template('modal_useractive.html', users=users, name=name, badge=badge, newbadge=newbadge)

@app.route("/admin/interface/newuser/modal/useractive/<name>/<badge>/<newbadge>")
def newuserActiveModal(name, badge, newbadge):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select id,code,deviceID from newuser")
  return render_template('modal_newuseractive.html', users=users, name=name, badge=badge, newbadge=newbadge)

@app.route("/admin/interface/user")
def adminInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select name,code,id,status from user where status IN ('A','S') order by status desc")
  return render_template('admin_user.html', users=users)

@app.route("/admin/interface/userAccess/<userid>")
def userAccessInterface(userid):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  # list of all the devices the user could have access to
  allDevices = query_db("select id, name from device where allUsers=0 except select device.id, device.name from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where deviceAccess.user=%s and device.allUsers=0" % userid)

  # list of devices with all user access
  allUserDevices = query_db("select name from device where allUsers=1")
  
  # list of devices the user currently has access to
  userAccess = query_db("select user.name, user.id, device.id, device.name, deviceAccess.time, deviceAccess.trainer from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where deviceAccess.user=%s and device.allUsers=0" % userid)
  
  username   = query_db("select user.name from user where id=%s" % userid)[0][0]

  s = query_db("select user.status from user where id=%s" % userid)[0][0]
  if s=='A':
    userstatus = "Active"
  elif s=='S':
    userstatus = "Active - 24 Hr"
  elif s=='I':
    userstatus = "Inactive"
  else:
    userstatus = "Unknown"
    
  return render_template('admin_userAccess.html', devices=allDevices, access=userAccess, alluserdevices=allUserDevices, userid=userid, username=username, userstatus=userstatus, ustatus=s)

@app.route("/admin/interface/devices")
def deviceInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  devices = query_db("select id,name,allUsers,lockout,lockout_start,lockout_end from device")
  return render_template('admin_devices.html', devices=devices)

@app.route("/admin/interface/deviceAccess/<deviceid>")
def deviceAccessInterface(deviceid):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  devicename = query_db("select device.name from device where id=%s" % deviceid)[0][0]
  userAccess = query_db("select user.id, user.name, user.code, deviceAccess.trainer from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where deviceAccess.device=%s and device.allUsers=0 and user.status IN ('A','S') order by deviceAccess.trainer desc" % deviceid)
  
  return render_template('admin_deviceAccess.html', access=userAccess, deviceid=deviceid, devicename=devicename)

@app.route("/toolSummary")
@app.route("/toolSummary/<start_date>")
@app.route("/toolSummary/<start_date>/<end_date>")
def toolSummaryInterface(start_date=None, end_date=None):
  #if request.cookies.get('password') != C_password:
  #  return redirect("/")

  # calculate default start and end dates
  if start_date is None:
    today = datetime.datetime.now()
    start_date = datetime.datetime(today.year - (today.month==1), ((today.month - 2)%12)+1, 1)
  else:
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

  if end_date is None:
    end_year = start_date.year + (start_date.month==12)
    end_month = ((start_date.month+1)%12)
    end_day = min(start_date.day, monthrange(end_year, end_month)[1])
    end_date = datetime.datetime(end_year, end_month, end_day)
  else:
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

  tool_summary = genToolSummary(start_date, end_date)
  return render_template('toolUse.html', tools = tool_summary,
          start = start_date.strftime("%Y-%m-%d"),
          end = end_date.strftime("%Y-%m-%d"))

@app.route("/admin/interface/log")
def viewLog():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  logs = query_db("select * from log")
  return render_template('admin_log.html', logs=logs)

@app.route("/admin/interface/csv")
def csvHTMLInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")
  
  return render_template('admin_csv.html')

#### Helper functions for tool summary ####

# define some classes for data records
class ToolSummary:
  __slots__ = ['logins', 'logouts', 'total_time']
  def __init__(self, logins=0, logouts=0, total_time=datetime.timedelta()):
    self.logins = logins
    self.logouts = logouts
    self.total_time = total_time

  def __repr__(self):
    return "ToolSummary(logins={}, logouts={}, total_time={})".format(
        self.logins, self.logouts, self.total_time)

class ToolState:
  __slots__ = ['in_use', 'active_user', 'login_time']
  def __init__(self, in_use=False, active_user=0, login_time=0):
    self.in_use = in_use
    self.active_user = active_user
    self.login_time = login_time

class UserToolSummary:
  __slots__ = ['name', 'logins', 'total_time']
  def __init__(self, name='', logins=0, total_time=datetime.timedelta()):
    self.name = ''
    self.logins = logins
    self.total_time = total_time

  def __repr__(self):
    return "UserToolSummary(logins={}, total_time={})".format(
        self.logins, self.total_time)

  def __lt__(self, other):
    return self.total_time < other.total_time

class DefaultDictByKey(dict):
    def __init__(self, message):
        self.message = str(message)

    def __missing__(self, key):
        return self.message+str(key)

def genToolSummary(start_date, end_date):
  '''Function to generate tool summaries given start and end dates
        Input: start_date, end_date; defaults to "last month"
        Output: Dictionary of tools, with associated summaries'''

  tools = query_db("SELECT id, name FROM device")
  toolnames = {}
  for tool in tools:
    toolnames[str(tool[0])] = tool[1]

  users = query_db("SELECT id, name, code FROM user")
  user_id_to_name = DefaultDictByKey("Unknown user, id ")
  user_code_to_id = {}
  for user in users:
    user_id_to_name[str(user[0])] = str(user[1])
    user_code_to_id[str(user[2])] = str(user[0])

  # generate summaries
  msgs = query_db("SELECT message, Timestamp FROM log WHERE Timestamp BETWEEN ? AND ?", (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

  summaries = defaultdict(ToolSummary)
  states = defaultdict(ToolState)
  user_summaries = defaultdict(UserToolSummary)

  other_msgs = 0;

  unmatched = 0
  for msg in msgs:
    ts = datetime.datetime.strptime(msg[1], '%Y-%m-%d %H:%M:%S')
    fields = msg[0].split(':')
    if (len(fields) != 3) or (fields[0] not in ('login', 'logout')):
      other_msgs += 1
      continue

    tool = fields[1]
    user = fields[2]
    if fields[0] == 'login':
      summaries[tool].logins += 1
      if states[tool].in_use:
        pass
        #print('Login without logout: ', ts, toolnames[tool],
            #user_id_to_name[user], states[tool].login_time)
      states[tool].in_use = True
      states[tool].active_user = user
      states[tool].login_time = ts
      user_summaries[(user, tool)].logins += 1
      user_summaries[(user, tool)].name = user_id_to_name[user]
    elif fields[0] == 'logout':
      try:
        user_id = user_code_to_id[user]
      except KeyError:
        if states[tool].in_use:
          user_id = states[tool].active_user
          user_code_to_id[user] = user_id
          print(("Unknown user, code {}. Assuming user id {} from "+
                  "prior tool login").format(user, user_id))
        else:
          print("Unknown user, code", user)

      summaries[tool].logouts += 1
      if not states[tool].in_use:
        pass
        #print('Logout without login: ', ts, toolnames[tool],
        #    user_id_to_name[user])
      else:
        states[tool].in_use = False
        summaries[tool].total_time += (ts - states[tool].login_time)
        if states[tool].active_user == user_id:
          user_summaries[(user_id, tool)].total_time += (ts - states[tool].login_time)
        else:
          unmatched += 1

  leaderboards = defaultdict(list)
  for ((_, tool), s) in user_summaries.items():
    leaderboards[tool].append(s)

  #print('non-login/logout messages:', other_msgs)
  #print('unmatched login/logout pairs:', unmatched)

  out_sum = dict()
  for (tool, s) in summaries.items():
    out_sum[tool] = dict()
    out_sum[tool]['name'] = toolnames[tool]
    out_sum[tool]['logins'] = s.logins
    out_sum[tool]['logouts'] = s.logouts
    out_sum[tool]['total'] = s.total_time
    out_sum[tool]['leaderboard'] = list()

    leaderboards[tool].sort()
    for s in list(reversed(leaderboards[tool]))[:10]:
      out_sum[tool]['leaderboard'].append((s.name, s.total_time))

  return out_sum

def captureImage(webcam_url):
    """Capture image from webcam and upload to Imgur; returns Imgur URL"""

    # grab image from webcam
    dl_resp = requests.get(webcam_url, auth=(c_webcam_username, c_webcam_password))
    if dl_resp.status_code != 200: 
        print("Webcam download status code:", dl_resp.status_code)
        print(dl_resp.text)
        return ""
    img_b64 = base64.b64encode(dl_resp.content)

    # upload to Imgur
    ul_resp = requests.post(
            'https://api.imgur.com/3/image',
            headers = {'Authorization': 'Client-ID ' + c_imgur_client_id},
            data = {'image': img_b64})
    if (ul_resp.status_code != 200):
        print("Imgur upload status code:", ul_resp.status_code)
        print(ul_resp.text)
        return ""
    return ul_resp.json()['data']['link']

if __name__ == "__main__":
  #app.run(host='0.0.0.0')
  use_reload = not (len(sys.argv) > 1 and sys.argv[1] == '--noreload')
  app.run(host='0.0.0.0', debug=True, use_reloader=use_reload)
