#!/bin/bash
#

dir="/opt/tinkeraccess"

if [ ! -f /usr/local/bin/pip ] ; then
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
fi

/usr/local/bin/pip install --upgrade pip
/usr/local/bin/pip install --upgrade pyserial
/usr/local/bin/pip install flask
/usr/local/bin/pip install requests

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
cp BADGE_SCAN_APP.py $dir
cp badgeScanModule.py  $dir
cp dataBaseAccess.py   $dir
cp devicemanager.py    $dir
cp lcdModule.py $dir
chmod 755 $dir/BADGE_SCAN_APP.py

# install the Server startup service
cp tinkeraccess /etc/init.d
chmod 755 /etc/init.d/tinkeraccess
update-rc.d  tinkeraccess defaults 91
service tinkeraccess restart

# install the Client startup service
cp tinkerclient /etc/init.d
chmod 755 /etc/init.d/tinkerclient
update-rc.d  tinkerclient defaults 91
service tinkerclient restart
