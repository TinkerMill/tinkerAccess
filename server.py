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
import csv
import re

app = Flask("simpleServer")


c = ConfigParser.SafeConfigParser()
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
else:
  print("config server.cfg not found")
  sys.exit(1)

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

  d = json.dumps({'text': "%s is now available" % output[0][0]  })
  requests.post(C_slackPostUrl, data=d )

  return ""

# given a device and a rfid code return if there is access to that device
# this is the login
@app.route("/device/<deviceid>/code/<code>")
def deviceCode(deviceid,code):
  output = query_db("select user.name, user.id, device.name, deviceAccess.time from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where user.code='%s' and device.id=%s" % (code,deviceid))
  #print output
  if len(output) == 0:
    addNewUser(code, deviceid)
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )
  else:

    # send the data to slack
    d = json.dumps({'text': "%s is now in use by %s" % (output[0][2], output[0][0]) })
    requests.post(C_slackPostUrl, data=d )

    # log it to the database
    exec_db("insert into log (message) values ('login:%s:%s')" % (deviceid, output[0][1]) )

    return json.dumps(
      {'devicename': output[0][2],
       'username': output[0][0],
       'userid': output[0][1],
       'time': output[0][3],
      }
    )


@app.route("/")
def defaultRoute():
  #return redirect("/admin/interface/newuser")
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

  a = query_db("select code from newuser where id=%s" % userid)
  badgeCode = a[0][0]
  userAdd(name,badgeCode)
  exec_db("delete from newuser where id=%s" % userid)

  return redirect("/admin/interface/user")


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

    name = row[0]
    code = row[1]

    # print("Loading", name, code)
    a = query_db("select code from user where code='%s'" % code)
    if len(a) == 0:
      userAdd(name, code)

  return redirect("/admin/interface/user")




"""
when a trainer logs in, he can register anyone on this device as a user
http://localhost:5000/admin/marioStar/1/150060E726B4/0/2
"""
@app.route("/admin/marioStar/<trainerid>/<trainerBadge>/<deviceid>/<userBadge>")
def marioStarMode(trainerid,trainerBadge, deviceid, userBadge):  
  trainer = query_db("select user.id from user join deviceAccess on deviceAccess.user=user.id  where user.id=%s and user.code='%s' and deviceAccess.trainer=1 and deviceAccess.device=%s" % (trainerid, trainerBadge,deviceid))
  
  # the user must already exist in the system
  userid = query_db("select id from user where code='%s'" % (userBadge) )

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
  return redirect("/admin/interface/user")

@app.route("/admin/delUser/<userid>")
def delUser(userid):
  if request.cookies.get('password') != C_password:
    return False

  exec_db("delete from user where id=%s" % userid)
  return redirect("/admin/interface/user")

@app.route("/admin/interface/newuser")
def newUserInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select id,code,deviceID from newuser")
  return render_template('admin_newuser.html', users=users)

@app.route("/admin/interface/user")
def adminInterface():
  if request.cookies.get('password') != C_password:
    return redirect("/")

  users = query_db("select name,code,id from user")
  return render_template('admin_user.html', users=users)

@app.route("/admin/interface/userAccess/<userid>")
def userAccessInterface(userid):
  if request.cookies.get('password') != C_password:
    return redirect("/")

  # list of all the devices
  allDevices = query_db("select id,name from device")

  # list of devices user has access to
  userAccess = query_db("select user.name, user.id, device.id, device.name, deviceAccess.time, deviceAccess.trainer from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where deviceAccess.user=%s" % userid)
  username   = query_db("select user.name from user where id=%s" % userid)[0][0]
  return render_template('admin_userAccess.html', devices=allDevices, access=userAccess, userid=userid, username=username)

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

if __name__ == "__main__":
  #app.run(host='0.0.0.0')
  app.run(host='0.0.0.0', debug=True)
