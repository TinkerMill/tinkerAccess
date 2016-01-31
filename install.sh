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
cp server.py $dir
cp server.cfg $dir
chmod 755 $dir/server.py
cp -r static $dir
cp -r templates $dir
cp client.py $dir
cp client.cfg $dir
cp lcdModule.py $dir

# install the Server startup service
cp scripts/tinkerserver /etc/init.d
chmod 755 /etc/init.d/tinkerserver
update-rc.d tinkerserver defaults 91
service tinkerserver restart

# install the Client startup service
cp scripts/tinkerclient /etc/init.d
chmod 755 /etc/init.d/tinkerclient
update-rc.d  tinkerclient defaults 91
service tinkerclient restart
