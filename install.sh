#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

dir="/opt/tinkeraccess"

apt-get update
apt-get install -U python-pip
easy_install -U pip
/usr/local/bin/pip install flask

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
cp devicemanager.py $dir

# install the Server startup service
cp scripts/tinkerserver /etc/init.d
chmod 755 /etc/init.d/tinkerserver
update-rc.d tinkerserver defaults 91
service tinkerserver restart

# install the Client startup service
pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client
