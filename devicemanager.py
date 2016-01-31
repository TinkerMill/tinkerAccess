#!/usr/bin/python

import sqlite3
import optparse
import sys

parser = optparse.OptionParser()
parser.add_option("-a", "--add", default=False,  help='add a device', dest="addDevice", action="store_true")
parser.add_option("-n", "--name", default=False,  help='name of device', dest="deviceName", action="store")
parser.add_option("-i", "--id", default=False,  help='id of device', dest="deviceId", action="store")
parser.add_option("-d", "--delete", default=False, help='delete device', dest="delDevice", action="store_true")
parser.add_option("-l", "--list", default=False , help='list devices', dest="deviceList", action="store_true")
parser.add_option("-r", "--rename", default=False , help='rename device id(-i) to name(-n)', dest="rename", action="store_true")
(opts, args) = parser.parse_args()

db = sqlite3.connect('db.db')

if opts.deviceList:
  cur = db.execute("select * from device")
  print("{: >5} {: >30}".format("ID", "Device Name"))
  for rec in cur.fetchall():
    print("{: >5} {: >30}".format(rec[0], rec[1]))

if opts.addDevice:
  if not opts.deviceName:
    print("Required name use -n option")
    sys.exit()

  db.cursor().execute("insert into device (name) values ('%s')" % opts.deviceName )
  db.commit()

if opts.delDevice:
  if not opts.deviceId:
    print("Required ID of device -i option")
    sys.exit()

  db.cursor().execute("delete from device where id=%s" % opts.deviceId)
  db.cursor().execute("delete from deviceAccess where device=%s" % opts.deviceId)
  db.commit()


if opts.rename:
  if not opts.deviceId:
    print("Required ID of device to rename -i option")
    sys.exit()
  if not opts.deviceName:
    print("Required name to rename to -n option")
    sys.exit
  db.cursor().execute("update device set name='%s' where id=%s" % (opts.deviceName, opts.deviceId) )
  db.commit()
