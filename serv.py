#!/usr/bin/python

# http://flask.pocoo.org/docs/0.10/patterns/sqlite3/
# http://ryrobes.com/python/running-python-scripts-as-a-windows-service/
# http://stackoverflow.com/questions/23550067/deploy-flask-app-as-windows-service

from flask import Flask,g,request,render_template
import sqlite3
import ConfigParser
import sys
import os
import json

app = Flask("simpleServer")

c = ConfigParser.SafeConfigParser()
if os.path.isfile("run.cfg"):
  c.read('run.cfg')
  #C_database = c.get('config', 'database')
  #C_password = c.get('config', 'password')
  C_database = "db.db"
else:
  print("config run.cfg not found")
  sys.exit(1)

def init_db():
  with app.app_context():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
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

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



# given a device and a rfid code return if there is access to that device
@app.route("/device/<deviceid>/code/<code>")
def deviceCode(deviceid,code):
  output = query_db("select user.name, user.id, device.name, deviceAccess.time from deviceAccess join device on device.id=deviceAccess.device join user on user.id = deviceAccess.user where user.code='%s' and device.id=%s" % (code,deviceid))

  print output
  if len(output) == 0:
    return json.dumps( {'devicename': 'none', 'username': 'none', 'userid': -1, 'time': 0 } )
  else:
    return json.dumps(
      {'devicename': output[0][2],
       'username': output[0][0],
       'userid': output[0][1],
       'time': output[0][3],
      }
    )


@app.route("/admin/interface/user")
def adminInterface():
  users = query_db("select user.name, device.name  from user inner join userAccess on userAccess.user = user.id inner join device on userAccess.device = device.id order by user.name")
  data = {}
  for  user in users:
    if user[0] in data:
      data[user[0]].append(user[1])
    else:
      data[user[0]] = [ user[1] ]

  return render_template('admin_user.html', users=data)


if __name__ == "__main__":
  #app.run(host='0.0.0.0')
  app.run(host='127.0.0.1', debug=True)
