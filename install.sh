#!/bin/bash
#

dir="/opt/tinkeraccess"

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
cp -r static $dir
cp -r templates $dir
cp devicemanager.py $dir
cp scan.py $dir
cp scan.cfg $dir

# install the startup service
cp tinkeraccess /etc/init.d
chkconfig --add  tinkeraccess
chkconfig tinkeraccess on
service tinkeraccess restart
