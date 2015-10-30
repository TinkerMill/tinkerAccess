#!/bin/bash
#

dir="/opt/tinkeraccess"

if [ ! -f /usr/bin/sqlite3 ] ; then
apt-get update
apt-get install sqlite3
fi

# if the directory doesn't exist create it
if [ ! -d $dir ] ; then
		mkdir -p $dir
fi

# if the database doesn't exist create it
if [ ! -f $dir/db.db ] ; then
		sqlite3 $dir/db.db < schema.sql
fi

# copy over the file we need
cp serv.py $dir
chmod 755 $dir/serv.py
cp -r static $dir
cp -r templates $dir
cp devicemanager.py $dir
cp run.cfg $dir
cp scan.py $dir
cp scan.cfg $dir

# install the startup service
cp tinkeraccess /etc/init.d
chmod 755 /etc/init.d/tinkeraccess
update-rc.d  tinkeraccess defaults 91
service tinkeraccess restart
